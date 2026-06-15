"""VarQC (Variational Quality Control) 数据同化算法.

变分质量控制同化将观测质量控制和同化分析同时进行，
通过修改代价函数自动识别和剔除异常观测。

算法原理:
  标准变分代价函数:
    J(x) = 0.5 * (x - xb)^T B^{-1} (x - xb)
         + 0.5 * (Hx - y)^T R^{-1} (Hx - y)

  VarQC 代价函数（使用概率密度函数描述观测误差）:
    J(x) = 0.5 * (x - xb)^T B^{-1} (x - xb)
         + 0.5 * sum_j [ -2 * log( p(y_j | Hx_j) ) ]

  其中 p(y_j | Hx_j) 是混合概率密度:
    p(d) = (1-p_g) * N(d; 0, sigma_o^2) + p_g * c_g

  - d = y_j - Hx_j: 新息（观测残差）
  - p_g: 坏观测的先验概率
  - c_g: 坏观测的均匀分布概率密度
  - sigma_o: 观测误差标准差

  通过变分方法，坏观测的权重自动降低，实现质量控制。

参考文献:
  Andersson and Jarvinen (1999), Tellus, 51A, 730-744
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class VarQC:
    """变分质量控制同化 (VarQC) 数据同化算法.

    特点:
    1. 观测质量控制和同化同时进行
    2. 使用概率密度函数描述观测误差
    3. 自动识别和剔除异常观测
    4. 支持高斯+均匀混合分布模型
    5. 提供观测质量诊断信息

    配置参数:
        gross_error_prob: 坏观测先验概率
        qc_threshold: 质量控制阈值（标准差倍数）
        background_error_scale: 背景误差标准差
        observation_error_scale: 观测误差标准差
        max_iterations: 最大迭代次数
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        # 网格配置
        self.grid_shape: tuple[int, ...] = self.config.get("grid_shape", (10, 10, 5))
        self.resolution: float = self.config.get("resolution", 50.0)

        # 优化器配置
        self.max_iterations: int = self.config.get("max_iterations", 50)
        self.tolerance: float = self.config.get("tolerance", 1e-6)
        self.learning_rate: float = self.config.get("learning_rate", 0.01)

        # 背景误差配置
        self.sigma_b: float = self.config.get("sigma_b", 1.0)
        self.observation_error_scale: float = self.config.get("observation_error_scale", 0.1)

        # 质量控制配置
        self.gross_error_prob: float = self.config.get("gross_error_prob", 0.05)
        self.qc_threshold: float = self.config.get("qc_threshold", 5.0)
        self.flat_distribution_width: float = self.config.get("flat_distribution_width", 10.0)

        # 质量控制模式
        self.qc_mode: str = self.config.get("qc_mode", "variational")
        # "variational": 变分质量控制
        # "pre_check": 预检查质量控制（先剔除再同化）
        # "post_check": 后检查质量控制（先同化再剔除）

    # ================================================================
    # 公共接口
    # ================================================================

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行VarQC变分质量控制同化.

        Args:
            params: 分析参数字典，包含:
                - background_field: 背景场 (numpy.ndarray)
                - observations: 观测数据列表，每个元素包含:
                    - position: 观测位置
                    - value: 观测值
                    - error: 观测误差（可选）
                    - quality_flag: 观测质量标记（可选）
                - qc_mode: 质量控制模式（可选）
                - gross_error_prob: 坏观测概率（可选）

        Returns:
            包含分析场、质量控制结果、观测权重等信息的字典
        """
        mode = params.get("qc_mode", self.qc_mode)
        self.gross_error_prob = params.get(
            "gross_error_prob", self.gross_error_prob
        )

        if mode == "pre_check":
            return self._pre_check_assimilation(params)
        elif mode == "post_check":
            return self._post_check_assimilation(params)
        else:
            return self._variational_qc_assimilation(params)

    # ================================================================
    # 变分质量控制
    # ================================================================

    def _variational_qc_assimilation(
        self, params: dict[str, Any]
    ) -> dict[str, Any]:
        """变分质量控制同化: 在代价函数中同时进行质量控制.

        使用混合概率密度函数替代标准高斯分布:
        p(d) = (1-p_g) * N(d; 0, sigma^2) + p_g * c_g

        代价函数:
        J(x) = J_b + sum_j [-log(p(d_j))]
        """
        background = np.asarray(
            params.get("background_field", np.zeros(self.grid_shape)),
            dtype=float,
        )
        observations = params.get("observations", [])

        xb = background.flatten()
        n_state = len(xb)
        x = xb.copy()

        # 构建观测算子
        y_obs, H, obs_errors = self._build_observation_operator_with_errors(  # noqa: N806
            xb, observations, background.shape
        )
        m = len(y_obs)

        # 构建背景误差矩阵
        B_inv = np.eye(n_state) / self.sigma_b**2  # noqa: N806

        cost_history: list[float] = []
        obs_weights_history: list[list[float]] = []

        for i in range(self.max_iterations):
            dx = x - xb

            # J_b: 背景约束项
            J_b = 0.5 * float(dx @ B_inv @ dx)  # noqa: N806

            # J_o: 观测约束项（VarQC版本）
            J_o = 0.0  # noqa: N806
            grad_o = np.zeros(n_state)
            obs_weights: list[float] = []

            for j in range(m):
                Hx_j = H[j, :] @ x  # noqa: N806
                d_j = y_obs[j] - Hx_j  # 新息
                sigma_j = obs_errors[j]

                # 计算混合概率密度
                p_good = self._gaussian_pdf(d_j, 0.0, sigma_j)
                p_bad = 1.0 / self.flat_distribution_width
                p_total = (1.0 - self.gross_error_prob) * p_good + self.gross_error_prob * p_bad

                # 避免零概率
                p_total = max(p_total, 1e-300)

                # 代价函数贡献: -log(p(d_j))
                J_o += -np.log(p_total)  # noqa: N806

                # 梯度贡献: d(-log p)/dx = (d/d) * H^T * dp/dd / p
                dp_dd = (1.0 - self.gross_error_prob) * (
                    -d_j / sigma_j**2
                ) * p_good
                grad_contribution = dp_dd / p_total
                grad_o += grad_contribution * H[j, :]

                # 计算观测权重（好观测的后验概率）
                w_good = (1.0 - self.gross_error_prob) * p_good / p_total
                obs_weights.append(float(w_good))

            total_cost = J_b + J_o  # noqa: N806
            cost_history.append(float(total_cost))
            obs_weights_history.append(obs_weights)

            # 总梯度
            grad_b = B_inv @ dx
            grad = grad_b + grad_o

            # 梯度下降更新
            lr = self._adaptive_learning_rate(cost_history, self.learning_rate)
            x = x - lr * grad

            # 收敛判断
            if (
                len(cost_history) > 1
                and abs(cost_history[-2] - cost_history[-1]) < self.tolerance
            ):
                logger.info("VarQC 收敛于迭代 %d", i)
                break

        analysis = x.reshape(background.shape)

        # 质量控制结果
        final_weights = obs_weights_history[-1] if obs_weights_history else [1.0] * m
        qc_results = self._compute_qc_results(
            observations, y_obs, H, x, final_weights
        )

        # 诊断统计
        diagnostics = self._compute_diagnostics(
            xb, x, observations, background.shape, cost_history
        )

        return {
            "analysis_field": analysis.tolist(),
            "increment": (x - xb).reshape(background.shape).tolist(),
            "cost": cost_history[-1] if cost_history else 0.0,
            "iterations": len(cost_history),
            "converged": len(cost_history) < self.max_iterations,
            "grid_shape": list(background.shape),
            "qc_results": qc_results,
            "obs_weights": final_weights,
            "obs_weights_history": obs_weights_history,
            "diagnostics": diagnostics,
        }

    # ================================================================
    # 预检查质量控制
    # ================================================================

    def _pre_check_assimilation(
        self, params: dict[str, Any]
    ) -> dict[str, Any]:
        """预检查质量控制: 先剔除异常观测再进行标准同化.

        使用背景场和新息的标准差进行初步质量控制。
        """
        background = np.asarray(
            params.get("background_field", np.zeros(self.grid_shape)),
            dtype=float,
        )
        observations = params.get("observations", [])

        xb = background.flatten()

        # 构建观测算子
        y_obs, H, obs_errors = self._build_observation_operator_with_errors(  # noqa: N806
            xb, observations, background.shape
        )
        m = len(y_obs)

        # 预检查: 计算新息
        Hxb = H @ xb  # noqa: N806
        innovations = y_obs - Hxb

        # 标记异常观测
        qc_flags: list[bool] = []
        for j in range(m):
            normalized_innovation = abs(innovations[j]) / max(obs_errors[j], 1e-10)
            is_good = normalized_innovation < self.qc_threshold
            qc_flags.append(is_good)

        # 仅保留好的观测
        good_indices = [j for j in range(m) if qc_flags[j]]
        good_observations = [observations[j] for j in good_indices]

        logger.info(
            "预检查QC: 剔除 %d/%d 个异常观测",
            m - len(good_indices), m,
        )

        # 使用过滤后的观测进行标准3D-VAR同化
        x = xb.copy()
        y_good, H_good = self._build_observation_operator(  # noqa: N806
            xb, good_observations, background.shape
        )
        m_good = len(y_good)

        cost_history: list[float] = []
        for i in range(self.max_iterations):
            dx = x - xb
            J_b = 0.5 * float(np.sum(dx**2)) / (self.sigma_b**2)  # noqa: N806

            if m_good > 0:
                Hx = H_good @ x  # noqa: N806
                dy = Hx - y_good
                J_o = 0.5 * float(np.sum((dy / self.observation_error_scale) ** 2))  # noqa: N806
                grad_o = H_good.T @ (dy / self.observation_error_scale**2)
            else:
                J_o = 0.0  # noqa: N806
                grad_o = np.zeros(len(xb))

            total_cost = J_b + J_o  # noqa: N806
            cost_history.append(float(total_cost))

            grad_b = dx / (self.sigma_b**2)
            grad = grad_b + grad_o
            x = x - self.learning_rate * grad

            if (
                len(cost_history) > 1
                and abs(cost_history[-2] - cost_history[-1]) < self.tolerance
            ):
                break

        analysis = x.reshape(background.shape)

        qc_results = {
            "n_total": m,
            "n_good": len(good_indices),
            "n_rejected": m - len(good_indices),
            "qc_flags": qc_flags,
            "normalized_innovations": (abs(innovations) / np.maximum(obs_errors, 1e-10)).tolist(),
        }

        return {
            "analysis_field": analysis.tolist(),
            "cost": cost_history[-1] if cost_history else 0.0,
            "iterations": len(cost_history),
            "converged": len(cost_history) < self.max_iterations,
            "grid_shape": list(background.shape),
            "qc_mode": "pre_check",
            "qc_results": qc_results,
        }

    # ================================================================
    # 后检查质量控制
    # ================================================================

    def _post_check_assimilation(
        self, params: dict[str, Any]
    ) -> dict[str, Any]:
        """后检查质量控制: 先进行标准同化再剔除异常观测.

        使用分析残差进行事后质量控制。
        """
        background = np.asarray(
            params.get("background_field", np.zeros(self.grid_shape)),
            dtype=float,
        )
        observations = params.get("observations", [])

        xb = background.flatten()
        x = xb.copy()

        # 标准同化
        y_obs, H = self._build_observation_operator(  # noqa: N806
            xb, observations, background.shape
        )
        m = len(y_obs)

        cost_history: list[float] = []
        for i in range(self.max_iterations):
            dx = x - xb
            J_b = 0.5 * float(np.sum(dx**2)) / (self.sigma_b**2)  # noqa: N806
            Hx = H @ x  # noqa: N806
            dy = Hx - y_obs
            J_o = 0.5 * float(np.sum((dy / self.observation_error_scale) ** 2))  # noqa: N806
            total_cost = J_b + J_o  # noqa: N806
            cost_history.append(float(total_cost))

            grad_b = dx / (self.sigma_b**2)
            grad_o = H.T @ (dy / self.observation_error_scale**2)
            x = x - self.learning_rate * (grad_b + grad_o)

            if (
                len(cost_history) > 1
                and abs(cost_history[-2] - cost_history[-1]) < self.tolerance
            ):
                break

        # 后检查: 使用分析残差
        Hxa = H @ x  # noqa: N806
        analysis_residuals = Hxa - y_obs
        qc_flags = [abs(r) < self.qc_threshold * self.observation_error_scale for r in analysis_residuals]

        analysis = x.reshape(background.shape)

        qc_results = {
            "n_total": m,
            "n_good": sum(qc_flags),
            "n_rejected": m - sum(qc_flags),
            "qc_flags": qc_flags,
            "analysis_residuals": analysis_residuals.tolist(),
        }

        return {
            "analysis_field": analysis.tolist(),
            "cost": cost_history[-1] if cost_history else 0.0,
            "iterations": len(cost_history),
            "converged": len(cost_history) < self.max_iterations,
            "grid_shape": list(background.shape),
            "qc_mode": "post_check",
            "qc_results": qc_results,
        }

    # ================================================================
    # 概率密度函数
    # ================================================================

    @staticmethod
    def _gaussian_pdf(x: float, mean: float, std: float) -> float:
        """计算高斯概率密度函数值."""
        return float(
            np.exp(-0.5 * ((x - mean) / max(std, 1e-10)) ** 2)
            / (std * np.sqrt(2.0 * np.pi))
        )

    # ================================================================
    # 质量控制结果
    # ================================================================

    def _compute_qc_results(
        self,
        observations: list[dict[str, Any]],
        y_obs: np.ndarray,
        H: np.ndarray,  # noqa: N806
        x: np.ndarray,
        weights: list[float],
    ) -> dict[str, Any]:
        """计算质量控制结果统计."""
        m = len(y_obs)
        Hx = H @ x  # noqa: N806
        residuals = Hx - y_obs

        # 按权重分类观测
        good_obs = [j for j in range(m) if weights[j] > 0.5]
        suspect_obs = [j for j in range(m) if 0.2 <= weights[j] <= 0.5]
        bad_obs = [j for j in range(m) if weights[j] < 0.2]

        return {
            "n_total": m,
            "n_good": len(good_obs),
            "n_suspect": len(suspect_obs),
            "n_bad": len(bad_obs),
            "obs_weights": weights,
            "residuals": residuals.tolist(),
            "mean_weight": float(np.mean(weights)),
            "min_weight": float(np.min(weights)) if weights else 0.0,
            "max_residual": float(np.max(np.abs(residuals))),
            "mean_residual": float(np.mean(np.abs(residuals))),
        }

    # ================================================================
    # 观测算子构建
    # ================================================================

    def _build_observation_operator(
        self,
        xb: np.ndarray,
        observations: list[dict[str, Any]],
        shape: tuple[int, ...],
    ) -> tuple[np.ndarray, np.ndarray]:
        """构建观测算子矩阵 H 和观测向量 y."""
        n = len(xb)
        m = len(observations)
        y_obs = np.zeros(m)
        H = np.zeros((m, n))  # noqa: N806
        for j, obs in enumerate(observations):
            pos = obs.get("position", [0] * len(shape))
            y_obs[j] = obs.get("value", 0.0)
            idx = self._position_to_index(pos, shape)
            if 0 <= idx < n:
                H[j, idx] = 1.0  # noqa: N806
        return y_obs, H

    def _build_observation_operator_with_errors(
        self,
        xb: np.ndarray,
        observations: list[dict[str, Any]],
        shape: tuple[int, ...],
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """构建观测算子矩阵 H、观测向量 y 和观测误差向量."""
        n = len(xb)
        m = len(observations)
        y_obs = np.zeros(m)
        H = np.zeros((m, n))  # noqa: N806
        obs_errors = np.zeros(m)

        for j, obs in enumerate(observations):
            pos = obs.get("position", [0] * len(shape))
            y_obs[j] = obs.get("value", 0.0)
            obs_errors[j] = obs.get("error", self.observation_error_scale)
            idx = self._position_to_index(pos, shape)
            if 0 <= idx < n:
                H[j, idx] = 1.0  # noqa: N806

        return y_obs, H, obs_errors

    # ================================================================
    # 自适应学习率
    # ================================================================

    def _adaptive_learning_rate(
        self,
        cost_history: list[float],
        base_lr: float,
    ) -> float:
        """根据代价函数变化自适应调整学习率."""
        if len(cost_history) < 2:
            return base_lr

        cost_change = cost_history[-2] - cost_history[-1]

        if cost_change > 0:
            return min(base_lr * 1.1, base_lr * 2.0)
        else:
            return max(base_lr * 0.5, base_lr * 0.01)

    # ================================================================
    # 诊断统计
    # ================================================================

    def _compute_diagnostics(
        self,
        xb: np.ndarray,
        xa: np.ndarray,
        observations: list[dict[str, Any]],
        shape: tuple[int, ...],
        cost_history: list[float],
    ) -> dict[str, Any]:
        """计算分析诊断统计."""
        increment = xa - xb
        increment_norm = float(np.linalg.norm(increment))
        increment_rms = float(np.sqrt(np.mean(increment**2)))

        y_obs, H = self._build_observation_operator(xb, observations, shape)  # noqa: N806
        if len(y_obs) > 0:
            Hxa = H @ xa  # noqa: N806
            Hxb = H @ xb  # noqa: N806
            residuals_analysis = Hxa - y_obs
            residuals_background = Hxb - y_obs

            rmse_analysis = float(np.sqrt(np.mean(residuals_analysis**2)))
            rmse_background = float(np.sqrt(np.mean(residuals_background**2)))
            improvement_ratio = (rmse_background - rmse_analysis) / max(rmse_background, 1e-10)
        else:
            rmse_analysis = 0.0
            rmse_background = 0.0
            improvement_ratio = 0.0

        cost_reduction = 0.0
        if len(cost_history) >= 2:
            cost_reduction = (cost_history[0] - cost_history[-1]) / max(cost_history[0], 1e-10)

        return {
            "increment": {
                "norm": increment_norm,
                "rms": increment_rms,
            },
            "fit": {
                "rmse_analysis": rmse_analysis,
                "rmse_background": rmse_background,
                "improvement_ratio": improvement_ratio,
            },
            "convergence": {
                "cost_reduction": cost_reduction,
                "final_cost": cost_history[-1] if cost_history else 0.0,
                "n_iterations": len(cost_history),
            },
        }

    # ================================================================
    # 工具方法
    # ================================================================

    @staticmethod
    def _position_to_index(pos: list[int], shape: tuple[int, ...]) -> int:
        """将多维位置索引转换为一维平坦索引."""
        idx = 0
        stride = 1
        for i in range(len(shape) - 1, -1, -1):
            idx += int(pos[i]) * stride
            stride *= shape[i]
        return idx

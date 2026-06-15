"""Hybrid EnVar (Hybrid Ensemble-Variational) 数据同化算法.

混合EnVar同化结合了集合方法和变分方法的优点:
- 集合方法提供流依赖的背景误差协方差
- 变分方法提供全局最优分析解
- 控制变量方法实现高效计算

算法原理:
  代价函数:
    J(v, alpha) = 0.5 * v^T v
                + 0.5 * (H M (x_b + Z v) - y)^T R^{-1} (H M (x_b + Z v) - y)

  其中:
    - v: 控制变量（扩展控制变量）
    - alpha: 混合权重系数
    - Z: 控制变量变换矩阵
      Z = [sqrt(alpha) * Z_static, sqrt(1-alpha) * Z_ensemble]
    - Z_static: 静态背景误差的平方根
    - Z_ensemble: 集合扰动的平方根

参考文献:
  Lorenc et al. (2015), Q.J.R. Meteorol. Soc., 141, 2107-2125
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class HybridEnVar:
    """混合EnVar (Hybrid Ensemble-Variational) 数据同化算法.

    特点:
    1. 结合集合和变分方法的优点
    2. 使用集合流依赖背景误差协方差
    3. 控制变量方法实现高效计算
    4. 支持静态和流依赖混合背景误差
    5. 通过alpha参数控制混合比例

    配置参数:
        hybrid_alpha: 集合部分的权重 (0-1)
        ensemble_size: 集合成员数
        static_error_scale: 静态背景误差标准差
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

        # 混合配置
        self.hybrid_alpha: float = self.config.get("hybrid_alpha", 0.5)
        self.ensemble_weight: float = self.config.get("ensemble_weight", 0.7)
        self.static_weight: float = 1.0 - self.ensemble_weight

        # 集合配置
        self.ensemble_size: int = self.config.get("ensemble_size", 30)
        self.background_error_scale: float = self.config.get("background_error_scale", 1.0)
        self.observation_error_scale: float = self.config.get("observation_error_scale", 0.1)

        # 静态背景误差配置
        self.static_error_scale: float = self.config.get("static_error_scale", 1.0)
        self.correlation_length: float = self.config.get("correlation_length", 100.0)

        # 时间维配置
        self.time_window: float = self.config.get("time_window", 6.0)
        self.n_time_slots: int = self.config.get("n_time_slots", 4)

    # ================================================================
    # 公共接口
    # ================================================================

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行Hybrid EnVar同化.

        Args:
            params: 分析参数字典，包含:
                - background_field: 背景场 (numpy.ndarray)
                - observations: 观测数据列表，每个元素包含:
                    - position: 观测位置
                    - value: 观测值
                    - error: 观测误差（可选）
                    - time_index: 时间窗口索引（可选）
                - ensemble: 预报集合成员（可选）
                - ensemble_size: 集合成员数（可选）
                - hybrid_alpha: 混合权重（可选）

        Returns:
            包含分析场、代价函数值、混合权重等信息的字典
        """
        background = np.asarray(
            params.get("background_field", np.zeros(self.grid_shape)),
            dtype=float,
        )
        observations = params.get("observations", [])
        n_ens = params.get("ensemble_size", self.ensemble_size)
        alpha = params.get("hybrid_alpha", self.hybrid_alpha)

        n_state = background.size
        xb = background.flatten()

        # 初始化集合
        ensemble = self._initialize_ensemble(xb, n_ens, params)

        # 构建控制变量变换矩阵 Z
        Z_static = self._build_static_control_variable(n_state)  # noqa: N806
        Z_ensemble = self._build_ensemble_control_variable(ensemble)  # noqa: N806

        # 混合: Z = [sqrt(alpha) * Z_static, sqrt(1-alpha) * Z_ensemble]
        Z = np.hstack([  # noqa: N806
            np.sqrt(alpha) * Z_static,
            np.sqrt(1.0 - alpha) * Z_ensemble,
        ])

        n_ctrl = Z.shape[1]  # 控制变量维度

        # 构建观测算子
        y_obs, H = self._build_observation_operator(  # noqa: N806
            xb, observations, background.shape
        )
        m = len(y_obs)

        # 构建观测误差协方差逆
        R_inv = self._build_observation_error_inverse(observations, m)  # noqa: N806

        # 构建时间传播算子
        obs_by_time = self._group_observations_by_time(observations)
        n_time = max(len(obs_by_time), 1)
        M_list = self._build_propagation_models(n_time, n_state)  # noqa: N806

        # 构建多时间步观测
        y_obs_all, H_all, R_inv_all = self._build_multi_time_obs_operator(  # noqa: N806
            xb, observations, background.shape
        )

        # 优化: 最小化 J(v) = 0.5 * v^T v + 0.5 * sum_t (H_t M_t (xb + Z v) - y_t)^T R_t^{-1} (...)
        v = np.zeros(n_ctrl)
        cost_history: list[float] = []
        J_b = J_o = 0.0  # noqa: N806

        for i in range(self.max_iterations):
            # 增量: dx = Z v
            dx = Z @ v

            # J_b: 控制变量约束项 = 0.5 * v^T v
            J_b = 0.5 * float(np.dot(v, v))  # noqa: N806

            # J_o: 观测约束项
            J_o = 0.0  # noqa: N806
            grad_o = np.zeros(n_ctrl)

            for t_idx, (y_t, H_t, R_inv_t, M_t) in enumerate(  # noqa: N806
                zip(y_obs_all, H_all, R_inv_all, M_list),
            ):
                x_t = xb + M_t @ dx  # noqa: N806
                Hx_t = H_t @ x_t  # noqa: N806
                residual_t = Hx_t - y_t

                J_o += 0.5 * float(residual_t @ R_inv_t @ residual_t)  # noqa: N806

                # 梯度: Z^T M_t^T H_t^T R_t^{-1} residual
                adj_obs = R_inv_t @ residual_t
                adj_H = H_t.T @ adj_obs  # noqa: N806
                adj_M = M_t.T @ adj_H  # noqa: N806
                grad_o += Z.T @ adj_M

            total_cost = J_b + J_o  # noqa: N806
            cost_history.append(float(total_cost))

            # 总梯度: grad_b = v, grad_o 已计算
            grad = v + grad_o

            # 自适应学习率
            lr = self._adaptive_learning_rate(cost_history, self.learning_rate)

            # 更新控制变量
            v = v - lr * grad

            # 收敛判断
            if (
                len(cost_history) > 1
                and abs(cost_history[-2] - cost_history[-1]) < self.tolerance
            ):
                logger.info("Hybrid EnVar 收敛于迭代 %d", i)
                break

        # 计算分析场
        dx_final = Z @ v
        xa = xb + dx_final
        analysis = xa.reshape(background.shape)

        # 诊断统计
        diagnostics = self._compute_diagnostics(
            xb, xa, observations, background.shape, cost_history
        )

        return {
            "analysis_field": analysis.tolist(),
            "increment": dx_final.reshape(background.shape).tolist(),
            "cost": cost_history[-1] if cost_history else 0.0,
            "cost_breakdown": {
                "J_b": float(J_b),
                "J_o": float(J_o),
            },
            "iterations": len(cost_history),
            "converged": len(cost_history) < self.max_iterations,
            "grid_shape": list(background.shape),
            "hybrid_alpha": alpha,
            "n_control_variables": n_ctrl,
            "n_time_slots": n_time,
            "diagnostics": diagnostics,
        }

    # ================================================================
    # 控制变量变换矩阵构建
    # ================================================================

    def _build_static_control_variable(self, n_state: int) -> np.ndarray:
        """构建静态背景误差的控制变量变换矩阵 Z_static.

        Z_static = B_static^{1/2}

        使用对角近似: Z_static = diag(sigma_b)
        """
        Z_static = np.eye(n_state) * self.static_error_scale  # noqa: N806
        return Z_static

    def _build_ensemble_control_variable(
        self, ensemble: np.ndarray
    ) -> np.ndarray:
        """构建集合控制变量变换矩阵 Z_ensemble.

        Z_ensemble = X' / sqrt(N-1)

        其中 X' 是集合扰动矩阵。
        """
        n_ens = ensemble.shape[0]
        x_mean = ensemble.mean(axis=0)
        X_pert = ensemble - x_mean[np.newaxis, :]  # (n_ens, n_state)
        Z_ensemble = X_pert.T / np.sqrt(n_ens - 1)  # (n_state, n_ens)
        return Z_ensemble

    # ================================================================
    # 集合初始化
    # ================================================================

    def _initialize_ensemble(
        self,
        xb: np.ndarray,
        n_ens: int,
        params: dict[str, Any],
    ) -> np.ndarray:
        """初始化集合成员."""
        provided_ensemble = params.get("ensemble", None)
        if provided_ensemble is not None:
            ensemble = np.asarray(provided_ensemble, dtype=float)
            if ensemble.ndim == 1:
                ensemble = ensemble.reshape(1, -1)
            return ensemble

        n_state = len(xb)
        np.random.seed(42)
        perturbation = np.random.randn(n_ens, n_state) * self.background_error_scale
        ensemble = xb[np.newaxis, :] + perturbation
        return ensemble

    # ================================================================
    # 多时间步观测算子
    # ================================================================

    def _group_observations_by_time(
        self,
        observations: list[dict[str, Any]],
    ) -> dict[int, list[dict[str, Any]]]:
        """按时间窗口索引分组观测."""
        time_windows: dict[int, list[dict[str, Any]]] = {}
        for obs in observations:
            t_idx = obs.get("time_index", 0)
            if t_idx not in time_windows:
                time_windows[t_idx] = []
            time_windows[t_idx].append(obs)
        return time_windows

    def _build_multi_time_obs_operator(
        self,
        xb: np.ndarray,
        observations: list[dict[str, Any]],
        shape: tuple[int, ...],
    ) -> tuple[list[np.ndarray], list[np.ndarray], list[np.ndarray]]:
        """构建多时间步的观测算子、观测向量和误差协方差逆."""
        time_windows = self._group_observations_by_time(observations)
        n_state = len(xb)

        y_obs_all: list[np.ndarray] = []
        H_all: list[np.ndarray] = []  # noqa: N806
        R_inv_all: list[np.ndarray] = []  # noqa: N806

        for t_idx in sorted(time_windows.keys()):
            window_obs = time_windows[t_idx]
            y_obs, H = self._build_observation_operator(xb, window_obs, shape)  # noqa: N806
            R_inv = self._build_observation_error_inverse(window_obs, len(window_obs))  # noqa: N806

            y_obs_all.append(y_obs)
            H_all.append(H)
            R_inv_all.append(R_inv)

        if not y_obs_all:
            y_obs_all.append(np.zeros(0))
            H_all.append(np.zeros((0, n_state)))
            R_inv_all.append(np.zeros((0, 0)))

        return y_obs_all, H_all, R_inv_all

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

    def _build_observation_error_inverse(
        self,
        observations: list[dict[str, Any]],
        m: int,
    ) -> np.ndarray:
        """构建观测误差协方差矩阵的逆 R^{-1}."""
        if m == 0:
            return np.zeros((0, 0))

        R = np.eye(m) * self.observation_error_scale**2  # noqa: N806
        for j, obs in enumerate(observations):
            obs_err = obs.get("error", self.observation_error_scale)
            R[j, j] = max(obs_err**2, 1e-10)  # noqa: N806

        try:
            R_inv = np.linalg.inv(R)  # noqa: N806
        except np.linalg.LinAlgError:
            R_inv = np.linalg.pinv(R)  # noqa: N806

        return R_inv

    def _build_propagation_models(
        self,
        n_time_slots: int,
        n_state: int,
    ) -> list[np.ndarray]:
        """构建简化的时间传播算子列表."""
        M_list = []  # noqa: N806
        for t in range(n_time_slots):
            M = np.eye(n_state)  # noqa: N806
            perturbation_scale = 0.01 * (t + 1)
            np.random.seed(42 + t)
            noise = np.random.randn(n_state, n_state) * perturbation_scale
            noise = 0.5 * (noise + noise.T)
            M = M + noise  # noqa: N806
            M_list.append(M)
        return M_list

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

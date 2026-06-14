"""4D-VAR Data Assimilation Algorithm -- 增强版.

在3D-VAR基础上增加时间维，支持时间窗口内的多时次观测同化。

代价函数:
  J(x) = 0.5 * (x - xb)^T B^{-1} (x - xb)
       + 0.5 * sum_t [ (H_t M_t x - y_t)^T R_t^{-1} (H_t M_t x - y_t) ]

其中:
  - B: 背景误差协方差
  - M_t: 时间步 t 的预报模式（线性化近似）
  - H_t: 时间步 t 的观测算子
  - y_t: 时间步 t 的观测向量
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class FourDimensionalVAR:
    """4D-VAR (Four-Dimensional Variational) 数据同化算法.

    在3D-VAR基础上扩展时间维度:
    1. 时间窗口: 支持多个时间步的观测同时同化
    2. 时间传播: 使用简化线性预报模型 M_t
    3. 多时次观测: 同一时间窗口内不同时刻的观测

    参数:
        time_window: 时间窗口大小（小时）
        n_time_slots: 时间插值点数
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        # 网格配置
        self.grid_shape: tuple[int, ...] = self.config.get("grid_shape", (10, 10, 5))
        self.resolution: float = self.config.get("resolution", 50.0)

        # 优化器配置
        self.max_iterations: int = self.config.get("max_iterations", 30)
        self.tolerance: float = self.config.get("tolerance", 1e-6)
        self.learning_rate: float = self.config.get("learning_rate", 0.01)

        # 时间维配置
        self.time_window: float = self.config.get("time_window", 6.0)
        self.n_time_slots: int = self.config.get("n_time_slots", 4)

        # 背景误差配置
        self.sigma_b: float = self.config.get("sigma_b", 1.0)
        self.observation_error_scale: float = self.config.get("observation_error_scale", 0.1)

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行4D-VAR同化.

        Args:
            params: 分析参数字典，包含:
                - background_field: 背景场 (numpy.ndarray)
                - observations: 观测数据列表，每个元素包含:
                    - position: 观测位置
                    - value: 观测值
                    - time_index: 时间窗口索引（可选，默认0）
                    - error: 观测误差（可选）

        Returns:
            包含分析结果和诊断统计的字典
        """
        background = np.asarray(
            params.get("background_field", np.zeros(self.grid_shape)),
            dtype=float,
        )
        observations = params.get("observations", [])

        # 按时间窗口分组观测
        obs_by_time = self._group_observations_by_time(observations)
        n_time = max(len(obs_by_time), 1)

        xb = background.flatten()
        n_state = len(xb)
        x = xb.copy()

        # 构建多时间步的观测算子和传播模型
        y_obs_all, H_all, R_inv_all = self._build_multi_time_obs_operator(
            x,
            observations,
            background.shape,
        )
        M_list = self._build_propagation_models(n_time, n_state)

        cost_history = []
        J_b = J_o = 0.0  # noqa: N806

        for i in range(self.max_iterations):
            dx = x - xb

            # J_b: 背景约束项
            J_b = 0.5 * float(np.sum(dx**2)) / (self.sigma_b**2)  # noqa: N806

            # J_o: 多时间步观测约束项
            J_o = 0.0  # noqa: N806
            grad_o = np.zeros(n_state)
            for t_idx, (y_t, H_t, R_inv_t, M_t) in enumerate(  # noqa: N806
                zip(y_obs_all, H_all, R_inv_all, M_list),
            ):
                Hx_t = H_t @ (M_t @ x)  # noqa: N806
                residual_t = Hx_t - y_t
                J_o += 0.5 * float(residual_t @ R_inv_t @ residual_t)  # noqa: N806
                grad_o += M_t.T @ H_t.T @ (R_inv_t @ residual_t)

            total_cost = J_b + J_o  # noqa: N806
            cost_history.append(float(total_cost))

            # 计算梯度
            grad_b = dx / (self.sigma_b**2)
            grad = grad_b + grad_o

            # 梯度下降更新
            x = x - self.learning_rate * grad

            if len(cost_history) > 1 and abs(cost_history[-2] - cost_history[-1]) < self.tolerance:
                logger.info("4D-VAR 收敛于迭代 %d", i)
                break

        analysis = x.reshape(background.shape)

        # 计算诊断统计
        diagnostics = self._compute_diagnostics(
            xb,
            x,
            observations,
            background.shape,
            cost_history,
        )

        return {
            "analysis_field": analysis.tolist(),
            "increment": (x - xb).reshape(background.shape).tolist(),
            "cost": cost_history[-1] if cost_history else 0.0,
            "cost_breakdown": {
                "J_b": float(J_b),
                "J_o": float(J_o),
            },
            "iterations": len(cost_history),
            "converged": len(cost_history) < self.max_iterations,
            "grid_shape": list(background.shape),
            "n_time_slots": n_time,
            "time_window": self.time_window,
            "diagnostics": diagnostics,
        }

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
        """构建多时间步的观测算子、观测向量和误差协方差逆.

        Returns:
            (y_obs_list, H_list, R_inv_list)
        """
        time_windows = self._group_observations_by_time(observations)
        n_state = len(xb)

        y_obs_all: list[np.ndarray] = []
        H_all: list[np.ndarray] = []  # noqa: N806
        R_inv_all: list[np.ndarray] = []  # noqa: N806

        for t_idx in sorted(time_windows.keys()):
            window_obs = time_windows[t_idx]
            y_obs, H = self._build_observation_operator(xb, window_obs, shape)  # noqa: N806
            R_inv = self._build_observation_error_inverse(window_obs)  # noqa: N806

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
    ) -> np.ndarray:
        """构建观测误差协方差矩阵的逆 R^{-1}."""
        n_obs = len(observations)
        if n_obs == 0:
            return np.zeros((0, 0))

        R = np.eye(n_obs) * self.observation_error_scale**2  # noqa: N806
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
        """构建简化的时间传播算子列表.

        M_t = I + epsilon * P，其中 P 是小随机扰动矩阵，
        模拟时间演化对状态的影响。
        """
        M_list = []
        for t in range(n_time_slots):
            M = np.eye(n_state)  # noqa: N806
            perturbation_scale = 0.01 * (t + 1)
            np.random.seed(42 + t)
            noise = np.random.randn(n_state, n_state) * perturbation_scale
            noise = 0.5 * (noise + noise.T)  # 对称化
            M = M + noise  # noqa: N806
            M_list.append(M)
        return M_list

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

        # 拟合度统计
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

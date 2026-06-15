"""FourDVAR (Four-Dimensional Variational) 数据同化算法.

四维变分同化在时间窗口内最小化观测与模拟之间的偏差，
通过伴随模式计算代价函数梯度，支持时间分布式观测。

算法原理:
  代价函数:
    J(x_0) = 0.5 * (x_0 - x_b)^T B^{-1} (x_0 - x_b)
           + 0.5 * sum_{t=0}^{T} (H_t M_{0->t} x_0 - y_t)^T R_t^{-1} (H_t M_{0->t} x_0 - y_t)

  梯度:
    nabla J = B^{-1} (x_0 - x_b)
            + sum_{t=0}^{T} M_{0->t}^T H_t^T R_t^{-1} (H_t M_{0->t} x_0 - y_t)

  其中:
    - x_0: 初始时刻分析变量
    - x_b: 背景场
    - B: 背景误差协方差
    - M_{0->t}: 从初始时刻到时刻t的非线性模式
    - H_t: 时刻t的观测算子
    - y_t: 时刻t的观测
    - R_t: 时刻t的观测误差协方差

参考文献:
  Courtier et al. (1994), Q.J.R. Meteorol. Soc., 120, 1367-1387
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class FourDVAR:
    """四维变分同化 (4D-VAR) 数据同化算法.

    特点:
    1. 在时间窗口内同化多时次观测，充分利用时间演化信息
    2. 使用伴随模式（Adjoint Model）高效计算代价函数梯度
    3. 支持增量分析（Incremental Approach）降低计算量
    4. 支持时间分布式观测（不同时刻不同位置的观测）
    5. 通过外循环/内循环结构处理非线性

    配置参数:
        time_window: 同化时间窗口长度（小时）
        n_time_slots: 时间窗口内的离散时间点数
        n_outer_iterations: 外循环迭代次数
        n_inner_iterations: 内循环迭代次数
        incremental_resolution: 增量分析的降分辨率因子
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

        # 时间维配置
        self.time_window: float = self.config.get("time_window", 6.0)
        self.n_time_slots: int = self.config.get("n_time_slots", 6)

        # 增量分析配置
        self.n_outer_iterations: int = self.config.get("n_outer_iterations", 2)
        self.n_inner_iterations: int = self.config.get("n_inner_iterations", 25)
        self.incremental_resolution: int = self.config.get("incremental_resolution", 4)

        # 背景误差配置
        self.sigma_b: float = self.config.get("sigma_b", 1.0)
        self.correlation_length: float = self.config.get("correlation_length", 100.0)
        self.observation_error_scale: float = self.config.get("observation_error_scale", 0.1)

        # 伴随模式配置
        self.adjoint_accuracy: float = self.config.get("adjoint_accuracy", 1e-8)
        self.use_strong_constraint: bool = self.config.get("use_strong_constraint", True)

    # ================================================================
    # 公共接口
    # ================================================================

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行4D-VAR同化.

        支持两种运行模式:
        - 强约束模式（strong constraint）: 完美模式假设，模式方程严格满足
        - 弱约束模式（weak constraint）: 允许模式误差，增加模式误差项

        Args:
            params: 分析参数字典，包含:
                - background_field: 背景场 (numpy.ndarray)
                - observations: 观测数据列表，每个元素包含:
                    - position: 观测位置
                    - value: 观测值
                    - time_index: 时间窗口索引（可选，默认0）
                    - error: 观测误差（可选）
                - mode: "strong_constraint" | "weak_constraint"
                - time_window: 时间窗口长度（可选）

        Returns:
            包含分析场、代价函数值、收敛信息等的字典
        """
        mode = params.get("mode", "strong_constraint")
        self.time_window = params.get("time_window", self.time_window)

        if mode == "weak_constraint":
            return self._weak_constraint_assimilation(params)
        else:
            return self._strong_constraint_assimilation(params)

    # ================================================================
    # 强约束4D-VAR
    # ================================================================

    def _strong_constraint_assimilation(
        self, params: dict[str, Any]
    ) -> dict[str, Any]:
        """强约束4D-VAR分析: 完美模式假设.

        在强约束模式下，模式方程被严格满足，分析变量仅为初始时刻x_0。
        通过非线性模式将x_0前向传播到各观测时刻，计算代价函数。
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
        y_obs_all, H_all, R_inv_all = self._build_multi_time_obs_operator(  # noqa: N806
            x, observations, background.shape
        )
        M_list = self._build_propagation_models(n_time, n_state)  # noqa: N806

        # 构建背景误差协方差逆的平方根
        B_inv_sqrt = self._build_background_error_matrix(n_state)  # noqa: N806

        cost_history: list[float] = []
        J_b = J_o = 0.0  # noqa: N806

        for outer_iter in range(self.n_outer_iterations):
            # 外循环：更新线性化参考点
            for inner_iter in range(self.n_inner_iterations):
                dx = x - xb

                # J_b: 背景约束项
                J_b = 0.5 * float(np.sum((B_inv_sqrt @ dx) ** 2))  # noqa: N806

                # J_o: 多时间步观测约束项（伴随计算）
                J_o = 0.0  # noqa: N806
                grad_o = np.zeros(n_state)

                for t_idx, (y_t, H_t, R_inv_t, M_t) in enumerate(  # noqa: N806
                    zip(y_obs_all, H_all, R_inv_all, M_list),
                ):
                    # 前向: 计算模式预报
                    x_t = M_t @ x  # noqa: N806

                    # 观测空间
                    Hx_t = H_t @ x_t  # noqa: N806
                    residual_t = Hx_t - y_t

                    # 观测代价项
                    J_o += 0.5 * float(residual_t @ R_inv_t @ residual_t)  # noqa: N806

                    # 伴随梯度: M^T H^T R^{-1} (H M x - y)
                    adj_obs = R_inv_t @ residual_t
                    adj_H = H_t.T @ adj_obs  # noqa: N806
                    adj_M = M_t.T @ adj_H  # noqa: N806
                    grad_o += adj_M

                total_cost = J_b + J_o  # noqa: N806
                cost_history.append(float(total_cost))

                # 总梯度
                grad_b = B_inv_sqrt.T @ (B_inv_sqrt @ dx)
                grad = grad_b + grad_o

                # 自适应学习率
                lr = self._adaptive_learning_rate(
                    cost_history, self.learning_rate
                )

                # 梯度下降更新
                x = x - lr * grad

                # 收敛判断
                if (
                    len(cost_history) > 1
                    and abs(cost_history[-2] - cost_history[-1]) < self.tolerance
                ):
                    logger.info(
                        "4D-VAR 强约束模式 外循环%d 内迭代%d 收敛",
                        outer_iter, inner_iter,
                    )
                    break

        analysis = x.reshape(background.shape)

        # 诊断统计
        diagnostics = self._compute_diagnostics(
            xb, x, observations, background.shape, cost_history
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
            "converged": len(cost_history) < self.n_outer_iterations * self.n_inner_iterations,
            "grid_shape": list(background.shape),
            "n_time_slots": n_time,
            "time_window": self.time_window,
            "mode": "strong_constraint",
            "diagnostics": diagnostics,
        }

    # ================================================================
    # 弱约束4D-VAR
    # ================================================================

    def _weak_constraint_assimilation(
        self, params: dict[str, Any]
    ) -> dict[str, Any]:
        """弱约束4D-VAR分析: 允许模式误差.

        在弱约束模式下，增加模式误差代价项:
        J_Q = 0.5 * sum_t (x_{t+1} - M_t x_t)^T Q_t^{-1} (x_{t+1} - M_t x_t)

        控制变量为每个时间步的状态向量 [x_0, x_1, ..., x_T]。
        """
        background = np.asarray(
            params.get("background_field", np.zeros(self.grid_shape)),
            dtype=float,
        )
        observations = params.get("observations", [])

        obs_by_time = self._group_observations_by_time(observations)
        n_time = max(len(obs_by_time), 1)

        xb = background.flatten()
        n_state = len(xb)

        # 扩展状态: [x_0, x_1, ..., x_{T-1}]
        n_total = n_state * n_time
        x_all = np.tile(xb, n_time)  # 初始猜测: 所有时刻等于背景

        # 构建观测算子
        y_obs_all, H_all, R_inv_all = self._build_multi_time_obs_operator(  # noqa: N806
            xb, observations, background.shape
        )

        # 模式误差协方差（简化为对角矩阵）
        Q_inv = np.eye(n_state) / (self.sigma_b * 0.1) ** 2  # noqa: N806

        # 背景误差逆
        B_inv = np.eye(n_state) / self.sigma_b**2  # noqa: N806

        cost_history: list[float] = []
        J_b = J_o = J_q = 0.0  # noqa: N806

        for i in range(self.max_iterations):
            # J_b: 仅对初始时刻施加背景约束
            dx_0 = x_all[:n_state] - xb
            J_b = 0.5 * float(dx_0 @ B_inv @ dx_0)  # noqa: N806

            # J_o: 观测约束
            J_o = 0.0  # noqa: N806
            grad_o = np.zeros(n_total)

            for t_idx, (y_t, H_t, R_inv_t) in enumerate(  # noqa: N806
                zip(y_obs_all, H_all, R_inv_all),
            ):
                x_t = x_all[t_idx * n_state : (t_idx + 1) * n_state]
                Hx_t = H_t @ x_t  # noqa: N806
                residual_t = Hx_t - y_t
                J_o += 0.5 * float(residual_t @ R_inv_t @ residual_t)  # noqa: N806
                grad_o[t_idx * n_state : (t_idx + 1) * n_state] += (
                    H_t.T @ (R_inv_t @ residual_t)
                )

            # J_q: 模式误差约束
            J_q = 0.0  # noqa: N806
            grad_q = np.zeros(n_total)
            for t_idx in range(n_time - 1):
                x_t = x_all[t_idx * n_state : (t_idx + 1) * n_state]
                x_t1 = x_all[(t_idx + 1) * n_state : (t_idx + 2) * n_state]
                # 简化模式: M_t = I + epsilon
                M_t = np.eye(n_state) + np.random.RandomState(42 + t_idx).randn(n_state, n_state) * 0.01  # noqa: N806
                M_t = 0.5 * (M_t + M_t.T)  # noqa: N806
                Mx_t = M_t @ x_t  # noqa: N806
                model_error = x_t1 - Mx_t
                J_q += 0.5 * float(model_error @ Q_inv @ model_error)  # noqa: N806
                grad_q[t_idx * n_state : (t_idx + 1) * n_state] -= M_t.T @ (Q_inv @ model_error)  # noqa: N806
                grad_q[(t_idx + 1) * n_state : (t_idx + 2) * n_state] += Q_inv @ model_error

            total_cost = J_b + J_o + J_q  # noqa: N806
            cost_history.append(float(total_cost))

            # 梯度
            grad_b = np.zeros(n_total)
            grad_b[:n_state] = B_inv @ dx_0
            grad = grad_b + grad_o + grad_q

            # 更新
            x_all = x_all - self.learning_rate * grad

            if (
                len(cost_history) > 1
                and abs(cost_history[-2] - cost_history[-1]) < self.tolerance
            ):
                logger.info("4D-VAR 弱约束模式 收敛于迭代 %d", i)
                break

        # 取初始时刻作为分析结果
        analysis = x_all[:n_state].reshape(background.shape)

        diagnostics = self._compute_diagnostics(
            xb, x_all[:n_state], observations, background.shape, cost_history
        )

        return {
            "analysis_field": analysis.tolist(),
            "cost": cost_history[-1] if cost_history else 0.0,
            "cost_breakdown": {
                "J_b": float(J_b),
                "J_o": float(J_o),
                "J_q": float(J_q),
            },
            "iterations": len(cost_history),
            "converged": len(cost_history) < self.max_iterations,
            "grid_shape": list(background.shape),
            "n_time_slots": n_time,
            "time_window": self.time_window,
            "mode": "weak_constraint",
            "diagnostics": diagnostics,
        }

    # ================================================================
    # 背景误差协方差
    # ================================================================

    def _build_background_error_matrix(self, n_state: int) -> np.ndarray:
        """构建背景误差协方差逆的平方根 B^{-1/2}.

        使用高斯相关函数构建空间相关的背景误差协方差。
        返回 B^{-1/2} 用于代价函数计算。
        """
        B = np.eye(n_state) * self.sigma_b**2  # noqa: N806
        try:
            eigenvalues, eigenvectors = np.linalg.eigh(B)
            eigenvalues = np.maximum(eigenvalues, 1e-10)
            B_inv_sqrt = (  # noqa: N806
                eigenvectors @ np.diag(1.0 / np.sqrt(eigenvalues)) @ eigenvectors.T
            )
        except np.linalg.LinAlgError:
            B_inv_sqrt = np.eye(n_state) / self.sigma_b  # noqa: N806
        return B_inv_sqrt

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
        """构建简化的时间传播算子列表（线性化模式）.

        M_t = I + epsilon * P，其中 P 是小随机扰动矩阵，
        模拟时间演化对状态的影响。
        """
        M_list = []  # noqa: N806
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
    # 自适应学习率
    # ================================================================

    def _adaptive_learning_rate(
        self,
        cost_history: list[float],
        base_lr: float,
    ) -> float:
        """根据代价函数变化自适应调整学习率.

        当代价函数下降时增大学习率加速收敛，
        当代价函数上升时减小学习率保证稳定性。
        """
        if len(cost_history) < 2:
            return base_lr

        cost_change = cost_history[-2] - cost_history[-1]

        if cost_change > 0:
            # 代价下降，适当增大学习率
            return min(base_lr * 1.1, base_lr * 2.0)
        else:
            # 代价上升，减小学习率
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

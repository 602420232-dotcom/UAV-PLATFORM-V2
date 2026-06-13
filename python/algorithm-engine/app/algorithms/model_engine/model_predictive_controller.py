"""模型预测控制器.

基于模型的预测控制（MPC），通过滚动优化计算最优控制序列。
适用于无人机航迹规划和气象场控制等需要考虑约束和不确定性的场景。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ModelPredictiveController:
    """模型预测控制器.

    基于内部预测模型，在有限预测时域内滚动优化控制序列，
    同时考虑状态约束、控制约束和模型不确定性。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.horizon = self.config.get("horizon", 10)
        self.dt = self.config.get("dt", 1.0)
        self.state_dim = self.config.get("state_dim", 4)
        self.control_dim = self.config.get("control_dim", 2)
        self.n_iterations = self.config.get("n_iterations", 50)
        self.learning_rate = self.config.get("learning_rate", 0.01)
        np.random.seed(42)

    def control(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行模型预测控制.

        Args:
            params: 包含以下键的字典:
                - current_state: 当前状态向量，形状 (state_dim,)
                - target_state: 目标状态向量，形状 (state_dim,)
                - horizon: 预测步长（时域长度）
                - constraints: 约束条件字典，包含:
                    - state_min: 状态下界
                    - state_max: 状态上界
                    - control_min: 控制下界
                    - control_max: 控制上界
                - model_params: 内部模型参数字典

        Returns:
            包含控制序列、预测轨迹和优化代价的字典。
        """
        np.random.seed(42)

        current_state = np.asarray(
            params.get("current_state", np.zeros(self.state_dim)),
        )
        target_state = np.asarray(
            params.get("target_state", np.ones(self.state_dim)),
        )
        horizon = params.get("horizon", self.horizon)
        constraints = params.get("constraints", {})
        model_params = params.get("model_params", {})

        state_dim = len(current_state)
        control_dim = self.control_dim

        # 解析约束
        state_min = np.asarray(constraints.get("state_min", np.full(state_dim, -np.inf)))
        state_max = np.asarray(constraints.get("state_max", np.full(state_dim, np.inf)))
        control_min = np.asarray(constraints.get("control_min", np.full(control_dim, -1.0)))
        control_max = np.asarray(constraints.get("control_max", np.full(control_dim, 1.0)))

        # 初始化控制序列
        control_sequence = np.zeros((horizon, control_dim))

        # 梯度下降优化控制序列
        best_cost = np.inf
        best_control = control_sequence.copy()

        for iteration in range(self.n_iterations):
            # 前向仿真预测轨迹
            trajectory = self._forward_simulate(current_state, control_sequence, model_params)

            # 计算代价
            cost = self._compute_cost(trajectory, target_state, control_sequence)

            if cost < best_cost:
                best_cost = cost
                best_control = control_sequence.copy()

            # 计算数值梯度
            grad = np.zeros_like(control_sequence)
            eps = 1e-5
            for t in range(horizon):
                for c in range(control_dim):
                    control_plus = control_sequence.copy()
                    control_plus[t, c] += eps
                    traj_plus = self._forward_simulate(current_state, control_plus, model_params)
                    cost_plus = self._compute_cost(traj_plus, target_state, control_plus)

                    control_minus = control_sequence.copy()
                    control_minus[t, c] -= eps
                    traj_minus = self._forward_simulate(current_state, control_minus, model_params)
                    cost_minus = self._compute_cost(traj_minus, target_state, control_minus)

                    grad[t, c] = (cost_plus - cost_minus) / (2 * eps)

            # 梯度更新
            control_sequence -= self.learning_rate * grad

            # 投影到控制约束
            control_sequence = np.clip(control_sequence, control_min, control_max)

        # 使用最优控制序列重新仿真
        predicted_trajectory = self._forward_simulate(current_state, best_control, model_params)

        # 对预测轨迹施加状态约束
        predicted_trajectory = np.clip(predicted_trajectory, state_min, state_max)

        final_cost = self._compute_cost(predicted_trajectory, target_state, best_control)

        return {
            "control_sequence": best_control.tolist(),
            "predicted_trajectory": predicted_trajectory.tolist(),
            "cost": float(final_cost),
            "horizon": horizon,
            "state_dim": state_dim,
            "control_dim": control_dim,
            "n_iterations": self.n_iterations,
        }

    def _forward_simulate(
        self,
        initial_state: np.ndarray,
        control_sequence: np.ndarray,
        model_params: dict[str, Any],
    ) -> np.ndarray:
        """前向仿真模型.

        使用简化的线性动力学模型进行前向仿真。

        Args:
            initial_state: 初始状态，形状 (state_dim,).
            control_sequence: 控制序列，形状 (horizon, control_dim).
            model_params: 模型参数.

        Returns:
            状态轨迹，形状 (horizon + 1, state_dim).
        """
        horizon = len(control_sequence)
        state_dim = len(initial_state)
        control_dim = control_sequence.shape[1]

        # 构建系统矩阵（简化线性模型）
        damping = model_params.get("damping", 0.9)
        A = np.eye(state_dim) * damping  # noqa: N806
        # 控制输入映射到状态空间
        B = np.zeros((state_dim, control_dim))  # noqa: N806
        for i in range(min(state_dim, control_dim)):
            B[i, i] = self.dt

        trajectory = np.zeros((horizon + 1, state_dim))
        trajectory[0] = initial_state.copy()

        for t in range(horizon):
            state = trajectory[t]
            control = control_sequence[t]
            # 添加轻微非线性（饱和效应）
            nonlinear = -0.01 * state ** 3
            next_state = A @ state + B @ control + nonlinear
            trajectory[t + 1] = next_state

        return trajectory

    def _compute_cost(
        self,
        trajectory: np.ndarray,
        target_state: np.ndarray,
        control_sequence: np.ndarray,
    ) -> float:
        """计算 MPC 代价函数.

        代价 = 状态跟踪代价 + 控制 effort 代价 + 终端代价

        Args:
            trajectory: 状态轨迹，形状 (horizon + 1, state_dim).
            target_state: 目标状态.
            control_sequence: 控制序列.

        Returns:
            总代价.
        """
        horizon = len(control_sequence)

        # 状态跟踪代价
        state_errors = trajectory[1:] - target_state[np.newaxis, :]
        state_cost = np.sum(state_errors ** 2)

        # 控制代价（惩罚过大的控制量）
        control_cost = 0.1 * np.sum(control_sequence ** 2)

        # 控制平滑性代价（惩罚控制量的剧烈变化）
        if horizon > 1:
            control_diff = np.diff(control_sequence, axis=0)
            smoothness_cost = 0.5 * np.sum(control_diff ** 2)
        else:
            smoothness_cost = 0.0

        # 终端代价（加大终端状态的惩罚）
        terminal_error = trajectory[-1] - target_state
        terminal_cost = 10.0 * np.sum(terminal_error ** 2)

        return float(state_cost + control_cost + smoothness_cost + terminal_cost)

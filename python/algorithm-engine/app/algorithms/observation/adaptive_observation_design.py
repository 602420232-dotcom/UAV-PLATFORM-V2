"""自适应观测设计优化.

基于信息论方法优化观测站位布局，包括:
1. 基于信息熵的观测站位优化（最大化信息增益）
2. Fisher信息矩阵计算（评估观测系统的信息含量）
3. 自适应观测时间窗口（根据不确定性动态调整观测频率）
4. 动态观测计划生成（考虑传感器约束和任务需求）

核心思想: 在有限的观测资源下，选择能最大程度降低分析不确定性的
观测位置和时间，实现观测效益最大化。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class AdaptiveObservationDesign:
    """自适应观测设计优化器.

    通过信息论方法优化观测站位布局和时间安排，在有限资源下
    最大化观测信息增益，降低分析场不确定性。

    主要方法:
    - 基于信息熵的站位优化: 选择使后验熵最小的观测位置
    - Fisher信息矩阵: 量化观测系统对状态估计的信息贡献
    - 自适应时间窗口: 根据不确定性演化动态调整观测频率
    - 贪心算法: 在观测预算约束下逐步选择最优观测组合
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        # 观测预算（最大观测站数量）
        self.budget: int = self.config.get("budget", 10)
        # 网格配置
        self.grid_shape: tuple[int, ...] = self.config.get("grid_shape", (10, 10))
        # 观测误差标准差
        self.obs_error_std: float = self.config.get("obs_error_std", 0.1)
        # 背景误差标准差
        self.bg_error_std: float = self.config.get("bg_error_std", 1.0)
        # 相关长度（用于构建背景误差协方差）
        self.correlation_length: float = self.config.get("correlation_length", 2.0)
        # 时间窗口配置
        self.time_horizon: float = self.config.get("time_horizon", 60.0)
        self.time_step: float = self.config.get("time_step", 10.0)
        # 不确定性增长速率
        self.uncertainty_growth_rate: float = self.config.get(
            "uncertainty_growth_rate", 0.05,
        )
        # 空间分辨率
        self.resolution: float = self.config.get("resolution", 1.0)

    # ================================================================
    # 公共接口
    # ================================================================

    def design(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行自适应观测设计优化.

        Args:
            params: 设计参数字典，包含:
                - uncertainty_field: 当前不确定性场 (numpy.ndarray)
                - background_field: 背景场（可选）
                - available_positions: 可选观测位置列表（可选）
                - budget: 观测预算（可选）
                - time_windows: 时间窗口配置（可选）
                - sensor_constraints: 传感器约束（可选）

        Returns:
            优化后的观测方案和预期信息增益
        """
        uncertainty_field = np.asarray(
            params.get("uncertainty_field", np.ones(self.grid_shape)),
            dtype=float,
        )
        budget = params.get("budget", self.budget)
        available_positions = params.get("available_positions", None)

        logger.info(
            "开始自适应观测设计: 网格=%s, 预算=%d",
            uncertainty_field.shape, budget,
        )

        # 1. 构建背景误差协方差矩阵
        B = self._build_background_covariance(uncertainty_field)  # noqa: N806

        # 2. 计算Fisher信息矩阵
        fisher_info = self._compute_fisher_information(
            uncertainty_field, available_positions,
        )

        # 3. 基于信息熵的观测站位优化
        optimal_positions = self._optimize_positions_entropy(
            uncertainty_field, B, budget, available_positions,
        )

        # 4. 自适应观测时间窗口
        time_windows = self._adaptive_time_windows(uncertainty_field)

        # 5. 生成动态观测计划
        observation_plan = self._generate_observation_plan(
            optimal_positions, time_windows, params,
        )

        # 6. 计算预期信息增益
        expected_gain = self._compute_expected_information_gain(
            uncertainty_field, optimal_positions, B,
        )

        return {
            "optimal_positions": optimal_positions,
            "time_windows": time_windows,
            "observation_plan": observation_plan,
            "expected_information_gain": expected_gain,
            "fisher_information": {
                "trace": float(np.trace(fisher_info)),
                "determinant": float(np.linalg.det(fisher_info)),
                "eigenvalues": np.linalg.eigvalsh(fisher_info).tolist(),
            },
            "design_summary": {
                "n_positions": len(optimal_positions),
                "budget_used": min(len(optimal_positions), budget),
                "grid_shape": list(uncertainty_field.shape),
                "method": "entropy_based_greedy",
            },
        }

    # ================================================================
    # 背景误差协方差矩阵
    # ================================================================

    def _build_background_covariance(
        self,
        uncertainty_field: np.ndarray,
    ) -> np.ndarray:
        """构建背景误差协方差矩阵 B.

        使用高斯相关模型:
        B(i,j) = sigma_i * sigma_j * exp(-d(i,j)^2 / (2*L^2))

        其中:
        - sigma_i: 位置i的背景误差标准差（来自不确定性场）
        - d(i,j): 位置i和j之间的距离
        - L: 相关长度
        """
        flat = uncertainty_field.flatten()
        n = len(flat)

        # 使用不确定性场作为局部误差标准差
        sigma = np.maximum(flat, 1e-6)

        # 构建位置坐标网格
        positions = self._get_grid_positions(uncertainty_field.shape)

        # 计算距离矩阵
        dist_matrix = self._compute_distance_matrix(positions)

        # 高斯相关函数
        L = self.correlation_length
        correlation = np.exp(-dist_matrix ** 2 / (2 * L ** 2))

        # 构建协方差矩阵
        B = np.outer(sigma, sigma) * correlation  # noqa: N806

        # 正则化
        B += np.eye(n) * 1e-10  # noqa: N806

        return B

    # ================================================================
    # Fisher 信息矩阵
    # ================================================================

    def _compute_fisher_information(
        self,
        uncertainty_field: np.ndarray,
        available_positions: Optional[list[list[int]]] = None,
    ) -> np.ndarray:
        """计算Fisher信息矩阵.

        Fisher信息矩阵衡量观测数据包含的关于模型参数的信息量:
        I_F = H^T R^{-1} H

        其中:
        - H: 观测算子（Jacobian矩阵）
        - R: 观测误差协方差矩阵

        Fisher信息矩阵的迹越大，说明观测系统对状态估计的
        约束越强，估计精度越高。
        """
        n_state = uncertainty_field.size
        shape = uncertainty_field.shape

        # 确定观测位置
        if available_positions is not None:
            n_obs = len(available_positions)
        else:
            # 使用所有网格点作为候选观测位置
            n_obs = n_state

        # 构建观测算子 H
        H = np.zeros((n_obs, n_state))  # noqa: N806
        for j in range(n_obs):
            if available_positions is not None:
                pos = available_positions[j]
            else:
                pos = [int(x) for x in np.unravel_index(j, shape)]
            idx = self._position_to_index(pos, shape)
            if 0 <= idx < n_state:
                H[j, idx] = 1.0  # noqa: N806

        # 构建观测误差协方差 R
        R = np.eye(n_obs) * self.obs_error_std ** 2  # noqa: N806

        # Fisher信息矩阵: I_F = H^T R^{-1} H
        try:
            R_inv = np.linalg.inv(R)  # noqa: N806
            fisher_info = H.T @ R_inv @ H  # noqa: N806
        except np.linalg.LinAlgError:
            fisher_info = H.T @ np.linalg.pinv(R) @ H

        return fisher_info

    # ================================================================
    # 基于信息熵的观测站位优化
    # ================================================================

    def _optimize_positions_entropy(
        self,
        uncertainty_field: np.ndarray,
        B: np.ndarray,  # noqa: N806
        budget: int,
        available_positions: Optional[list[list[int]]] = None,
    ) -> list[dict[str, Any]]:
        """基于信息熵的贪心观测站位优化.

        算法步骤:
        1. 初始化: 选择不确定性最大的位置
        2. 迭代: 每次选择使后验熵降低最大的位置
        3. 终止: 达到预算上限或信息增益饱和

        后验熵降低量等价于观测信息增益:
        delta_H = 0.5 * log|B_a| - 0.5 * log|B_b|
                = 0.5 * log|B + HB^T R^{-1} HB| - 0.5 * log|B|
        """
        shape = uncertainty_field.shape
        n_state = uncertainty_field.size

        # 生成候选位置列表
        if available_positions is not None:
            candidates = [[int(x) for x in p] for p in available_positions]
        else:
            # 使用高不确定性区域作为候选
            flat = uncertainty_field.flatten()
            # 选择不确定性高于中位数的网格点
            threshold = np.median(flat)
            candidates = []
            for idx in np.where(flat >= threshold)[0]:
                pos = [int(x) for x in np.unravel_index(idx, shape)]
                candidates.append(pos)

        if not candidates:
            candidates = [[int(x) for x in np.unravel_index(0, shape)]]

        n_candidates = len(candidates)
        budget = min(budget, n_candidates)

        logger.info(
            "贪心优化: %d个候选位置, 预算=%d",
            n_candidates, budget,
        )

        # 贪心选择
        selected: list[dict[str, Any]] = []
        selected_indices: set[int] = set()

        for step in range(budget):
            best_gain = -np.inf
            best_idx = -1

            for c_idx, pos in enumerate(candidates):
                if c_idx in selected_indices:
                    continue

                # 计算添加此位置后的信息增益
                gain = self._compute_marginal_gain(
                    B, selected, pos, shape, n_state,
                )

                if gain > best_gain:
                    best_gain = gain
                    best_idx = c_idx

            if best_idx >= 0 and best_gain > 1e-10:
                pos = candidates[best_idx]
                flat_idx = self._position_to_index(pos, shape)
                selected.append({
                    "position": pos,
                    "flat_index": int(flat_idx),
                    "uncertainty": float(uncertainty_field[tuple(pos)]),
                    "marginal_gain": float(best_gain),
                })
                selected_indices.add(best_idx)
                logger.debug(
                    "步骤 %d: 选择位置 %s, 边际增益=%.6f",
                    step + 1, pos, best_gain,
                )
            else:
                logger.info("信息增益饱和，提前终止")
                break

        return selected

    def _compute_marginal_gain(
        self,
        B: np.ndarray,  # noqa: N806
        selected: list[dict[str, Any]],
        candidate_pos: list[int],
        shape: tuple[int, ...],
        n_state: int,
    ) -> float:
        """计算添加一个候选观测位置的边际信息增益.

        使用简化公式: 边际增益正比于该位置的观测对总不确定性的降低。
        """
        # 构建包含已选位置和新候选的观测算子
        n_selected = len(selected) + 1
        H = np.zeros((n_selected, n_state))  # noqa: N806

        for i, s in enumerate(selected):
            idx = s["flat_index"]
            if 0 <= idx < n_state:
                H[i, idx] = 1.0  # noqa: N806

        # 添加候选位置
        cand_idx = self._position_to_index(candidate_pos, shape)
        if 0 <= cand_idx < n_state:
            H[n_selected - 1, cand_idx] = 1.0  # noqa: N806

        # 观测误差协方差
        R = np.eye(n_selected) * self.obs_error_std ** 2  # noqa: N806

        # 分析误差协方差: B_a = (B^{-1} + H^T R^{-1} H)^{-1}
        try:
            B_inv = np.linalg.inv(B)  # noqa: N806
            R_inv = np.linalg.inv(R)  # noqa: N806
            Ba_inv = B_inv + H.T @ R_inv @ H  # noqa: N806
            Ba = np.linalg.inv(Ba_inv)  # noqa: N806
            # 信息增益 = 0.5 * (log|B| - log|Ba|)
            sign_B, logdet_B = np.linalg.slogdet(B)
            sign_Ba, logdet_Ba = np.linalg.slogdet(Ba)
            if sign_B > 0 and sign_Ba > 0:
                gain = 0.5 * (logdet_B - logdet_Ba)
            else:
                # 后备方案：使用迹的减少量
                gain = 0.5 * (np.trace(B) - np.trace(Ba))
        except np.linalg.LinAlgError:
            # 矩阵不可逆时使用简化估计
            gain = float(np.sum(B[cand_idx, cand_idx])) / (self.obs_error_std ** 2)

        return max(float(gain), 0.0)

    # ================================================================
    # 自适应观测时间窗口
    # ================================================================

    def _adaptive_time_windows(
        self,
        uncertainty_field: np.ndarray,
    ) -> list[dict[str, Any]]:
        """根据不确定性场动态计算最优观测时间窗口.

        原理:
        - 不确定性高的区域需要更频繁的观测
        - 不确定性低的区域可以降低观测频率
        - 观测间隔与局部不确定性成正比（反比于观测频率）

        时间窗口计算:
        delta_t = base_interval / (1 + alpha * uncertainty_normalized)
        """
        n_slots = max(1, int(self.time_horizon / self.time_step))
        mean_uncertainty = float(np.mean(uncertainty_field))
        max_uncertainty = float(np.max(uncertainty_field))

        time_windows = []
        for t in range(n_slots):
            # 模拟不确定性随时间的增长
            time_factor = 1.0 + self.uncertainty_growth_rate * t
            effective_uncertainty = mean_uncertainty * time_factor

            # 自适应观测间隔
            if max_uncertainty > 1e-10:
                normalized_uncertainty = effective_uncertainty / max_uncertainty
            else:
                normalized_uncertainty = 0.5

            # 观测间隔与不确定性正相关（不确定性高 -> 间隔短 -> 频率高）
            adaptive_interval = self.time_step / (1.0 + 2.0 * normalized_uncertainty)
            adaptive_interval = max(adaptive_interval, 1.0)

            # 观测优先级
            priority = min(1.0, normalized_uncertainty * 1.5)

            time_windows.append({
                "time_slot": t,
                "start_time": t * self.time_step,
                "end_time": (t + 1) * self.time_step,
                "adaptive_interval": float(adaptive_interval),
                "priority": float(priority),
                "expected_uncertainty": float(effective_uncertainty),
                "recommended_n_observations": max(
                    1, int(self.budget * priority / n_slots),
                ),
            })

        return time_windows

    # ================================================================
    # 动态观测计划生成
    # ================================================================

    def _generate_observation_plan(
        self,
        optimal_positions: list[dict[str, Any]],
        time_windows: list[dict[str, Any]],
        params: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """生成完整的动态观测计划.

        将优化后的观测站位与时间窗口结合，生成具体的观测任务列表。
        考虑传感器约束（移动速度、续航时间、观测范围等）。
        """
        sensor_constraints = params.get("sensor_constraints", {})
        max_speed = sensor_constraints.get("max_speed", 50.0)  # m/s
        max_flight_time = sensor_constraints.get("max_flight_time", 3600.0)  # s

        observation_plan = []
        task_id = 0

        for tw in time_windows:
            # 根据时间窗口优先级分配观测任务
            n_obs_this_window = tw["recommended_n_observations"]
            priority = tw["priority"]

            # 选择优先级最高的位置
            sorted_positions = sorted(
                optimal_positions,
                key=lambda p: p.get("uncertainty", 0) * priority,
                reverse=True,
            )

            for i in range(min(n_obs_this_window, len(sorted_positions))):
                pos_info = sorted_positions[i]
                task_id += 1

                observation_plan.append({
                    "task_id": task_id,
                    "time_slot": tw["time_slot"],
                    "scheduled_time": tw["start_time"],
                    "position": pos_info["position"],
                    "priority": float(priority),
                    "expected_uncertainty_reduction": float(
                        pos_info.get("marginal_gain", 0),
                    ),
                    "sensor_type": "uav_observer",
                    "estimated_duration": float(
                        self._estimate_observation_duration(
                            pos_info["position"], optimal_positions, max_speed,
                        ),
                    ),
                    "feasible": True,
                })

        # 检查可行性并标记不可行任务
        total_flight_time = sum(
            t["estimated_duration"] for t in observation_plan
        )
        if total_flight_time > max_flight_time:
            logger.warning(
                "总飞行时间 %.1fs 超过最大续航 %.1fs，需要裁剪任务",
                total_flight_time, max_flight_time,
            )
            # 按优先级排序，保留高优先级任务
            observation_plan.sort(key=lambda t: t["priority"], reverse=True)
            cumulative_time = 0.0
            for task in observation_plan:
                if cumulative_time + task["estimated_duration"] <= max_flight_time:
                    cumulative_time += task["estimated_duration"]
                else:
                    task["feasible"] = False

        return observation_plan

    def _estimate_observation_duration(
        self,
        position: list[int],
        all_positions: list[dict[str, Any]],
        max_speed: float,
    ) -> float:
        """估算单次观测的持续时间（包含转移时间）.

        简化模型: 持续时间 = 转移距离 / 速度 + 观测时间
        """
        observation_time = 30.0  # 固定观测时间30秒
        transfer_distance = 0.0

        if all_positions:
            # 估算到最近已选位置的转移距离
            min_dist = float("inf")
            for p in all_positions:
                d = sum(
                    (a - b) ** 2 for a, b in zip(position, p["position"])
                ) ** 0.5
                if d < min_dist:
                    min_dist = d
            transfer_distance = min_dist * self.resolution

        transfer_time = (
            transfer_distance / max_speed if max_speed > 0 else 0
        )
        return observation_time + transfer_time

    # ================================================================
    # 预期信息增益计算
    # ================================================================

    def _compute_expected_information_gain(
        self,
        uncertainty_field: np.ndarray,
        optimal_positions: list[dict[str, Any]],
        B: np.ndarray,  # noqa: N806
    ) -> dict[str, Any]:
        """计算优化后观测方案的预期信息增益.

        信息增益 = H(先验) - H(后验)
        其中 H 为微分熵。

        对于高斯分布:
        H = 0.5 * n * (1 + ln(2*pi)) + 0.5 * ln|Sigma|
        """
        n_state = uncertainty_field.size

        if not optimal_positions:
            return {
                "total_gain": 0.0,
                "relative_gain": 0.0,
                "entropy_reduction_pct": 0.0,
            }

        # 构建观测算子
        n_obs = len(optimal_positions)
        H = np.zeros((n_obs, n_state))  # noqa: N806
        for i, pos_info in enumerate(optimal_positions):
            idx = pos_info["flat_index"]
            if 0 <= idx < n_state:
                H[i, idx] = 1.0  # noqa: N806

        # 观测误差协方差
        R = np.eye(n_obs) * self.obs_error_std ** 2  # noqa: N806

        # 计算分析误差协方差
        try:
            B_inv = np.linalg.inv(B)  # noqa: N806
            R_inv = np.linalg.inv(R)  # noqa: N806
            Ba_inv = B_inv + H.T @ R_inv @ H  # noqa: N806
            Ba = np.linalg.inv(Ba_inv)  # noqa: N806

            # 先验熵
            sign_B, logdet_B = np.linalg.slogdet(B)
            prior_entropy = 0.5 * n_state * (1 + np.log(2 * np.pi))
            if sign_B > 0:
                prior_entropy += 0.5 * logdet_B

            # 后验熵
            sign_Ba, logdet_Ba = np.linalg.slogdet(Ba)
            posterior_entropy = 0.5 * n_state * (1 + np.log(2 * np.pi))
            if sign_Ba > 0:
                posterior_entropy += 0.5 * logdet_Ba

            total_gain = max(prior_entropy - posterior_entropy, 0.0)
            relative_gain = (
                total_gain / prior_entropy if prior_entropy > 1e-10 else 0.0
            )
            entropy_reduction_pct = relative_gain * 100.0

            # 各位置贡献的边际增益
            marginal_gains = [
                float(p.get("marginal_gain", 0)) for p in optimal_positions
            ]

        except np.linalg.LinAlgError:
            total_gain = sum(
                float(p.get("marginal_gain", 0)) for p in optimal_positions
            )
            relative_gain = 0.0
            entropy_reduction_pct = 0.0
            marginal_gains = []

        return {
            "total_gain": float(total_gain),
            "relative_gain": float(relative_gain),
            "entropy_reduction_pct": float(entropy_reduction_pct),
            "marginal_gains": marginal_gains,
            "n_observations": n_obs,
        }

    # ================================================================
    # 工具方法
    # ================================================================

    def _get_grid_positions(
        self,
        shape: tuple[int, ...],
    ) -> np.ndarray:
        """生成网格位置坐标数组."""
        grids = np.meshgrid(
            *[np.arange(s) for s in shape],
            indexing="ij",
        )
        positions = np.column_stack([g.flatten() for g in grids])
        return positions

    @staticmethod
    def _compute_distance_matrix(positions: np.ndarray) -> np.ndarray:
        """计算位置之间的欧氏距离矩阵."""
        diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
        return np.sqrt(np.sum(diff ** 2, axis=2))

    @staticmethod
    def _position_to_index(pos: list[int], shape: tuple[int, ...]) -> int:
        """将多维位置索引转换为一维平坦索引."""
        idx = 0
        stride = 1
        for i in range(len(shape) - 1, -1, -1):
            idx += int(pos[i]) * stride
            stride *= shape[i]
        return idx

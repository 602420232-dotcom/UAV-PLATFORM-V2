"""增强型动态窗口法（Dynamic Window Approach）路径规划算法。

基于速度空间的实时局部规划方法。
在当前速度约束和加速度约束形成的动态窗口内，
搜索使评价函数最优的速度指令。
考虑速度、方向、障碍物距离和路径偏离度。

与基础DWA的区别：支持更精细的速度采样、
多目标评价函数和轨迹预测。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class DynamicWindowPlanner:
    """增强型动态窗口法路径规划器。

    在动态窗口（由当前速度、加速度限制和安全速度组成）
    内搜索最优速度指令。评价函数综合考虑：
    - 目标方向奖励
    - 障碍物距离惩罚
    - 速度奖励
    - 路径平滑度

    Args:
        config: 配置字典，支持以下参数：
            - max_speed: 最大线速度，默认3.0
            - max_yaw_rate: 最大角速度，默认1.0
            - max_accel: 最大加速度，默认2.0
            - predict_time: 轨迹预测时间，默认2.0
            - velocity_samples: 速度采样数，默认20
            - heading_weight: 目标方向权重，默认1.0
            - clearance_weight: 障碍物距离权重，默认1.0
            - velocity_weight: 速度权重，默认0.5
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.max_speed: float = self.config.get("max_speed", 3.0)
        self.max_yaw_rate: float = self.config.get("max_yaw_rate", 1.0)
        self.max_accel: float = self.config.get("max_accel", 2.0)
        self.predict_time: float = self.config.get("predict_time", 2.0)
        self.velocity_samples: int = self.config.get("velocity_samples", 20)
        self.heading_weight: float = self.config.get("heading_weight", 1.0)
        self.clearance_weight: float = self.config.get("clearance_weight", 1.0)
        self.velocity_weight: float = self.config.get("velocity_weight", 0.5)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行动态窗口法路径规划。

        Args:
            params: 规划参数字典，包含：
                - start: 当前位置 [x, y]
                - goal: 目标位置 [x, y]
                - obstacles: 障碍物列表 list[tuple]
                - current_velocity: 当前速度 [vx, vy]（可选）

        Returns:
            包含 trajectory（预测轨迹）和 velocity（最优速度）的字典。
        """
        np.random.seed(42)

        current = np.array(params.get("start", [0, 0]), dtype=float)
        goal = np.array(params.get("goal", [10, 10]), dtype=float)
        obstacles = [np.array(obs[:2], dtype=float) for obs in params.get("obstacles", [])]
        current_vel = np.array(
            params.get("current_velocity", [0.0, 0.0]), dtype=float
        )

        logger.info(
            "动态窗口法规划: 位置=%s, 目标=%s, 当前速度=%s",
            tuple(current.astype(int)),
            tuple(goal.astype(int)),
            tuple(current_vel.round(2)),
        )

        # 计算动态窗口
        dw = self._compute_dynamic_window(current_vel)

        # 在动态窗口内搜索最优速度
        best_velocity = current_vel.copy()
        best_score = -float("inf")
        best_trajectory = [current.copy()]

        v_samples = np.linspace(dw["v_min"], dw["v_max"], self.velocity_samples)
        w_samples = np.linspace(dw["w_min"], dw["w_max"], self.velocity_samples)

        for v in v_samples:
            for w in w_samples:
                # 预测轨迹
                trajectory = self._predict_trajectory(current, v, w)

                # 评价轨迹
                score = self._evaluate_trajectory(
                    trajectory, goal, obstacles, v
                )

                if score > best_score:
                    best_score = score
                    best_velocity = np.array([v * np.cos(w), v * np.sin(w)])
                    best_trajectory = trajectory

        # 生成完整轨迹
        full_trajectory = self._predict_trajectory(
            current,
            np.linalg.norm(best_velocity),
            np.arctan2(best_velocity[1], best_velocity[0]),
        )

        path = [[int(round(p[0])), int(round(p[1]))] for p in full_trajectory]

        logger.info(
            "动态窗口法完成: 最优速度=%s, 评分=%.2f",
            tuple(best_velocity.round(2)),
            best_score,
        )
        return {
            "path": path,
            "trajectory": [[int(round(p[0])), int(round(p[1]))] for p in best_trajectory],
            "velocity": best_velocity.tolist(),
            "score": float(best_score),
        }

    def _compute_dynamic_window(
        self,
        current_vel: np.ndarray,
    ) -> dict[str, float]:
        """计算动态窗口范围。"""
        speed = float(np.linalg.norm(current_vel))

        # 速度空间：[当前速度 - 加速度*dt, 当前速度 + 加速度*dt]
        v_min = max(0.0, speed - self.max_accel * self.predict_time)
        v_max = min(self.max_speed, speed + self.max_accel * self.predict_time)

        # 角速度空间
        w_min = -self.max_yaw_rate
        w_max = self.max_yaw_rate

        return {"v_min": v_min, "v_max": v_max, "w_min": w_min, "w_max": w_max}

    def _predict_trajectory(
        self,
        position: np.ndarray,
        v: float,
        w: float,
    ) -> list[np.ndarray]:
        """预测给定速度下的轨迹。"""
        trajectory = [position.copy()]
        x, y = position[0], position[1]
        dt = 0.1

        for _ in range(int(self.predict_time / dt)):
            x += v * np.cos(w) * dt
            y += v * np.sin(w) * dt
            trajectory.append(np.array([x, y]))

        return trajectory

    def _evaluate_trajectory(
        self,
        trajectory: list[np.ndarray],
        goal: np.ndarray,
        obstacles: list[np.ndarray],
        speed: float,
    ) -> float:
        """评价轨迹质量。"""
        # 目标方向评分
        last_point = trajectory[-1]
        heading = np.linalg.norm(goal - last_point)
        heading_score = self.max_speed / (heading + 0.1)

        # 障碍物距离评分
        min_dist = float("inf")
        for point in trajectory:
            for obs in obstacles:
                dist = float(np.linalg.norm(point - obs))
                obs_r = 1.0
                min_dist = min(min_dist, dist - obs_r)

        if min_dist < 0:
            clearance_score = -10.0
        else:
            clearance_score = min_dist / (min_dist + 1.0)

        # 速度评分
        velocity_score = speed / self.max_speed

        # 综合评分
        score = (
            self.heading_weight * heading_score
            + self.clearance_weight * clearance_score
            + self.velocity_weight * velocity_score
        )

        return score

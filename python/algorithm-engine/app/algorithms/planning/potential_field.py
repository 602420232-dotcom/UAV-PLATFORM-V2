"""人工势场法路径规划算法。

基于物理学中势场概念的路径规划方法。
目标位置产生引力势场，障碍物产生斥力势场，
UAV在合力作用下沿势场梯度方向移动至目标。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class PotentialFieldPlanner:
    """人工势场法路径规划器。

    构建引力场（吸引至目标）和斥力场（排斥远离障碍物），
    通过合力引导UAV从起点移动到目标位置。

    Args:
        config: 配置字典，支持以下参数：
            - k_att: 引力系数，默认1.0
            - k_rep: 斥力系数，默认100.0
            - d0: 斥力影响距离，默认5.0
            - step_size: 移动步长，默认0.5
            - max_steps: 最大步数，默认1000
            - goal_threshold: 到达目标的距离阈值，默认1.0
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.k_att: float = self.config.get("k_att", 1.0)
        self.k_rep: float = self.config.get("k_rep", 100.0)
        self.d0: float = self.config.get("d0", 5.0)
        self.step_size: float = self.config.get("step_size", 0.5)
        self.max_steps: int = self.config.get("max_steps", 1000)
        self.goal_threshold: float = self.config.get("goal_threshold", 1.0)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行人工势场法路径规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 (int, int)
                - goal: 终点坐标 (int, int)
                - grid_size: 网格尺寸 (int, int)
                - obstacles: 障碍物列表 list[tuple[int, int]]

        Returns:
            包含 path（路径点列表）和 cost（路径代价）的字典。
        """
        np.random.seed(42)

        start = np.array(params.get("start", (0, 0)), dtype=float)
        goal = np.array(params.get("goal", (10, 10)), dtype=float)
        grid_size = params.get("grid_size", (50, 50))
        obstacles = [np.array(obs[:2], dtype=float) for obs in params.get("obstacles", [])]

        logger.info(
            "人工势场法规划: 起点=%s, 终点=%s, 障碍物=%d",
            tuple(start.astype(int)), tuple(goal.astype(int)), len(obstacles),
        )

        rows, cols = grid_size
        path = [start.copy()]
        current = start.copy()
        total_cost = 0.0

        for step in range(self.max_steps):
            # 计算到目标的距离
            dist_to_goal = np.linalg.norm(goal - current)

            if dist_to_goal < self.goal_threshold:
                path.append(goal.copy())
                total_cost += dist_to_goal
                logger.info(
                    "人工势场法完成: 到达目标, 步数=%d, 代价=%.2f",
                    step + 1, total_cost,
                )
                return {
                    "path": [[int(round(p[0])), int(round(p[1]))] for p in path],
                    "cost": total_cost,
                    "steps": step + 1,
                }

            # 引力（指向目标）
            f_att = self.k_att * (goal - current)

            # 斥力（远离障碍物）
            f_rep = np.zeros(2)
            for obs in obstacles:
                diff = current - obs
                dist = np.linalg.norm(diff)
                if dist < self.d0 and dist > 1e-6:
                    # 斥力大小与距离成反比
                    magnitude = self.k_rep * (1.0 / dist - 1.0 / self.d0) * (1.0 / dist ** 2)
                    f_rep += magnitude * diff / dist

            # 合力
            f_total = f_att + f_rep
            force_mag = np.linalg.norm(f_total)

            if force_mag < 1e-6:
                # 陷入局部最小值，添加随机扰动
                logger.debug("步 %d: 检测到局部最小值，添加随机扰动", step)
                f_total = np.random.randn(2) * 0.5
                force_mag = np.linalg.norm(f_total)

            # 归一化并移动
            direction = f_total / force_mag
            step_vec = direction * min(self.step_size, float(dist_to_goal))
            new_pos = current + step_vec

            # 边界约束
            new_pos[0] = np.clip(new_pos[0], 0, rows - 1)
            new_pos[1] = np.clip(new_pos[1], 0, cols - 1)

            total_cost += np.linalg.norm(step_vec)
            current = new_pos
            path.append(current.copy())

            if step % 100 == 0:
                logger.debug(
                    "步 %d: 位置=%s, 到目标距离=%.2f, 合力=%.4f",
                    step, tuple(current.astype(int)), dist_to_goal, force_mag,
                )

        logger.warning(
            "人工势场法未在最大步数内到达目标, 最终距离=%.2f",
            np.linalg.norm(goal - current),
        )
        return {
            "path": [[int(round(p[0])), int(round(p[1]))] for p in path],
            "cost": total_cost,
            "steps": self.max_steps,
            "reached": False,
        }

"""滚动时域规划（Receding Horizon Planning）算法。

基于有限时域预测和滚动优化的实时路径规划方法。
在每个时间步：
1. 在预测时域内求解最优局部路径
2. 执行局部路径的第一步
3. 滚动时域窗口，重复上述过程

适用于动态环境和需要实时响应的场景。
"""

from __future__ import annotations

import heapq
import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class RecedingHorizonPlanner:
    """滚动时域路径规划器。

    在有限的预测时域内使用A*搜索求解局部最优路径，
    执行第一步后滚动时域窗口继续规划。
    通过局部-全局结合实现实时路径规划。

    Args:
        config: 配置字典，支持以下参数：
            - horizon: 预测时域长度（步数），默认15
            - sub_horizon: 子目标更新频率，默认5
            - goal_weight: 目标方向权重，默认2.0
            - allow_diagonal: 是否允许对角移动，默认True
            - max_iterations: 最大滚动步数，默认500
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.horizon: int = self.config.get("horizon", 15)
        self.sub_horizon: int = self.config.get("sub_horizon", 5)
        self.goal_weight: float = self.config.get("goal_weight", 2.0)
        self.allow_diagonal: bool = self.config.get("allow_diagonal", True)
        self.max_iterations: int = self.config.get("max_iterations", 500)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行滚动时域路径规划。

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

        _start = params.get("start", (0, 0))
        start: tuple[int, int] = (int(_start[0]), int(_start[1]))
        _goal = params.get("goal", (10, 10))
        goal: tuple[int, int] = (int(_goal[0]), int(_goal[1]))
        grid_size = params.get("grid_size", (50, 50))
        obstacles = set(map(tuple, params.get("obstacles", [])))

        logger.info(
            "滚动时域规划: 起点=%s, 终点=%s, 时域=%d",
            start,
            goal,
            self.horizon,
        )

        rows, cols = grid_size

        if start == goal:
            return {"path": [list(start)], "cost": 0.0, "steps": 0}

        self._rows = rows
        self._cols = cols
        self._obstacles = obstacles

        current = start
        path = [list(current)]
        total_cost = 0.0
        steps = 0

        for iteration in range(self.max_iterations):
            if current == goal:
                logger.info(
                    "滚动时域规划完成: 到达目标, 步数=%d, 代价=%.2f",
                    steps,
                    total_cost,
                )
                break

            # 确定当前时域内的子目标
            sub_goal = self._compute_sub_goal(current, goal)

            # 在时域内搜索局部最优路径
            local_path = self._local_search(current, sub_goal, self.horizon)

            if not local_path or len(local_path) < 2:
                logger.warning("滚动时域: 无法找到局部路径, 步数=%d", steps)
                break

            # 执行局部路径（前进sub_horizon步或到达子目标）
            n_execute = min(self.sub_horizon, len(local_path) - 1)

            for i in range(1, n_execute + 1):
                next_pos = tuple(local_path[i])
                step_cost = self._edge_cost(current, next_pos)
                total_cost += step_cost
                current = next_pos
                path.append(list(current))
                steps += 1

                if current == goal:
                    break

            if steps % 20 == 0:
                logger.debug(
                    "滚动时域步 %d: 位置=%s, 到目标距离=%.1f",
                    steps,
                    current,
                    float(np.sqrt((current[0] - goal[0]) ** 2 + (current[1] - goal[1]) ** 2)),
                )

        return {
            "path": path,
            "cost": total_cost,
            "steps": steps,
            "iterations": iteration + 1,
        }

    def _compute_sub_goal(
        self,
        current: tuple[int, int],
        goal: tuple[int, int],
    ) -> tuple[int, int]:
        """计算当前时域的子目标。

        子目标位于当前到目标的连线上，距离不超过horizon。
        """
        dx = goal[0] - current[0]
        dy = goal[1] - current[1]
        dist = np.sqrt(dx**2 + dy**2)

        if dist <= self.horizon:
            return goal

        # 在当前到目标方向上取horizon距离的点
        ratio = self.horizon / dist
        sub_x = int(round(current[0] + dx * ratio))
        sub_y = int(round(current[1] + dy * ratio))

        # 确保在网格内
        sub_x = max(0, min(self._rows - 1, sub_x))
        sub_y = max(0, min(self._cols - 1, sub_y))

        # 如果子目标在障碍物上，搜索最近的自由点
        if (sub_x, sub_y) in self._obstacles:
            for r in range(1, self.horizon):
                for angle_offset in np.linspace(0, 2 * np.pi, 8, endpoint=False):
                    nx = int(round(sub_x + r * np.cos(angle_offset)))
                    ny = int(round(sub_y + r * np.sin(angle_offset)))
                    if (
                        0 <= nx < self._rows
                        and 0 <= ny < self._cols
                        and (nx, ny) not in self._obstacles
                    ):
                        return (nx, ny)

        return (sub_x, sub_y)

    def _local_search(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
        max_depth: int,
    ) -> list[list[int]]:
        """在有限深度内执行局部A*搜索。"""
        open_set: list[tuple[float, tuple[int, int], int]] = []
        h0 = self._heuristic(start, goal)
        heapq.heappush(open_set, (h0, start, 0))
        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], float] = {start: 0.0}
        closed: set[tuple[int, int]] = set()

        while open_set:
            _, current, depth = heapq.heappop(open_set)

            if current in closed:
                continue
            closed.add(current)

            if current == goal or depth >= max_depth:
                # 回溯路径
                path = [list(current)]
                node = current
                while node in came_from:
                    node = came_from[node]
                    path.append(list(node))
                path.reverse()
                return path

            for neighbor in self._get_neighbors(current):
                if neighbor in closed:
                    continue

                edge_cost = self._edge_cost(current, neighbor)
                new_g = g_score[current] + edge_cost

                if new_g < g_score.get(neighbor, float("inf")):
                    g_score[neighbor] = new_g
                    came_from[neighbor] = current
                    # 使用加权启发式引导向全局目标方向
                    h = self._heuristic(neighbor, goal) * self.goal_weight
                    heapq.heappush(open_set, (new_g + h, neighbor, depth + 1))

        return []

    def _heuristic(
        self,
        a: tuple[int, int],
        b: tuple[int, int],
    ) -> float:
        """欧几里得距离启发式。"""
        return float(np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))

    def _edge_cost(
        self,
        a: tuple[int, int],
        b: tuple[int, int],
    ) -> float:
        """计算边代价。"""
        dx = abs(b[0] - a[0])
        dy = abs(b[1] - a[1])
        return 1.414 if dx + dy == 2 else 1.0

    def _get_neighbors(
        self,
        pos: tuple[int, int],
    ) -> list[tuple[int, int]]:
        """获取可行邻居节点。"""
        if self.allow_diagonal:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        neighbors = []
        for dx, dy in directions:
            nx, ny = pos[0] + dx, pos[1] + dy
            if 0 <= nx < self._rows and 0 <= ny < self._cols and (nx, ny) not in self._obstacles:
                neighbors.append((nx, ny))
        return neighbors

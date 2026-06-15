"""优先级规划（Prioritized Planning）多智能体路径规划算法。

为多个智能体按优先级依次规划路径的方法。
按照预设优先级顺序，依次为每个智能体规划路径，
已规划的智能体路径作为后续智能体的动态障碍物。
简单高效，但不保证全局最优。
"""

from __future__ import annotations

import heapq
import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class PrioritizedPlanningPlanner:
    """优先级规划多智能体路径规划器。

    按优先级顺序依次为每个智能体规划路径。
    高优先级智能体的路径作为低优先级智能体的
    时间-空间约束（动态障碍物）。

    Args:
        config: 配置字典，支持以下参数：
            - time_limit: 单智能体路径规划最大步数，默认200
            - priority_strategy: 优先级策略，默认"distance"（按到目标距离排序）
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.time_limit: int = self.config.get("time_limit", 200)
        self.priority_strategy: str = self.config.get("priority_strategy", "distance")

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行优先级规划多智能体路径规划。

        Args:
            params: 规划参数字典，包含：
                - agents: 智能体列表，每个智能体为字典，含 start 和 goal
                - grid_size: 网格尺寸 (int, int)
                - obstacles: 障碍物列表 list[tuple[int, int]]

        Returns:
            包含以下键的字典：
                - paths: 每个智能体的路径列表
                - cost: 总代价（所有路径长度之和）
                - priorities: 智能体优先级顺序
        """
        np.random.seed(42)

        agents = params.get("agents", [])
        grid_size = tuple(params.get("grid_size", (50, 50)))
        obstacles = set(map(tuple, params.get("obstacles", [])))

        if not agents:
            logger.warning("优先级规划: 无智能体输入")
            return {"paths": [], "cost": 0.0, "priorities": []}

        logger.info(
            "优先级规划: 智能体数=%d, 网格=%s, 障碍物=%d",
            len(agents),
            grid_size,
            len(obstacles),
        )

        rows, cols = grid_size
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

        # 确定优先级顺序
        priorities = self._compute_priorities(agents)

        paths: list[list] = [None] * len(agents)
        dynamic_constraints: dict[int, set] = {}  # time -> set of occupied positions

        total_cost = 0.0
        success = True

        for rank, agent_idx in enumerate(priorities):
            agent = agents[agent_idx]
            raw_start = agent.get("start", (0, 0))
            raw_goal = agent.get("goal", (0, 0))
            start = (int(raw_start[0]), int(raw_start[1]))
            goal = (int(raw_goal[0]), int(raw_goal[1]))

            # 合并静态障碍物和动态约束
            all_obstacles = obstacles.copy()

            # 使用时空A*搜索
            path = self._spacetime_astar(
                start, goal, rows, cols, all_obstacles, directions, dynamic_constraints
            )

            if path is None:
                logger.warning(
                    "优先级规划: 智能体 %d (优先级 %d) 无法找到路径",
                    agent_idx,
                    rank,
                )
                success = False
                paths[agent_idx] = []
                continue

            paths[agent_idx] = path
            total_cost += len(path)

            # 将该智能体的路径加入动态约束
            for t, pos in enumerate(path):
                if t not in dynamic_constraints:
                    dynamic_constraints[t] = set()
                dynamic_constraints[t].add((pos[0], pos[1]))

            logger.debug(
                "智能体 %d (优先级 %d): 路径长度=%d",
                agent_idx,
                rank,
                len(path),
            )

        if success:
            logger.info(
                "优先级规划完成: 总代价=%.1f, 优先级=%s",
                total_cost,
                priorities,
            )
        else:
            logger.warning("优先级规划: 部分智能体规划失败")

        return {
            "paths": paths,
            "cost": total_cost,
            "priorities": priorities,
            "success": success,
        }

    def _compute_priorities(self, agents: list[dict]) -> list[int]:
        """计算智能体优先级顺序。"""
        if self.priority_strategy == "distance":
            # 按到目标距离排序（远的优先）
            distances = []
            for i, agent in enumerate(agents):
                s = np.array(agent.get("start", (0, 0)), dtype=float)
                g = np.array(agent.get("goal", (0, 0)), dtype=float)
                distances.append((float(np.linalg.norm(g - s)), i))
            distances.sort(reverse=True)
            return [idx for _, idx in distances]
        elif self.priority_strategy == "index":
            return list(range(len(agents)))
        else:
            return list(range(len(agents)))

    def _spacetime_astar(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
        directions: list,
        dynamic_constraints: dict[int, set],
    ) -> list[list[int]] | None:
        """时空A*搜索，考虑动态障碍物约束。"""
        open_heap: list[tuple] = []
        g_score: dict[tuple, float] = {}
        came_from: dict[tuple, tuple] = {}

        start_state = (start[0], start[1], 0)
        h0 = abs(start[0] - goal[0]) + abs(start[1] - goal[1])
        g_score[start_state] = 0.0
        heapq.heappush(open_heap, (h0, start_state))

        while open_heap:
            _f, current = heapq.heappop(open_heap)
            cx, cy, ct = current

            if (cx, cy) == goal:
                path = []
                state = current
                while state in came_from:
                    path.append([state[0], state[1]])
                    state = came_from[state]
                path.append([start[0], start[1]])
                path.reverse()
                return path

            if g_score.get(current, float("inf")) < ct:
                continue

            for dx, dy in directions:
                nx, ny = cx + dx, cy + dy
                nt = ct + 1

                if not (0 <= nx < rows and 0 <= ny < cols):
                    continue
                if (nx, ny) in obstacles:
                    continue

                # 动态约束检查
                if nt in dynamic_constraints and (nx, ny) in dynamic_constraints[nt]:
                    continue

                move_cost = 1.414 if abs(dx) + abs(dy) == 2 else 1.0
                new_g = g_score[current] + move_cost
                next_state = (nx, ny, nt)

                if new_g < g_score.get(next_state, float("inf")):
                    g_score[next_state] = new_g
                    h = abs(nx - goal[0]) + abs(ny - goal[1])
                    heapq.heappush(open_heap, (new_g + h, next_state))
                    came_from[next_state] = current

            # 允许等待
            wait_state = (cx, cy, ct + 1)
            if ct + 1 not in dynamic_constraints or (cx, cy) not in dynamic_constraints.get(ct + 1, set()):
                new_g = g_score[current] + 1.0
                if new_g < g_score.get(wait_state, float("inf")):
                    g_score[wait_state] = new_g
                    h = abs(cx - goal[0]) + abs(cy - goal[1])
                    heapq.heappush(open_heap, (new_g + h, wait_state))
                    came_from[wait_state] = current

            if ct >= self.time_limit:
                break

        return None

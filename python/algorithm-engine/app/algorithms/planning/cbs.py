"""CBS（Conflict-Based Search，冲突基搜索）多智能体路径规划算法。

基于两层搜索框架的多智能体路径规划方法：
- 高层搜索：维护约束树（Constraint Tree），选择冲突并添加约束进行分支
- 低层搜索：在给定约束条件下，为单个智能体规划最优路径
通过迭代解决冲突，最终找到所有智能体的无冲突路径集合。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ConflictBasedSearch:
    """CBS多智能体路径规划器。

    使用冲突基搜索算法为多个智能体规划无冲突路径。
    高层搜索在约束树中选择冲突并分支，低层搜索为受约束的
    单个智能体规划最优路径（基于A*算法）。

    Args:
        config: 配置字典，支持以下参数：
            - max_iterations: 最大迭代次数，默认100
            - time_limit: 单智能体路径规划最大步数，默认200
            - priority_planning: 是否使用优先级规划作为初始解，默认True
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.max_iterations: int = self.config.get("max_iterations", 100)
        self.time_limit: int = self.config.get("time_limit", 200)
        self.priority_planning: bool = self.config.get("priority_planning", True)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行CBS多智能体路径规划。

        Args:
            params: 规划参数字典，包含：
                - agents: 智能体列表，每个智能体为字典，含 start 和 goal
                - grid_size: 网格尺寸 (int, int)
                - obstacles: 障碍物列表 list[tuple[int, int]]
                - max_iterations: 最大迭代次数（可选，覆盖配置）

        Returns:
            包含以下键的字典：
                - paths: 每个智能体的路径列表
                - conflicts: 解决的冲突列表
                - cost: 总代价（所有路径长度之和）
        """
        np.random.seed(42)

        agents = params.get("agents", [])
        grid_size = tuple(params.get("grid_size", (50, 50)))
        obstacles = set(map(tuple, params.get("obstacles", [])))
        max_iter = params.get("max_iterations", self.max_iterations)

        if not agents:
            logger.warning("CBS规划: 无智能体输入")
            return {"paths": [], "conflicts": [], "cost": 0.0}

        logger.info(
            "CBS规划: 智能体数=%d, 网格=%s, 障碍物=%d",
            len(agents), grid_size, len(obstacles),
        )

        rows, cols = grid_size
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                      (-1, -1), (-1, 1), (1, -1), (1, 1)]

        # 初始约束：每个智能体无约束
        initial_constraints: list[dict[int, list]] = [
            {} for _ in agents
        ]

        # 为每个智能体规划初始路径
        initial_solution = self._find_initial_solution(
            agents, rows, cols, obstacles, directions,
        )

        if initial_solution is None:
            logger.warning("CBS规划: 无法为所有智能体找到初始路径")
            return {"paths": [], "conflicts": [], "cost": float("inf")}

        initial_paths, initial_cost = initial_solution

        # 约束树节点: (cost, paths, constraints, conflicts)
        open_list: list[tuple] = []
        root_conflicts = self._find_all_conflicts(initial_paths)
        open_list.append((initial_cost, initial_paths, initial_constraints, root_conflicts))

        resolved_conflicts: list[dict[str, Any]] = []
        iteration = 0

        while open_list and iteration < max_iter:
            iteration += 1

            # 按代价排序，取最优节点
            open_list.sort(key=lambda x: x[0])
            current_cost, current_paths, current_constraints, current_conflicts = open_list.pop(0)

            if not current_conflicts:
                logger.info(
                    "CBS规划完成: 无冲突解, 总代价=%.2f, 迭代=%d",
                    current_cost, iteration,
                )
                return {
                    "paths": current_paths,
                    "conflicts": resolved_conflicts,
                    "cost": current_cost,
                }

            # 选择第一个冲突
            conflict = current_conflicts[0]
            resolved_conflicts.append(conflict)

            # 对冲突中的两个智能体分别添加约束
            agent_a = conflict["agent_a"]
            agent_b = conflict["agent_b"]
            conflict_time = conflict["time"]
            conflict_pos = conflict["position"]

            for constrained_agent, other_agent in [(agent_a, agent_b), (agent_b, agent_a)]:
                # 创建新约束
                new_constraints = [dict(c) for c in current_constraints]
                if constrained_agent not in new_constraints[constrained_agent]:
                    new_constraints[constrained_agent][constrained_agent] = []
                new_constraints[constrained_agent][constrained_agent].append({
                    "time": conflict_time,
                    "position": conflict_pos,
                })

                # 重新规划受约束智能体的路径
                new_path = self._low_level_search(
                    agents[constrained_agent]["start"],
                    agents[constrained_agent]["goal"],
                    rows, cols, obstacles, directions,
                    new_constraints[constrained_agent].get(constrained_agent, []),
                )

                if new_path is None:
                    continue

                # 计算新解的总代价
                new_paths = list(current_paths)
                new_paths[constrained_agent] = new_path
                new_cost = sum(len(p) for p in new_paths)

                # 检测新解中的冲突
                new_conflicts = self._find_all_conflicts(new_paths)
                open_list.append((new_cost, new_paths, new_constraints, new_conflicts))

            if iteration % 10 == 0:
                logger.debug(
                    "CBS迭代 %d: 开放节点=%d, 已解决冲突=%d",
                    iteration, len(open_list), len(resolved_conflicts),
                )

        logger.warning(
            "CBS规划达到迭代上限: 迭代=%d, 已解决冲突=%d",
            iteration, len(resolved_conflicts),
        )

        # 返回当前最优解
        if open_list:
            open_list.sort(key=lambda x: x[0])
            best_cost, best_paths, _, _ = open_list[0]
            return {
                "paths": best_paths,
                "conflicts": resolved_conflicts,
                "cost": best_cost,
            }

        return {
            "paths": initial_paths,
            "conflicts": resolved_conflicts,
            "cost": initial_cost,
        }

    def _find_initial_solution(
        self,
        agents: list[dict],
        rows: int,
        cols: int,
        obstacles: set,
        directions: list,
    ) -> Optional[tuple[list, float]]:
        """为所有智能体规划初始路径。

        使用优先级规划策略，依次为每个智能体规划路径，
        已规划的智能体路径作为后续智能体的动态障碍物。

        Returns:
            (paths, total_cost) 或 None（若有智能体无法规划）
        """
        paths: list[list] = []
        dynamic_obstacles: set = set()

        for i, agent in enumerate(agents):
            raw_start = agent.get("start", (0, 0))
            raw_goal = agent.get("goal", (0, 0))
            start = (int(raw_start[0]), int(raw_start[1]))
            goal = (int(raw_goal[0]), int(raw_goal[1]))

            all_obstacles = obstacles | dynamic_obstacles
            path = self._low_level_search(
                start, goal, rows, cols, all_obstacles, directions, [],
            )

            if path is None:
                logger.warning("CBS: 智能体 %d 无法找到初始路径", i)
                return None

            paths.append(path)
            # 将该智能体的路径加入动态障碍物（仅位置，不包含时间维度）
            for pos in path:
                dynamic_obstacles.add(pos)

        total_cost = sum(len(p) for p in paths)
        return paths, float(total_cost)

    def _low_level_search(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
        directions: list,
        constraints: list[dict],
    ) -> Optional[list[list[int]]]:
        """低层搜索：带约束的A*路径规划。

        在给定顶点约束和时间约束条件下，为单个智能体规划
        从起点到终点的最短路径。

        Args:
            start: 起点坐标
            goal: 终点坐标
            rows: 网格行数
            cols: 网格列数
            obstacles: 障碍物集合
            directions: 可移动方向列表
            constraints: 约束列表，每个约束含 time 和 position

        Returns:
            路径列表（每个元素为 [x, y]），或 None
        """
        # 构建约束集合用于快速查询
        constraint_set: set[tuple[int, tuple[int, int]]] = set()
        for c in constraints:
            t = c.get("time", -1)
            pos = tuple(c.get("position", (-1, -1)))
            constraint_set.add((t, pos))

        # A* 搜索（状态: (x, y, time)）
        import heapq

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
                # 回溯路径
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

                # 边界检查
                if not (0 <= nx < rows and 0 <= ny < cols):
                    continue

                # 障碍物检查
                if (nx, ny) in obstacles:
                    continue

                # 约束检查：在时间 nt 不能位于 (nx, ny)
                if (nt, (nx, ny)) in constraint_set:
                    continue

                move_cost = 1.414 if abs(dx) + abs(dy) == 2 else 1.0
                new_g = g_score[current] + move_cost
                next_state = (nx, ny, nt)

                if new_g < g_score.get(next_state, float("inf")):
                    g_score[next_state] = new_g
                    h = abs(nx - goal[0]) + abs(ny - goal[1])
                    heapq.heappush(open_heap, (new_g + h, next_state))
                    came_from[next_state] = current

            # 允许等待（原地不动）
            wait_state = (cx, cy, ct + 1)
            if (ct + 1, (cx, cy)) not in constraint_set:
                new_g = g_score[current] + 1.0
                if new_g < g_score.get(wait_state, float("inf")):
                    g_score[wait_state] = new_g
                    h = abs(cx - goal[0]) + abs(cy - goal[1])
                    heapq.heappush(open_heap, (new_g + h, wait_state))
                    came_from[wait_state] = current

            if ct >= self.time_limit:
                break

        return None

    def _find_all_conflicts(self, paths: list) -> list[dict[str, Any]]:
        """检测所有智能体路径之间的冲突。

        支持顶点冲突（两个智能体在同一时间位于同一位置）
        和跟随冲突（两个智能体在相邻时间交换位置）。

        Args:
            paths: 所有智能体的路径列表

        Returns:
            冲突列表，每个冲突为字典
        """
        conflicts: list[dict[str, Any]] = []
        max_len = max((len(p) for p in paths), default=0)

        # 构建位置-时间映射
        for i in range(len(paths)):
            for j in range(i + 1, len(paths)):
                path_a = paths[i]
                path_b = paths[j]

                for t in range(max_len):
                    pos_a = path_a[min(t, len(path_a) - 1)]
                    pos_b = path_b[min(t, len(path_b) - 1)]

                    # 顶点冲突
                    if pos_a[0] == pos_b[0] and pos_a[1] == pos_b[1]:
                        conflicts.append({
                            "type": "vertex",
                            "agent_a": i,
                            "agent_b": j,
                            "time": t,
                            "position": [pos_a[0], pos_a[1]],
                        })

                    # 跟随冲突（交换位置）
                    if t > 0:
                        prev_a = path_a[min(t - 1, len(path_a) - 1)]
                        prev_b = path_b[min(t - 1, len(path_b) - 1)]
                        if (pos_a[0] == prev_b[0] and pos_a[1] == prev_b[1]
                                and pos_b[0] == prev_a[0] and pos_b[1] == prev_a[1]):
                            conflicts.append({
                                "type": "swap",
                                "agent_a": i,
                                "agent_b": j,
                                "time": t,
                                "position": [pos_a[0], pos_a[1]],
                            })

        return conflicts

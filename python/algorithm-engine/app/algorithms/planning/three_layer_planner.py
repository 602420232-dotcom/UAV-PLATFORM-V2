"""三层规划器（Three-Layer Planner）路径规划算法。

采用分层架构的路径规划方法，将规划任务分解为三个层次：
战略层（Strategic Layer）负责全局航点生成，确定关键途经点；
战术层（Tactical Layer）负责相邻航点间的路径规划，生成可执行路径；
执行层（Execution Layer）负责局部避障和实时控制指令生成。
各层协同工作，实现从全局到局部的完整规划能力。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ThreeLayerPlanner:
    """三层路径规划器。

    将路径规划任务分解为战略层、战术层和执行层三个层次：
    - 战略层：基于全局信息生成关键航点序列，考虑地形特征和任务约束
    - 战术层：在相邻航点间进行详细路径规划，生成平滑可执行路径
    - 执行层：在局部范围内进行实时避障，生成底层控制指令

    Args:
        config: 配置字典，支持以下参数：
            - strategic_resolution: 战略层网格分辨率，默认5
            - strategic_smoothing: 战略层路径平滑系数，默认0.3
            - tactical_method: 战术层规划方法，默认"astar"
            - tactical_smoothing: 战术层路径平滑迭代次数，默认3
            - execution_horizon: 执行层感知范围，默认5
            - execution_step_size: 执行层步长，默认1
            - execution_safety_margin: 执行层安全边距，默认2
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.strategic_resolution: int = self.config.get(
            "strategic_resolution",
            5,
        )
        self.strategic_smoothing: float = self.config.get(
            "strategic_smoothing",
            0.3,
        )
        self.tactical_method: str = self.config.get(
            "tactical_method",
            "astar",
        )
        self.tactical_smoothing: int = self.config.get(
            "tactical_smoothing",
            3,
        )
        self.execution_horizon: int = self.config.get(
            "execution_horizon",
            5,
        )
        self.execution_step_size: int = self.config.get(
            "execution_step_size",
            1,
        )
        self.execution_safety_margin: int = self.config.get(
            "execution_safety_margin",
            2,
        )

        # 8方向移动
        self.directions = [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
        ]

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行三层路径规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 (int, int)
                - goal: 终点坐标 (int, int)
                - grid_size: 网格尺寸 (int, int)
                - obstacles: 障碍物列表 list[tuple[int, int]]
                - waypoints: 可选中间航点列表 list[tuple[int, int]]

        Returns:
            包含以下字段的字典：
                - strategic_plan: 战略层航点序列 list[list[int]]
                - tactical_path: 战术层路径 list[list[int]]
                - execution_controls: 执行层控制指令 list[dict]
                - layers_output: 各层详细输出 dict
        """
        np.random.seed(42)

        raw_start = params.get("start", (0, 0))
        raw_goal = params.get("goal", (10, 10))
        start: tuple[int, int] = (int(raw_start[0]), int(raw_start[1]))
        goal: tuple[int, int] = (int(raw_goal[0]), int(raw_goal[1]))
        grid_size = tuple(params.get("grid_size", (50, 50)))
        obstacles = set(map(tuple, params.get("obstacles", [])))
        user_waypoints = [(int(w[0]), int(w[1])) for w in params.get("waypoints", [])]

        logger.info(
            "三层规划: 起点=%s, 终点=%s, 网格=%s, 障碍物=%d, 用户航点=%d",
            start,
            goal,
            grid_size,
            len(obstacles),
            len(user_waypoints),
        )

        rows, cols = grid_size

        # ===== 战略层：生成全局航点序列 =====
        strategic_plan, strategic_output = self._strategic_layer(
            start,
            goal,
            rows,
            cols,
            obstacles,
            user_waypoints,
        )
        logger.info(
            "战略层完成: 航点数=%d, 距离=%.2f",
            len(strategic_plan),
            strategic_output["total_distance"],
        )

        # ===== 战术层：航点间路径规划 =====
        tactical_path, tactical_output = self._tactical_layer(
            strategic_plan,
            rows,
            cols,
            obstacles,
        )
        logger.info(
            "战术层完成: 路径点数=%d, 代价=%.2f",
            len(tactical_path),
            tactical_output["total_cost"],
        )

        # ===== 执行层：局部避障与控制指令 =====
        execution_controls, execution_output = self._execution_layer(
            tactical_path,
            rows,
            cols,
            obstacles,
        )
        logger.info(
            "执行层完成: 控制指令数=%d, 避障次数=%d",
            len(execution_controls),
            execution_output["avoidance_count"],
        )

        # 汇总各层输出
        layers_output = {
            "strategic": strategic_output,
            "tactical": tactical_output,
            "execution": execution_output,
        }

        logger.info(
            "三层规划完成: 战略航点=%d, 战术路径=%d, 控制指令=%d",
            len(strategic_plan),
            len(tactical_path),
            len(execution_controls),
        )

        return {
            "strategic_plan": strategic_plan,
            "tactical_path": tactical_path,
            "execution_controls": execution_controls,
            "layers_output": layers_output,
        }

    # ==================== 战略层 ====================

    def _strategic_layer(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
        user_waypoints: list[tuple[int, int]],
    ) -> tuple[list[list[int]], dict[str, Any]]:
        """战略层：生成全局航点序列。

        在粗分辨率网格上规划全局路径，生成关键航点。
        如果用户提供了中间航点，则将其纳入规划。
        使用简化搜索在低分辨率空间中快速生成全局路线。

        Args:
            start: 起点。
            goal: 终点。
            rows: 网格行数。
            cols: 网格列数。
            obstacles: 障碍物集合。
            user_waypoints: 用户指定的中间航点。

        Returns:
            (航点序列, 战略层输出信息)。
        """
        res = self.strategic_resolution
        s_rows = max(rows // res, 2)
        s_cols = max(cols // res, 2)

        # 构建粗分辨率障碍物地图
        coarse_obstacles: set[tuple[int, int]] = set()
        for ox, oy in obstacles:
            cx, cy = ox // res, oy // res
            coarse_obstacles.add((cx, cy))

        # 粗分辨率坐标
        s_start = (start[0] // res, start[1] // res)
        s_goal = (goal[0] // res, goal[1] // res)

        # 确保起终点不在障碍物中
        s_start = self._find_nearest_free(
            s_start,
            s_rows,
            s_cols,
            coarse_obstacles,
        )
        s_goal = self._find_nearest_free(
            s_goal,
            s_rows,
            s_cols,
            coarse_obstacles,
        )

        # 构建航点序列（包含用户航点）
        coarse_waypoints = [(w[0] // res, w[1] // res) for w in user_waypoints]
        coarse_waypoints = [
            self._find_nearest_free(wp, s_rows, s_cols, coarse_obstacles)
            for wp in coarse_waypoints
        ]

        # 在航点间依次搜索
        all_coarse_points = [s_start] + coarse_waypoints + [s_goal]
        coarse_path: list[tuple[int, int]] = [all_coarse_points[0]]

        for i in range(len(all_coarse_points) - 1):
            segment = self._coarse_astar(
                all_coarse_points[i],
                all_coarse_points[i + 1],
                s_rows,
                s_cols,
                coarse_obstacles,
            )
            if segment:
                # 避免重复添加连接点
                if len(coarse_path) > 0 and segment[0] == coarse_path[-1]:
                    coarse_path.extend(segment[1:])
                else:
                    coarse_path.extend(segment)
            else:
                # 搜索失败，直接连接
                coarse_path.append(all_coarse_points[i + 1])

        # 降采样航点（每隔几个点取一个关键航点）
        strategic_waypoints = self._downsample_path(
            coarse_path,
            min_interval=max(2, len(coarse_path) // 10),
        )

        # 转换回原始分辨率
        strategic_plan = [[int(p[0] * res), int(p[1] * res)] for p in strategic_waypoints]

        # 确保起点和终点精确
        strategic_plan[0] = [start[0], start[1]]
        strategic_plan[-1] = [goal[0], goal[1]]

        # 计算航点间距
        total_distance = 0.0
        for i in range(len(strategic_plan) - 1):
            dx = strategic_plan[i + 1][0] - strategic_plan[i][0]
            dy = strategic_plan[i + 1][1] - strategic_plan[i][1]
            total_distance += np.sqrt(dx**2 + dy**2)

        strategic_output = {
            "coarse_grid_size": (s_rows, s_cols),
            "coarse_path_length": len(coarse_path),
            "num_waypoints": len(strategic_plan),
            "total_distance": total_distance,
            "user_waypoints_included": len(user_waypoints),
            "resolution": res,
        }

        return strategic_plan, strategic_output

    def _coarse_astar(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
    ) -> list[tuple[int, int]]:
        """在粗分辨率网格上执行A*搜索。

        Args:
            start: 起点。
            goal: 终点。
            rows: 网格行数。
            cols: 网格列数。
            obstacles: 障碍物集合。

        Returns:
            路径点列表，搜索失败返回空列表。
        """
        import heapq

        if start == goal:
            return [start]

        open_set: list[tuple] = []
        heapq.heappush(open_set, (0, start))
        came_from: dict[tuple, tuple] = {}
        g_score = {start: 0.0}

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                return path

            for dx, dy in self.directions:
                nx, ny = current[0] + dx, current[1] + dy
                neighbor = (nx, ny)

                if not (0 <= nx < rows and 0 <= ny < cols):
                    continue
                if neighbor in obstacles:
                    continue

                move_cost = 1.414 if abs(dx) + abs(dy) == 2 else 1.0
                tentative_g = g_score[current] + move_cost

                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h = abs(nx - goal[0]) + abs(ny - goal[1])
                    heapq.heappush(open_set, (tentative_g + h, neighbor))

        return []

    def _find_nearest_free(
        self,
        pos: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
    ) -> tuple[int, int]:
        """找到距离给定位置最近的自由格子。

        Args:
            pos: 目标位置。
            rows: 网格行数。
            cols: 网格列数。
            obstacles: 障碍物集合。

        Returns:
            最近的自由格子坐标。
        """
        if pos not in obstacles and 0 <= pos[0] < rows and 0 <= pos[1] < cols:
            return pos

        for r in range(1, max(rows, cols)):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    nx, ny = pos[0] + dx, pos[1] + dy
                    if 0 <= nx < rows and 0 <= ny < cols and (nx, ny) not in obstacles:
                        return (nx, ny)

        return (min(pos[0], rows - 1), min(pos[1], cols - 1))

    def _downsample_path(
        self,
        path: list[tuple[int, int]],
        min_interval: int = 2,
    ) -> list[tuple[int, int]]:
        """对路径进行降采样，保留关键转折点。

        Args:
            path: 原始路径。
            min_interval: 最小采样间隔。

        Returns:
            降采样后的路径点列表。
        """
        if len(path) <= 2:
            return list(path)

        result = [path[0]]
        for i in range(1, len(path) - 1):
            prev_dir = (
                path[i][0] - path[i - 1][0],
                path[i][1] - path[i - 1][1],
            )
            next_dir = (
                path[i + 1][0] - path[i][0],
                path[i + 1][1] - path[i][1],
            )
            # 保留方向改变的点（转折点）
            if prev_dir != next_dir:
                result.append(path[i])
            # 按间隔采样
            elif len(result) == 0 or (
                abs(path[i][0] - result[-1][0]) + abs(path[i][1] - result[-1][1]) >= min_interval
            ):
                result.append(path[i])

        result.append(path[-1])
        return result

    # ==================== 战术层 ====================

    def _tactical_layer(
        self,
        strategic_plan: list[list[int]],
        rows: int,
        cols: int,
        obstacles: set,
    ) -> tuple[list[list[int]], dict[str, Any]]:
        """战术层：在相邻战略航点间进行详细路径规划。

        使用A*算法在原始分辨率网格上规划相邻航点间的路径，
        然后进行路径平滑处理，生成连续可执行的路径。

        Args:
            strategic_plan: 战略层航点序列。
            rows: 网格行数。
            cols: 网格列数。
            obstacles: 障碍物集合。

        Returns:
            (完整路径, 战术层输出信息)。
        """
        full_path: list[list[int]] = []
        segment_costs: list[float] = []
        segment_lengths: list[int] = []

        for i in range(len(strategic_plan) - 1):
            wp_start = (strategic_plan[i][0], strategic_plan[i][1])
            wp_goal = (strategic_plan[i + 1][0], strategic_plan[i + 1][1])

            segment = self._tactical_astar(
                wp_start,
                wp_goal,
                rows,
                cols,
                obstacles,
            )

            if segment:
                cost = self._segment_cost(segment)
                segment_costs.append(cost)
                segment_lengths.append(len(segment))

                # 避免重复添加连接点
                if full_path and segment[0] == (
                    full_path[-1][0],
                    full_path[-1][1],
                ):
                    full_path.extend(
                        [[p[0], p[1]] for p in segment[1:]],
                    )
                else:
                    full_path.extend([[p[0], p[1]] for p in segment])
            else:
                # 搜索失败，直线连接
                full_path.append(strategic_plan[i + 1])
                segment_costs.append(0.0)
                segment_lengths.append(0)

        # 路径平滑
        smoothed_path = self._smooth_path(full_path, obstacles, rows, cols)

        total_cost = sum(segment_costs)
        total_smoothness = self._compute_smoothness(smoothed_path)

        tactical_output = {
            "method": self.tactical_method,
            "num_segments": len(strategic_plan) - 1,
            "segment_costs": segment_costs,
            "segment_lengths": segment_lengths,
            "total_cost": total_cost,
            "path_length": len(smoothed_path),
            "smoothness": total_smoothness,
            "smoothing_iterations": self.tactical_smoothing,
        }

        return smoothed_path, tactical_output

    def _tactical_astar(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
    ) -> list[tuple[int, int]]:
        """在原始分辨率网格上执行A*搜索。

        Args:
            start: 起点。
            goal: 终点。
            rows: 网格行数。
            cols: 网格列数。
            obstacles: 障碍物集合。

        Returns:
            路径点列表，搜索失败返回空列表。
        """
        import heapq

        if start == goal:
            return [start]

        open_set: list[tuple] = []
        heapq.heappush(open_set, (0, start))
        came_from: dict[tuple, tuple] = {}
        g_score = {start: 0.0}

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                return path

            for dx, dy in self.directions:
                nx, ny = current[0] + dx, current[1] + dy
                neighbor = (nx, ny)

                if not (0 <= nx < rows and 0 <= ny < cols):
                    continue
                if neighbor in obstacles:
                    continue

                move_cost = 1.414 if abs(dx) + abs(dy) == 2 else 1.0
                tentative_g = g_score[current] + move_cost

                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h = abs(nx - goal[0]) + abs(ny - goal[1])
                    heapq.heappush(open_set, (tentative_g + h, neighbor))

        return []

    def _segment_cost(self, segment: list[tuple[int, int]]) -> float:
        """计算路径段的代价。

        Args:
            segment: 路径段。

        Returns:
            路径段代价。
        """
        cost = 0.0
        for i in range(len(segment) - 1):
            dx = abs(segment[i + 1][0] - segment[i][0])
            dy = abs(segment[i + 1][1] - segment[i][1])
            cost += 1.414 if dx + dy == 2 else 1.0
        return cost

    def _smooth_path(
        self,
        path: list[list[int]],
        obstacles: set,
        rows: int,
        cols: int,
    ) -> list[list[int]]:
        """路径平滑处理。

        通过迭代移除不必要的中间点来简化路径，
        仅当两点间存在无障碍直线连接时才移除中间点。

        Args:
            path: 原始路径。
            obstacles: 障碍物集合。
            rows: 网格行数。
            cols: 网格列数。

        Returns:
            平滑后的路径。
        """
        if len(path) <= 2:
            return list(path)

        smoothed = list(path)
        for _ in range(self.tactical_smoothing):
            new_smoothed = [smoothed[0]]
            i = 0
            while i < len(smoothed) - 1:
                # 尝试跳过中间点
                best_j = i + 1
                for j in range(len(smoothed) - 1, i + 1, -1):
                    if self._line_of_sight(
                        smoothed[i],
                        smoothed[j],
                        obstacles,
                        rows,
                        cols,
                    ):
                        best_j = j
                        break
                new_smoothed.append(smoothed[best_j])
                i = best_j

            smoothed = new_smoothed
            if len(smoothed) <= 2:
                break

        return smoothed

    def _line_of_sight(
        self,
        p1: list[int],
        p2: list[int],
        obstacles: set,
        rows: int,
        cols: int,
    ) -> bool:
        """检查两点之间是否存在无障碍视线。

        使用Bresenham直线算法检查路径上的所有格子是否无障碍。

        Args:
            p1: 起点。
            p2: 终点。
            obstacles: 障碍物集合。
            rows: 网格行数。
            cols: 网格列数。

        Returns:
            True表示视线通畅。
        """
        x0, y0 = p1[0], p1[1]
        x1, y1 = p2[0], p2[1]

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            if (x0, y0) in obstacles:
                return False
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

        return True

    def _compute_smoothness(self, path: list[list[int]]) -> float:
        """计算路径平滑度（转角总和）。

        Args:
            path: 路径点列表。

        Returns:
            平滑度值（越小越平滑）。
        """
        if len(path) < 3:
            return 0.0

        smoothness = 0.0
        for i in range(1, len(path) - 1):
            v1 = np.array(
                [
                    path[i][0] - path[i - 1][0],
                    path[i][1] - path[i - 1][1],
                ],
                dtype=float,
            )
            v2 = np.array(
                [
                    path[i + 1][0] - path[i][0],
                    path[i + 1][1] - path[i][1],
                ],
                dtype=float,
            )

            n1 = np.linalg.norm(v1)
            n2 = np.linalg.norm(v2)
            if n1 > 1e-6 and n2 > 1e-6:
                cos_angle = np.clip(
                    np.dot(v1, v2) / (n1 * n2),
                    -1.0,
                    1.0,
                )
                smoothness += 1.0 - cos_angle

        return smoothness

    # ==================== 执行层 ====================

    def _execution_layer(
        self,
        tactical_path: list[list[int]],
        rows: int,
        cols: int,
        obstacles: set,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """执行层：局部避障和实时控制指令生成。

        沿战术层路径逐点前进，在每个位置检测局部范围内的障碍物，
        生成包含速度方向、避障偏移等信息的控制指令。

        Args:
            tactical_path: 战术层路径。
            rows: 网格行数。
            cols: 网格列数。
            obstacles: 障碍物集合。

        Returns:
            (控制指令列表, 执行层输出信息)。
        """
        if len(tactical_path) < 2:
            return [], {
                "avoidance_count": 0,
                "avg_speed": 0.0,
                "num_controls": 0,
            }

        controls: list[dict[str, Any]] = []
        avoidance_count = 0
        speeds: list[float] = []

        for i in range(len(tactical_path) - 1):
            current = tactical_path[i]
            next_wp = tactical_path[i + 1]

            # 计算期望方向
            dx = next_wp[0] - current[0]
            dy = next_wp[1] - current[1]
            dist = np.sqrt(dx**2 + dy**2)

            if dist < 1e-6:
                continue

            direction = [dx / dist, dy / dist]
            speed = min(dist, float(self.execution_step_size))
            speeds.append(speed)

            # 检测局部障碍物
            local_obstacles = self._detect_local_obstacles(
                current,
                obstacles,
                rows,
                cols,
            )

            # 计算避障偏移
            avoidance_offset = [0.0, 0.0]
            needs_avoidance = False

            if local_obstacles:
                needs_avoidance = True
                avoidance_count += 1
                avoidance_offset = self._compute_avoidance_offset(
                    current,
                    local_obstacles,
                    direction,
                )

            # 应用避障偏移后的实际方向
            actual_direction = np.array(direction) + np.array(avoidance_offset)
            actual_norm = np.linalg.norm(actual_direction)
            if actual_norm > 1e-6:
                actual_direction = (actual_direction / actual_norm).tolist()
            else:
                actual_direction = direction

            # 生成控制指令
            control: dict[str, Any] = {
                "position": list(current),
                "target": list(next_wp),
                "direction": [round(d, 4) for d in actual_direction],
                "speed": round(speed, 4),
                "avoidance": needs_avoidance,
                "avoidance_offset": [round(a, 4) for a in avoidance_offset],
                "local_obstacle_count": len(local_obstacles),
                "step_index": i,
            }
            controls.append(control)

        avg_speed = float(np.mean(speeds)) if speeds else 0.0

        execution_output = {
            "num_controls": len(controls),
            "avoidance_count": avoidance_count,
            "avg_speed": avg_speed,
            "horizon": self.execution_horizon,
            "safety_margin": self.execution_safety_margin,
        }

        return controls, execution_output

    def _detect_local_obstacles(
        self,
        position: list[int],
        obstacles: set,
        rows: int,
        cols: int,
    ) -> list[tuple[int, int, float]]:
        """检测当前位置感知范围内的障碍物。

        Args:
            position: 当前位置。
            obstacles: 全局障碍物集合。
            rows: 网格行数。
            cols: 网格列数。

        Returns:
            障碍物列表 [(x, y, distance), ...]。
        """
        horizon = self.execution_horizon
        local_obs: list[tuple[int, int, float]] = []

        px, py = position[0], position[1]
        for ox, oy in obstacles:
            dist = np.sqrt((px - ox) ** 2 + (py - oy) ** 2)
            if dist <= horizon:
                local_obs.append((ox, oy, dist))

        # 按距离排序
        local_obs.sort(key=lambda o: o[2])
        return local_obs

    def _compute_avoidance_offset(
        self,
        position: list[int],
        local_obstacles: list[tuple[int, int, float]],
        direction: list[float],
    ) -> list[float]:
        """计算避障偏移向量。

        使用势场法原理，根据局部障碍物位置和期望运动方向，
        计算排斥力产生的偏移向量。

        Args:
            position: 当前位置。
            local_obstacles: 局部障碍物列表。
            direction: 期望运动方向。

        Returns:
            避障偏移向量 [dx, dy]。
        """
        margin = self.execution_safety_margin
        offset_x, offset_y = 0.0, 0.0

        for ox, oy, dist in local_obstacles:
            if dist < 1e-6:
                continue

            # 排斥力（与距离平方成反比）
            repulsion = margin / (dist**2 + 0.1)

            # 排斥方向（从障碍物指向当前位置）
            rx = (position[0] - ox) / dist
            ry = (position[1] - oy) / dist

            offset_x += rx * repulsion
            offset_y += ry * repulsion

        # 限制偏移幅度
        offset_norm = np.sqrt(offset_x**2 + offset_y**2)
        max_offset = 0.5
        if offset_norm > max_offset:
            offset_x = offset_x / offset_norm * max_offset
            offset_y = offset_y / offset_norm * max_offset

        return [offset_x, offset_y]

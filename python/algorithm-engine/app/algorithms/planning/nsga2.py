"""NSGA-II（Non-dominated Sorting Genetic Algorithm II，非支配排序遗传算法II）多目标优化。

一种经典的多目标进化优化算法，通过非支配排序和拥挤度距离机制
维护种群多样性，在Pareto前沿上搜索一组均衡的解集。
支持2-3个优化目标（如距离、风险、能耗），最终输出Pareto前沿
解集及推荐解。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class NSGAII:
    """NSGA-II多目标路径优化器。

    使用非支配排序遗传算法II对路径进行多目标优化。
    通过快速非支配排序将种群分层，利用拥挤度距离保持多样性，
    通过锦标赛选择、交叉和变异算子进化种群。

    Args:
        config: 配置字典，支持以下参数：
            - population_size: 种群大小，默认100
            - max_generations: 最大进化代数，默认200
            - crossover_rate: 交叉概率，默认0.9
            - mutation_rate: 变异概率，默认0.1
            - tournament_size: 锦标赛选择大小，默认2
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.population_size: int = self.config.get("population_size", 100)
        self.max_generations: int = self.config.get("max_generations", 200)
        self.crossover_rate: float = self.config.get("crossover_rate", 0.9)
        self.mutation_rate: float = self.config.get("mutation_rate", 0.1)
        self.tournament_size: int = self.config.get("tournament_size", 2)

    def optimize(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行NSGA-II多目标路径优化。

        Args:
            params: 优化参数字典，包含：
                - start: 起点坐标 (int, int)
                - goal: 终点坐标 (int, int)
                - objectives: 目标函数列表，每个为字符串标识：
                    "distance"（距离）、"risk"（风险）、"energy"（能耗）
                - population_size: 种群大小（可选）
                - max_generations: 最大代数（可选）
                - grid_size: 网格尺寸 (int, int)
                - obstacles: 障碍物列表 list[tuple[int, int]]

        Returns:
            包含以下键的字典：
                - pareto_front: Pareto前沿解集（路径列表）
                - best_solution: 推荐解（路径）
                - objectives_values: 各解的目标函数值列表
        """
        np.random.seed(42)

        raw_start = params.get("start", (0, 0))
        raw_goal = params.get("goal", (10, 10))
        start: tuple[int, int] = (int(raw_start[0]), int(raw_start[1]))
        goal: tuple[int, int] = (int(raw_goal[0]), int(raw_goal[1]))
        grid_size = tuple(params.get("grid_size", (50, 50)))
        obstacles = set(map(tuple, params.get("obstacles", [])))
        objectives = params.get("objectives", ["distance", "risk"])
        pop_size = params.get("population_size", self.population_size)
        max_gen = params.get("max_generations", self.max_generations)

        logger.info(
            "NSGA-II优化: 起点=%s, 终点=%s, 目标=%s, 种群=%d, 代数=%d",
            start,
            goal,
            objectives,
            pop_size,
            max_gen,
        )

        rows, cols = grid_size
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

        # 风险区域（模拟：障碍物附近的格子风险值较高）
        risk_map = self._build_risk_map(rows, cols, obstacles)

        # 初始化种群
        population = self._initialize_population(
            start,
            goal,
            rows,
            cols,
            obstacles,
            directions,
            pop_size,
        )

        # 评估初始种群
        obj_values = self._evaluate_population(
            population,
            objectives,
            risk_map,
            start,
            goal,
        )

        for gen in range(max_gen):
            # 非支配排序
            fronts = self._fast_non_dominated_sort(obj_values)

            # 计算拥挤度距离
            crowding = self._crowding_distance(fronts, obj_values)

            # 锦标赛选择
            selected_indices = self._tournament_selection(
                fronts,
                crowding,
                pop_size,
            )

            # 交叉与变异生成子代
            offspring = self._create_offspring(
                population,
                selected_indices,
                rows,
                cols,
                obstacles,
                directions,
                start,
                goal,
            )

            # 合并父代和子代
            combined_pop = population + offspring
            combined_obj = self._evaluate_population(
                combined_pop,
                objectives,
                risk_map,
                start,
                goal,
            )

            # 非支配排序 + 拥挤度选择
            combined_fronts = self._fast_non_dominated_sort(combined_obj)
            combined_crowding = self._crowding_distance(
                combined_fronts,
                combined_obj,
            )

            # 选择下一代
            population, obj_values = self._select_next_generation(
                combined_pop,
                combined_obj,
                combined_fronts,
                combined_crowding,
                pop_size,
            )

            if gen % 20 == 0:
                front0_size = len(combined_fronts[0]) if combined_fronts else 0
                logger.debug(
                    "NSGA-II代 %d: 第一前沿大小=%d, 种群=%d",
                    gen,
                    front0_size,
                    len(population),
                )

        # 提取Pareto前沿
        final_fronts = self._fast_non_dominated_sort(obj_values)
        pareto_indices = final_fronts[0] if final_fronts else list(range(len(population)))
        pareto_front = [population[i] for i in pareto_indices]
        pareto_obj = [obj_values[i] for i in pareto_indices]

        # 选择推荐解（使用归一化后加权和最小的解）
        best_idx = self._select_best_solution(pareto_obj)
        best_solution = pareto_front[best_idx]

        logger.info(
            "NSGA-II优化完成: Pareto前沿解数=%d, 推荐解目标值=%s",
            len(pareto_front),
            pareto_obj[best_idx],
        )

        return {
            "pareto_front": pareto_front,
            "best_solution": best_solution,
            "objectives_values": pareto_obj,
        }

    def _build_risk_map(
        self,
        rows: int,
        cols: int,
        obstacles: set,
    ) -> np.ndarray:
        """构建风险地图。

        障碍物附近区域的格子具有较高的风险值，
        距离障碍物越远风险越低。

        Returns:
            风险值矩阵 (rows x cols)
        """
        risk_map = np.zeros((rows, cols), dtype=np.float64)
        for obs in obstacles:
            ox, oy = int(obs[0]), int(obs[1])
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    nx, ny = ox + dx, oy + dy
                    if 0 <= nx < rows and 0 <= ny < cols:
                        dist = abs(dx) + abs(dy)
                        risk_map[nx, ny] += max(0, 1.0 - dist * 0.25)
        return risk_map

    def _initialize_population(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
        directions: list,
        pop_size: int,
    ) -> list[list[list[int]]]:
        """初始化种群。

        使用随机化路径生成方法创建初始种群，
        每条路径从起点到终点，带有随机偏移以增加多样性。

        Returns:
            种群列表，每个个体为路径（点列表）
        """
        population: list[list[list[int]]] = []

        for _ in range(pop_size):
            path = self._generate_random_path(
                start,
                goal,
                rows,
                cols,
                obstacles,
                directions,
            )
            if path:
                population.append(path)
            else:
                # 回退：直线路径
                population.append([[start[0], start[1]], [goal[0], goal[1]]])

        return population

    def _generate_random_path(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
        directions: list,
    ) -> Optional[list[list[int]]]:
        """生成随机路径。

        使用贪心策略加随机扰动生成从起点到终点的路径。

        Returns:
            路径列表或None
        """
        path = [[start[0], start[1]]]
        current = start
        visited = {start}
        max_steps = rows * cols

        for _ in range(max_steps):
            if current == goal:
                break

            neighbors = []
            for dx, dy in directions:
                nx, ny = current[0] + dx, current[1] + dy
                if 0 <= nx < rows and 0 <= ny < cols and (nx, ny) not in obstacles and (nx, ny) not in visited:
                    neighbors.append((nx, ny))

            if not neighbors:
                break

            # 混合贪心和随机选择
            dists = [abs(n[0] - goal[0]) + abs(n[1] - goal[1]) for n in neighbors]
            min_dist = min(dists)

            # 50%概率选最优方向，50%随机
            if np.random.random() < 0.5:
                candidates = [n for n, d in zip(neighbors, dists) if d == min_dist]
                next_node = candidates[np.random.randint(len(candidates))]
            else:
                idx = np.random.randint(len(neighbors))
                next_node = neighbors[idx]

            current = next_node
            path.append([current[0], current[1]])
            visited.add(current)

        if current != goal:
            return None

        return path

    def _evaluate_population(
        self,
        population: list,
        objectives: list[str],
        risk_map: np.ndarray,
        start: tuple[int, int],
        goal: tuple[int, int],
    ) -> list[list[float]]:
        """评估种群中每个个体的目标函数值。

        Args:
            population: 种群（路径列表）
            objectives: 目标函数标识列表
            risk_map: 风险值矩阵
            start: 起点
            goal: 终点

        Returns:
            目标值列表，每个元素为该个体各目标的值
        """
        obj_values: list[list[float]] = []

        for path in population:
            values: list[float] = []

            for obj_name in objectives:
                if obj_name == "distance":
                    values.append(self._calc_distance(path))
                elif obj_name == "risk":
                    values.append(self._calc_risk(path, risk_map))
                elif obj_name == "energy":
                    values.append(self._calc_energy(path))
                else:
                    values.append(0.0)

            obj_values.append(values)

        return obj_values

    def _calc_distance(self, path: list) -> float:
        """计算路径总距离。"""
        dist = 0.0
        for i in range(len(path) - 1):
            dx = abs(path[i + 1][0] - path[i][0])
            dy = abs(path[i + 1][1] - path[i][1])
            dist += 1.414 if dx + dy == 2 else 1.0
        return dist

    def _calc_risk(self, path: list, risk_map: np.ndarray) -> float:
        """计算路径总风险值。"""
        risk = 0.0
        for point in path:
            x, y = int(point[0]), int(point[1])
            if 0 <= x < risk_map.shape[0] and 0 <= y < risk_map.shape[1]:
                risk += risk_map[x, y]
        return risk

    def _calc_energy(self, path: list) -> float:
        """计算路径总能耗。

        能耗模型：转弯消耗额外能量，直线飞行消耗较少。
        """
        energy = 0.0
        for i in range(len(path) - 1):
            dx = abs(path[i + 1][0] - path[i][0])
            dy = abs(path[i + 1][1] - path[i][1])
            move_cost = 1.414 if dx + dy == 2 else 1.0

            # 转弯惩罚
            if i > 0:
                prev_dx = path[i][0] - path[i - 1][0]
                prev_dy = path[i][1] - path[i - 1][1]
                curr_dx = path[i + 1][0] - path[i][0]
                curr_dy = path[i + 1][1] - path[i][1]
                if prev_dx != curr_dx or prev_dy != curr_dy:
                    move_cost += 0.3  # 转弯额外能耗

            energy += move_cost
        return energy

    def _fast_non_dominated_sort(
        self,
        obj_values: list[list[float]],
    ) -> list[list[int]]:
        """快速非支配排序。

        将种群按非支配关系分层，第一层为Pareto最优解。

        Args:
            obj_values: 目标值列表

        Returns:
            分层列表，每层为个体索引列表
        """
        n = len(obj_values)
        domination_count: list[int] = [0] * n
        dominated_set: list[list[int]] = [[] for _ in range(n)]
        rank: list[int] = [0] * n
        fronts: list[list[int]] = [[]]

        for i in range(n):
            for j in range(i + 1, n):
                if self._dominates(obj_values[i], obj_values[j]):
                    dominated_set[i].append(j)
                    domination_count[j] += 1
                elif self._dominates(obj_values[j], obj_values[i]):
                    dominated_set[j].append(i)
                    domination_count[i] += 1

            if domination_count[i] == 0:
                rank[i] = 0
                fronts[0].append(i)

        current_front = 0
        while fronts[current_front]:
            next_front: list[int] = []
            for i in fronts[current_front]:
                for j in dominated_set[i]:
                    domination_count[j] -= 1
                    if domination_count[j] == 0:
                        rank[j] = current_front + 1
                        next_front.append(j)
            current_front += 1
            if next_front:
                fronts.append(next_front)

        return fronts

    def _dominates(
        self,
        a: list[float],
        b: list[float],
    ) -> bool:
        """判断解a是否支配解b。

        a支配b当且仅当a在所有目标上不差于b，
        且至少在一个目标上严格优于b。
        """
        at_least_one_better = False
        for ai, bi in zip(a, b):
            if ai > bi:
                return False
            if ai < bi:
                at_least_one_better = True
        return at_least_one_better

    def _crowding_distance(
        self,
        fronts: list[list[int]],
        obj_values: list[list[float]],
    ) -> list[float]:
        """计算拥挤度距离。

        在同一前沿内，根据各目标维度上的距离计算拥挤度，
        拥挤度越大表示该解周围越稀疏，多样性越好。

        Args:
            fronts: 非支配排序分层
            obj_values: 目标值列表

        Returns:
            每个个体的拥挤度距离列表
        """
        n = len(obj_values)
        if n == 0:
            return []
        num_obj = len(obj_values[0])
        crowding = [float("inf")] * n

        for front in fronts:
            if len(front) <= 2:
                continue

            for m in range(num_obj):
                # 按第m个目标排序
                sorted_front = sorted(front, key=lambda i: obj_values[i][m])
                crowding[sorted_front[0]] = float("inf")
                crowding[sorted_front[-1]] = float("inf")

                obj_range = obj_values[sorted_front[-1]][m] - obj_values[sorted_front[0]][m]
                if obj_range < 1e-12:
                    continue

                for k in range(1, len(sorted_front) - 1):
                    crowding[sorted_front[k]] += (
                        obj_values[sorted_front[k + 1]][m] - obj_values[sorted_front[k - 1]][m]
                    ) / obj_range

        return crowding

    def _tournament_selection(
        self,
        fronts: list[list[int]],
        crowding: list[float],
        pop_size: int,
    ) -> list[int]:
        """锦标赛选择。

        随机选取tournament_size个个体，选择非支配层级更低
        （或同层级拥挤度更大）的个体。

        Returns:
            被选中的个体索引列表
        """
        # 构建排名映射
        rank_map: dict[int, int] = {}
        for rank, front in enumerate(fronts):
            for idx in front:
                rank_map[idx] = rank

        selected: list[int] = []
        n = sum(len(f) for f in fronts)
        if n == 0:
            return selected

        indices = list(range(n))

        for _ in range(pop_size):
            candidates = [indices[np.random.randint(n)] for _ in range(self.tournament_size)]
            winner = min(
                candidates,
                key=lambda i: (rank_map.get(i, float("inf")), -crowding[i]),
            )
            selected.append(winner)

        return selected

    def _create_offspring(
        self,
        population: list,
        selected_indices: list[int],
        rows: int,
        cols: int,
        obstacles: set,
        directions: list,
        start: tuple[int, int],
        goal: tuple[int, int],
    ) -> list[list[list[int]]]:
        """通过交叉和变异创建子代。

        Args:
            population: 当前种群
            selected_indices: 选中的父代索引
            其他参数用于变异后的路径修复

        Returns:
            子代个体列表
        """
        offspring: list[list[list[int]]] = []

        for i in range(0, len(selected_indices) - 1, 2):
            p1 = population[selected_indices[i]]
            p2 = population[selected_indices[i + 1]]

            if np.random.random() < self.crossover_rate:
                c1, c2 = self._crossover(p1, p2)
            else:
                c1, c2 = list(p1), list(p2)

            # 变异
            if np.random.random() < self.mutation_rate:
                c1 = self._mutate(c1, rows, cols, obstacles, directions)
            if np.random.random() < self.mutation_rate:
                c2 = self._mutate(c2, rows, cols, obstacles, directions)

            # 确保路径有效
            if c1 and c1[0] == [start[0], start[1]]:
                offspring.append(c1)
            if c2 and c2[0] == [start[0], start[1]]:
                offspring.append(c2)

        return offspring

    def _crossover(
        self,
        parent1: list,
        parent2: list,
    ) -> tuple[list, list]:
        """路径交叉操作。

        在两条路径的公共节点处进行交叉，生成两条子路径。

        Returns:
            两条子代路径
        """
        if len(parent1) <= 2 or len(parent2) <= 2:
            return list(parent1), list(parent2)

        # 找公共节点
        set2 = set(tuple(p) for p in parent2)
        common_points = []
        for i, p in enumerate(parent1):
            if tuple(p) in set2:
                common_points.append(i)

        if not common_points:
            return list(parent1), list(parent2)

        # 随机选择交叉点
        cp1 = common_points[np.random.randint(len(common_points))]
        cross_point = tuple(parent1[cp1])

        # 在parent2中找到对应位置
        cp2 = 0
        for i, p in enumerate(parent2):
            if tuple(p) == cross_point:
                cp2 = i
                break

        child1 = parent1[: cp1 + 1] + parent2[cp2 + 1 :]
        child2 = parent2[: cp2 + 1] + parent1[cp1 + 1 :]

        return child1, child2

    def _mutate(
        self,
        path: list,
        rows: int,
        cols: int,
        obstacles: set,
        directions: list,
    ) -> list:
        """路径变异操作。

        随机选择路径中的一个节点，尝试用随机邻居替换，
        生成路径变体。

        Returns:
            变异后的路径
        """
        if len(path) <= 2:
            return path

        mutated = list(path)
        idx = np.random.randint(1, len(mutated) - 1)
        point = mutated[idx]

        neighbors = []
        for dx, dy in directions:
            nx, ny = point[0] + dx, point[1] + dy
            if 0 <= nx < rows and 0 <= ny < cols and (nx, ny) not in obstacles:
                neighbors.append([nx, ny])

        if neighbors:
            mutated[idx] = neighbors[np.random.randint(len(neighbors))]

        return mutated

    def _select_next_generation(
        self,
        population: list,
        obj_values: list[list[float]],
        fronts: list[list[int]],
        crowding: list[float],
        pop_size: int,
    ) -> tuple[list, list[list[float]]]:
        """选择下一代种群。

        按非支配层级依次填充，最后一层使用拥挤度距离截断。

        Returns:
            (新种群, 新种群目标值)
        """
        new_pop: list = []
        new_obj: list[list[float]] = []

        for front in fronts:
            if len(new_pop) + len(front) <= pop_size:
                for idx in front:
                    new_pop.append(population[idx])
                    new_obj.append(obj_values[idx])
            else:
                # 按拥挤度排序，取前若干个
                remaining = pop_size - len(new_pop)
                sorted_front = sorted(
                    front,
                    key=lambda i: -crowding[i],
                )
                for idx in sorted_front[:remaining]:
                    new_pop.append(population[idx])
                    new_obj.append(obj_values[idx])
                break

        return new_pop, new_obj

    def _select_best_solution(
        self,
        pareto_obj: list[list[float]],
    ) -> int:
        """从Pareto前沿中选择推荐解。

        使用归一化后各目标等权加和，选择加权和最小的解。

        Args:
            pareto_obj: Pareto前沿各解的目标值

        Returns:
            推荐解的索引
        """
        if not pareto_obj:
            return 0

        n_obj = len(pareto_obj[0])
        mins = [min(o[i] for o in pareto_obj) for i in range(n_obj)]
        maxs = [max(o[i] for o in pareto_obj) for i in range(n_obj)]

        best_idx = 0
        best_score = float("inf")

        for i, obj in enumerate(pareto_obj):
            score = 0.0
            for m in range(n_obj):
                rng = maxs[m] - mins[m]
                if rng > 1e-12:
                    score += (obj[m] - mins[m]) / rng
            if score < best_score:
                best_score = score
                best_idx = i

        return best_idx

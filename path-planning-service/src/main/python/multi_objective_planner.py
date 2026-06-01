"""
多目标优化路径规划
使用NSGA-II算法同时优化距离、时间、风险、能耗
支持用户偏好自适应
"""
import numpy as np
import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Solution:
    waypoints: List[Tuple[float, float]]
    objectives: List[float] = field(default_factory=list)
    rank: int = 0
    crowding_distance: float = 0.0


class MultiObjectivePlanner:
    """多目标路径规划器 - NSGA-II"""

    def __init__(self, population_size: int = 100, generations: int = 200):
        self.population_size = population_size
        self.generations = generations
        self.user_preferences = {'distance': 0.25, 'time': 0.25, 'risk': 0.25, 'energy': 0.25}
        self.mutation_rate = 0.1
        self.crossover_rate = 0.9

    def set_user_preferences(self, preferences: dict):
        """设置用户偏好权重"""
        total = sum(preferences.values())
        self.user_preferences = {k: v / total for k, v in preferences.items()}

    def evaluate_objectives(self, waypoints: List[Tuple[float, float]], weather_data: dict = None) -> List[float]:
        """评估四个目标函数"""
        total_distance = sum(np.linalg.norm(np.array(waypoints[i]) - np.array(waypoints[i + 1]))
                             for i in range(len(waypoints) - 1))
        total_time = total_distance / 10.0
        wind = weather_data.get('wind_speed', 0) if weather_data else 0
        risk = total_distance * wind / 100
        energy = total_distance * (1 + wind * 0.05)
        return [total_distance, total_time, risk, energy]

    def crossover(self, parent1: List[Tuple], parent2: List[Tuple]) -> Tuple[List[Tuple], List[Tuple]]:
        """模拟二进制交叉"""
        if len(parent1) < 2 or np.random.rand() > self.crossover_rate:
            return parent1, parent2
        point = np.random.randint(1, min(len(parent1), len(parent2)) - 1)
        child1 = parent1[:point] + parent2[point:]
        child2 = parent2[:point] + parent1[point:]
        return child1, child2

    def mutate(self, waypoints: List[Tuple]) -> List[Tuple]:
        """多项式变异"""
        mutated = list(waypoints)
        for i in range(1, len(mutated) - 1):
            if np.random.rand() < self.mutation_rate:
                x, y = mutated[i]
                x += np.random.normal(0, 0.5)
                y += np.random.normal(0, 0.5)
                mutated[i] = (x, y)
        return mutated

    def non_dominated_sort(self, solutions: List[Solution]) -> List[List[Solution]]:
        """非支配排序"""
        n = len(solutions)
        dominated = [set() for _ in range(n)]
        domination_count = [0] * n
        fronts = [[]]

        for i in range(n):
            for j in range(i + 1, n):
                if all(solutions[i].objectives[k] <= solutions[j].objectives[k] for k in range(4)) and \
                   any(solutions[i].objectives[k] < solutions[j].objectives[k] for k in range(4)):
                    dominated[i].add(j)
                    domination_count[j] += 1
                elif all(solutions[j].objectives[k] <= solutions[i].objectives[k] for k in range(4)) and \
                     any(solutions[j].objectives[k] < solutions[i].objectives[k] for k in range(4)):
                    dominated[j].add(i)
                    domination_count[i] += 1

        for i in range(n):
            if domination_count[i] == 0:
                fronts[0].append(i)
                solutions[i].rank = 0

        front_idx = 0
        while fronts[front_idx]:
            next_front = []
            for i in fronts[front_idx]:
                for j in dominated[i]:
                    domination_count[j] -= 1
                    if domination_count[j] == 0:
                        next_front.append(j)
                        solutions[j].rank = front_idx + 1
            front_idx += 1
            fronts.append(next_front)
        return fronts[:-1]

    def crowding_distance(self, solutions: List[Solution], front: List[int]) -> None:
        """计算拥挤距离"""
        if len(front) <= 1:
            return
        m = len(solutions[front[0]].objectives)
        for i in front:
            solutions[i].crowding_distance = 0.0
        for obj_idx in range(m):
            front.sort(key=lambda i: solutions[i].objectives[obj_idx])
            solutions[front[0]].crowding_distance = float('inf')
            solutions[front[-1]].crowding_distance = float('inf')
            obj_range = solutions[front[-1]].objectives[obj_idx] - solutions[front[0]].objectives[obj_idx]
            if obj_range == 0:
                continue
            for j in range(1, len(front) - 1):
                solutions[front[j]].crowding_distance += \
                    (solutions[front[j + 1]].objectives[obj_idx] - solutions[front[j - 1]].objectives[obj_idx]) / obj_range

    def select(self, solutions: List[Solution]) -> List[Solution]:
        """锦标赛选择"""
        selected = []
        for _ in range(self.population_size):
            i, j = np.random.randint(0, len(solutions), 2)
            if solutions[i].rank < solutions[j].rank or \
               (solutions[i].rank == solutions[j].rank and
                solutions[i].crowding_distance > solutions[j].crowding_distance):
                selected.append(solutions[i])
            else:
                selected.append(solutions[j])
        return selected

    def plan(self, start: Tuple[float, float], goal: Tuple[float, float],
             obstacles: List[Tuple] = None, weather_data: dict = None) -> dict:
        """执行多目标优化路径规划"""
        obstacles = obstacles or []
        solutions = []

        for _ in range(self.population_size):
            n_waypoints = np.random.randint(2, 6)
            waypoints = [start]
            for _ in range(n_waypoints - 2):
                x = np.random.uniform(min(start[0], goal[0]), max(start[0], goal[0]))
                y = np.random.uniform(min(start[1], goal[1]), max(start[1], goal[1]))
                waypoints.append((x, y))
            waypoints.append(goal)
            objs = self.evaluate_objectives(waypoints, weather_data)
            solutions.append(Solution(waypoints=waypoints, objectives=objs))

        for gen in range(self.generations):
            offspring = []
            for i in range(0, self.population_size, 2):
                p1, p2 = solutions[i], solutions[(i + 1) % self.population_size]
                c1, c2 = self.crossover(p1.waypoints, p2.waypoints)
                c1 = self.mutate(c1)
                c2 = self.mutate(c2)
                offspring.append(Solution(waypoints=c1, objectives=self.evaluate_objectives(c1, weather_data)))
                offspring.append(Solution(waypoints=c2, objectives=self.evaluate_objectives(c2, weather_data)))

            combined = solutions + offspring
            fronts = self.non_dominated_sort(combined)
            for front in fronts:
                self.crowding_distance(combined, front)

            solutions = self.select(combined)
            logger.debug(f"NSGA-II 第 {gen + 1} 代: 种群规模 {len(solutions)}")

        fronts = self.non_dominated_sort(solutions)
        pareto_front = [solutions[i] for i in fronts[0]]
        weights = [self.user_preferences.get('distance', 0.25),
                   self.user_preferences.get('time', 0.25),
                   self.user_preferences.get('risk', 0.25),
                   self.user_preferences.get('energy', 0.25)]

        best_idx = np.argmin([sum(w * o for w, o in zip(weights, s.objectives)) for s in pareto_front])
        best = pareto_front[best_idx]

        return {
            'success': True,
            'path': best.waypoints,
            'objectives': {
                'distance': best.objectives[0],
                'time': best.objectives[1],
                'risk': best.objectives[2],
                'energy': best.objectives[3]
            },
            'pareto_front_size': len(pareto_front),
            'user_preferences': self.user_preferences
        }

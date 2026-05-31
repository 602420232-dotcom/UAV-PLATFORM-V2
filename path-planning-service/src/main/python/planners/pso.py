import random
import logging
from typing import Tuple, Optional, List, Dict

from .base import BasePlanner

logger = logging.getLogger(__name__)


class ParticleSwarmOptimizationPlanner(BasePlanner):
    """
    粒子群优化路径规划器

    使用 PSO 算法进行路径规划，通过粒子群体协作搜索最优路径。
    """

    def __init__(self, start: Tuple[float, float], goal: Tuple[float, float],
                 obstacles: Optional[List] = None,
                 swarm_size: int = 50, iterations: int = 100,
                 c1: float = 2.0, c2: float = 2.0, w: float = 0.5):
        super().__init__(start=start, goal=goal, obstacles=obstacles)
        self.swarm_size = swarm_size
        self.iterations = iterations
        self.c1 = c1
        self.c2 = c2
        self.w = w
        self.num_waypoints = 10

    def calculate_fitness(self, path: List[Tuple[float, float]]) -> float:
        total_distance = sum(
            self.calculate_distance(path[i], path[i + 1])
            for i in range(len(path) - 1)
        )
        collision_penalty = sum(
            1000 for i in range(len(path) - 1)
            if self.is_path_collision(path[i], path[i + 1])
        )
        return 1 / (total_distance + collision_penalty + 1e-6)

    def _generate_path(self):
        path = [self.start]
        for _ in range(self.num_waypoints):
            t = random.random()
            x = self.start[0] + (self.goal[0] - self.start[0]) * t + random.uniform(-5, 5)
            y = self.start[1] + (self.goal[1] - self.start[1]) * t + random.uniform(-5, 5)
            path.append((x, y))
        path.append(self.goal)
        return path

    def _validate_path(self, path):
        total_distance = 0
        for i in range(len(path) - 1):
            if self.is_path_collision(path[i], path[i + 1]):
                return False, 0
            total_distance += self.calculate_distance(path[i], path[i + 1])
        return True, total_distance

    def plan(self) -> Dict:
        try:
            swarm = []
            personal_best = []
            personal_best_fitness = []

            for _ in range(self.swarm_size):
                path = self._generate_path()
                swarm.append(path)
                personal_best.append(path)
                personal_best_fitness.append(self.calculate_fitness(path))

            gbi = personal_best_fitness.index(max(personal_best_fitness))
            global_best = personal_best[gbi]
            global_best_fitness = personal_best_fitness[gbi]

            velocities = []
            for _ in range(self.swarm_size):
                velocity = [(random.uniform(-1, 1), random.uniform(-1, 1))
                            for _ in range(self.num_waypoints + 2)]
                velocities.append(velocity)

            for _ in range(self.iterations):
                for i in range(self.swarm_size):
                    new_velocity = []
                    for j in range(len(swarm[i])):
                        cognitive = (
                            self.c1 * random.random() * (personal_best[i][j][0] - swarm[i][j][0]),
                            self.c1 * random.random() * (personal_best[i][j][1] - swarm[i][j][1]),
                        )
                        social = (
                            self.c2 * random.random() * (global_best[j][0] - swarm[i][j][0]),
                            self.c2 * random.random() * (global_best[j][1] - swarm[i][j][1]),
                        )
                        nvx = self.w * velocities[i][j][0] + cognitive[0] + social[0]
                        nvy = self.w * velocities[i][j][1] + cognitive[1] + social[1]
                        new_velocity.append((nvx, nvy))
                    velocities[i] = new_velocity

                    new_path = []
                    for j in range(len(swarm[i])):
                        if j == 0:
                            new_path.append(self.start)
                        elif j == len(swarm[i]) - 1:
                            new_path.append(self.goal)
                        else:
                            new_path.append((
                                swarm[i][j][0] + velocities[i][j][0],
                                swarm[i][j][1] + velocities[i][j][1],
                            ))
                    swarm[i] = new_path

                    cf = self.calculate_fitness(new_path)
                    if cf > personal_best_fitness[i]:
                        personal_best[i] = new_path
                        personal_best_fitness[i] = cf
                    if cf > global_best_fitness:
                        global_best = new_path
                        global_best_fitness = cf

            if global_best:
                valid, distance = self._validate_path(global_best)
                if valid:
                    logger.info("粒子群优化路径规划完成")
                    return self._make_result(True, path=global_best, cost=distance)

            logger.warning("粒子群优化无法找到路径")
            return self._make_result(False, error='无法找到路径')

        except Exception as e:
            logger.error(f"粒子群优化路径规划失败: {e}")
            return self._make_result(False, error=str(e))

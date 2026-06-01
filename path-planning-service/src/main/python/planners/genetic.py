import random
import logging
from typing import Tuple, Optional, List, Dict

from .base import BasePlanner

logger = logging.getLogger(__name__)


class GeneticAlgorithmPlanner(BasePlanner):
    """
    遗传算法路径规划器

    使用遗传算法（GA）进行路径规划，通过选择、交叉、变异操作优化路径。
    """

    def __init__(self, start: Tuple[float, float], goal: Tuple[float, float],
                 obstacles: Optional[List] = None,
                 population_size: int = 50, generations: int = 100,
                 mutation_rate: float = 0.1):
        super().__init__(start=start, goal=goal, obstacles=obstacles)
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.num_waypoints = 10

    def generate_individual(self) -> List[Tuple[float, float]]:
        """Generate a random path from start to goal via waypoints."""
        individual = [self.start]
        for _ in range(self.num_waypoints):
            t = random.random()
            x = self.start[0] + (self.goal[0] - self.start[0]) * t + random.uniform(-5, 5)
            y = self.start[1] + (self.goal[1] - self.start[1]) * t + random.uniform(-5, 5)
            individual.append((x, y))
        individual.append(self.goal)
        return individual

    def calculate_fitness(self, individual: List[Tuple[float, float]]) -> float:
        """Evaluate path fitness: shorter and collision-free paths score higher."""
        total_distance = sum(
            self.calculate_distance(individual[i], individual[i + 1])
            for i in range(len(individual) - 1)
        )
        collision_penalty = sum(
            1000 for i in range(len(individual) - 1)
            if self.is_path_collision(individual[i], individual[i + 1])
        )
        return 1 / (total_distance + collision_penalty + 1e-6)

    def select_parents(self, population: List[List[Tuple[float, float]]],
                       fitnesses: List[float]):
        """Select two parent individuals using fitness-proportional (roulette wheel) selection."""
        total_fitness = sum(fitnesses)
        probabilities = [f / total_fitness for f in fitnesses]
        return (
            random.choices(population, weights=probabilities, k=1)[0],
            random.choices(population, weights=probabilities, k=1)[0],
        )

    @staticmethod
    def crossover(parent1, parent2):
        """Perform single-point crossover between two parent paths."""
        point = random.randint(1, len(parent1) - 2)
        return parent1[:point] + parent2[point:]

    def mutate(self, individual):
        """Apply random mutation to waypoints with given mutation_rate."""
        mutated = individual.copy()
        for i in range(1, len(mutated) - 1):
            if random.random() < self.mutation_rate:
                mutated[i] = (
                    mutated[i][0] + random.uniform(-2, 2),
                    mutated[i][1] + random.uniform(-2, 2),
                )
        return mutated

    def _validate_path(self, path):
        """Check if a path is collision-free and return total distance."""
        total_distance = 0
        for i in range(len(path) - 1):
            if self.is_path_collision(path[i], path[i + 1]):
                return False, 0
            total_distance += self.calculate_distance(path[i], path[i + 1])
        return True, total_distance

    def plan(self) -> Dict:
        try:
            population = [self.generate_individual()
                          for _ in range(self.population_size)]
            best_individual = None
            best_fitness = -float('inf')

            for _ in range(self.generations):
                fitnesses = [self.calculate_fitness(ind) for ind in population]
                idx = fitnesses.index(max(fitnesses))
                if fitnesses[idx] > best_fitness:
                    best_individual = population[idx]
                    best_fitness = fitnesses[idx]

                new_population = []
                for _ in range(self.population_size):
                    p1, p2 = self.select_parents(population, fitnesses)
                    child = self.crossover(p1, p2)
                    child = self.mutate(child)
                    new_population.append(child)
                population = new_population

            if best_individual:
                valid, distance = self._validate_path(best_individual)
                if valid:
                    logger.info("遗传算法路径规划完成")
                    return self._make_result(True, path=best_individual, cost=distance)

            logger.warning("遗传算法无法找到路径")
            return self._make_result(False, error='无法找到路径')

        except Exception as e:
            logger.error(f"遗传算法路径规划失败: {e}")
            return self._make_result(False, error=str(e))

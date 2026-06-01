import random
import logging
from typing import Tuple, Optional, List, Dict

from .base import BasePlanner

logger = logging.getLogger(__name__)


class Node:
    """RRT 树节点"""

    def __init__(self, position: Tuple[float, float]):
        self.position = position
        self.parent: Optional[Node] = None
        self.cost = 0.0


class RRTP(BasePlanner):
    """
    RRT* 路径规划器

    使用快速扩展随机树优化算法进行路径规划。
    """

    def __init__(self, start: Tuple[float, float], goal: Tuple[float, float],
                 obstacles: Optional[List] = None,
                 max_iterations: int = 1000, step_size: float = 1.0,
                 goal_radius: float = 1.0):
        super().__init__(start=start, goal=goal, obstacles=obstacles)
        self.max_iterations = max_iterations
        self.step_size = step_size
        self.goal_radius = goal_radius
        self.nodes: List[Node] = []

    def get_random_point(self) -> Tuple[float, float]:
        """Sample a random point with 10% goal bias for faster convergence."""
        if random.random() < 0.1:
            return self.goal
        return (random.uniform(-50, 50), random.uniform(-50, 50))

    def get_nearest_node(self, point: Tuple[float, float]) -> Node:
        """Find the tree node nearest to the given point."""
        min_distance = float('inf')
        nearest_node = None
        for node in self.nodes:
            distance = self.calculate_distance(node.position, point)
            if distance < min_distance:
                min_distance = distance
                nearest_node = node
        return nearest_node

    def steer(self, from_node: Node, to_point: Tuple[float, float]) -> Tuple[float, float]:
        """Steer from a node towards a point, limited by step_size."""
        distance = self.calculate_distance(from_node.position, to_point)
        if distance <= self.step_size:
            return to_point
        direction = (
            (to_point[0] - from_node.position[0]) / distance,
            (to_point[1] - from_node.position[1]) / distance
        )
        return (
            from_node.position[0] + direction[0] * self.step_size,
            from_node.position[1] + direction[1] * self.step_size
        )

    def get_near_nodes(self, point: Tuple[float, float], radius: float) -> List[Node]:
        """Find all nodes within a given radius of a point."""
        return [node for node in self.nodes
                if self.calculate_distance(node.position, point) <= radius]

    def plan(self) -> Dict:
        try:
            self.nodes = [Node(self.start)]

            for _ in range(self.max_iterations):
                random_point = self.get_random_point()
                nearest_node = self.get_nearest_node(random_point)
                new_position = self.steer(nearest_node, random_point)

                if self.is_collision(new_position):
                    continue
                if self.is_path_collision(nearest_node.position, new_position):
                    continue

                new_node = Node(new_position)
                new_node.parent = nearest_node
                new_node.cost = nearest_node.cost + self.calculate_distance(
                    nearest_node.position, new_position)

                near_nodes = self.get_near_nodes(new_position, 5.0)
                for near_node in near_nodes:
                    if not self.is_path_collision(near_node.position, new_position):
                        new_cost = near_node.cost + self.calculate_distance(
                            near_node.position, new_position)
                        if new_cost < new_node.cost:
                            new_node.parent = near_node
                            new_node.cost = new_cost

                for near_node in near_nodes:
                    if not self.is_path_collision(new_node.position, near_node.position):
                        new_cost = new_node.cost + self.calculate_distance(
                            new_node.position, near_node.position)
                        if new_cost < near_node.cost:
                            near_node.parent = new_node
                            near_node.cost = new_cost

                self.nodes.append(new_node)

                if self.calculate_distance(new_position, self.goal) <= self.goal_radius:
                    goal_node = Node(self.goal)
                    goal_node.parent = new_node
                    goal_node.cost = new_node.cost + self.calculate_distance(
                        new_node.position, self.goal)
                    self.nodes.append(goal_node)

                    path = []
                    current = goal_node
                    while current:
                        path.append(current.position)
                        current = current.parent
                    path.reverse()

                    logger.info("RRT*路径规划完成")
                    return self._make_result(True, path=path, cost=goal_node.cost)

            logger.warning("RRT*无法找到路径")
            return self._make_result(False, error='无法找到路径')

        except Exception as e:
            logger.error(f"RRT*路径规划失败: {e}")
            return self._make_result(False, error=str(e))


RRTStarPlanner = RRTP

import logging
from typing import Tuple, Optional, List, Dict, Set

from .base import BasePlanner

logger = logging.getLogger(__name__)


class DijkstraPlanner(BasePlanner):
    """
    Dijkstra 路径规划器

    基于网格的 Dijkstra 最短路径算法实现。
    """

    def __init__(self, grid_size: Tuple[int, int] = (100, 100),
                 obstacles: Optional[List] = None):
        super().__init__(obstacles=obstacles)
        self.grid_size = grid_size

    def _grid_to_world(self, grid_pos: Tuple[int, int]) -> Tuple[float, float]:
        """Convert grid coordinates to world coordinates."""
        return (grid_pos[0] - self.grid_size[0] / 2,
                grid_pos[1] - self.grid_size[1] / 2)

    def _world_to_grid(self, world_pos: Tuple[float, float]) -> Tuple[int, int]:
        """Convert world coordinates to grid coordinates."""
        return (int(world_pos[0] + self.grid_size[0] / 2),
                int(world_pos[1] + self.grid_size[1] / 2))

    def _in_bounds(self, pos: Tuple[int, int]) -> bool:
        """Check if a grid position is within bounds."""
        return (0 <= pos[0] < self.grid_size[0] and
                0 <= pos[1] < self.grid_size[1])

    def plan(self, start: Tuple[float, float],
             goal: Tuple[float, float]) -> Dict:
        try:
            start_grid = self._world_to_grid(start)
            goal_grid = self._world_to_grid(goal)

            if not self._in_bounds(start_grid):
                return self._make_result(False, error='起点超出网格范围')
            if not self._in_bounds(goal_grid):
                return self._make_result(False, error='终点超出网格范围')
            if self.is_collision(start):
                return self._make_result(False, error='起点碰撞')
            if self.is_collision(goal):
                return self._make_result(False, error='终点碰撞')

            w, h = self.grid_size
            distances = [[float('inf') for _ in range(h)] for _ in range(w)]
            predecessors = [[None for _ in range(h)] for _ in range(w)]
            distances[start_grid[0]][start_grid[1]] = 0

            priority_queue = [(0, start_grid)]
            visited: Set = set()
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0),
                          (1, 1), (1, -1), (-1, 1), (-1, -1)]

            while priority_queue:
                priority_queue.sort()
                current_distance, current_pos = priority_queue.pop(0)

                if current_pos == goal_grid:
                    path = []
                    cur = current_pos
                    while cur:
                        path.append(self._grid_to_world(cur))
                        cur = predecessors[cur[0]][cur[1]]
                    path.reverse()

                    logger.info("Dijkstra路径规划完成")
                    return self._make_result(
                        True, path=path,
                        cost=distances[goal_grid[0]][goal_grid[1]])

                if (current_pos[0], current_pos[1]) in visited:
                    continue
                visited.add((current_pos[0], current_pos[1]))

                for dx, dy in directions:
                    nx, ny = current_pos[0] + dx, current_pos[1] + dy
                    if not self._in_bounds((nx, ny)):
                        continue
                    new_world = self._grid_to_world((nx, ny))
                    if self.is_collision(new_world):
                        continue

                    nd = current_distance + (dx ** 2 + dy ** 2) ** 0.5
                    if nd < distances[nx][ny]:
                        distances[nx][ny] = nd
                        predecessors[nx][ny] = current_pos
                        priority_queue.append((nd, (nx, ny)))

            logger.warning("Dijkstra无法找到路径")
            return self._make_result(False, error='无法找到路径')

        except Exception as e:
            logger.error(f"Dijkstra路径规划失败: {e}")
            return self._make_result(False, error=str(e))

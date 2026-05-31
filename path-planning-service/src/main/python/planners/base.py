import numpy as np
import logging
from typing import List, Tuple, Optional, Dict

logger = logging.getLogger(__name__)


class BasePlanner:
    """
    路径规划器基类

    提供所有规划器共享的工具方法，包括：
    - 距离计算
    - 碰撞检测
    - 路径碰撞检测
    - 统一的规划结果格式
    """

    def __init__(self, start: Optional[Tuple[float, float]] = None,
                 goal: Optional[Tuple[float, float]] = None,
                 obstacles: Optional[List] = None):
        self.start = start
        self.goal = goal
        self.obstacles = obstacles or []

    @staticmethod
    def calculate_distance(loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        return np.sqrt((loc1[0] - loc2[0]) ** 2 + (loc1[1] - loc2[1]) ** 2)

    def is_collision(self, location: Tuple[float, float]) -> bool:
        for obstacle in self.obstacles:
            distance = self.calculate_distance(location, obstacle.location)
            if distance < obstacle.radius:
                return True
        return False

    def is_path_collision(self, start: Tuple[float, float], end: Tuple[float, float], steps: int = 10) -> bool:
        for i in range(steps + 1):
            t = i / steps
            x = start[0] + (end[0] - start[0]) * t
            y = start[1] + (end[1] - start[1]) * t
            if self.is_collision((x, y)):
                return True
        return False

    def plan(self) -> Dict:
        raise NotImplementedError("子类必须实现 plan 方法")

    @staticmethod
    def _make_result(success: bool, path: Optional[List] = None,
                     cost: Optional[float] = None, error: Optional[str] = None) -> Dict:
        if success:
            return {'success': True, 'path': path, 'cost': cost}
        return {'success': False, 'error': error}

    @staticmethod
    def _make_obstacles(obstacle_data: List[Dict]) -> List:
        return [
            type('Obstacle', (), {
                'location': tuple(o['location']),
                'radius': o['radius']
            })()
            for o in obstacle_data
        ]

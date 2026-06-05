"""
规划器工厂模块

提供统一的规划器创建接口，支持多种路径规划算法：
- RRT*
- Dijkstra
- 遗传算法
- 粒子群优化
- 蚁群算法
- 冲突基搜索(CBS)
"""

from .cbs import CBSPlanner
from .informed_rrt_star import InformedRRTStarPlanner
from .aco import ACOPlanner
from .pso import ParticleSwarmOptimizationPlanner
from .genetic import GeneticAlgorithmPlanner
from .dijkstra import DijkstraPlanner
from .rrt_star import RRTP
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class PlannerFactory:
    """规划器工厂，统一创建各类路径规划器实例"""

    _registry: Dict[str, type] = {
        'rrt_star': RRTP,
        'rrt': RRTP,
        'dijkstra': DijkstraPlanner,
        'genetic': GeneticAlgorithmPlanner,
        'genetic_algorithm': GeneticAlgorithmPlanner,
        'pso': ParticleSwarmOptimizationPlanner,
        'particle_swarm': ParticleSwarmOptimizationPlanner,
        'aco': ACOPlanner,
        'ant_colony': ACOPlanner,
        'informed_rrt_star': InformedRRTStarPlanner,
        'cbs': CBSPlanner,
        'conflict_based_search': CBSPlanner,
    }

    @classmethod
    def register(cls, name: str, planner_cls: type) -> None:
        """注册新的规划器类型"""
        cls._registry[name] = planner_cls

    @classmethod
    def create(cls, planner_type: str, **kwargs) -> object:
        """
        根据类型名称创建规划器实例

        Args:
            planner_type: 规划器类型 ('rrt_star'/'dijkstra'/'genetic'/'pso')
            **kwargs: 规划器构造参数

        Returns:
            对应类型的规划器实例

        Raises:
            ValueError: 未知的规划器类型
        """
        planner_type = planner_type.lower()
        planner_cls = cls._registry.get(planner_type)
        if planner_cls is None:
            available = ', '.join(sorted(set(cls._registry.keys())))
            raise ValueError(
                f"未知的规划器类型: '{planner_type}'。可用类型: {available}"
            )
        return planner_cls(**kwargs)

    @classmethod
    def list_types(cls) -> List[str]:
        """列出所有已注册的规划器类型"""
        return sorted(set(cls._registry.keys()))


def create_planner(
    planner_type: str,
    start: Optional[Tuple[float, float]] = None,
    goal: Optional[Tuple[float, float]] = None,
    obstacles: Optional[List] = None,
    **kwargs
) -> object:
    """
    便捷函数：创建规划器实例

    Args:
        planner_type: 规划器类型
        start: 起点坐标
        goal: 终点坐标
        obstacles: 障碍物列表
        **kwargs: 其他规划器参数

    Returns:
        规划器实例
    """
    return PlannerFactory.create(
        planner_type, start=start, goal=goal, obstacles=obstacles, **kwargs
    )

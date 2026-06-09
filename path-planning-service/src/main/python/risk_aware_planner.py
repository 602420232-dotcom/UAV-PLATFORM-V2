#!/usr/bin/env python3
"""
风险感知路径规划器封装

将风险映射模块与现有路径规划算法集成
支持A*、RRT*等算法的风险感知扩展
"""

import numpy as np
import heapq
from typing import List, Dict, Tuple, Optional, Any
import sys
import os
import logging

# 添加路径以便导入
SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SRC_DIR))

# 添加data-assimilation-platform的路径
DATA_ASSIMILATION_PATH = os.path.join(
    PROJECT_ROOT, 'data-assimilation-platform', 'algorithm_core', 'src'
)
if DATA_ASSIMILATION_PATH not in sys.path:
    sys.path.insert(0, DATA_ASSIMILATION_PATH)

try:
    from bayesian_assimilation.utils.risk_mapper import (  # type: ignore[assignment]
        WeatherToRiskMapper,  # type: ignore[assignment]
        RiskAwarePathCostCalculator,  # type: ignore[assignment]
        RiskLevel  # type: ignore[assignment]
    )
except ImportError:
    # 如果无法导入，使用简化版本
    sys.path.insert(0, SRC_DIR)
    try:
        from risk_mapper import (  # type: ignore[import]
            WeatherToRiskMapper, RiskAwarePathCostCalculator, RiskLevel)
    except ImportError:
        # 定义简化版本
        class RiskLevel:
            LOW = "LOW"
            MEDIUM = "MEDIUM"
            HIGH = "HIGH"
            EXTREME = "EXTREME"

        class WeatherToRiskMapper:
            def __init__(self, grid_resolution=100.0, constraints=None):
                self.grid_resolution = grid_resolution

            def compute_comprehensive_risk(self, assimilation_result, heading=0.0):
                shape = assimilation_result.get('grid', {}).get('shape', (10, 10))
                return {
                    'risk_grid': np.zeros(shape),
                    'risk_level': np.full(shape, RiskLevel.LOW, dtype=object),
                    'summary': {'avg_risk': 0.0, 'max_risk': 0.0}
                }

        class RiskAwarePathCostCalculator:
            def __init__(self, mapper):
                self.mapper = mapper

            def set_risk_field(self, risk_result):
                pass

            def get_risk_at_position(self, position):
                return 0.0

            def is_high_risk_zone(self, position, threshold=0.6):
                return False

logger = logging.getLogger(__name__)


class RiskAwareAStarPlanner:
    """
    风险感知A*路径规划器

    在A*算法基础上增加气象风险代价
    """

    def __init__(
        self,
        risk_result: Optional[Dict] = None,
        obstacles: Optional[List] = None,
        no_fly_zones: Optional[List] = None,
        risk_weight: float = 0.4
    ):
        """
        Args:
            risk_result: 风险计算结果
            obstacles: 静态障碍物列表
            no_fly_zones: 禁飞区列表
            risk_weight: 风险权重 (0-1)，越高表示越重视风险
        """
        self.obstacles = obstacles or []
        self.no_fly_zones = no_fly_zones or []
        self.risk_weight = risk_weight

        # 初始化风险计算器
        if risk_result:
            self.risk_mapper = WeatherToRiskMapper()
            self.cost_calculator = RiskAwarePathCostCalculator(self.risk_mapper)
            self.cost_calculator.set_risk_field(risk_result)
        else:
            self.cost_calculator = None

    def set_risk_field(self, risk_result: Dict):
        """设置风险场"""
        self.risk_mapper = WeatherToRiskMapper()
        self.cost_calculator = RiskAwarePathCostCalculator(self.risk_mapper)
        self.cost_calculator.set_risk_field(risk_result)

    @staticmethod
    def calculate_distance(loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """计算两点间距离"""
        return np.sqrt((loc1[0] - loc2[0]) ** 2 + (loc1[1] - loc2[1]) ** 2)

    def is_collision(self, location: Tuple[float, float]) -> bool:
        """检查碰撞"""
        # 检查障碍物
        for obstacle in self.obstacles:
            if self.calculate_distance(location, obstacle.location) < obstacle.radius:
                return True
        # 检查禁飞区
        for no_fly_zone in self.no_fly_zones:
            if self.calculate_distance(location, no_fly_zone.location) < no_fly_zone.radius:
                return True
        return False

    def is_high_risk(self, location: Tuple[float, float]) -> bool:
        """检查是否为高风险区域"""
        if self.cost_calculator:
            return self.cost_calculator.is_high_risk_zone(location, threshold=0.6)
        return False

    def compute_node_cost(
        self,
        node: Tuple[float, float],
        base_cost: float
    ) -> float:
        """
        计算节点综合代价

        综合代价 = (1-risk_weight) * 基础代价 + risk_weight * 风险代价
        """
        if not self.cost_calculator:
            return base_cost

        risk_value = self.cost_calculator.get_risk_at_position(node)

        # 基础代价归一化 (假设最大基础代价为100)
        normalized_base = min(base_cost / 100.0, 1.0)

        # 综合代价
        # 高风险区域指数级增加代价
        if risk_value >= 0.6:
            risk_penalty = 3.0 + (risk_value - 0.6) * 5.0  # 指数惩罚
        elif risk_value >= 0.3:
            risk_penalty = 1.0 + (risk_value - 0.3) * 2.0
        else:
            risk_penalty = 1.0

        return (1 - self.risk_weight) * normalized_base + self.risk_weight * risk_penalty

    def plan(
        self,
        start: Tuple[float, float],
        goal: Tuple[float, float],
        grid_resolution: float = 10.0
    ) -> Dict:
        """
        执行风险感知A*路径规划

        Args:
            start: 起点
            goal: 终点
            grid_resolution: 网格分辨率

        Returns:
            规划结果
        """
        try:
            # 离散化坐标到网格
            start_grid = (round(start[0] / grid_resolution) * grid_resolution,
                          round(start[1] / grid_resolution) * grid_resolution)
            goal_grid = (round(goal[0] / grid_resolution) * grid_resolution,
                         round(goal[1] / grid_resolution) * grid_resolution)

            # A*搜索
            open_set = {start_grid}
            heap = [(0.0, 0, start_grid)]
            came_from = {}
            g_score = {start_grid: 0.0}
            tie_breaker = 1

            iterations = 0
            max_iterations = 5000

            while heap and iterations < max_iterations:
                iterations += 1
                _, _, current = heapq.heappop(heap)

                if current not in open_set:
                    continue

                # 检查是否到达目标
                if self.calculate_distance(current, goal_grid) < grid_resolution * 1.5:
                    # 重建路径
                    path = []
                    node = current
                    total_risk = 0.0
                    while node in came_from:
                        path.append(node)
                        if self.cost_calculator:
                            total_risk += self.cost_calculator.get_risk_at_position(node)
                        node = came_from[node]
                    path.append(start_grid)
                    path.reverse()

                    # 添加起点和终点
                    full_path = [start] + path + [goal]

                    return {
                        'success': True,
                        'path': full_path,
                        'distance': g_score.get(current, float('inf')),
                        'avg_risk': total_risk / len(path) if path else 0.0,
                        'iterations': iterations
                    }

                open_set.remove(current)

                # 生成邻居
                neighbors = [
                    (current[0] + grid_resolution, current[1]),
                    (current[0] - grid_resolution, current[1]),
                    (current[0], current[1] + grid_resolution),
                    (current[0], current[1] - grid_resolution),
                ]

                for neighbor in neighbors:
                    # 跳过碰撞和高风险区域
                    if self.is_collision(neighbor):
                        continue
                    # 允许通过中等风险区域，但增加代价
                    if self.is_high_risk(neighbor):
                        continue  # 严格模式：完全规避高风险区域

                    # 计算代价
                    move_cost = self.calculate_distance(current, neighbor)
                    risk_cost = self.compute_node_cost(neighbor, move_cost)
                    tentative_g = g_score[current] + move_cost + risk_cost * 10

                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f_score = tentative_g + self.calculate_distance(neighbor, goal_grid)
                        heapq.heappush(heap, (f_score, tie_breaker, neighbor))
                        tie_breaker += 1

            logger.warning(f"无法找到路径 (迭代{iterations}次)")
            return {
                'success': False,
                'error': '无法找到可行路径',
                'iterations': iterations
            }

        except Exception as e:
            logger.error(f"路径规划失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class RiskAwareRRTStarPlanner:
    """
    风险感知RRT*路径规划器

    在RRT*算法基础上优先向低风险区域采样
    """

    def __init__(
        self,
        risk_result: Optional[Dict] = None,
        obstacles: Optional[List] = None,
        no_fly_zones: Optional[List] = None,
        risk_weight: float = 0.4,
        max_iterations: int = 300,
        goal_bias: float = 0.2
    ):
        self.obstacles = obstacles or []
        self.no_fly_zones = no_fly_zones or []
        self.risk_weight = risk_weight
        self.max_iterations = max_iterations
        self.goal_bias = goal_bias

        # 初始化风险计算器
        if risk_result:
            self.risk_mapper = WeatherToRiskMapper()
            self.cost_calculator = RiskAwarePathCostCalculator(self.risk_mapper)
            self.cost_calculator.set_risk_field(risk_result)
        else:
            self.cost_calculator = None

    def set_risk_field(self, risk_result: Dict):
        """设置风险场"""
        self.risk_mapper = WeatherToRiskMapper()
        self.cost_calculator = RiskAwarePathCostCalculator(self.risk_mapper)
        self.cost_calculator.set_risk_field(risk_result)

    @staticmethod
    def calculate_distance(loc1, loc2):
        return np.sqrt((loc1[0] - loc2[0]) ** 2 + (loc1[1] - loc2[1]) ** 2)

    def get_risk_at(self, position: Tuple[float, float]) -> float:
        if self.cost_calculator:
            return self.cost_calculator.get_risk_at_position(position)
        return 0.0

    def sample_with_risk_bias(
        self,
        goal: Tuple[float, float],
        bounds: Tuple[float, float, float, float]
    ) -> Tuple[float, float]:
        """
        风险偏置采样

        以goal_bias概率返回目标点
        否则优先在低风险区域采样
        """
        if np.random.rand() < self.goal_bias:
            return goal

        x_min, x_max, y_min, y_max = bounds

        # 多次尝试采样低风险点
        for _ in range(10):
            x = np.random.uniform(x_min, x_max)
            y = np.random.uniform(y_min, y_max)
            risk = self.get_risk_at((x, y))

            # 低风险区域优先被选中
            if risk < 0.4 or np.random.rand() > risk:
                return (x, y)

        # 如果找不到低风险点，返回随机点
        return (np.random.uniform(x_min, x_max), np.random.uniform(y_min, y_max))

    def is_collision(self, location: Tuple[float, float]) -> bool:
        for obstacle in self.obstacles:
            if self.calculate_distance(location, obstacle.location) < obstacle.radius:
                return True
        for no_fly_zone in self.no_fly_zones:
            if self.calculate_distance(location, no_fly_zone.location) < no_fly_zone.radius:
                return True
        return False

    def is_collision_free(self, start: Tuple, end: Tuple, steps: int = 5) -> bool:
        for i in range(steps + 1):
            t = i / steps
            x = start[0] + t * (end[0] - start[0])
            y = start[1] + t * (end[1] - start[1])
            if self.is_collision((x, y)):
                return False
            # 检查高风险区域
            if self.get_risk_at((x, y)) >= 0.7:
                return False
        return True

    def nearest(self, nodes: List, point: Tuple) -> Tuple:
        min_dist = float('inf')
        nearest_node = None
        for node in nodes:
            dist = self.calculate_distance(node, point)
            if dist < min_dist:
                min_dist = dist
                nearest_node = node
        assert nearest_node is not None
        return nearest_node

    def steer(self, from_node: Tuple, to_point: Tuple, max_step: float = 15.0) -> Tuple:
        dist = self.calculate_distance(from_node, to_point)
        if dist <= max_step:
            return to_point
        angle = np.arctan2(to_point[1] - from_node[1], to_point[0] - from_node[0])
        return (
            from_node[0] + max_step * np.cos(angle),
            from_node[1] + max_step * np.sin(angle)
        )

    def plan(
        self,
        start: Tuple[float, float],
        goal: Tuple[float, float],
        bounds: Tuple[float, float, float, float] = (-100, 100, -100, 100)
    ) -> Dict:
        """执行风险感知RRT*路径规划"""
        try:
            nodes = [start]
            parent_map: Dict[Tuple, Optional[Tuple]] = {start: None}
            cost_map = {start: 0.0}
            risk_cost_map = {start: 0.0}

            for i in range(self.max_iterations):
                # 风险偏置采样
                sample_point = self.sample_with_risk_bias(goal, bounds)

                # 找到最近的节点
                nearest_node = self.nearest(nodes, sample_point)

                # 移动到采样点
                new_node = self.steer(nearest_node, sample_point)

                # 检查碰撞和风险
                if self.is_collision(new_node):
                    continue
                if not self.is_collision_free(nearest_node, new_node):
                    continue

                # 计算代价 (距离 + 风险)
                dist = self.calculate_distance(nearest_node, new_node)
                risk = self.get_risk_at(new_node)
                segment_cost = dist + risk * 20 * self.risk_weight

                nodes.append(new_node)
                parent_map[new_node] = nearest_node
                cost_map[new_node] = cost_map[nearest_node] + dist
                risk_cost_map[new_node] = risk_cost_map[nearest_node] + segment_cost

                # 重连
                for node in nodes[:-1]:
                    if node == new_node:
                        continue
                    dist_to_node = self.calculate_distance(node, new_node)
                    if dist_to_node <= 20.0:
                        if self.is_collision_free(node, new_node):
                            new_cost = cost_map[node] + dist_to_node
                            if new_cost < cost_map.get(new_node, float('inf')):
                                parent_map[new_node] = node
                                cost_map[new_node] = new_cost

                # 检查是否到达目标
                if self.calculate_distance(new_node, goal) < 5.0:
                    if self.is_collision_free(new_node, goal):
                        # 连接到目标
                        nodes.append(goal)
                        dist_to_goal = self.calculate_distance(new_node, goal)
                        parent_map[goal] = new_node
                        cost_map[goal] = cost_map[new_node] + dist_to_goal

                        # 重建路径
                        path = []
                        current = goal
                        while current is not None:
                            path.append(current)
                            current = parent_map[current]
                        path.reverse()

                        return {
                            'success': True,
                            'path': path,
                            'distance': cost_map[goal],
                            'avg_risk': risk_cost_map.get(goal, 0) / len(path) if path else 0,
                            'iterations': i + 1
                        }

            return {
                'success': False,
                'error': '无法找到路径',
                'iterations': self.max_iterations
            }

        except Exception as e:
            logger.error(f"RRT*规划失败: {e}")
            return {'success': False, 'error': str(e)}


def create_risk_aware_planner(
    planner_type: str,
    risk_result: Optional[Dict] = None,
    **kwargs
) -> Any:
    """
    工厂函数：创建风险感知规划器

    Args:
        planner_type: 'astar' 或 'rrt_star'
        risk_result: 风险计算结果
        **kwargs: 其他参数

    Returns:
        风险感知规划器实例
    """
    if planner_type.lower() == 'astar':
        return RiskAwareAStarPlanner(risk_result=risk_result, **kwargs)
    elif planner_type.lower() in ('rrt_star', 'rrt*', 'derrt'):
        return RiskAwareRRTStarPlanner(risk_result=risk_result, **kwargs)
    else:
        raise ValueError(f"不支持的规划器类型: {planner_type}")


def demo():
    """演示风险感知路径规划"""
    logger.info("=" * 60)
    logger.info("风险感知路径规划器 - 演示")
    logger.info("=" * 60)

    # 创建示例风险场
    np.random.seed(42)
    shape = (20, 20)

    x = np.linspace(0, 2 * np.pi, shape[0])
    y = np.linspace(0, 2 * np.pi, shape[1])
    X, Y = np.meshgrid(x, y)

    u_wind = 5 + 3 * np.sin(X) + np.random.normal(0, 0.5, shape)
    v_wind = 3 + 2 * np.cos(Y) + np.random.normal(0, 0.5, shape)

    # 模拟高风险区域
    u_wind[:, 12:] += 8

    assimilation_result = {
        'variables': {'u_wind': u_wind, 'v_wind': v_wind},
        'grid': {'shape': shape}
    }

    # 计算风险
    mapper = WeatherToRiskMapper(grid_resolution=10.0)
    risk_result = mapper.compute_comprehensive_risk(assimilation_result)

    logger.info("风险统计:")
    logger.info(f"  - 平均风险: {risk_result['summary'].get('avg_risk', 0):.3f}")
    safe_ratio = risk_result['summary'].get('safe_area_ratio', 0)
    logger.info(f"  - 安全区域占比: {safe_ratio:.1%}")

    # 创建风险感知A*规划器
    logger.info("1. 测试风险感知A*规划器...")
    astar = RiskAwareAStarPlanner(risk_result=risk_result, risk_weight=0.5)

    start = (10, 10)
    goal = (180, 180)

    result = astar.plan(start, goal, grid_resolution=10.0)

    if result['success']:
        logger.info("   路径找到!")
        logger.info(f"   - 路径长度: {result['distance']:.1f}")
        logger.info(f"   - 平均风险: {result['avg_risk']:.3f}")
        logger.info(f"   - 迭代次数: {result['iterations']}")
    else:
        logger.error(f"   路径规划失败: {result['error']}")

    # 创建风险感知RRT*规划器
    logger.info("2. 测试风险感知RRT*规划器...")
    rrt = RiskAwareRRTStarPlanner(risk_result=risk_result, risk_weight=0.5)

    result = rrt.plan(start, goal, bounds=(0, 200, 0, 200))

    if result['success']:
        logger.info("   路径找到!")
        logger.info(f"   - 路径长度: {result['distance']:.1f}")
        logger.info(f"   - 平均风险: {result['avg_risk']:.3f}")
        logger.info(f"   - 迭代次数: {result['iterations']}")
    else:
        logger.error(f"   路径规划失败: {result['error']}")

    logger.info("=" * 60)
    logger.info("演示完成!")


if __name__ == "__main__":
    demo()

#!/usr/bin/env python3
"""
Informed RRT* 路径规划算法

在 RRT* 基础上加入椭圆启发式采样，当找到初始路径后，
将采样区域限制在一个以起点和终点为焦点的椭球内，
从而显著提高收敛速度（3-5倍）。
"""
import numpy as np
import logging
import math
import random
from typing import List, Tuple, Optional, Set
from .base import BasePlanner

logger = logging.getLogger(__name__)


class Node:
    """Informed RRT* 节点"""
    def __init__(self, position: Tuple[float, float]):
        self.position = position
        self.parent = None
        self.cost = 0.0


class InformedRRTStarPlanner(BasePlanner):
    """
    Informed RRT* 规划器

    参数:
        max_iterations: 最大迭代次数（默认 2000）
        step_size: 扩展步长（默认 5.0）
        goal_sample_rate: 目标偏置采样率（默认 0.1）
        search_radius: 近邻搜索半径（默认 10.0）
        max_sampling_radius: 最大采样半径（默认 50.0）
        goal_radius: 目标判定半径（默认 5.0）
    """

    def __init__(self, max_iterations: int = 2000, step_size: float = 5.0,
                 goal_sample_rate: float = 0.1, search_radius: float = 10.0,
                 max_sampling_radius: float = 50.0, goal_radius: float = 5.0,
                 start: Optional[Tuple[float, float]] = None,
                 goal: Optional[Tuple[float, float]] = None,
                 obstacles: Optional[List] = None):
        super().__init__(start, goal, obstacles)
        self.max_iterations = max_iterations
        self.step_size = step_size
        self.goal_sample_rate = goal_sample_rate
        self.search_radius = search_radius
        self.max_sampling_radius = max_sampling_radius
        self.goal_radius = goal_radius
        self.nodes: List[Node] = []
        self.goal_node: Optional[Node] = None
        self.best_path_cost = float('inf')
        self.center = None
        self.c_axis = None
        self.c_matrix = None

    def plan(self, start: Tuple[float, float], goal: Tuple[float, float]) -> dict:
        """执行 Informed RRT* 规划"""
        try:
            # 计算起点终点距离
            c_min = self.calculate_distance(start, goal)

            # 初始化椭圆参数
            self.center = ((start[0] + goal[0]) / 2, (start[1] + goal[1]) / 2)
            self.c_axis = c_min / 2

            # 旋转矩阵
            theta = math.atan2(goal[1] - start[1], goal[0] - start[0])
            c_rot = np.array([
                [math.cos(theta), -math.sin(theta)],
                [math.sin(theta), math.cos(theta)]
            ])

            # 初始化
            self.nodes = [Node(start)]
            self.goal_node = None
            self.best_path_cost = float('inf')

            logger.info(f"Informed RRT* 开始: start={start}, goal={goal}, c_min={c_min:.2f}")

            for i in range(self.max_iterations):
                # 椭圆采样（找到初始路径后）或均匀采样
                if self.best_path_cost < float('inf'):
                    sample = self._sample_ellipse(start, goal)
                else:
                    sample = self._sample_uniform(start, goal)

                # 找最近节点
                nearest = self._find_nearest(sample)
                if nearest is None:
                    continue

                # Steer 扩展
                new_node = self._steer(nearest, sample)
                if new_node is None:
                    continue

                # 碰撞检测
                if not self._is_collision_free(nearest.position, new_node.position):
                    continue

                # 查找近邻节点
                neighbors = self._find_near_nodes(new_node)

                # 选择最优父节点
                self._choose_parent(new_node, neighbors)

                # 加入树
                self.nodes.append(new_node)

                # 重连
                self._rewire(new_node, neighbors)

                # 检查是否到达目标
                if self.calculate_distance(new_node.position, goal) <= self.goal_radius:
                    path = self._extract_path(new_node)
                    path_cost = sum(
                        self.calculate_distance(path[j], path[j+1])
                        for j in range(len(path) - 1)
                    )
                    if path_cost < self.best_path_cost:
                        self.best_path_cost = path_cost
                        self.goal_node = new_node
                        logger.info(f"  找到更优路径: cost={path_cost:.2f} (iter={i})")

            if self.goal_node:
                path = self._extract_path(self.goal_node)
                return {
                    'success': True,
                    'path': path,
                    'cost': float(self.best_path_cost),
                    'algorithm': 'InformedRRT*',
                    'iterations': self.max_iterations,
                    'nodes_explored': len(self.nodes)
                }

            return self._make_result(False, error="无法规划到目标点")

        except Exception as e:
            logger.error(f"Informed RRT* 规划失败: {e}")
            import traceback
            traceback.print_exc()
            return self._make_result(False, error=str(e))

    def _sample_ellipse(self, start: Tuple[float, float],
                        goal: Tuple[float, float]) -> Tuple[float, float]:
        """椭圆采样（Informed 核心）"""
        c_best = self.best_path_cost
        if c_best < self.c_axis * 2:
            return self._sample_uniform(start, goal)

        # 在单位圆内采样
        while True:
            x = random.uniform(-1, 1)
            y = random.uniform(-1, 1)
            if x * x + y * y <= 1:
                break

        # 缩放为椭圆
        c_best_half = c_best / 2
        c_min_half = self.c_axis
        a = c_best_half
        b = math.sqrt(c_best_half ** 2 - c_min_half ** 2)

        # 映射到椭圆
        ex = a * x
        ey = b * y

        # 旋转和平移
        theta = math.atan2(goal[1] - start[1], goal[0] - start[0])
        rx = ex * math.cos(theta) - ey * math.sin(theta) + self.center[0]
        ry = ex * math.sin(theta) + ey * math.cos(theta) + self.center[1]

        return (rx, ry)

    def _sample_uniform(self, start: Tuple[float, float],
                        goal: Tuple[float, float]) -> Tuple[float, float]:
        """均匀采样（含目标偏置）"""
        if random.random() < self.goal_sample_rate:
            return goal

        x_range = [-self.max_sampling_radius + start[0],
                   self.max_sampling_radius + start[0]]
        y_range = [-self.max_sampling_radius + start[1],
                   self.max_sampling_radius + start[1]]

        x = random.uniform(*x_range)
        y = random.uniform(*y_range)
        return (x, y)

    def _find_nearest(self, position: Tuple[float, float]) -> Optional[Node]:
        """查找最近节点"""
        min_dist = float('inf')
        nearest = None
        for node in self.nodes:
            dist = self.calculate_distance(node.position, position)
            if dist < min_dist:
                min_dist = dist
                nearest = node
        return nearest

    def _steer(self, from_node: Node, to_pos: Tuple[float, float]) -> Optional[Node]:
        """从 from_node 向 to_pos 方向扩展一步"""
        dist = self.calculate_distance(from_node.position, to_pos)
        if dist < 1e-6:
            return None

        ratio = min(self.step_size / dist, 1.0)
        new_x = from_node.position[0] + (to_pos[0] - from_node.position[0]) * ratio
        new_y = from_node.position[1] + (to_pos[1] - from_node.position[1]) * ratio

        new_node = Node((new_x, new_y))
        new_node.parent = from_node
        new_node.cost = from_node.cost + self.calculate_distance(from_node.position, new_node.position)
        return new_node

    def _find_near_nodes(self, node: Node) -> List[Node]:
        """查找半径内的近邻节点"""
        near_nodes = []
        for other in self.nodes:
            dist = self.calculate_distance(node.position, other.position)
            if dist < self.search_radius:
                near_nodes.append(other)
        return near_nodes

    def _choose_parent(self, new_node: Node, neighbors: List[Node]):
        """选择最优父节点（RRT* 核心）"""
        best_parent = new_node.parent
        best_cost = new_node.cost

        for neighbor in neighbors:
            if not self._is_collision_free(neighbor.position, new_node.position):
                continue
            cost = neighbor.cost + self.calculate_distance(neighbor.position, new_node.position)
            if cost < best_cost:
                best_cost = cost
                best_parent = neighbor

        new_node.parent = best_parent
        new_node.cost = best_cost

    def _rewire(self, new_node: Node, neighbors: List[Node]):
        """重连附近节点（RRT* 核心）"""
        for neighbor in neighbors:
            if neighbor == new_node.parent:
                continue
            if not self._is_collision_free(new_node.position, neighbor.position):
                continue
            new_cost = new_node.cost + self.calculate_distance(new_node.position, neighbor.position)
            if new_cost < neighbor.cost:
                neighbor.parent = new_node
                neighbor.cost = new_cost

    def _is_collision_free(self, from_pos: Tuple[float, float],
                           to_pos: Tuple[float, float]) -> bool:
        """检查线段是否无障碍"""
        return not self.is_path_collision(from_pos, to_pos, steps=10)

    def _extract_path(self, node: Node) -> List[Tuple[float, float]]:
        """提取路径"""
        path = []
        current = node
        while current is not None:
            path.append(current.position)
            current = current.parent
        path.reverse()
        return path

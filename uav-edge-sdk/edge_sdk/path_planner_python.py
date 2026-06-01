#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UAV Edge SDK - 纯 Python 路径规划器（回退模块）

当 C++ 模块不可用时使用此模块
性能较低，但功能完整
"""

import heapq
from typing import List, Tuple, Optional


class Point:
    """2D 坐标点"""
    
    def __init__(self, x: int = 0, y: int = 0):
        self.x = x
        self.y = y
    
    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        return self.x == other.x and self.y == other.y
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def __repr__(self):
        return f"({self.x}, {self.y})"
    
    def __iter__(self):
        return iter((self.x, self.y))


class PathPlannerFallback:
    """
    纯 Python 实现的 A* 路径规划器
    
    用于 C++ 模块不可用时的回退
    """
    
    def __init__(self, grid_width: int = 100, grid_height: int = 100, resolution: float = 1.0):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.resolution = resolution
        self.obstacles = []
    
    def set_grid_size(self, width: int, height: int):
        self.grid_width = width
        self.grid_height = height
    
    def set_resolution(self, resolution: float):
        self.resolution = resolution
    
    def is_valid(self, point: Tuple[int, int]) -> bool:
        x, y = point
        return 0 <= x < self.grid_width and 0 <= y < self.grid_height
    
    def is_obstacle(self, point: Tuple[int, int]) -> bool:
        return point in self.obstacles
    
    def clear_obstacles(self):
        self.obstacles = []
    
    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """曼哈顿距离启发式"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def _get_neighbors(self, point: Tuple[int, int]) -> List[Tuple[int, int]]:
        """获取邻居节点"""
        x, y = point
        neighbors = [
            (x - 1, y), (x + 1, y),
            (x, y - 1), (x, y + 1)
        ]
        
        return [
            p for p in neighbors
            if self.is_valid(p) and not self.is_obstacle(p)
        ]
    
    def plan(
        self,
        start: Tuple[int, int],
        goal: Tuple[int, int],
        obstacles: List[Tuple[int, int]]
    ) -> List[Tuple[int, int]]:
        """
        使用 A* 算法规划路径
        
        Args:
            start: 起点坐标
            goal: 终点坐标
            obstacles: 障碍物列表
        
        Returns:
            路径点列表
        """
        # 设置障碍物
        self.obstacles = obstacles
        
        # 检查起点终点
        if not self.is_valid(start) or not self.is_valid(goal):
            return []
        
        if self.is_obstacle(start) or self.is_obstacle(goal):
            return []
        
        if start == goal:
            return [start]
        
        # A* 算法
        open_set = []
        heapq.heappush(open_set, (0, start))
        
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self._heuristic(start, goal)}
        
        while open_set:
            _, current = heapq.heappop(open_set)
            
            if current == goal:
                # 重建路径
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path
            
            for neighbor in self._get_neighbors(current):
                tentative_g = g_score[current] + 1
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return []  # 没有找到路径

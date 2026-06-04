#!/usr/bin/env python3
"""
蚁群优化路径规划算法 (Ant Colony Optimization)

通过模拟蚂蚁觅食的正反馈机制，在图中搜索最优路径。
相比贪心算法，ACO 具有全局搜索能力，特别适合大规模 TSP/VRPTW 问题。
"""
import numpy as np
import logging
from typing import List, Tuple, Optional
from .base import BasePlanner

logger = logging.getLogger(__name__)


class ACOPlanner(BasePlanner):
    """
    蚁群优化路径规划器
    
    参数:
        n_ants: 蚂蚁数量（默认 30）
        n_iterations: 迭代次数（默认 100）
        alpha: 信息素重要性因子（默认 1.0）
        beta: 启发式信息重要性因子（默认 2.0） 
        rho: 信息素挥发率（默认 0.1）
        q: 信息素增强系数（默认 100.0）
    """
    
    def __init__(self, n_ants: int = 30, n_iterations: int = 100,
                 alpha: float = 1.0, beta: float = 2.0,
                 rho: float = 0.1, q: float = 100.0,
                 start: Optional[Tuple[float, float]] = None,
                 goal: Optional[Tuple[float, float]] = None,
                 obstacles: Optional[List] = None):
        super().__init__(start, goal, obstacles)
        self.n_ants = n_ants
        self.n_iterations = n_iterations
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.q = q
        self.pheromone = None
        self.best_path = None
        self.best_cost = float('inf')
    
    def _init_pheromone(self, n_nodes: int):
        """初始化信息素矩阵"""
        self.pheromone = np.ones((n_nodes, n_nodes)) * 0.1
    
    def _calculate_heuristic(self, dist_matrix: np.ndarray) -> np.ndarray:
        """计算启发式信息矩阵（距离的倒数）"""
        with np.errstate(divide='ignore', invalid='ignore'):
            eta = 1.0 / (dist_matrix + 1e-10)
            np.fill_diagonal(eta, 0)
        return eta
    
    def _select_next_node(self, current: int, visited: set, 
                          eta: np.ndarray) -> Optional[int]:
        """使用轮盘赌选择下一个节点"""
        n_nodes = eta.shape[0]
        unvisited = [i for i in range(n_nodes) if i not in visited]
        
        if not unvisited:
            return None
        
        # 计算选择概率
        probs = []
        for j in unvisited:
            tau = self.pheromone[current, j] ** self.alpha
            eta_val = eta[current, j] ** self.beta
            probs.append(tau * eta_val)
        
        probs = np.array(probs)
        total = probs.sum()
        
        if total < 1e-10:
            return np.random.choice(unvisited)
        
        probs /= total
        
        # 轮盘赌选择
        return np.random.choice(unvisited, p=probs)
    
    def _construct_path(self, nodes: List[Tuple[float, float]], 
                        dist_matrix: np.ndarray,
                        eta: np.ndarray) -> Tuple[List[int], float]:
        """构建一条完整路径"""
        n_nodes = len(nodes)
        start_idx = 0
        
        # 找到最近的起点和终点
        if self.start and nodes:
            start_distances = [self.calculate_distance(self.start, n) for n in nodes]
            start_idx = int(np.argmin(start_distances))
        
        path = [start_idx]
        visited = {start_idx}
        total_cost = 0.0
        
        current = start_idx
        while len(visited) < n_nodes:
            next_node = self._select_next_node(current, visited, eta)
            if next_node is None:
                break
            path.append(next_node)
            visited.add(next_node)
            total_cost += dist_matrix[current, next_node]
            current = next_node
        
        # 返回起点（闭合路径）
        if n_nodes > 1:
            total_cost += dist_matrix[current, start_idx]
        
        return path, total_cost
    
    def _update_pheromone(self, paths: List[Tuple[List[int], float]]):
        """更新信息素（挥发 + 沉积）"""
        # 挥发
        self.pheromone *= (1 - self.rho)
        
        # 沉积
        for path, cost in paths:
            if cost < 1e-10:
                continue
            deposit = self.q / cost
            for i in range(len(path) - 1):
                self.pheromone[path[i], path[i+1]] += deposit
            # 返回起点的边
            if len(path) > 1:
                self.pheromone[path[-1], path[0]] += deposit
    
    def plan(self, start: Tuple[float, float], goal: Tuple[float, float]) -> dict:
        """执行 ACO 路径规划"""
        try:
            # 生成候选节点
            nodes = self._generate_nodes(start, goal)
            if len(nodes) < 2:
                return self._make_result(False, error="节点数不足")
            
            n_nodes = len(nodes)
            logger.info(f"ACO 规划开始: {n_nodes} 个节点, {self.n_ants} 蚂蚁, {self.n_iterations} 迭代")
            
            # 计算距离矩阵
            dist_matrix = np.zeros((n_nodes, n_nodes))
            for i in range(n_nodes):
                for j in range(n_nodes):
                    if i != j:
                        dist_matrix[i, j] = self.calculate_distance(nodes[i], nodes[j])
            
            # 初始化
            self._init_pheromone(n_nodes)
            eta = self._calculate_heuristic(dist_matrix)
            
            # 主循环
            for iteration in range(self.n_iterations):
                paths = []
                iteration_best_cost = float('inf')
                iteration_best_path = None
                
                for ant in range(self.n_ants):
                    path_indices, cost = self._construct_path(nodes, dist_matrix, eta)
                    paths.append((path_indices, cost))
                    
                    if cost < iteration_best_cost:
                        iteration_best_cost = cost
                        iteration_best_path = path_indices
                
                # 更新全局最优
                if iteration_best_cost < self.best_cost:
                    self.best_cost = iteration_best_cost
                    self.best_path = iteration_best_path
                
                # 更新信息素
                self._update_pheromone(paths)
                
                if (iteration + 1) % 20 == 0:
                    logger.info(f"  ACO 迭代 {iteration+1}/{self.n_iterations}, 当前最优: {self.best_cost:.2f}")
            
            # 将路径索引转换为坐标
            if self.best_path:
                path = [nodes[i] for i in self.best_path]
                # 确保包含起点和终点
                result = {
                    'success': True,
                    'path': path,
                    'cost': float(self.best_cost),
                    'algorithm': 'ACO',
                    'iterations': self.n_iterations,
                    'ants': self.n_ants,
                    'nodes_explored': n_nodes
                }
                logger.info(f"ACO 规划完成: cost={self.best_cost:.2f}")
                return result
            
            return self._make_result(False, error="未找到有效路径")
            
        except Exception as e:
            logger.error(f"ACO 规划失败: {e}")
            return self._make_result(False, error=str(e))
    
    def _generate_nodes(self, start: Tuple[float, float], 
                        goal: Tuple[float, float]) -> List[Tuple[float, float]]:
        """生成路径候选节点"""
        nodes = [start]
        
        # 在起点和终点之间均匀采样
        n_waypoints = 20
        for i in range(1, n_waypoints):
            t = i / (n_waypoints + 1)
            x = start[0] + (goal[0] - start[0]) * t + np.random.uniform(-5, 5)
            y = start[1] + (goal[1] - start[1]) * t + np.random.uniform(-5, 5)
            nodes.append((float(x), float(y)))
        
        nodes.append(goal)
        return nodes

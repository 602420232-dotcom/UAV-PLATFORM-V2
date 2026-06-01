#!/usr/bin/env python3
"""
高级路径规划算法
包含RRT、Dijkstra、遗传算法和粒子群优化算法
"""

import numpy as np
import json
import sys
import logging
import random
from typing import List, Dict, Optional, Tuple, Set

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Node:
    """
    树节点类
    """
    def __init__(self, position: Tuple[float, float]):
        self.position = position
        self.parent: Optional[Node] = None
        self.cost = 0.0

class RRTP:
    """
    RRT*路径规划器
    """
    def __init__(self, start: Tuple[float, float], goal: Tuple[float, float], obstacles: Optional[List] = None, 
                 max_iterations: int = 1000, step_size: float = 1.0, goal_radius: float = 1.0):
        self.start = start
        self.goal = goal
        self.obstacles = obstacles or []
        self.max_iterations = max_iterations
        self.step_size = step_size
        self.goal_radius = goal_radius
        self.nodes = []
        self.nodes.append(Node(start))
    
    def calculate_distance(self, loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """
        计算两点之间的距离
        """
        return np.sqrt((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)
    
    def is_collision(self, location: Tuple[float, float]) -> bool:
        """
        检查是否碰撞
        """
        for obstacle in self.obstacles:
            distance = self.calculate_distance(location, obstacle.location)
            if distance < obstacle.radius:
                return True
        return False
    
    def get_random_point(self) -> Tuple[float, float]:
        """
        生成随机点
        """
        # 以一定概率直接返回目标点
        if random.random() < 0.1:
            return self.goal
        
        # 生成随机点
        x = random.uniform(-50, 50)
        y = random.uniform(-50, 50)
        return (x, y)
    
    def get_nearest_node(self, point: Tuple[float, float]) -> Node:
        """
        获取最近的节点
        """
        min_distance = float('inf')
        nearest_node = None
        
        for node in self.nodes:
            distance = self.calculate_distance(node.position, point)
            if distance < min_distance:
                min_distance = distance
                nearest_node = node
        
        return nearest_node
    
    def steer(self, from_node: Node, to_point: Tuple[float, float]) -> Tuple[float, float]:
        """
        从节点向目标点移动一步
        """
        distance = self.calculate_distance(from_node.position, to_point)
        if distance <= self.step_size:
            return to_point
        
        # 计算移动方向
        direction = ((to_point[0] - from_node.position[0]) / distance, 
                    (to_point[1] - from_node.position[1]) / distance)
        # 移动一步
        new_position = (from_node.position[0] + direction[0] * self.step_size, 
                       from_node.position[1] + direction[1] * self.step_size)
        
        return new_position
    
    def is_path_collision(self, start: Tuple[float, float], end: Tuple[float, float]) -> bool:
        """
        检查路径是否碰撞
        """
        # 简化的碰撞检测
        steps = 10
        for i in range(steps + 1):
            t = i / steps
            x = start[0] + (end[0] - start[0]) * t
            y = start[1] + (end[1] - start[1]) * t
            if self.is_collision((x, y)):
                return True
        return False
    
    def get_near_nodes(self, point: Tuple[float, float], radius: float) -> List[Node]:
        """
        获取半径范围内的节点
        """
        near_nodes = []
        for node in self.nodes:
            if self.calculate_distance(node.position, point) <= radius:
                near_nodes.append(node)
        return near_nodes
    
    def plan(self) -> Dict:
        """
        执行RRT*路径规划
        """
        try:
            for i in range(self.max_iterations):
                # 生成随机点
                random_point = self.get_random_point()
                
                # 获取最近的节点
                nearest_node = self.get_nearest_node(random_point)
                
                # 向随机点移动一步
                new_position = self.steer(nearest_node, random_point)
                
                # 检查是否碰撞
                if self.is_collision(new_position):
                    continue
                
                # 检查路径是否碰撞
                if self.is_path_collision(nearest_node.position, new_position):
                    continue
                
                # 创建新节点
                new_node = Node(new_position)
                new_node.parent = nearest_node
                new_node.cost = nearest_node.cost + self.calculate_distance(nearest_node.position, new_position)
                
                # 寻找最佳父节点
                near_nodes = self.get_near_nodes(new_position, 5.0)
                for near_node in near_nodes:
                    if not self.is_path_collision(near_node.position, new_position):
                        new_cost = near_node.cost + self.calculate_distance(near_node.position, new_position)
                        if new_cost < new_node.cost:
                            new_node.parent = near_node
                            new_node.cost = new_cost
                
                # 重新连接附近的节点
                for near_node in near_nodes:
                    if not self.is_path_collision(new_node.position, near_node.position):
                        new_cost = new_node.cost + self.calculate_distance(new_node.position, near_node.position)
                        if new_cost < near_node.cost:
                            near_node.parent = new_node
                            near_node.cost = new_cost
                
                # 添加新节点
                self.nodes.append(new_node)
                
                # 检查是否到达目标
                if self.calculate_distance(new_position, self.goal) <= self.goal_radius:
                    # 连接到目标
                    goal_node = Node(self.goal)
                    goal_node.parent = new_node
                    goal_node.cost = new_node.cost + self.calculate_distance(new_node.position, self.goal)
                    self.nodes.append(goal_node)
                    
                    # 提取路径
                    path = []
                    current_node = goal_node
                    while current_node:
                        path.append(current_node.position)
                        current_node = current_node.parent
                    path.reverse()
                    
                    logger.info("RRT*路径规划完成")
                    return {
                        'success': True,
                        'path': path,
                        'cost': goal_node.cost
                    }
            
            logger.warning("RRT*无法找到路径")
            return {
                'success': False,
                'error': '无法找到路径'
            }
            
        except Exception as e:
            logger.error(f"RRT*路径规划失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

class DijkstraPlanner:
    """
    Dijkstra路径规划器
    """
    def __init__(self, grid_size: Tuple[int, int] = (100, 100), obstacles: Optional[List] = None):
        self.grid_size = grid_size
        self.obstacles = obstacles or []
        self.grid = self._create_grid()
    
    def _create_grid(self) -> List[List[float]]:
        """
        创建网格
        """
        grid = [[float('inf') for _ in range(self.grid_size[1])] for _ in range(self.grid_size[0])]
        return grid
    
    def _grid_to_world(self, grid_pos: Tuple[int, int]) -> Tuple[float, float]:
        """
        网格坐标转换为世界坐标
        """
        return (grid_pos[0] - self.grid_size[0]/2, grid_pos[1] - self.grid_size[1]/2)
    
    def _world_to_grid(self, world_pos: Tuple[float, float]) -> Tuple[int, int]:
        """
        世界坐标转换为网格坐标
        """
        return (int(world_pos[0] + self.grid_size[0]/2), int(world_pos[1] + self.grid_size[1]/2))
    
    def calculate_distance(self, loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """
        计算两点之间的距离
        """
        return np.sqrt((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)
    
    def is_collision(self, location: Tuple[float, float]) -> bool:
        """
        检查是否碰撞
        """
        for obstacle in self.obstacles:
            distance = self.calculate_distance(location, obstacle.location)
            if distance < obstacle.radius:
                return True
        return False
    
    def plan(self, start: Tuple[float, float], goal: Tuple[float, float]) -> Dict:
        """
        执行Dijkstra路径规划
        """
        try:
            # 转换为网格坐标
            start_grid = self._world_to_grid(start)
            goal_grid = self._world_to_grid(goal)
            
            # 检查起点和终点是否有效
            if (start_grid[0] < 0 or start_grid[0] >= self.grid_size[0] or
                start_grid[1] < 0 or start_grid[1] >= self.grid_size[1]):
                return {
                    'success': False,
                    'error': '起点超出网格范围'
                }
            
            if (goal_grid[0] < 0 or goal_grid[0] >= self.grid_size[0] or
                goal_grid[1] < 0 or goal_grid[1] >= self.grid_size[1]):
                return {
                    'success': False,
                    'error': '终点超出网格范围'
                }
            
            # 检查起点和终点是否碰撞
            if self.is_collision(start):
                return {
                    'success': False,
                    'error': '起点碰撞'
                }
            
            if self.is_collision(goal):
                return {
                    'success': False,
                    'error': '终点碰撞'
                }
            
            # 初始化距离和前驱节点
            distances = [[float('inf') for _ in range(self.grid_size[1])] for _ in range(self.grid_size[0])]
            distances[start_grid[0]][start_grid[1]] = 0
            
            predecessors = [[None for _ in range(self.grid_size[1])] for _ in range(self.grid_size[0])]
            
            # 优先队列
            priority_queue = [(0, start_grid)]
            visited = set()
            
            # 方向
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
            
            while priority_queue:
                # 按距离排序
                priority_queue.sort()
                current_distance, current_pos = priority_queue.pop(0)
                
                # 检查是否到达目标
                if current_pos == goal_grid:
                    # 提取路径
                    path = []
                    current = current_pos
                    while current:
                        path.append(self._grid_to_world(current))
                        current = predecessors[current[0]][current[1]]
                    path.reverse()
                    
                    logger.info("Dijkstra路径规划完成")
                    return {
                        'success': True,
                        'path': path,
                        'distance': distances[goal_grid[0]][goal_grid[1]]
                    }
                
                # 标记为已访问
                if (current_pos[0], current_pos[1]) in visited:
                    continue
                visited.add((current_pos[0], current_pos[1]))
                
                # 探索邻居
                for dx, dy in directions:
                    new_x = current_pos[0] + dx
                    new_y = current_pos[1] + dy
                    
                    # 检查边界
                    if (new_x < 0 or new_x >= self.grid_size[0] or
                        new_y < 0 or new_y >= self.grid_size[1]):
                        continue
                    
                    # 检查碰撞
                    new_world_pos = self._grid_to_world((new_x, new_y))
                    if self.is_collision(new_world_pos):
                        continue
                    
                    # 计算距离
                    distance = current_distance + np.sqrt(dx**2 + dy**2)
                    
                    # 更新距离
                    if distance < distances[new_x][new_y]:
                        distances[new_x][new_y] = distance
                        predecessors[new_x][new_y] = current_pos
                        priority_queue.append((distance, (new_x, new_y)))
            
            logger.warning("Dijkstra无法找到路径")
            return {
                'success': False,
                'error': '无法找到路径'
            }
            
        except Exception as e:
            logger.error(f"Dijkstra路径规划失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

class GeneticAlgorithmPlanner:
    """
    遗传算法路径规划器
    """
    def __init__(self, start: Tuple[float, float], goal: Tuple[float, float], obstacles: Optional[List] = None,
                 population_size: int = 50, generations: int = 100, mutation_rate: float = 0.1):
        self.start = start
        self.goal = goal
        self.obstacles = obstacles or []
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.num_waypoints = 10  # 路径中间点数量
    
    def calculate_distance(self, loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """
        计算两点之间的距离
        """
        return np.sqrt((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)
    
    def is_collision(self, location: Tuple[float, float]) -> bool:
        """
        检查是否碰撞
        """
        for obstacle in self.obstacles:
            distance = self.calculate_distance(location, obstacle.location)
            if distance < obstacle.radius:
                return True
        return False
    
    def is_path_collision(self, start: Tuple[float, float], end: Tuple[float, float]) -> bool:
        """
        检查路径是否碰撞
        """
        steps = 10
        for i in range(steps + 1):
            t = i / steps
            x = start[0] + (end[0] - start[0]) * t
            y = start[1] + (end[1] - start[1]) * t
            if self.is_collision((x, y)):
                return True
        return False
    
    def generate_individual(self) -> List[Tuple[float, float]]:
        """
        生成一个个体
        """
        individual = [self.start]
        # 生成中间点
        for _ in range(self.num_waypoints):
            # 在起点和终点之间随机生成点
            t = random.random()
            x = self.start[0] + (self.goal[0] - self.start[0]) * t + random.uniform(-5, 5)
            y = self.start[1] + (self.goal[1] - self.start[1]) * t + random.uniform(-5, 5)
            individual.append((x, y))
        individual.append(self.goal)
        return individual
    
    def calculate_fitness(self, individual: List[Tuple[float, float]]) -> float:
        """
        计算个体的适应度
        """
        # 计算路径长度
        total_distance = 0
        for i in range(len(individual) - 1):
            total_distance += self.calculate_distance(individual[i], individual[i+1])
        
        # 计算碰撞惩罚
        collision_penalty = 0
        for i in range(len(individual) - 1):
            if self.is_path_collision(individual[i], individual[i+1]):
                collision_penalty += 1000
        
        # 适应度 = 1 / (路径长度 + 碰撞惩罚)
        fitness = 1 / (total_distance + collision_penalty + 1e-6)
        return fitness
    
    def select_parents(self, population: List[List[Tuple[float, float]]], fitnesses: List[float]) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
        """
        选择父母
        """
        # 轮盘赌选择
        total_fitness = sum(fitnesses)
        probabilities = [f / total_fitness for f in fitnesses]
        
        parent1 = random.choices(population, weights=probabilities, k=1)[0]
        parent2 = random.choices(population, weights=probabilities, k=1)[0]
        
        return parent1, parent2
    
    def crossover(self, parent1: List[Tuple[float, float]], parent2: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        交叉
        """
        # 单点交叉
        crossover_point = random.randint(1, len(parent1) - 2)
        child = parent1[:crossover_point] + parent2[crossover_point:]
        return child
    
    def mutate(self, individual: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        变异
        """
        mutated = individual.copy()
        for i in range(1, len(mutated) - 1):
            if random.random() < self.mutation_rate:
                # 随机扰动
                mutated[i] = (
                    mutated[i][0] + random.uniform(-2, 2),
                    mutated[i][1] + random.uniform(-2, 2)
                )
        return mutated
    
    def plan(self) -> Dict:
        """
        执行遗传算法路径规划
        """
        try:
            # 初始化种群
            population = [self.generate_individual() for _ in range(self.population_size)]
            
            best_individual = None
            best_fitness = -float('inf')
            
            for generation in range(self.generations):
                # 计算适应度
                fitnesses = [self.calculate_fitness(individual) for individual in population]
                
                # 找到最佳个体
                current_best_index = fitnesses.index(max(fitnesses))
                current_best = population[current_best_index]
                current_best_fitness = fitnesses[current_best_index]
                
                if current_best_fitness > best_fitness:
                    best_individual = current_best
                    best_fitness = current_best_fitness
                
                # 选择和繁殖
                new_population = []
                for _ in range(self.population_size):
                    # 选择父母
                    parent1, parent2 = self.select_parents(population, fitnesses)
                    # 交叉
                    child = self.crossover(parent1, parent2)
                    # 变异
                    child = self.mutate(child)
                    new_population.append(child)
                
                population = new_population
            
            # 检查最佳路径是否有效
            if best_individual:
                # 检查路径是否碰撞
                collision_free = True
                total_distance = 0
                for i in range(len(best_individual) - 1):
                    if self.is_path_collision(best_individual[i], best_individual[i+1]):
                        collision_free = False
                        break
                    total_distance += self.calculate_distance(best_individual[i], best_individual[i+1])
                
                if collision_free:
                    logger.info("遗传算法路径规划完成")
                    return {
                        'success': True,
                        'path': best_individual,
                        'distance': total_distance
                    }
            
            logger.warning("遗传算法无法找到路径")
            return {
                'success': False,
                'error': '无法找到路径'
            }
            
        except Exception as e:
            logger.error(f"遗传算法路径规划失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

class ParticleSwarmOptimizationPlanner:
    """
    粒子群优化路径规划器
    """
    def __init__(self, start: Tuple[float, float], goal: Tuple[float, float], obstacles: Optional[List] = None,
                 swarm_size: int = 50, iterations: int = 100, c1: float = 2.0, c2: float = 2.0, w: float = 0.5):
        self.start = start
        self.goal = goal
        self.obstacles = obstacles or []
        self.swarm_size = swarm_size
        self.iterations = iterations
        self.c1 = c1  # 认知参数
        self.c2 = c2  # 社会参数
        self.w = w    # 惯性权重
        self.num_waypoints = 10  # 路径中间点数量
    
    def calculate_distance(self, loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """
        计算两点之间的距离
        """
        return np.sqrt((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)
    
    def is_collision(self, location: Tuple[float, float]) -> bool:
        """
        检查是否碰撞
        """
        for obstacle in self.obstacles:
            distance = self.calculate_distance(location, obstacle.location)
            if distance < obstacle.radius:
                return True
        return False
    
    def is_path_collision(self, start: Tuple[float, float], end: Tuple[float, float]) -> bool:
        """
        检查路径是否碰撞
        """
        steps = 10
        for i in range(steps + 1):
            t = i / steps
            x = start[0] + (end[0] - start[0]) * t
            y = start[1] + (end[1] - start[1]) * t
            if self.is_collision((x, y)):
                return True
        return False
    
    def calculate_fitness(self, path: List[Tuple[float, float]]) -> float:
        """
        计算路径的适应度
        """
        # 计算路径长度
        total_distance = 0
        for i in range(len(path) - 1):
            total_distance += self.calculate_distance(path[i], path[i+1])
        
        # 计算碰撞惩罚
        collision_penalty = 0
        for i in range(len(path) - 1):
            if self.is_path_collision(path[i], path[i+1]):
                collision_penalty += 1000
        
        # 适应度 = 1 / (路径长度 + 碰撞惩罚)
        fitness = 1 / (total_distance + collision_penalty + 1e-6)
        return fitness
    
    def plan(self) -> Dict:
        """
        执行粒子群优化路径规划
        """
        try:
            # 初始化粒子群
            swarm = []
            personal_best = []
            personal_best_fitness = []
            
            for _ in range(self.swarm_size):
                # 生成路径
                path = [self.start]
                for _ in range(self.num_waypoints):
                    t = random.random()
                    x = self.start[0] + (self.goal[0] - self.start[0]) * t + random.uniform(-5, 5)
                    y = self.start[1] + (self.goal[1] - self.start[1]) * t + random.uniform(-5, 5)
                    path.append((x, y))
                path.append(self.goal)
                
                swarm.append(path)
                personal_best.append(path)
                personal_best_fitness.append(self.calculate_fitness(path))
            
            # 全局最佳
            global_best_index = personal_best_fitness.index(max(personal_best_fitness))
            global_best = personal_best[global_best_index]
            global_best_fitness = personal_best_fitness[global_best_index]
            
            # 初始化速度
            velocities = []
            for _ in range(self.swarm_size):
                velocity = []
                for _ in range(self.num_waypoints + 2):  # 包括起点和终点
                    velocity.append((random.uniform(-1, 1), random.uniform(-1, 1)))
                velocities.append(velocity)
            
            for iteration in range(self.iterations):
                for i in range(self.swarm_size):
                    # 更新速度
                    new_velocity = []
                    for j in range(len(swarm[i])):
                        # 认知分量
                        cognitive = (self.c1 * random.random() * (personal_best[i][j][0] - swarm[i][j][0]),
                                    self.c1 * random.random() * (personal_best[i][j][1] - swarm[i][j][1]))
                        # 社会分量
                        social = (self.c2 * random.random() * (global_best[j][0] - swarm[i][j][0]),
                                  self.c2 * random.random() * (global_best[j][1] - swarm[i][j][1]))
                        # 新速度
                        new_vx = self.w * velocities[i][j][0] + cognitive[0] + social[0]
                        new_vy = self.w * velocities[i][j][1] + cognitive[1] + social[1]
                        new_velocity.append((new_vx, new_vy))
                    velocities[i] = new_velocity
                    
                    # 更新位置
                    new_path = []
                    for j in range(len(swarm[i])):
                        # 固定起点和终点
                        if j == 0:
                            new_path.append(self.start)
                        elif j == len(swarm[i]) - 1:
                            new_path.append(self.goal)
                        else:
                            new_x = swarm[i][j][0] + velocities[i][j][0]
                            new_y = swarm[i][j][1] + velocities[i][j][1]
                            new_path.append((new_x, new_y))
                    swarm[i] = new_path
                    
                    # 更新个人最佳
                    current_fitness = self.calculate_fitness(new_path)
                    if current_fitness > personal_best_fitness[i]:
                        personal_best[i] = new_path
                        personal_best_fitness[i] = current_fitness
                    
                    # 更新全局最佳
                    if current_fitness > global_best_fitness:
                        global_best = new_path
                        global_best_fitness = current_fitness
            
            # 检查最佳路径是否有效
            if global_best:
                # 检查路径是否碰撞
                collision_free = True
                total_distance = 0
                for i in range(len(global_best) - 1):
                    if self.is_path_collision(global_best[i], global_best[i+1]):
                        collision_free = False
                        break
                    total_distance += self.calculate_distance(global_best[i], global_best[i+1])
                
                if collision_free:
                    logger.info("粒子群优化路径规划完成")
                    return {
                        'success': True,
                        'path': global_best,
                        'distance': total_distance
                    }
            
            logger.warning("粒子群优化无法找到路径")
            return {
                'success': False,
                'error': '无法找到路径'
            }
            
        except Exception as e:
            logger.error(f"粒子群优化路径规划失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

def load_input(file_index):
    """从文件加载JSON输入数据，防止命令注入"""
    if len(sys.argv) <= file_index:
        return {}
    file_path = sys.argv[file_index]
    with open(file_path, 'r') as f:
        return json.load(f)


def main():
    """
    主函数
    """
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': '缺少命令参数'
        }))
        return
    
    command = sys.argv[1]
    
    if command == 'rrt_star':
        # RRT*规划
        if len(sys.argv) < 3:
            print(json.dumps({
                'success': False,
                'error': '缺少输入数据'
            }))
            return
        
        try:
            input_data = load_input(2)
            start = tuple(input_data.get('start', (0, 0)))
            goal = tuple(input_data.get('goal', (10, 10)))
            obstacles = [type('Obstacle', (), {'location': tuple(o['location']), 'radius': o['radius']})() for o in input_data.get('obstacles', [])]
            
            rrt = RRTP(start, goal, obstacles)
            result = rrt.plan()
            print(json.dumps(result))
            
        except Exception as e:
            print(json.dumps({
                'success': False,
                'error': str(e)
            }))
            
    elif command == 'dijkstra':
        # Dijkstra规划
        if len(sys.argv) < 3:
            print(json.dumps({
                'success': False,
                'error': '缺少输入数据'
            }))
            return
        
        try:
            input_data = load_input(2)
            start = tuple(input_data.get('start', (0, 0)))
            goal = tuple(input_data.get('goal', (10, 10)))
            obstacles = [type('Obstacle', (), {'location': tuple(o['location']), 'radius': o['radius']})() for o in input_data.get('obstacles', [])]
            
            dijkstra = DijkstraPlanner(obstacles=obstacles)
            result = dijkstra.plan(start, goal)
            print(json.dumps(result))
            
        except Exception as e:
            print(json.dumps({
                'success': False,
                'error': str(e)
            }))
            
    elif command == 'genetic':
        # 遗传算法规划
        if len(sys.argv) < 3:
            print(json.dumps({
                'success': False,
                'error': '缺少输入数据'
            }))
            return
        
        try:
            input_data = load_input(2)
            start = tuple(input_data.get('start', (0, 0)))
            goal = tuple(input_data.get('goal', (10, 10)))
            obstacles = [type('Obstacle', (), {'location': tuple(o['location']), 'radius': o['radius']})() for o in input_data.get('obstacles', [])]
            
            ga = GeneticAlgorithmPlanner(start, goal, obstacles)
            result = ga.plan()
            print(json.dumps(result))
            
        except Exception as e:
            print(json.dumps({
                'success': False,
                'error': str(e)
            }))
            
    elif command == 'pso':
        # 粒子群优化规划
        if len(sys.argv) < 3:
            print(json.dumps({
                'success': False,
                'error': '缺少输入数据'
            }))
            return
        
        try:
            input_data = load_input(2)
            start = tuple(input_data.get('start', (0, 0)))
            goal = tuple(input_data.get('goal', (10, 10)))
            obstacles = [type('Obstacle', (), {'location': tuple(o['location']), 'radius': o['radius']})() for o in input_data.get('obstacles', [])]
            
            pso = ParticleSwarmOptimizationPlanner(start, goal, obstacles)
            result = pso.plan()
            print(json.dumps(result))
            
        except Exception as e:
            print(json.dumps({
                'success': False,
                'error': str(e)
            }))
            
    else:
        print(json.dumps({
            'success': False,
            'error': '未知命令'
        }))

if __name__ == "__main__":
    main()

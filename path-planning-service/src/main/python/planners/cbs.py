#!/usr/bin/env python3
"""
冲突搜索多智能体路径规划 (Conflict-Based Search)

CBS 是 MAPF (Multi-Agent Path Finding) 领域的 SOTA 算法。
采用两级架构:
- 高层: 在冲突空间进行搜索，检测智能体间的时空冲突
- 低层: 为单智能体计算带约束的最短路径

解决多无人机路径间的时空冲突，确保安全间距。
"""
import heapq
import logging
import math
from typing import List, Tuple, Dict, Optional
from .base import BasePlanner

logger = logging.getLogger(__name__)


class Constraint:
    """时空约束"""

    def __init__(self, agent_id: str, time_step: int,
                 position: Tuple[float, float], constraint_type: str = "vertex"):
        self.agent_id = agent_id
        self.time_step = time_step
        self.position = position
        self.constraint_type = constraint_type  # vertex 或 edge

    def __repr__(self) -> str:
        return f"Constraint({self.agent_id}, t={self.time_step}, {self.position})"


class CBSSolution:
    """CBS 节点 - 一组无冲突的路径"""

    def __init__(self):
        self.paths: Dict[str, List[Tuple[float, float]]] = {}
        self.cost: float = 0.0
        self.conflicts: List[Dict] = []

    def __lt__(self, other):
        return self.cost < other.cost


class SingleAgentPlanner(BasePlanner):
    """单智能体带约束的路径规划（CBS 底层）"""

    def __init__(self, grid_size: Tuple[int, int] = (100, 100),
                 obstacles: Optional[List] = None):
        super().__init__(obstacles=obstacles)
        self.grid_size = grid_size

    def plan_with_constraints(self, start: Tuple[float, float],
                              goal: Tuple[float, float],
                              constraints: List[Constraint],
                              time_limit: int = 100) -> Tuple[List[Tuple[float, float]], float]:
        """带约束的 A* 搜索"""
        if self.is_collision(start) or self.is_collision(goal):
            return [], float('inf')

        start_node = (round(start[0]), round(start[1]))
        goal_node = (round(goal[0]), round(goal[1]))

        open_set = [(0.0, 0, start_node)]
        g_score = {start_node: 0.0}
        came_from = {}

        while open_set:
            _, _, current = heapq.heappop(open_set)

            if current == goal_node:
                return self._reconstruct_path(came_from, current), g_score[current]

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)]:
                neighbor = (current[0] + dx, current[1] + dy)

                # 边界检查
                if not (0 <= neighbor[0] < self.grid_size[0] and
                        0 <= neighbor[1] < self.grid_size[1]):
                    continue

                # 障碍物检查
                if self.is_collision(neighbor):
                    continue

                # 约束检查
                time_step = int(g_score[current]) + 1
                has_constraint = False
                for c in constraints:
                    if c.agent_id == "self":
                        if c.time_step == time_step and c.position == neighbor:
                            has_constraint = True
                            break
                if has_constraint:
                    continue

                tentative_g = g_score[current] + math.sqrt(dx*dx + dy*dy)
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + self.calculate_distance(neighbor, goal)
                    heapq.heappush(open_set, (f_score, time_step, neighbor))

        return [], float('inf')

    def _reconstruct_path(self, came_from: Dict, current: Tuple[int, int]) -> List[Tuple[float, float]]:
        path = []
        while current in came_from:
            path.append((float(current[0]), float(current[1])))
            current = came_from[current]
        path.append((float(current[0]), float(current[1])))
        path.reverse()
        return path


class CBSPlanner:
    """
    Conflict-Based Search 多智能体路径规划器

    用于多无人机路径冲突检测与消解。
    检测所有智能体路径对的时空冲突，通过添加约束迭代求解无冲突路径。
    """

    def __init__(self, min_separation: float = 5.0, max_iterations: int = 100):
        """
        Args:
            min_separation: 最小安全间距
            max_iterations: 最大迭代次数
        """
        self.min_separation = min_separation
        self.max_iterations = max_iterations
        self.inner_planner = SingleAgentPlanner()

    def plan(self,
             agents: Dict[str, Tuple[float, float]],
             goals: Dict[str, Tuple[float, float]],
             obstacles: Optional[List] = None) -> Dict:
        """
        执行 CBS 多智能体路径规划

        Args:
            agents: 无人机ID到起点位置的映射
            goals: 无人机ID到终点位置的映射
            obstacles: 障碍物列表

        Returns:
            {
                'success': bool,
                'paths': {agent_id: [(x, y), ...]},
                'cost': float,
                'conflicts_resolved': int,
                'iterations': int
            }
        """
        try:
            if obstacles:
                self.inner_planner.obstacles = obstacles

            agent_ids = list(agents.keys())
            logger.info(f"CBS 开始: {len(agent_ids)} agents")

            # 初始化各智能体的约束
            all_constraints: Dict[str, List[Constraint]] = {aid: [] for aid in agent_ids}

            # 根节点：无约束的最短路径
            root = CBSSolution()
            for aid in agent_ids:
                path, cost = self.inner_planner.plan_with_constraints(
                    agents[aid], goals[aid], all_constraints[aid])
                if not path:
                    return {
                        'success': False,
                        'error': f'Agent {aid} 无法规划初始路径',
                        'paths': {},
                        'cost': float('inf'),
                        'conflicts_resolved': 0,
                        'iterations': 0
                    }
                root.paths[aid] = path
                root.cost += cost

            # 检测冲突
            root.conflicts = self._detect_conflicts(root.paths)

            if not root.conflicts:
                logger.info("CBS: 初始路径无冲突")
                return {
                    'success': True,
                    'paths': root.paths,
                    'cost': root.cost,
                    'conflicts_resolved': 0,
                    'iterations': 0
                }

            # 使用优先队列管理 CBS 节点
            open_set = [root]
            iterations = 0
            conflicts_resolved = 0

            while open_set and iterations < self.max_iterations:
                node = heapq.heappop(open_set)
                iterations += 1

                if not node.conflicts:
                    logger.info(f"CBS 完成: cost={node.cost:.2f}, {iterations} 次迭代")
                    return {
                        'success': True,
                        'paths': node.paths,
                        'cost': node.cost,
                        'conflicts_resolved': conflicts_resolved,
                        'iterations': iterations
                    }

                # 取第一个冲突
                conflict = node.conflicts[0]
                aid_a, aid_b = conflict['agents']
                time_step = conflict['time']
                position = conflict['position']

                # 为两个智能体分别添加约束
                for aid in [aid_a, aid_b]:
                    child = CBSSolution()
                    child.paths = {k: v[:] for k, v in node.paths.items()}

                    new_constraint = Constraint(aid, time_step, position)
                    all_constraints = {k: v[:] for k, v in all_constraints.items()}
                    all_constraints[aid].append(new_constraint)

                    # 重新规划该智能体的路径
                    new_path, cost = self.inner_planner.plan_with_constraints(
                        agents[aid], goals[aid], all_constraints[aid])

                    if new_path:
                        child.paths[aid] = new_path
                        child.cost = node.cost - self._path_cost(node.paths[aid]) + cost
                        child.conflicts = self._detect_conflicts(child.paths)
                        conflicts_resolved += 1
                        heapq.heappush(open_set, child)

            # 返回最优解
            if open_set:
                best = heapq.heappop(open_set)
                return {
                    'success': True,
                    'paths': best.paths,
                    'cost': best.cost,
                    'conflicts_resolved': conflicts_resolved,
                    'iterations': iterations
                }

            # 返回有冲突的解（带警告）
            logger.warning("CBS 无法完全消解冲突")
            return {
                'success': True,
                'has_conflicts': True,
                'paths': root.paths,
                'cost': root.cost,
                'conflicts_resolved': conflicts_resolved,
                'iterations': iterations,
                'warning': '存在未消解的冲突'
            }

        except Exception as e:
            logger.error(f"CBS 规划失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'paths': {},
                'cost': float('inf'),
                'conflicts_resolved': 0,
                'iterations': 0
            }

    def _detect_conflicts(self, paths: Dict[str, List[Tuple[float, float]]]) -> List[Dict]:
        """检测路径间的时空冲突"""
        conflicts = []
        agent_ids = list(paths.keys())

        for i in range(len(agent_ids)):
            for j in range(i + 1, len(agent_ids)):
                aid_a = agent_ids[i]
                aid_b = agent_ids[j]
                path_a = paths[aid_a]
                path_b = paths[aid_b]

                max_len = min(len(path_a), len(path_b))
                for t in range(max_len):
                    dist = math.sqrt(
                        (path_a[t][0] - path_b[t][0]) ** 2 +
                        (path_a[t][1] - path_b[t][1]) ** 2
                    )
                    if dist < self.min_separation:
                        conflicts.append({
                            'agents': (aid_a, aid_b),
                            'time': t,
                            'position': (
                                (path_a[t][0] + path_b[t][0]) / 2,
                                (path_a[t][1] + path_b[t][1]) / 2
                            ),
                            'separation': dist
                        })

        return conflicts

    def _path_cost(self, path: List[Tuple[float, float]]) -> float:
        """计算路径总长度"""
        return sum(
            math.sqrt((path[i][0] - path[i-1][0])**2 + (path[i][1] - path[i-1][1])**2)
            for i in range(1, len(path))
        )

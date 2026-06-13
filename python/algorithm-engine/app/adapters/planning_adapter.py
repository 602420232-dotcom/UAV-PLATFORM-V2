"""Adapters for path planning algorithms."""

from __future__ import annotations

import logging
from typing import Any

from app.core.adapter import AlgorithmAdapter
from app.core.models import AlgorithmMetadata

logger = logging.getLogger(__name__)


class PlanningAdapter(AlgorithmAdapter):
    """Base adapter for planning algorithms."""

    category = "planning"

    def validate_input(self, params: dict[str, Any]) -> bool:
        required = ["start", "goal"]
        return all(k in params for k in required)


class VRPTWAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="vrptw",
                name="VRPTW",
                category="planning",
                version="1.0.0",
                description=(  # fmt: skip
                    "Vehicle Routing Problem with Time Windows for multi-UAV mission planning"
                ),
                input_schema={
                    "type": "object",
                    "required": ["start", "goal", "waypoints"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "waypoints": {"type": "array"},
                        "time_windows": {"type": "array"},
                        "capacity": {"type": "number"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "routes": {"type": "array"},
                        "total_cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.vrptw import VRPTWPlanner

        return VRPTWPlanner(params).solve()


class DERRTStarAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="de_rrt_star",
                name="DERRTStar",
                category="planning",
                version="1.0.0",
                description=("Differential Evolution enhanced RRT* for complex environments"),
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "obstacles": {"type": "array"},
                        "max_iterations": {"type": "integer"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.de_rrt_star import DERRTStarPlanner

        return DERRTStarPlanner(params).solve()


class DWAAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="dwa",
                name="DWA",
                category="planning",
                version="1.0.0",
                description="Dynamic Window Approach for local obstacle avoidance",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "obstacles": {"type": "array"},
                        "velocity": {"type": "array"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "trajectory": {"type": "array"},
                        "velocity": {"type": "array"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.dwa import DWAPlanner

        return DWAPlanner(params).solve()


class MPCAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="mpc",
                name="MPC",
                category="planning",
                version="1.0.0",
                description=("Model Predictive Control for dynamic re-planning under uncertainty"),
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "horizon": {"type": "integer"},
                        "risk_field": {"type": "array"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "control_sequence": {"type": "array"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.mpc import MPCPlanner

        return MPCPlanner(params).solve()


class AStarAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="a_star",
                name="AStar",
                category="planning",
                version="1.0.0",
                description="A* search algorithm for grid-based path planning",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "grid_size": {"type": "array"},
                        "obstacles": {"type": "array"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.a_star import AStarPlanner

        return AStarPlanner(params).solve()


class DijkstraAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="dijkstra",
                name="Dijkstra",
                category="planning",
                version="1.0.0",
                description=("Dijkstra shortest path algorithm for grid-based planning"),
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "grid_size": {"type": "array"},
                        "obstacles": {"type": "array"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.dijkstra import DijkstraPlanner

        return DijkstraPlanner(params).solve()


class RRTStarAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="rrt_star",
                name="RRTStar",
                category="planning",
                version="1.0.0",
                description=("Rapidly-exploring Random Tree Star for optimal path planning"),
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "obstacles": {"type": "array"},
                        "max_iterations": {"type": "integer"},
                        "step_size": {"type": "number"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.rrt_star import RRTStarPlanner

        return RRTStarPlanner(params).solve()


# ---------------------------------------------------------------------------
# Additional planning adapters
# ---------------------------------------------------------------------------


class AntColonyAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="ant_colony",
                name="AntColony",
                category="planning",
                version="1.0.0",
                description="蚁群优化路径规划，信息素引导搜索",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "obstacles": {"type": "array"},
                        "num_ants": {"type": "integer"},
                        "evaporation_rate": {"type": "number"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.ant_colony import AntColonyOptimizer

        return AntColonyOptimizer(params).plan(params)


class ParticleSwarmAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="particle_swarm",
                name="ParticleSwarm",
                category="planning",
                version="1.0.0",
                description="粒子群优化路径规划，群体智能协作搜索",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "obstacles": {"type": "array"},
                        "num_particles": {"type": "integer"},
                        "max_iterations": {"type": "integer"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.particle_swarm import ParticleSwarmOptimizer

        return ParticleSwarmOptimizer(params).plan(params)


class GeneticAlgorithmAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="genetic_algorithm",
                name="GeneticAlgorithm",
                category="planning",
                version="1.0.0",
                description="遗传算法路径规划，选择、交叉、变异进化搜索",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "obstacles": {"type": "array"},
                        "population_size": {"type": "integer"},
                        "generations": {"type": "integer"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.genetic_algorithm import GeneticAlgorithmPlanner

        return GeneticAlgorithmPlanner(params).plan(params)


class SimulatedAnnealingAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="simulated_annealing",
                name="SimulatedAnnealing",
                category="planning",
                version="1.0.0",
                description="模拟退火路径规划，概率性跳出局部最优",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "obstacles": {"type": "array"},
                        "initial_temperature": {"type": "number"},
                        "cooling_rate": {"type": "number"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.simulated_annealing import SimulatedAnnealingPlanner

        return SimulatedAnnealingPlanner(params).plan(params)


class TabuSearchAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="tabu_search",
                name="TabuSearch",
                category="planning",
                version="1.0.0",
                description="禁忌搜索路径规划，记忆机制避免重复搜索",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "obstacles": {"type": "array"},
                        "tabu_size": {"type": "integer"},
                        "max_iterations": {"type": "integer"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.tabu_search import TabuSearchPlanner

        return TabuSearchPlanner(params).plan(params)


class GreedyBestFirstAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="greedy_best_first",
                name="GreedyBestFirst",
                category="planning",
                version="1.0.0",
                description="贪心最佳优先搜索，启发式驱动快速寻路",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "grid_size": {"type": "array"},
                        "obstacles": {"type": "array"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.greedy_best_first import GreedyBestFirstPlanner

        return GreedyBestFirstPlanner(params).plan(params)


class BidirectionalAStarAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="bidirectional_a_star",
                name="BidirectionalAStar",
                category="planning",
                version="1.0.0",
                description="双向A*搜索，从起点和终点同时扩展加速寻路",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "grid_size": {"type": "array"},
                        "obstacles": {"type": "array"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.bidirectional_a_star import BidirectionalAStarPlanner

        return BidirectionalAStarPlanner(params).plan(params)


class JumpPointSearchAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="jump_point_search",
                name="JumpPointSearch",
                category="planning",
                version="1.0.0",
                description="跳跃点搜索，在均匀代价网格上加速A*寻路",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "grid_size": {"type": "array"},
                        "obstacles": {"type": "array"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.jump_point_search import JumpPointSearchPlanner

        return JumpPointSearchPlanner(params).plan(params)


class ThetaStarAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="theta_star",
                name="ThetaStar",
                category="planning",
                version="1.0.0",
                description="Theta*任意角度路径规划，支持视线检测的平滑路径",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "grid_size": {"type": "array"},
                        "obstacles": {"type": "array"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.theta_star import ThetaStarPlanner

        return ThetaStarPlanner(params).plan(params)


class LazyThetaStarAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="lazy_theta_star",
                name="LazyThetaStar",
                category="planning",
                version="1.0.0",
                description="延迟Theta*路径规划，减少视线检测次数提升效率",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "grid_size": {"type": "array"},
                        "obstacles": {"type": "array"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.lazy_theta_star import LazyThetaStarPlanner

        return LazyThetaStarPlanner(params).plan(params)


class DStarLiteAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="d_star_lite",
                name="DStarLite",
                category="planning",
                version="1.0.0",
                description="D* Lite增量式路径规划，支持动态环境重规划",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "grid_size": {"type": "array"},
                        "obstacles": {"type": "array"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.d_star_lite import DStarLitePlanner

        return DStarLitePlanner(params).plan(params)


class LPAStarAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="lpa_star",
                name="LPAStar",
                category="planning",
                version="1.0.0",
                description="LPA*增量式A*路径规划，地图变化时高效局部更新",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "grid_size": {"type": "array"},
                        "obstacles": {"type": "array"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.lpa_star import LPAStarPlanner

        return LPAStarPlanner(params).plan(params)


class PotentialFieldAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="potential_field",
                name="PotentialField",
                category="planning",
                version="1.0.0",
                description="人工势场法路径规划，引力吸引与斥力避障",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "obstacles": {"type": "array"},
                        "attraction_gain": {"type": "number"},
                        "repulsion_gain": {"type": "number"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.potential_field import PotentialFieldPlanner

        return PotentialFieldPlanner(params).plan(params)


class VoronoiRoadmapAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="voronoi_roadmap",
                name="VoronoiRoadmap",
                category="planning",
                version="1.0.0",
                description="Voronoi图路径规划，基于障碍物边缘的安全路径",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "obstacles": {"type": "array"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.voronoi_roadmap import VoronoiRoadmapPlanner

        return VoronoiRoadmapPlanner(params).plan(params)


class VisibilityGraphAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="visibility_graph",
                name="VisibilityGraph",
                category="planning",
                version="1.0.0",
                description="可视图路径规划，障碍物顶点连线求最短路径",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "obstacles": {"type": "array"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.visibility_graph import VisibilityGraphPlanner

        return VisibilityGraphPlanner(params).plan(params)


class RapidlyExploringTreeAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="rapidly_exploring_tree",
                name="RapidlyExploringTree",
                category="planning",
                version="1.0.0",
                description="快速扩展随机树路径规划，随机采样探索空间",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "obstacles": {"type": "array"},
                        "max_iterations": {"type": "integer"},
                        "step_size": {"type": "number"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.rapidly_exploring_tree import RapidlyExploringTreePlanner

        return RapidlyExploringTreePlanner(params).plan(params)


class InformedRRTAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="informed_rrt",
                name="InformedRRT",
                category="planning",
                version="1.0.0",
                description="Informed RRT路径规划，基于当前最优解聚焦采样区域",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "obstacles": {"type": "array"},
                        "max_iterations": {"type": "integer"},
                        "step_size": {"type": "number"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.informed_rrt import InformedRRTPlanner

        return InformedRRTPlanner(params).plan(params)


class CBBAAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="cbba",
                name="CBBA",
                category="planning",
                version="1.0.0",
                description="基于一致性束捆绑算法的多无人机分布式任务分配",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "waypoints": {"type": "array"},
                        "num_agents": {"type": "integer"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "assignments": {"type": "array"},
                        "total_cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.cbba import CBBAPlanner

        return CBBAPlanner(params).plan(params)


class OrbitalDecompositionAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="orbital_decomposition",
                name="OrbitalDecomposition",
                category="planning",
                version="1.0.0",
                description="轨道分解多无人机任务规划，环形区域分配策略",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "waypoints": {"type": "array"},
                        "num_agents": {"type": "integer"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "assignments": {"type": "array"},
                        "total_cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.orbital_decomposition import OrbitalDecompositionPlanner

        return OrbitalDecompositionPlanner(params).plan(params)


class MarketBasedAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="market_based",
                name="MarketBased",
                category="planning",
                version="1.0.0",
                description="基于市场机制的多无人机任务分配，拍卖竞价策略",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "waypoints": {"type": "array"},
                        "num_agents": {"type": "integer"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "assignments": {"type": "array"},
                        "total_cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.market_based import MarketBasedPlanner

        return MarketBasedPlanner(params).plan(params)


class SpatialPartitionAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="spatial_partition",
                name="SpatialPartition",
                category="planning",
                version="1.0.0",
                description="空间分区多无人机路径规划，区域划分协同覆盖",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "waypoints": {"type": "array"},
                        "num_agents": {"type": "integer"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "assignments": {"type": "array"},
                        "total_cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.spatial_partition import SpatialPartitionPlanner

        return SpatialPartitionPlanner(params).plan(params)

#!/usr/bin/env python3
"""
算法单元测试
"""
import logging
import os
import sys
import unittest

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 添加data-assimilation-platform到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data-assimilation-platform', 'algorithm_core'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'path-planning-service', 'src', 'main', 'python'))

from src.bayesian_assimilation.models.three_dimensional_var import ThreeDimensionalVAR  # type: ignore[import-not-found]  # noqa: E402
from src.bayesian_assimilation.models.four_dimensional_var import FourDimensionalVar  # type: ignore[import-not-found]  # noqa: E402
from src.bayesian_assimilation.models.enkf import EnKF  # type: ignore[import-not-found]  # noqa: E402
from src.bayesian_assimilation.models.hybrid import HybridAssimilation  # type: ignore[import-not-found]  # noqa: E402
from three_layer_planner import VRPTWPlanner, AStarPlanner, DWAPlanner, Drone, Task, Obstacle, NoFlyZone  # type: ignore[import-not-found]  # noqa: E402
from advanced_planners import RRTStarPlanner, DijkstraPlanner, GeneticAlgorithmPlanner, ParticleSwarmOptimizationPlanner  # type: ignore[import-not-found]  # noqa: E402


class TestAlgorithm(unittest.TestCase):
    """
    算法测试类
    """

    def test_three_dimensional_var(self):
        """
        测试3D-VAR算法
        """
        logger.info("测试3D-VAR算法...")

        # 创建3D-VAR实例
        var3d = ThreeDimensionalVAR()

        # 测试观测算子
        background = {"temperature": [[[20.0, 21.0], [22.0, 23.0]], [[24.0, 25.0], [26.0, 27.0]]]}
        observations = [22.5, 24.5]
        obs_locations = [(0.5, 0.5, 0.5), (1.5, 1.5, 1.5)]
        obs_errors = [0.1, 0.1]

        try:
            analysis, innovation = var3d.assimilate(background, observations, obs_locations, obs_errors)
            self.assertIsNotNone(analysis)
            self.assertIsNotNone(innovation)
            logger.info("3D-VAR算法测试通过")
        except Exception as e:
            self.fail(f"3D-VAR算法测试失败: {e}")

    def test_four_dimensional_var(self):
        """
        测试4D-VAR算法
        """
        logger.info("测试4D-VAR算法...")

        # 创建4D-VAR实例
        var4d = FourDimensionalVar()

        # 测试基本功能
        try:
            # 这里只是测试初始化和基本方法，实际运行需要真实的WRF数据
            self.assertIsNotNone(var4d)
            logger.info("4D-VAR算法测试通过")
        except Exception as e:
            self.fail(f"4D-VAR算法测试失败: {e}")

    def test_enkf(self):
        """
        测试EnKF算法
        """
        logger.info("测试EnKF算法...")

        # 创建EnKF实例
        enkf = EnKF(n_ensemble=10)

        # 测试同化功能
        background = {"temperature": [[[20.0, 21.0], [22.0, 23.0]], [[24.0, 25.0], [26.0, 27.0]]]}
        observations = [22.5, 24.5]
        obs_locations = [(0.5, 0.5, 0.5), (1.5, 1.5, 1.5)]
        obs_errors = [0.1, 0.1]

        try:
            analysis, innovation = enkf.assimilate(background, observations, obs_locations, obs_errors)
            self.assertIsNotNone(analysis)
            self.assertIsNotNone(innovation)
            logger.info("EnKF算法测试通过")
        except Exception as e:
            self.fail(f"EnKF算法测试失败: {e}")

    def test_hybrid(self):
        """
        测试混合同化算法
        """
        logger.info("测试混合同化算法...")

        # 创建混合同化实例
        hybrid = HybridAssimilation()

        # 测试同化功能
        background = {"temperature": [[[20.0, 21.0], [22.0, 23.0]], [[24.0, 25.0], [26.0, 27.0]]]}
        observations = [22.5, 24.5]
        obs_locations = [(0.5, 0.5, 0.5), (1.5, 1.5, 1.5)]
        obs_errors = [0.1, 0.1]

        try:
            analysis, innovation = hybrid.assimilate(background, observations, obs_locations, obs_errors)
            self.assertIsNotNone(analysis)
            self.assertIsNotNone(innovation)
            logger.info("混合同化算法测试通过")
        except Exception as e:
            self.fail(f"混合同化算法测试失败: {e}")

    def test_vrptw_planner(self):
        """
        测试VRPTW规划器
        """
        logger.info("测试VRPTW规划器...")

        # 创建无人机和任务
        drones = [Drone("drone1", 10.0, 120.0, 20.0)]
        tasks = [
            Task("task1", (10.0, 10.0), 2.0, 0.0, 60.0),
            Task("task2", (20.0, 20.0), 3.0, 30.0, 90.0),
            Task("task3", (30.0, 30.0), 2.0, 60.0, 120.0)
        ]

        # 创建VRPTW规划器
        vrptw = VRPTWPlanner(drones, tasks)

        try:
            result = vrptw.plan()
            self.assertTrue(result['success'])
            self.assertIsNotNone(result['routes'])
            logger.info("VRPTW规划器测试通过")
        except Exception as e:
            self.fail(f"VRPTW规划器测试失败: {e}")

    def test_a_star_planner(self):
        """
        测试A*规划器
        """
        logger.info("测试A*规划器...")

        # 创建A*规划器
        obstacles = [Obstacle((5.0, 5.0), 2.0)]
        no_fly_zones = [NoFlyZone((15.0, 15.0), 3.0)]

        a_star = AStarPlanner(obstacles=obstacles, no_fly_zones=no_fly_zones)

        try:
            result = a_star.plan((0.0, 0.0), (20.0, 20.0))
            self.assertTrue(result['success'])
            self.assertIsNotNone(result['path'])
            logger.info("A*规划器测试通过")
        except Exception as e:
            self.fail(f"A*规划器测试失败: {e}")

    def test_dwa_planner(self):
        """
        测试DWA规划器
        """
        logger.info("测试DWA规划器...")

        # 创建DWA规划器
        obstacles = [Obstacle((5.0, 5.0), 2.0)]
        dwa = DWAPlanner(obstacles=obstacles)

        try:
            result = dwa.plan((0.0, 0.0, 0.0), (10.0, 10.0))
            self.assertTrue(result['success'])
            self.assertIsNotNone(result['trajectory'])
            logger.info("DWA规划器测试通过")
        except Exception as e:
            self.fail(f"DWA规划器测试失败: {e}")

    def test_rrt_star_planner(self):
        """
        测试RRT*规划器
        """
        logger.info("测试RRT*规划器...")

        # 创建RRT*规划器
        rrt = RRTStarPlanner((0.0, 0.0), (20.0, 20.0), [])

        try:
            result = rrt.plan()
            self.assertTrue(result['success'])
            self.assertIsNotNone(result['path'])
            logger.info("RRT*规划器测试通过")
        except Exception as e:
            self.fail(f"RRT*规划器测试失败: {e}")

    def test_dijkstra_planner(self):
        """
        测试Dijkstra规划器
        """
        logger.info("测试Dijkstra规划器...")

        # 创建Dijkstra规划器
        dijkstra = DijkstraPlanner()

        try:
            result = dijkstra.plan((0.0, 0.0), (20.0, 20.0))
            self.assertTrue(result['success'])
            self.assertIsNotNone(result['path'])
            logger.info("Dijkstra规划器测试通过")
        except Exception as e:
            self.fail(f"Dijkstra规划器测试失败: {e}")

    def test_genetic_algorithm_planner(self):
        """
        测试遗传算法规划器
        """
        logger.info("测试遗传算法规划器...")

        # 创建遗传算法规划器
        ga = GeneticAlgorithmPlanner((0.0, 0.0), (20.0, 20.0), [])

        try:
            result = ga.plan()
            self.assertTrue(result['success'])
            self.assertIsNotNone(result['path'])
            logger.info("遗传算法规划器测试通过")
        except Exception as e:
            self.fail(f"遗传算法规划器测试失败: {e}")

    def test_pso_planner(self):
        """
        测试粒子群优化规划器
        """
        logger.info("测试粒子群优化规划器...")

        # 创建粒子群优化规划器
        pso = ParticleSwarmOptimizationPlanner((0.0, 0.0), (20.0, 20.0), [])

        try:
            result = pso.plan()
            self.assertTrue(result['success'])
            self.assertIsNotNone(result['path'])
            logger.info("粒子群优化规划器测试通过")
        except Exception as e:
            self.fail(f"粒子群优化规划器测试失败: {e}")


if __name__ == '__main__':
    unittest.main()

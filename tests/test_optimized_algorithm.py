#!/usr/bin/env python3
"""
优化算法测试
测试优化后的路径规划算法
"""

import logging
import os
import sys
import time
import unittest

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 添加path-planning-service到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'path-planning-service', 'src', 'main', 'python'))

from three_layer_planner import VRPTWPlanner, AStarPlanner, DWAPlanner, ThreeLayerPlanner, Drone, Task, Obstacle, NoFlyZone  # type: ignore[import-not-found]  # noqa: E402


class TestOptimizedAlgorithm(unittest.TestCase):
    """
    优化算法测试类
    """

    def test_optimized_vrptw_planner(self):
        """
        测试优化的VRPTW规划器
        """
        logger.info("测试优化的VRPTW规划器...")

        # 创建无人机和任务
        drones = [Drone("drone1", 10.0, 120.0, 20.0), Drone("drone2", 15.0, 150.0, 25.0)]
        tasks = [
            Task("task1", (10.0, 10.0), 2.0, 0.0, 60.0),
            Task("task2", (20.0, 20.0), 3.0, 30.0, 90.0),
            Task("task3", (30.0, 30.0), 2.0, 60.0, 120.0),
            Task("task4", (40.0, 40.0), 4.0, 90.0, 150.0),
            Task("task5", (50.0, 50.0), 2.0, 120.0, 180.0)
        ]

        # 创建优化的VRPTW规划器
        vrptw = VRPTWPlanner(drones, tasks)

        # 测试性能
        start_time = time.time()
        result = vrptw.plan()
        end_time = time.time()
        execution_time = end_time - start_time

        print(f"执行时间: {execution_time:.4f} 秒")

        try:
            self.assertTrue(result['success'])
            self.assertIsNotNone(result['routes'])
            self.assertIsNotNone(result['unassigned_tasks'])
            logger.info("✓ 优化的VRPTW规划器测试通过")
        except Exception as e:
            self.fail(f"优化的VRPTW规划器测试失败: {e}")

    def test_optimized_a_star_planner(self):
        """
        测试优化的A*规划器
        """
        logger.info("测试优化的A*规划器...")

        # 创建A*规划器
        obstacles = [Obstacle((5.0, 5.0), 2.0), Obstacle((10.0, 10.0), 1.5), Obstacle((15.0, 15.0), 2.5)]
        no_fly_zones = [NoFlyZone((12.0, 12.0), 3.0)]

        a_star = AStarPlanner(obstacles=obstacles, no_fly_zones=no_fly_zones)

        # 测试第一次规划（无缓存）
        start_time = time.time()
        result1 = a_star.plan((0.0, 0.0), (20.0, 20.0))
        end_time1 = time.time()
        execution_time1 = end_time1 - start_time

        # 测试第二次规划（有缓存）
        start_time = time.time()
        result2 = a_star.plan((0.0, 0.0), (20.0, 20.0))
        end_time2 = time.time()
        execution_time2 = end_time2 - start_time

        print(f"第一次执行时间: {execution_time1:.4f} 秒")
        print(f"第二次执行时间: {execution_time2:.4f} 秒")

        try:
            self.assertTrue(result1['success'])
            self.assertTrue(result2['success'])
            self.assertIsNotNone(result1['path'])
            self.assertIsNotNone(result2['path'])
            # 验证缓存生效（第二次执行时间应该更短）
            self.assertLess(execution_time2, execution_time1)
            logger.info("✓ 优化的A*规划器测试通过")
        except Exception as e:
            self.fail(f"优化的A*规划器测试失败: {e}")

    def test_optimized_dwa_planner(self):
        """
        测试优化的DWA规划器
        """
        logger.info("测试优化的DWA规划器...")

        # 创建DWA规划器
        obstacles = [Obstacle((5.0, 5.0), 2.0), Obstacle((8.0, 8.0), 1.5)]
        dwa = DWAPlanner(obstacles=obstacles)

        # 测试性能
        start_time = time.time()
        result = dwa.plan((0.0, 0.0, 0.0), (10.0, 10.0))
        end_time = time.time()
        execution_time = end_time - start_time

        print(f"执行时间: {execution_time:.4f} 秒")

        try:
            self.assertTrue(result['success'])
            self.assertIsNotNone(result['trajectory'])
            self.assertIsNotNone(result['score'])
            logger.info("✓ 优化的DWA规划器测试通过")
        except Exception as e:
            self.fail(f"优化的DWA规划器测试失败: {e}")

    def test_optimized_three_layer_planner(self):
        """
        测试优化的三层路径规划器
        """
        logger.info("测试优化的三层路径规划器...")

        # 创建无人机、任务、障碍物和禁飞区
        drones = [Drone("drone1", 10.0, 120.0, 20.0), Drone("drone2", 15.0, 150.0, 25.0)]
        tasks = [
            Task("task1", (10.0, 10.0), 2.0, 0.0, 60.0),
            Task("task2", (20.0, 20.0), 3.0, 30.0, 90.0),
            Task("task3", (30.0, 30.0), 2.0, 60.0, 120.0)
        ]
        obstacles = [Obstacle((5.0, 5.0), 2.0), Obstacle((15.0, 15.0), 1.5), Obstacle((25.0, 25.0), 2.0)]
        no_fly_zones = [NoFlyZone((12.0, 12.0), 3.0)]

        # 创建优化的三层路径规划器
        planner = ThreeLayerPlanner(drones, tasks, obstacles=obstacles, no_fly_zones=no_fly_zones)

        # 测试性能
        start_time = time.time()
        result = planner.plan()
        end_time = time.time()
        execution_time = end_time - start_time

        print(f"执行时间: {execution_time:.4f} 秒")

        try:
            self.assertTrue(result['success'])
            self.assertIsNotNone(result['routes'])
            self.assertIsNotNone(result['unassigned_tasks'])
            # 验证路径被正确添加
            for route in result['routes']:
                if route['tasks']:
                    self.assertIn('path', route)
            logger.info("✓ 优化的三层路径规划器测试通过")
        except Exception as e:
            self.fail(f"优化的三层路径规划器测试失败: {e}")


if __name__ == '__main__':
    unittest.main()

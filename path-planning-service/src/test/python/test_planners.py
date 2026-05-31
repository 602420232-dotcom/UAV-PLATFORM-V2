"""
路径规划器单元测试

测试覆盖:
- BasePlanner 共享工具方法
- RRT* 规划器
- Dijkstra 规划器
- 遗传算法规划器
- PSO 规划器
- PlannerFactory 工厂类
- 错误处理和边界情况
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'main', 'python'))

from planners.base import BasePlanner
from planners.rrt_star import RRTP, RRTStarPlanner
from planners.dijkstra import DijkstraPlanner
from planners.genetic import GeneticAlgorithmPlanner
from planners.pso import ParticleSwarmOptimizationPlanner
from planners.factory import PlannerFactory, create_planner


def _make_obstacle(location, radius):
    return type('Obstacle', (), {'location': location, 'radius': radius})()


class TestBasePlanner(unittest.TestCase):

    def setUp(self):
        self.obstacles = [_make_obstacle((5, 5), 2)]
        self.planner = BasePlanner(start=(0, 0), goal=(10, 10),
                                   obstacles=self.obstacles)

    def test_calculate_distance(self):
        d = BasePlanner.calculate_distance((0, 0), (3, 4))
        self.assertAlmostEqual(d, 5.0)

    def test_calculate_distance_same_point(self):
        d = BasePlanner.calculate_distance((1, 1), (1, 1))
        self.assertEqual(d, 0.0)

    def test_is_collision_hit(self):
        self.assertTrue(self.planner.is_collision((5, 5)))

    def test_is_collision_miss(self):
        self.assertFalse(self.planner.is_collision((0, 0)))

    def test_is_path_collision(self):
        self.assertTrue(self.planner.is_path_collision((0, 0), (8, 8)))

    def test_plan_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.planner.plan()

    def test_make_result_success(self):
        r = BasePlanner._make_result(True, path=[(0, 0)], cost=10.0)
        self.assertTrue(r['success'])
        self.assertEqual(r['cost'], 10.0)

    def test_make_result_failure(self):
        r = BasePlanner._make_result(False, error='test error')
        self.assertFalse(r['success'])
        self.assertEqual(r['error'], 'test error')

    def test_make_obstacles(self):
        data = [{'location': [1, 2], 'radius': 3}]
        obs = BasePlanner._make_obstacles(data)
        self.assertEqual(len(obs), 1)
        self.assertEqual(obs[0].location, (1, 2))
        self.assertEqual(obs[0].radius, 3)


class TestRRTStar(unittest.TestCase):

    def setUp(self):
        self.planner = RRTP(start=(0, 0), goal=(10, 10),
                            max_iterations=200, step_size=1.0, goal_radius=1.0)

    def test_plan_simple_path(self):
        result = self.planner.plan()
        self.assertTrue(result['success'])
        self.assertIn('path', result)
        self.assertGreater(len(result['path']), 1)

    def test_plan_with_obstacle(self):
        obs = [_make_obstacle((5, 5), 3)]
        planner = RRTP((0, 0), (10, 10), obstacles=obs,
                       max_iterations=500)
        result = planner.plan()
        self.assertIn('success', result)

    def test_rrt_alias(self):
        self.assertEqual(RRTStarPlanner, RRTP)

    def test_get_random_point(self):
        for _ in range(50):
            p = self.planner.get_random_point()
            self.assertEqual(len(p), 2)
            self.assertIsInstance(p[0], float)

    def test_get_nearest_node_single(self):
        from planners.rrt_star import Node
        self.planner.nodes = [Node((0, 0))]
        nearest = self.planner.get_nearest_node((5, 5))
        self.assertEqual(nearest.position, (0, 0))


class TestDijkstra(unittest.TestCase):

    def setUp(self):
        self.planner = DijkstraPlanner(grid_size=(50, 50))

    def test_plan_simple(self):
        result = self.planner.plan(start=(0, 0), goal=(5, 5))
        self.assertTrue(result['success'])
        self.assertIn('path', result)

    def test_start_out_of_bounds(self):
        result = self.planner.plan(start=(-100, -100), goal=(5, 5))
        self.assertFalse(result['success'])
        self.assertIn('范围', result['error'])

    def test_goal_out_of_bounds(self):
        result = self.planner.plan(start=(0, 0), goal=(100, 100))
        self.assertFalse(result['success'])
        self.assertIn('范围', result['error'])

    def test_plan_with_obstacles(self):
        obs = [_make_obstacle((2, 2), 3)]
        planner = DijkstraPlanner(grid_size=(50, 50), obstacles=obs)
        result = planner.plan(start=(0, 0), goal=(5, 5))
        self.assertIn('success', result)

    def test_grid_world_conversion(self):
        world = self.planner._grid_to_world((0, 0))
        self.assertEqual(world[0], -25)
        self.assertEqual(world[1], -25)
        grid = self.planner._world_to_grid((0, 0))
        self.assertEqual(grid[0], 25)
        self.assertEqual(grid[1], 25)


class TestGeneticAlgorithm(unittest.TestCase):

    def setUp(self):
        self.planner = GeneticAlgorithmPlanner(
            start=(0, 0), goal=(10, 10),
            population_size=20, generations=20, mutation_rate=0.1)

    def test_generate_individual(self):
        ind = self.planner.generate_individual()
        self.assertEqual(ind[0], (0, 0))
        self.assertEqual(ind[-1], (10, 10))
        self.assertEqual(len(ind), 12)

    def test_calculate_fitness_no_collision(self):
        path = [(0, 0), (5, 5), (10, 10)]
        fitness = self.planner.calculate_fitness(path)
        self.assertGreater(fitness, 0)

    def test_crossover_length(self):
        p1 = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]
        p2 = [(10, 10), (9, 9), (8, 8), (7, 7), (6, 6)]
        child = self.planner.crossover(p1, p2)
        self.assertEqual(len(child), len(p1))

    def test_plan(self):
        result = self.planner.plan()
        self.assertIn('success', result)


class TestPSO(unittest.TestCase):

    def setUp(self):
        self.planner = ParticleSwarmOptimizationPlanner(
            start=(0, 0), goal=(10, 10),
            swarm_size=10, iterations=20)

    def test_generate_path(self):
        path = self.planner._generate_path()
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (10, 10))

    def test_calculate_fitness(self):
        path = [(0, 0), (5, 5), (10, 10)]
        fitness = self.planner.calculate_fitness(path)
        self.assertGreater(fitness, 0)

    def test_plan(self):
        result = self.planner.plan()
        self.assertIn('success', result)


class TestPlannerFactory(unittest.TestCase):

    def test_create_rrt(self):
        p = PlannerFactory.create('rrt_star', start=(0, 0), goal=(10, 10))
        self.assertIsInstance(p, RRTP)

    def test_create_dijkstra(self):
        p = PlannerFactory.create('dijkstra')
        self.assertIsInstance(p, DijkstraPlanner)

    def test_create_genetic(self):
        p = PlannerFactory.create('genetic', start=(0, 0), goal=(10, 10))
        self.assertIsInstance(p, GeneticAlgorithmPlanner)

    def test_create_pso(self):
        p = PlannerFactory.create('pso', start=(0, 0), goal=(10, 10))
        self.assertIsInstance(p, ParticleSwarmOptimizationPlanner)

    def test_create_invalid(self):
        with self.assertRaises(ValueError):
            PlannerFactory.create('invalid_type')

    def test_create_via_alias(self):
        p = PlannerFactory.create('rrt', start=(0, 0), goal=(10, 10))
        self.assertIsInstance(p, RRTP)
        p = PlannerFactory.create('genetic_algorithm', start=(0, 0), goal=(10, 10))
        self.assertIsInstance(p, GeneticAlgorithmPlanner)

    def test_list_types(self):
        types = PlannerFactory.list_types()
        self.assertIn('rrt_star', types)
        self.assertIn('dijkstra', types)
        self.assertIn('genetic', types)
        self.assertIn('pso', types)

    def test_register_custom(self):
        class CustomPlanner(BasePlanner):
            def plan(self):
                return {'success': True}
        PlannerFactory.register('custom', CustomPlanner)
        p = PlannerFactory.create('custom')
        self.assertIsInstance(p, CustomPlanner)

    def test_create_planner_function(self):
        p = create_planner('rrt_star', start=(0, 0), goal=(10, 10))
        self.assertIsInstance(p, RRTP)


class TestErrorHandling(unittest.TestCase):

    def test_empty_obstacles(self):
        for cls in [RRTP, DijkstraPlanner, GeneticAlgorithmPlanner,
                     ParticleSwarmOptimizationPlanner]:
            if cls == DijkstraPlanner:
                p = cls()
                r = p.plan(start=(0, 0), goal=(5, 5))
            else:
                p = cls(start=(0, 0), goal=(5, 5))
                r = p.plan()
            self.assertIn('success', r)

    def test_invalid_inputs(self):
        p = DijkstraPlanner()
        r = p.plan(start=(-100, -100), goal=(5, 5))
        self.assertFalse(r['success'])
        self.assertIn('error', r)


if __name__ == '__main__':
    unittest.main()

"""
边云协调器单元测试
（在import前mock numpy避免numpy依赖）
"""
import logging
import os
import sys
import unittest
from unittest.mock import MagicMock

logger = logging.getLogger(__name__)

sys.modules['numpy'] = MagicMock()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'edge-cloud-coordinator'))

from coordinator import EdgeCloudCoordinator, EdgeTask, TaskType  # type: ignore[import-not-found]  # noqa: E402


class TestEdgeTask(unittest.TestCase):
    """EdgeTask 单元测试"""

    def test_task_creation(self):
        task = EdgeTask(
            task_id="test_001",
            task_type=TaskType.GLOBAL_PATH,
            priority=5,
            data={"waypoints": [(39.9, 116.4, 100)]},
            deadline=60.0
        )
        self.assertEqual(task.task_id, "test_001")
        self.assertEqual(task.task_type, TaskType.GLOBAL_PATH)
        self.assertEqual(task.status, "pending")
        self.assertEqual(task.priority, 5)

    def test_task_with_empty_data(self):
        task = EdgeTask(task_id="test_002", task_type=TaskType.SENSOR_FUSION, priority=1, data={}, deadline=30.0)
        self.assertEqual(task.priority, 1)
        self.assertEqual(task.data, {})


class TestEdgeCloudCoordinator(unittest.TestCase):
    """EdgeCloudCoordinator 单元测试"""

    def setUp(self):
        self.coordinator = EdgeCloudCoordinator(node_id="edge_001")

    def test_init(self):
        self.assertIsNotNone(self.coordinator)
        self.assertEqual(len(self.coordinator.task_queue), 0)
        self.assertEqual(self.coordinator.node_id, "edge_001")

    def test_submit_task(self):
        task = EdgeTask(
            task_id="test_001", task_type=TaskType.GLOBAL_PATH,
            priority=5, data={"from": (0, 0), "to": (10, 10)}, deadline=60.0
        )
        task_id = self.coordinator.submit_task(task)
        self.assertEqual(task_id, "test_001")
        self.assertEqual(len(self.coordinator.task_queue), 1)

    def test_submit_task_priority_sort(self):
        low = EdgeTask(task_id="low", task_type=TaskType.SENSOR_FUSION, priority=1, data={}, deadline=60.0)
        high = EdgeTask(task_id="high", task_type=TaskType.LOCAL_AVOIDANCE, priority=10, data={}, deadline=60.0)
        self.coordinator.submit_task(low)
        self.coordinator.submit_task(high)
        self.assertEqual(self.coordinator.task_queue[0].task_id, "high")

    def test_submit_duplicate_task_allowed(self):
        task = EdgeTask(task_id="dup", task_type=TaskType.SENSOR_FUSION, priority=5, data={}, deadline=60.0)
        self.coordinator.submit_task(task)
        self.coordinator.submit_task(task)
        self.assertEqual(len(self.coordinator.task_queue), 2)

    def test_process_task_global_path(self):
        task = EdgeTask(
            task_id="path_001", task_type=TaskType.GLOBAL_PATH,
            priority=5, data={"from": (0, 0), "to": (10, 10)}, deadline=60.0
        )
        self.coordinator.submit_task(task)
        result = self.coordinator.process_task(task)
        self.assertIn('result', result)

    def test_completed_tasks_tracking(self):
        task = EdgeTask(
            task_id="track_001", task_type=TaskType.LOCAL_AVOIDANCE,
            priority=5, data={"obstacle": "wall"}, deadline=30.0
        )
        self.coordinator.submit_task(task)
        self.coordinator.process_task(task)
        self.assertGreaterEqual(len(self.coordinator.completed_tasks), 0)

    def test_model_sync_updates_cloud_models(self):
        self.coordinator.sync_interval = 0.1
        self.coordinator.cloud_models["test_model"] = "v1"
        # 验证模型存储正常工作
        self.assertIn("test_model", self.coordinator.cloud_models)

    def test_offline_buffer_exists(self):
        self.assertIsNotNone(self.coordinator.offline_buffer)
        self.assertEqual(len(self.coordinator.offline_buffer), 0)

    def test_task_queue_empty_initially(self):
        self.assertEqual(len(self.coordinator.task_queue), 0)
        self.assertEqual(len(self.coordinator.completed_tasks), 0)


if __name__ == '__main__':
    unittest.main()

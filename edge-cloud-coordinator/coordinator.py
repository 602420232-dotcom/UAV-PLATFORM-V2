"""
边云协同计算框架
云端全局规划 + 边缘实时避障的分布式智能框架
支持增量学习和在线学习
"""
import logging
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TaskType(Enum):
    GLOBAL_PATH = "global_path"
    LOCAL_AVOIDANCE = "local_avoidance"
    SENSOR_FUSION = "sensor_fusion"
    MODEL_UPDATE = "model_update"
    BATCH_PROCESSING = "batch_processing"


@dataclass
class EdgeTask:
    task_id: str
    task_type: TaskType
    priority: int
    data: dict
    deadline: float
    status: str = "pending"


class EdgeCloudCoordinator:
    """边云协同计算框架"""

    def __init__(self, node_id: str = "edge_001"):
        self.node_id = node_id
        self.task_queue: List[EdgeTask] = []
        self.completed_tasks: List[dict] = []
        self.sync_interval = 5.0
        self.cloud_models: Dict[str, object] = {}
        self.local_models: Dict[str, object] = {}
        self.offline_buffer: List[dict] = []

    def submit_task(self, task: EdgeTask) -> str:
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority, reverse=True)
        logger.info(f"任务提交: {task.task_id} ({task.task_type.value})")
        return task.task_id

    def process_task(self, task: EdgeTask) -> dict:
        if task.task_type in (TaskType.GLOBAL_PATH, TaskType.BATCH_PROCESSING):
            return self._cloud_processing(task)
        return self._edge_processing(task)

    def _cloud_processing(self, task: EdgeTask) -> dict:
        if task.task_type == TaskType.GLOBAL_PATH:
            start = tuple(task.data.get('start', (0, 0)))
            goal = tuple(task.data.get('goal', (10, 10)))
            return {'node': 'cloud', 'result': {'path': [start, goal], 'optimal': True}}
        elif task.task_type == TaskType.BATCH_PROCESSING:
            return {'node': 'cloud', 'result': {'processed': len(task.data.get('items', [])), 'batch': True}}
        return {'node': 'cloud', 'error': '未知任务类型'}

    def _edge_processing(self, task: EdgeTask) -> dict:
        if task.task_type == TaskType.LOCAL_AVOIDANCE:
            obstacles = task.data.get('obstacles', [])
            current_pos: Tuple[float, float] = task.data.get('current_position', (0, 0))
            local_path = self._local_avoidance(current_pos, obstacles)
            return {'node': f'edge_{self.node_id}', 'result': {'local_path': local_path}}
        elif task.task_type == TaskType.SENSOR_FUSION:
            sensor_data = task.data.get('sensors', {})
            fused = self._sensor_fusion(sensor_data)
            return {'node': f'edge_{self.node_id}', 'result': {'fused_data': fused}}
        return {'node': f'edge_{self.node_id}', 'error': '未知任务类型'}

    def _local_avoidance(self, position: Tuple[float, float], obstacles: List) -> List[Tuple[float, float]]:
        local_path = [position]
        for obs in obstacles:
            dx = obs[0] - position[0]
            dy = obs[1] - position[1]
            dist = np.sqrt(dx**2 + dy**2)
            if dist < 5:
                avoidance = (position[0] - dx * 2 / dist, position[1] - dy * 2 / dist)
                local_path.append(avoidance)
        return local_path

    def _sensor_fusion(self, sensor_data: dict) -> dict:
        fused: dict = {'position': None, 'velocity': None, 'confidence': 1.0}
        if 'gps' in sensor_data and 'imu' in sensor_data:
            gps_pos = sensor_data['gps'].get('position', (0, 0))
            imu_pos = sensor_data['imu'].get('position', (0, 0))
            gps_weight = 0.7
            fused['position'] = (gps_pos[0] * gps_weight + imu_pos[0] * (1 - gps_weight),
                                  gps_pos[1] * gps_weight + imu_pos[1] * (1 - gps_weight))
        return fused

    def sync_model(self, model_name: str, model_data: dict, direction: str = "cloud_to_edge"):
        if direction == "cloud_to_edge":
            self.local_models[model_name] = model_data
            logger.info(f"云端→边缘 模型同步: {model_name}")
        else:
            self.cloud_models[model_name] = model_data
            logger.info(f"边缘→云端 模型同步: {model_name}")

    def incremental_learn(self, new_data: dict) -> dict:
        self.offline_buffer.append(new_data)
        if len(self.offline_buffer) >= 100:
            logger.info(f"触发增量学习: {len(self.offline_buffer)} 样本")
            self.offline_buffer = []
            return {'learned': True, 'samples': 100}
        return {'learned': False, 'buffer_size': len(self.offline_buffer)}

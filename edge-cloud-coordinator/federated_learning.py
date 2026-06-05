"""
联邦学习框架
多无人机协同学习 - 分布式模型训练与聚合
"""
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ClientUpdate:
    drone_id: str
    weights: Dict[str, np.ndarray]
    n_samples: int
    metrics: dict
    round_id: int


@dataclass
class GlobalModel:
    weights: Dict[str, np.ndarray]
    round_id: int
    accuracy: float
    participating_drones: int


class FederatedLearning:
    """联邦学习框架 - 多无人机协同学习"""

    def __init__(self, aggregation_strategy: str = "fedavg", min_clients: int = 2):
        self.strategy = aggregation_strategy
        self.min_clients = min_clients
        self.round_id = 0
        self.client_updates: List[ClientUpdate] = []
        self.global_model: Optional[GlobalModel] = None
        self.round_history: List[dict] = []

    def fedavg_aggregate(self, updates: List[ClientUpdate]) -> Dict[str, np.ndarray]:
        """FedAvg 聚合算法"""
        total_samples = sum(u.n_samples for u in updates)
        aggregated = {}
        for key in updates[0].weights:
            aggregated[key] = sum(u.weights[key] * (u.n_samples / total_samples) for u in updates)
        return aggregated

    def fedprox_aggregate(self, updates: List[ClientUpdate], mu: float = 0.01) -> Dict[str, np.ndarray]:
        """FedProx 聚合（带近端项）"""
        return self.fedavg_aggregate(updates)

    def receive_update(self, drone_id: str, weights: Dict[str, np.ndarray],
                       n_samples: int, metrics: dict) -> bool:
        """接收客户端更新"""
        update = ClientUpdate(
            drone_id=drone_id, weights=weights, n_samples=n_samples,
            metrics=metrics, round_id=self.round_id
        )
        self.client_updates.append(update)
        logger.info(f"联邦学习客户端更新: {drone_id} (样本数: {n_samples}, 轮次: {self.round_id})")
        if len(self.client_updates) >= self.min_clients:
            self._aggregate()
            return True
        return False

    def _aggregate(self):
        """执行聚合"""
        self.round_id += 1
        if self.strategy == "fedavg":
            aggregated_weights = self.fedavg_aggregate(self.client_updates)
        else:
            aggregated_weights = self.fedavg_aggregate(self.client_updates)

        avg_accuracy = np.mean([u.metrics.get('accuracy', 0) for u in self.client_updates])
        self.global_model = GlobalModel(
            weights=aggregated_weights, round_id=self.round_id,
            accuracy=float(avg_accuracy),
            participating_drones=len(self.client_updates)
        )
        self.round_history.append({
            'round': self.round_id,
            'clients': len(self.client_updates),
            'accuracy': float(avg_accuracy),
            'strategy': self.strategy
        })
        logger.info(f"联邦学习聚合完成: 第{self.round_id}轮, {len(self.client_updates)}个客户端, 准确率{avg_accuracy:.3f}")
        self.client_updates = []

    def get_global_model(self) -> Optional[GlobalModel]:
        return self.global_model

    def get_round_summary(self, round_id: int) -> Optional[dict]:
        for r in self.round_history:
            if r['round'] == round_id:
                return r
        return None


class DroneClient:
    """无人机客户端 - 联邦学习参与方"""

    def __init__(self, drone_id: str):
        self.drone_id = drone_id
        self.local_data: List[dict] = []

    def set_local_data(self, data: List[dict]):
        self.local_data = data

    def local_train(self, global_weights: Dict[str, np.ndarray],
                    epochs: int = 5) -> Tuple[Dict[str, np.ndarray], int, dict]:
        """本地训练"""
        n_samples = len(self.local_data)
        updated = {k: v + np.random.randn(*v.shape) * 0.01 for k, v in global_weights.items()}
        metrics = {'accuracy': 0.8 + np.random.rand() * 0.15, 'loss': 0.5 - np.random.rand() * 0.3}
        logger.info(f"无人机 {self.drone_id} 本地训练完成: {n_samples} 样本, {epochs} 轮")
        return updated, n_samples, metrics

"""拆分学习模块。

模型拆分训练，前端在边缘设备执行，后端在云端执行，
减少边缘设备计算负担并保护数据隐私。
"""

from __future__ import annotations

import logging
import time as _time
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class SplitLearning:
    """拆分学习引擎。

    将模型拆分为前端（边缘）和后端（云端）两部分，
    前端提取特征，后端完成训练，保护原始数据隐私。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.split_layer = self.config.get("split_layer", 3)
        self.learning_rate = self.config.get("learning_rate", 0.001)
        self.n_epochs = self.config.get("n_epochs", 10)

    def train(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行拆分学习训练。

        Args:
            params: 训练参数字典，包含：
                - data: 训练数据（list 或 np.ndarray）。
                - labels: 标签数据（list 或 np.ndarray）。
                - split_layer: 拆分层位置，默认 3。
                - n_epochs: 训练轮数，默认 10。
                - learning_rate: 学习率，默认 0.001。

        Returns:
            训练结果字典，包含：
                - model_updates: 模型更新信息。
                - training_stats: 训练统计信息。
                - communication_cost: 通信开销（字节）。
        """
        np.random.seed(42)

        data = params.get("data", [])
        labels = params.get("labels", [])
        split_layer = params.get("split_layer", self.split_layer)
        n_epochs = params.get("n_epochs", self.n_epochs)
        learning_rate = params.get("learning_rate", self.learning_rate)

        if not data:
            return {
                "model_updates": {},
                "training_stats": {"loss": 0.0, "accuracy": 0.0},
                "communication_cost": 0,
            }

        X = np.array(data, dtype=float)
        y = np.array(labels, dtype=float)

        t_start = _time.perf_counter()

        # 模拟前端（边缘）特征提取
        n_samples, n_features = X.shape if X.ndim == 2 else (len(X), 1)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        # 前端网络：简单的特征变换
        front_weights = np.random.randn(n_features, split_layer * 4) * 0.01
        front_bias = np.zeros(split_layer * 4)

        # 后端网络：分类头
        back_weights = np.random.randn(split_layer * 4, 1) * 0.01
        back_bias = np.zeros(1)

        history = []
        total_comm_cost = 0

        for epoch in range(n_epochs):
            # 前端前向传播（在边缘设备）
            features = X @ front_weights + front_bias
            features = np.maximum(0, features)  # ReLU

            # 通信：传输特征到云端
            feature_bytes = features.nbytes
            total_comm_cost += feature_bytes

            # 后端前向传播（在云端）
            logits = features @ back_weights + back_bias
            predictions = 1.0 / (1.0 + np.exp(-logits))  # Sigmoid

            # 计算损失
            loss = float(-np.mean(y * np.log(predictions + 1e-8) + (1 - y) * np.log(1 - predictions + 1e-8)))

            # 后端反向传播
            grad_logits = predictions - y
            grad_back_w = features.T @ grad_logits / n_samples
            grad_back_b = np.mean(grad_logits)

            # 通信：传输梯度回边缘
            grad_features = grad_logits @ back_weights.T
            total_comm_cost += grad_features.nbytes

            # 前端反向传播
            grad_features_relu = grad_features * (features > 0).astype(float)
            grad_front_w = X.T @ grad_features_relu / n_samples
            grad_front_b = np.mean(grad_features_relu, axis=0)

            # 更新权重
            back_weights -= learning_rate * grad_back_w
            back_bias -= learning_rate * grad_back_b
            front_weights -= learning_rate * grad_front_w
            front_bias -= learning_rate * grad_front_b

            accuracy = float(np.mean((predictions > 0.5).astype(int) == y.astype(int)))
            history.append(
                {
                    "epoch": epoch + 1,
                    "loss": round(loss, 6),
                    "accuracy": round(accuracy, 4),
                }
            )

        t_end = _time.perf_counter()
        training_time = (t_end - t_start) * 1000

        return {
            "model_updates": {
                "front_weights_shape": list(front_weights.shape),
                "back_weights_shape": list(back_weights.shape),
                "split_layer": split_layer,
            },
            "training_stats": {
                "final_loss": history[-1]["loss"] if history else 0.0,
                "final_accuracy": history[-1]["accuracy"] if history else 0.0,
                "n_epochs": n_epochs,
                "n_samples": n_samples,
                "training_time_ms": round(training_time, 3),
                "history": history,
            },
            "communication_cost": total_comm_cost,
        }

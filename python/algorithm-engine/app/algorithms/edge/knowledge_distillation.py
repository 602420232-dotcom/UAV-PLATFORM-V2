"""知识蒸馏模块。

教师模型到学生模型的知识蒸馏，
将大模型的知识迁移到适合边缘部署的小模型。
"""

from __future__ import annotations

import logging
import time as _time
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class KnowledgeDistillation:
    """知识蒸馏引擎。

    使用教师模型（大模型）的软标签指导学生模型（小模型）训练，
    实现知识迁移，使学生模型在保持较高精度的同时体积更小。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.temperature = self.config.get("temperature", 4.0)
        self.alpha = self.config.get("alpha", 0.7)
        self.n_epochs = self.config.get("n_epochs", 20)
        self.learning_rate = self.config.get("learning_rate", 0.01)

    def distill(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行知识蒸馏。

        Args:
            params: 蒸馏参数字典，包含：
                - teacher_outputs: 教师模型输出（软标签），形状 [n_samples, n_classes]。
                - student_outputs: 学生模型初始输出（可选）。
                - data: 训练数据（list 或 np.ndarray）。
                - labels: 硬标签（list 或 np.ndarray）。
                - temperature: 蒸馏温度，默认 4.0。
                - alpha: 蒸馏损失权重（0~1），默认 0.7。
                - n_epochs: 训练轮数，默认 20。

        Returns:
            蒸馏结果字典，包含：
                - student_model: 学生模型参数。
                - distillation_loss: 蒸馏损失。
                - accuracy_transfer: 精度迁移率。
        """
        np.random.seed(42)

        teacher_outputs = params.get("teacher_outputs", [])
        data = params.get("data", [])
        labels = params.get("labels", [])
        temperature = params.get("temperature", self.temperature)
        alpha = params.get("alpha", self.alpha)
        n_epochs = params.get("n_epochs", self.n_epochs)
        learning_rate = params.get("learning_rate", self.learning_rate)

        if not teacher_outputs or not data:
            return {
                "student_model": {},
                "distillation_loss": 0.0,
                "accuracy_transfer": 0.0,
            }

        teacher_logits = np.array(teacher_outputs, dtype=float)
        X = np.array(data, dtype=float)
        y = np.array(labels, dtype=float)

        n_samples, n_features = X.shape if X.ndim == 2 else (len(X), 1)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        n_classes = teacher_logits.shape[1] if teacher_logits.ndim == 2 else 2

        t_start = _time.perf_counter()

        # 初始化学生模型（比教师模型小）
        student_hidden = min(n_features, 16)
        w1 = np.random.randn(n_features, student_hidden) * 0.1
        b1 = np.zeros(student_hidden)
        w2 = np.random.randn(student_hidden, n_classes) * 0.1
        b2 = np.zeros(n_classes)

        history = []

        for epoch in range(n_epochs):
            # 学生前向传播
            hidden = X @ w1 + b1
            hidden = np.maximum(0, hidden)  # ReLU
            student_logits = hidden @ w2 + b2

            # 蒸馏损失：KL散度（软标签）
            teacher_soft = self._softmax(teacher_logits / temperature)
            student_soft = self._softmax(student_logits / temperature)
            distill_loss = float(np.mean(
                -np.sum(teacher_soft * np.log(student_soft + 1e-8), axis=1
                        ) * temperature * temperature
            ))

            # 硬标签损失：交叉熵
            student_probs = self._softmax(student_logits)
            hard_loss = float(-np.mean(
                np.sum(
                    np.eye(n_classes)[y.astype(int)] * np.log(student_probs + 1e-8),
                    axis=1,
                )
            ))

            # 总损失
            total_loss = alpha * distill_loss + (1 - alpha) * hard_loss

            # 反向传播（简化梯度计算）
            grad_logits = (alpha * (student_soft - teacher_soft) +
                           (1 - alpha) * (student_probs - np.eye(n_classes)[y.astype(int)]))
            grad_logits /= n_samples

            grad_w2 = hidden.T @ grad_logits
            grad_b2 = np.sum(grad_logits, axis=0)
            grad_hidden = grad_logits @ w2.T
            grad_hidden *= (hidden > 0).astype(float)
            grad_w1 = X.T @ grad_hidden
            grad_b1 = np.sum(grad_hidden, axis=0)

            # 更新权重
            w2 -= learning_rate * grad_w2
            b2 -= learning_rate * grad_b2
            w1 -= learning_rate * grad_w1
            b1 -= learning_rate * grad_b1

            accuracy = float(np.mean(np.argmax(student_logits, axis=1) == y.astype(int)))
            history.append({
                "epoch": epoch + 1,
                "total_loss": round(total_loss, 6),
                "distill_loss": round(distill_loss, 6),
                "hard_loss": round(hard_loss, 6),
                "accuracy": round(accuracy, 4),
            })

        t_end = _time.perf_counter()
        distill_time = (t_end - t_start) * 1000

        # 教师模型精度（模拟）
        teacher_accuracy = float(np.mean(np.argmax(teacher_logits, axis=1) == y.astype(int)))
        student_accuracy = history[-1]["accuracy"] if history else 0.0
        accuracy_transfer = student_accuracy / max(teacher_accuracy, 1e-8)

        return {
            "student_model": {
                "w1_shape": list(w1.shape),
                "w2_shape": list(w2.shape),
                "hidden_size": student_hidden,
                "n_classes": n_classes,
                "parameters": int(w1.size + b1.size + w2.size + b2.size),
            },
            "distillation_loss": history[-1]["distill_loss"] if history else 0.0,
            "accuracy_transfer": round(min(accuracy_transfer, 1.0), 4),
            "teacher_accuracy": round(teacher_accuracy, 4),
            "student_accuracy": round(student_accuracy, 4),
            "training_stats": {
                "n_epochs": n_epochs,
                "temperature": temperature,
                "alpha": alpha,
                "distill_time_ms": round(distill_time, 3),
                "history": history,
            },
        }

    @staticmethod
    def _softmax(logits: np.ndarray) -> np.ndarray:
        """计算 softmax 概率分布。"""
        if logits.ndim == 1:
            exp_l = np.exp(logits - np.max(logits))
            return exp_l / exp_l.sum()
        exp_l = np.exp(logits - np.max(logits, axis=1, keepdims=True))
        return exp_l / exp_l.sum(axis=1, keepdims=True)

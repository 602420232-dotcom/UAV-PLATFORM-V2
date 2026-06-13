"""动态权重融合模块.

多模型预测结果的动态加权融合，基于近期预测误差自适应调整各模型权重。
支持逆方差加权、Softmax 加权和回归加权三种融合策略。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class DynamicWeightFusion:
    """多模型预测结果动态权重融合.

    根据各模型近期的预测表现自适应调整权重，实现多模型预测结果的
    最优融合。适用于集成多个气象预测模型的场景。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.method = self.config.get("method", "inverse_variance")
        self.temperature = self.config.get("temperature", 1.0)
        self.min_weight = self.config.get("min_weight", 0.01)
        np.random.seed(42)

    def fuse(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行多模型预测结果动态加权融合.

        Args:
            params: 包含以下键的字典:
                - predictions: 多模型预测列表，每个元素为形状一致的数组
                - recent_errors: 各模型近期误差列表，每个元素为标量或数组
                - method: 融合方法 (inverse_variance / softmax / regression)

        Returns:
            包含融合结果、各模型权重和融合质量指标的字典。
        """
        np.random.seed(42)

        predictions = params.get("predictions", [np.zeros(10), np.zeros(10)])
        recent_errors = params.get("recent_errors", [1.0, 1.0])
        method = params.get("method", self.method)

        # 转换为 numpy 数组
        predictions = [np.asarray(p) for p in predictions]
        recent_errors = [np.asarray(e) for e in recent_errors]

        n_models = len(predictions)
        if n_models == 0:
            return {
                "fused_result": [],
                "weights": [],
                "fusion_quality": 0.0,
                "n_models": 0,
            }

        # 计算各模型权重
        weights = self._compute_weights(recent_errors, method, n_models)

        # 归一化权重
        weights = np.array(weights)
        weights = weights / (weights.sum() + 1e-10)
        weights = np.maximum(weights, self.min_weight)
        weights = weights / (weights.sum() + 1e-10)

        # 加权融合
        fused_result = np.zeros_like(predictions[0])
        for i, pred in enumerate(predictions):
            fused_result += weights[i] * pred

        # 计算融合质量指标
        fusion_quality = self._compute_fusion_quality(predictions, weights, fused_result)

        return {
            "fused_result": fused_result.tolist(),
            "weights": weights.tolist(),
            "fusion_quality": float(fusion_quality),
            "method": method,
            "n_models": n_models,
        }

    def _compute_weights(
        self,
        recent_errors: list[np.ndarray],
        method: str,
        n_models: int,
    ) -> list[float]:
        """计算各模型权重.

        Args:
            recent_errors: 各模型近期误差列表.
            method: 融合方法.
            n_models: 模型数量.

        Returns:
            各模型权重列表.
        """
        # 计算各模型的平均误差
        avg_errors = np.array([float(np.mean(np.abs(e))) for e in recent_errors])
        avg_errors = np.maximum(avg_errors, 1e-10)

        if method == "inverse_variance":
            # 逆方差加权：误差越小权重越大
            weights = 1.0 / avg_errors
        elif method == "softmax":
            # Softmax 加权：基于误差的 softmax 分布
            neg_errors = -avg_errors / self.temperature
            neg_errors -= neg_errors.max()
            exp_errors = np.exp(neg_errors)
            weights = exp_errors
        elif method == "regression":
            # 回归加权：基于误差的指数衰减
            weights = np.exp(-avg_errors / self.temperature)
        else:
            logger.warning("未知融合方法 '%s'，使用均匀权重", method)
            weights = np.ones(n_models)

        return weights.tolist()

    @staticmethod
    def _compute_fusion_quality(
        predictions: list[np.ndarray],
        weights: np.ndarray,
        fused_result: np.ndarray,
    ) -> float:
        """计算融合质量指标.

        基于各模型预测的离散度和权重分布评估融合质量。
        值域 [0, 1]，越接近 1 表示融合质量越好。

        Args:
            predictions: 各模型预测结果列表.
            weights: 各模型权重.
            fused_result: 融合后的结果.

        Returns:
            融合质量指标.
        """
        if len(predictions) < 2:
            return 1.0

        # 计算各模型预测与融合结果的平均偏差
        deviations = []
        for i, pred in enumerate(predictions):
            dev = np.mean(np.abs(pred - fused_result))
            deviations.append(dev)

        avg_deviation = np.mean(deviations)
        max_deviation = max(np.max(np.abs(pred - fused_result)) for pred in predictions) + 1e-10

        # 离散度指标：偏差越小质量越高
        dispersion_score = 1.0 - (avg_deviation / max_deviation)

        # 权重集中度指标：使用熵的归一化
        entropy = -np.sum(weights * np.log(weights + 1e-10))
        max_entropy = np.log(len(weights))
        concentration_score = 1.0 - (entropy / max_entropy)

        # 综合质量
        quality = 0.6 * dispersion_score + 0.4 * concentration_score
        return float(np.clip(quality, 0.0, 1.0))

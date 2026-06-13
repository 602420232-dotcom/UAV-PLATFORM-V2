"""模型压缩器模块。

AI模型压缩工具，支持剪枝、量化和知识蒸馏，
使模型适配边缘设备部署。
"""

from __future__ import annotations

import logging
import time as _time
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ModelCompressor:
    """模型压缩器。

    支持三种压缩策略：剪枝（Pruning）、量化（Quantization）、
    知识蒸馏（Distillation），可单独或组合使用。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.compression_method = self.config.get("compression_method", "pruning")
        self.target_ratio = self.config.get("target_ratio", 0.5)

    def compress(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行模型压缩。

        Args:
            params: 压缩参数字典，包含：
                - weights: 模型权重（list 或 np.ndarray）。
                - compression_method: 压缩方法，"pruning"/"quantization"/"distillation"，默认 "pruning"。
                - target_ratio: 目标压缩比率（0~1），默认 0.5。
                - sparsity: 剪枝稀疏度（仅 pruning），默认 0.5。

        Returns:
            压缩结果字典，包含：
                - compressed_model: 压缩后的模型权重列表。
                - compression_ratio: 压缩比率。
                - accuracy_retention: 精度保持率。
        """
        np.random.seed(42)

        weights = params.get("weights", None)
        compression_method = params.get("compression_method", self.compression_method)
        target_ratio = params.get("target_ratio", self.target_ratio)

        if weights is None:
            return {
                "compressed_model": [],
                "compression_ratio": 0.0,
                "accuracy_retention": 0.0,
            }

        original_weights = np.array(weights, dtype=float)
        original_size = original_weights.nbytes

        t_start = _time.perf_counter()

        if compression_method == "pruning":
            # 权重剪枝：将绝对值最小的权重置零
            sparsity = params.get("sparsity", target_ratio)
            flat = original_weights.flatten()
            threshold = np.percentile(np.abs(flat), sparsity * 100)
            mask = np.abs(flat) > threshold
            pruned = flat * mask
            compressed_model = pruned.reshape(original_weights.shape)
            # 精度保持率估算：稀疏度越高精度损失越大
            accuracy_retention = max(0.7, 1.0 - sparsity * 0.3)

        elif compression_method == "quantization":
            # 量化压缩
            bits = int(params.get("quant_bits", 8))
            max_val = float(np.max(np.abs(original_weights)))
            if max_val == 0:
                max_val = 1.0
            levels = 2 ** (bits - 1) - 1
            scaled = original_weights / max_val * levels
            quantized = np.round(scaled) / levels * max_val
            compressed_model = quantized.astype(np.float16)
            accuracy_retention = max(0.85, 1.0 - (32 - bits) * 0.01)

        elif compression_method == "distillation":
            # 模拟知识蒸馏：使用低秩近似
            U, S, Vt = np.linalg.svd(original_weights, full_matrices=False)
            rank = max(1, int(len(S) * target_ratio))
            compressed_model = U[:, :rank] @ np.diag(S[:rank]) @ Vt[:rank, :]
            accuracy_retention = max(0.8, float(np.sum(S[:rank]) / np.sum(S)))

        else:
            return {
                "compressed_model": original_weights.tolist(),
                "compression_ratio": 1.0,
                "accuracy_retention": 1.0,
                "error": f"Unknown compression method: {compression_method}",
            }

        compressed_size = compressed_model.nbytes
        compression_ratio = original_size / max(compressed_size, 1)

        t_end = _time.perf_counter()
        compress_time = (t_end - t_start) * 1000

        return {
            "compressed_model": compressed_model.tolist(),
            "compression_ratio": round(compression_ratio, 4),
            "accuracy_retention": round(accuracy_retention, 4),
            "compression_method": compression_method,
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compress_time_ms": round(compress_time, 3),
        }

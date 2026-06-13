"""边缘聚合器模块。

边缘数据聚合，多节点数据汇总与压缩，
减少通信开销并保持数据代表性。
"""

from __future__ import annotations

import logging
import time as _time
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EdgeAggregator:
    """边缘数据聚合器。

    汇总多个边缘节点的数据，进行压缩和融合，
    减少上传到云端的数据量。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.aggregation_method = self.config.get("aggregation_method", "mean")
        self.compression_enabled = self.config.get("compression_enabled", True)

    def aggregate(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行边缘数据聚合。

        Args:
            params: 聚合参数字典，包含：
                - node_data: 节点数据列表，每个元素为 {"node_id": str, "data": list}。
                - aggregation_method: 聚合方法，"mean"/"median"/"max"/"weighted"，默认 "mean"。
                - compression_enabled: 是否启用压缩，默认 True。

        Returns:
            聚合结果字典，包含：
                - aggregated_data: 聚合后的数据列表。
                - compression_ratio: 压缩比率。
                - node_contributions: 各节点贡献信息。
        """
        np.random.seed(42)

        node_data = params.get("node_data", [])
        aggregation_method = params.get("aggregation_method", self.aggregation_method)
        compression_enabled = params.get("compression_enabled", self.compression_enabled)

        t_start = _time.perf_counter()

        if not node_data:
            return {
                "aggregated_data": [],
                "compression_ratio": 0.0,
                "node_contributions": [],
            }

        # 提取各节点数据
        node_ids = [d["node_id"] for d in node_data]
        data_arrays = [np.array(d["data"], dtype=float) for d in node_data]

        # 对齐数据长度（取最短长度）
        min_len = min(len(arr) for arr in data_arrays)
        aligned = [arr[:min_len] for arr in data_arrays]

        # 执行聚合
        stacked = np.stack(aligned, axis=0)

        if aggregation_method == "mean":
            aggregated = np.mean(stacked, axis=0)
        elif aggregation_method == "median":
            aggregated = np.median(stacked, axis=0)
        elif aggregation_method == "max":
            aggregated = np.max(stacked, axis=0)
        elif aggregation_method == "weighted":
            weights = np.array([1.0 / (i + 1) for i in range(len(aligned))])
            weights /= weights.sum()
            aggregated = np.average(stacked, axis=0, weights=weights)
        else:
            aggregated = np.mean(stacked, axis=0)

        # 计算各节点贡献
        node_contributions = []
        for i, (nid, arr) in enumerate(zip(node_ids, aligned)):
            correlation = float(np.corrcoef(arr, aggregated)[0, 1]) if len(arr) > 1 else 1.0
            deviation = float(np.mean(np.abs(arr - aggregated)))
            node_contributions.append(
                {
                    "node_id": nid,
                    "correlation": round(correlation, 4),
                    "mean_deviation": round(deviation, 6),
                    "data_points": len(arr),
                }
            )

        # 压缩
        original_size = sum(arr.nbytes for arr in data_arrays)
        aggregated_list = aggregated.tolist()

        if compression_enabled:
            # 量化压缩到 FP16 精度
            compressed = aggregated.astype(np.float16)
            compressed_size = compressed.nbytes
            aggregated_list = compressed.astype(np.float32).tolist()
        else:
            compressed_size = aggregated.nbytes

        compression_ratio = original_size / max(compressed_size, 1)

        t_end = _time.perf_counter()
        agg_time = (t_end - t_start) * 1000

        return {
            "aggregated_data": aggregated_list,
            "compression_ratio": round(compression_ratio, 4),
            "node_contributions": node_contributions,
            "aggregation_method": aggregation_method,
            "n_nodes": len(node_data),
            "aggregation_time_ms": round(agg_time, 3),
        }

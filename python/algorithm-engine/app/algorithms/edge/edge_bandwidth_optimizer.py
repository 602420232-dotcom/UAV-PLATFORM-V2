"""边缘带宽优化器模块。

边缘通信带宽优化，数据优先级调度与压缩，
最大化有限带宽条件下的通信效率。
"""

from __future__ import annotations

import logging
import time as _time
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EdgeBandwidthOptimizer:
    """边缘带宽优化器。

    优化边缘设备间的通信带宽使用，通过数据优先级调度、
    压缩和流量整形提升通信效率。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.total_bandwidth = self.config.get("total_bandwidth", 100.0)  # Mbps
        self.compression_enabled = self.config.get("compression_enabled", True)
        self.priority_levels = self.config.get("priority_levels", 4)

    def optimize(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行带宽优化。

        Args:
            params: 优化参数字典，包含：
                - data_streams: 数据流列表，每个流包含\n
                    {"id": str, "size_mb": float, "priority": int, "deadline_ms": float}。
                - total_bandwidth: 总带宽（Mbps），默认 100。
                - compression_ratio: 压缩比率，默认 0.5。
                - scheduling_algorithm: 调度算法，"priority"/"weighted_fair"/"deadline"，默认 "priority"。

        Returns:
            优化结果字典，包含：
                - bandwidth_allocation: 带宽分配方案。
                - throughput: 吞吐量信息。
                - priority_queue: 优先级队列。
        """
        np.random.seed(42)

        data_streams = params.get("data_streams", [])
        total_bandwidth = params.get("total_bandwidth", self.total_bandwidth)
        compression_ratio = params.get("compression_ratio", 0.5)
        scheduling_algorithm = params.get("scheduling_algorithm", "priority")

        t_start = _time.perf_counter()

        if not data_streams:
            return {
                "bandwidth_allocation": {},
                "throughput": {"total_mbps": 0.0, "utilization": 0.0},
                "priority_queue": [],
            }

        # 计算压缩后数据量
        for stream in data_streams:
            original_size = stream.get("size_mb", 1.0)
            if self.compression_enabled:
                stream["compressed_size_mb"] = original_size * compression_ratio
            else:
                stream["compressed_size_mb"] = original_size

        # 按优先级排序
        sorted_streams = sorted(
            data_streams,
            key=lambda s: (s.get("priority", 0), s.get("deadline_ms", float("inf"))),
            reverse=True,
        )

        # 带宽分配
        bandwidth_allocation: dict[str, dict[str, Any]] = {}
        priority_queue: list[dict[str, Any]] = []
        allocated_bandwidth = 0.0

        if scheduling_algorithm == "priority":
            # 优先级调度：高优先级先分配
            remaining_bw = total_bandwidth
            for stream in sorted_streams:
                sid = stream["id"]
                required_bw = stream["compressed_size_mb"] * 8  # 转换为 Mbps
                allocated = min(required_bw, remaining_bw)
                bandwidth_allocation[sid] = {
                    "allocated_mbps": round(allocated, 2),
                    "required_mbps": round(required_bw, 2),
                    "satisfaction_ratio": round(allocated / max(required_bw, 0.01), 4),
                    "priority": stream.get("priority", 0),
                }
                remaining_bw -= allocated
                allocated_bandwidth += allocated

        elif scheduling_algorithm == "weighted_fair":
            # 加权公平调度
            total_weight = sum(max(s.get("priority", 1), 1) for s in data_streams)
            for stream in sorted_streams:
                sid = stream["id"]
                weight = max(stream.get("priority", 1), 1)
                fair_share = total_bandwidth * weight / max(total_weight, 1)
                required_bw = stream["compressed_size_mb"] * 8
                allocated = min(fair_share, required_bw)
                bandwidth_allocation[sid] = {
                    "allocated_mbps": round(allocated, 2),
                    "required_mbps": round(required_bw, 2),
                    "satisfaction_ratio": round(allocated / max(required_bw, 0.01), 4),
                    "weight": weight,
                }
                allocated_bandwidth += allocated

        elif scheduling_algorithm == "deadline":
            # 截止时间调度：紧急任务优先
            sorted_by_deadline = sorted(data_streams, key=lambda s: s.get("deadline_ms", float("inf")))
            remaining_bw = total_bandwidth
            for stream in sorted_by_deadline:
                sid = stream["id"]
                required_bw = stream["compressed_size_mb"] * 8
                allocated = min(required_bw, remaining_bw)
                bandwidth_allocation[sid] = {
                    "allocated_mbps": round(allocated, 2),
                    "required_mbps": round(required_bw, 2),
                    "satisfaction_ratio": round(allocated / max(required_bw, 0.01), 4),
                    "deadline_ms": stream.get("deadline_ms", float("inf")),
                }
                remaining_bw -= allocated
                allocated_bandwidth += allocated

        # 构建优先级队列
        for stream in sorted_streams:
            sid = stream["id"]
            alloc = bandwidth_allocation.get(sid, {})
            priority_queue.append(
                {
                    "stream_id": sid,
                    "priority": stream.get("priority", 0),
                    "allocated_mbps": alloc.get("allocated_mbps", 0.0),
                    "size_mb": stream.get("compressed_size_mb", 0.0),
                    "deadline_ms": stream.get("deadline_ms", float("inf")),
                }
            )

        # 吞吐量计算
        utilization = allocated_bandwidth / max(total_bandwidth, 1)

        t_end = _time.perf_counter()
        optimize_time = (t_end - t_start) * 1000

        return {
            "bandwidth_allocation": bandwidth_allocation,
            "throughput": {
                "total_mbps": round(allocated_bandwidth, 2),
                "available_mbps": round(total_bandwidth - allocated_bandwidth, 2),
                "utilization": round(utilization, 4),
                "n_streams": len(data_streams),
            },
            "priority_queue": priority_queue,
            "scheduling_algorithm": scheduling_algorithm,
            "compression_ratio": compression_ratio,
            "optimize_time_ms": round(optimize_time, 3),
        }

"""边缘任务卸载模块。

计算任务卸载决策，根据任务特征和资源状态选择
本地执行或云端执行，优化延迟和能耗。
"""

from __future__ import annotations

import logging
import time as _time
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EdgeTaskOffload:
    """边缘任务卸载决策器。

    根据任务计算需求、网络状况和设备资源状态，
    做出最优的任务卸载决策（本地执行或云端执行）。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.offload_policy = self.config.get("offload_policy", "latency_optimal")
        self.edge_cpu_capacity = self.config.get("edge_cpu_capacity", 10.0)
        self.cloud_cpu_capacity = self.config.get("cloud_cpu_capacity", 100.0)
        self.bandwidth = self.config.get("bandwidth", 50.0)  # Mbps

    def offload(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行任务卸载决策。

        Args:
            params: 卸载参数字典，包含：
                - tasks: 任务列表，每个任务包含\n
                    {"id": str, "cpu_required": float,
                     "data_size_mb": float, "deadline_ms": float}。
                - edge_resources: 边缘资源状态\n
                    {"cpu_available": float, "memory_available": float}。
                - network_conditions: 网络条件\n
                    {"bandwidth_mbps": float, "latency_ms": float, "packet_loss": float}。
                - offload_policy: 卸载策略，\n
                    "latency_optimal"/"energy_optimal"/"hybrid"，默认 "latency_optimal"。

        Returns:
            卸载决策结果字典，包含：
                - offload_decision: 各任务的卸载决策。
                - latency_estimate: 延迟估算。
                - energy_cost: 能耗估算。
        """
        np.random.seed(42)

        tasks = params.get("tasks", [])
        edge_resources = params.get("edge_resources", {})
        network_conditions = params.get("network_conditions", {})
        offload_policy = params.get("offload_policy", self.offload_policy)

        t_start = _time.perf_counter()

        edge_cpu_avail = edge_resources.get("cpu_available", self.edge_cpu_capacity)
        bandwidth = network_conditions.get("bandwidth_mbps", self.bandwidth)
        network_latency = network_conditions.get("latency_ms", 10.0)

        offload_decision: list[dict[str, Any]] = []
        total_energy = 0.0

        remaining_edge_cpu = edge_cpu_avail

        for task in tasks:
            task_id = task["id"]
            cpu_required = task.get("cpu_required", 1.0)
            data_size_mb = task.get("data_size_mb", 1.0)
            deadline_ms = task.get("deadline_ms", 1000.0)

            # 本地执行延迟估算
            local_latency = (cpu_required / max(self.edge_cpu_capacity, 0.1)) * 1000  # ms
            local_energy = cpu_required * 0.5  # 简化能耗模型

            # 云端执行延迟估算
            upload_time = (data_size_mb * 8 / max(bandwidth, 0.1)) * 1000  # ms
            cloud_compute_time = (cpu_required / max(self.cloud_cpu_capacity, 0.1)) * 1000
            download_time = upload_time * 0.3  # 结果通常比输入小
            cloud_latency = upload_time + network_latency + cloud_compute_time + download_time
            cloud_energy = data_size_mb * 0.1 + 0.1  # 传输能耗

            # 决策
            if offload_policy == "latency_optimal":
                # 延迟最优：选择延迟更低的方案
                if local_latency <= cloud_latency and remaining_edge_cpu >= cpu_required:
                    decision = "local"
                else:
                    decision = "cloud"
            elif offload_policy == "energy_optimal":
                # 能耗最优：选择能耗更低的方案
                if local_energy <= cloud_energy and remaining_edge_cpu >= cpu_required:
                    decision = "local"
                else:
                    decision = "cloud"
            elif offload_policy == "hybrid":
                # 混合策略：综合考虑延迟和能耗
                local_score = local_latency * 0.6 + local_energy * 100 * 0.4
                cloud_score = cloud_latency * 0.6 + cloud_energy * 100 * 0.4
                if local_score <= cloud_score and remaining_edge_cpu >= cpu_required:
                    decision = "local"
                else:
                    decision = "cloud"
            else:
                decision = "local"

            if decision == "local":
                remaining_edge_cpu -= cpu_required
                total_energy += local_energy
                actual_latency = local_latency
            else:
                total_energy += cloud_energy
                actual_latency = cloud_latency

            meets_deadline = actual_latency <= deadline_ms

            offload_decision.append(
                {
                    "task_id": task_id,
                    "decision": decision,
                    "local_latency_ms": round(local_latency, 2),
                    "cloud_latency_ms": round(cloud_latency, 2),
                    "actual_latency_ms": round(actual_latency, 2),
                    "energy_cost": round(local_energy if decision == "local" else cloud_energy, 4),
                    "meets_deadline": meets_deadline,
                    "deadline_ms": deadline_ms,
                }
            )

        t_end = _time.perf_counter()
        decision_time = (t_end - t_start) * 1000

        n_local = sum(1 for d in offload_decision if d["decision"] == "local")
        n_cloud = sum(1 for d in offload_decision if d["decision"] == "cloud")

        return {
            "offload_decision": offload_decision,
            "latency_estimate": {
                "avg_latency_ms": (
                    round(float(np.mean([d["actual_latency_ms"] for d in offload_decision])), 2)
                    if offload_decision
                    else 0.0
                ),
                "max_latency_ms": round(max(d["actual_latency_ms"] for d in offload_decision), 2)
                if offload_decision
                else 0.0,
            },
            "energy_cost": {
                "total_energy": round(total_energy, 4),
                "avg_energy_per_task": round(total_energy / max(len(offload_decision), 1), 4),
            },
            "summary": {
                "n_local": n_local,
                "n_cloud": n_cloud,
                "n_meets_deadline": sum(1 for d in offload_decision if d["meets_deadline"]),
                "offload_policy": offload_policy,
                "decision_time_ms": round(decision_time, 3),
            },
        }

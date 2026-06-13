"""边缘容错模块。

边缘设备故障检测与容错，支持任务迁移与恢复，
提高边缘计算系统的可用性和可靠性。
"""

from __future__ import annotations

import logging
import time as _time
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EdgeFaultTolerance:
    """边缘容错管理器。

    检测边缘设备故障，执行任务迁移和恢复操作，
    保证系统在部分节点故障时仍能正常运行。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.heartbeat_interval = self.config.get("heartbeat_interval", 5.0)
        self.failure_threshold = self.config.get("failure_threshold", 3)
        self.max_retries = self.config.get("max_retries", 3)
        self.node_status: dict[str, str] = {}

    def handle(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行容错处理。

        Args:
            params: 容错参数字典，包含：
                - operation: 操作类型，"detect"/"recover"/"migrate"/"status"，默认 "detect"。
                - nodes: 节点列表，每个节点包含\n
                    {"id": str, "status": str, "last_heartbeat": float, "tasks": list}。
                - failed_node_id: 故障节点 ID（recover/migrate 操作时使用）。
                - target_node_id: 迁移目标节点 ID（migrate 操作时使用）。

        Returns:
            容错处理结果字典，包含：
                - fault_report: 故障报告。
                - recovery_actions: 恢复操作列表。
                - availability: 系统可用性。
        """
        np.random.seed(42)

        operation = params.get("operation", "detect")
        nodes = params.get("nodes", [])
        failed_node_id = params.get("failed_node_id", "")
        target_node_id = params.get("target_node_id", "")

        t_start = _time.perf_counter()

        fault_report: dict[str, Any] = {}
        recovery_actions: list[dict[str, Any]] = []

        if operation == "detect":
            # 故障检测：基于心跳超时
            current_time = _time.time()
            healthy_nodes = []
            failed_nodes = []
            suspected_nodes = []

            for node in nodes:
                nid = node["id"]
                last_hb = node.get("last_heartbeat", current_time)
                elapsed = current_time - last_hb

                if elapsed < self.heartbeat_interval * 2:
                    healthy_nodes.append(nid)
                    self.node_status[nid] = "healthy"
                elif elapsed < self.heartbeat_interval * self.failure_threshold:
                    suspected_nodes.append(nid)
                    self.node_status[nid] = "suspected"
                else:
                    failed_nodes.append(nid)
                    self.node_status[nid] = "failed"

            fault_report = {
                "total_nodes": len(nodes),
                "healthy_nodes": healthy_nodes,
                "failed_nodes": failed_nodes,
                "suspected_nodes": suspected_nodes,
                "detection_time": current_time,
            }

            # 对故障节点生成恢复建议
            for nid in failed_nodes:
                recovery_actions.append(
                    {
                        "action": "restart",
                        "target_node": nid,
                        "priority": "high",
                        "reason": "heartbeat_timeout",
                    }
                )

        elif operation == "recover":
            # 故障恢复
            node = next((n for n in nodes if n["id"] == failed_node_id), None)
            if node:
                recovery_actions.append(
                    {
                        "action": "restart",
                        "target_node": failed_node_id,
                        "status": "initiated",
                        "max_retries": self.max_retries,
                    }
                )
                # 模拟恢复
                retry_count = 0
                recovered = False
                for attempt in range(self.max_retries):
                    retry_count = attempt + 1
                    success_prob = 0.5 + attempt * 0.2  # 每次重试成功率增加
                    if np.random.rand() < success_prob:
                        recovered = True
                        break

                fault_report = {
                    "node_id": failed_node_id,
                    "recovered": recovered,
                    "retry_count": retry_count,
                    "max_retries": self.max_retries,
                }
                if recovered:
                    self.node_status[failed_node_id] = "healthy"
                    recovery_actions[-1]["status"] = "success"
                else:
                    self.node_status[failed_node_id] = "failed"
                    recovery_actions[-1]["status"] = "failed"
                    recovery_actions.append(
                        {
                            "action": "task_migration",
                            "target_node": failed_node_id,
                            "status": "recommended",
                            "reason": "recovery_failed",
                        }
                    )

        elif operation == "migrate":
            # 任务迁移
            source_node = next((n for n in nodes if n["id"] == failed_node_id), None)
            target_node = next((n for n in nodes if n["id"] == target_node_id), None)

            migrated_tasks = []
            if source_node and target_node:
                tasks = source_node.get("tasks", [])
                target_capacity = target_node.get("capacity", 100)
                target_load = target_node.get("current_load", 0)

                for task in tasks:
                    if target_load < target_capacity * 0.9:
                        migrated_tasks.append(task["id"])
                        target_load += task.get("resource_required", 1)

                recovery_actions.append(
                    {
                        "action": "task_migration",
                        "from_node": failed_node_id,
                        "to_node": target_node_id,
                        "migrated_tasks": migrated_tasks,
                        "n_migrated": len(migrated_tasks),
                        "n_total": len(tasks),
                        "status": "completed" if migrated_tasks else "no_tasks_migrated",
                    }
                )

            fault_report = {
                "source_node": failed_node_id,
                "target_node": target_node_id,
                "migrated_tasks": migrated_tasks,
            }

        elif operation == "status":
            fault_report = {
                "node_status": dict(self.node_status),
                "n_healthy": sum(1 for v in self.node_status.values() if v == "healthy"),
                "n_failed": sum(1 for v in self.node_status.values() if v == "failed"),
                "n_suspected": sum(1 for v in self.node_status.values() if v == "suspected"),
            }

        # 计算系统可用性
        total = len(nodes) if nodes else max(len(self.node_status), 1)
        healthy = sum(1 for v in self.node_status.values() if v == "healthy")
        availability = healthy / max(total, 1)

        t_end = _time.perf_counter()
        handle_time = (t_end - t_start) * 1000

        return {
            "fault_report": fault_report,
            "recovery_actions": recovery_actions,
            "availability": round(availability, 4),
            "operation": operation,
            "handle_time_ms": round(handle_time, 3),
        }

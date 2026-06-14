"""边缘调度器模块。

边缘计算任务调度，实现负载均衡与资源分配，
优化边缘集群的计算效率。
"""

from __future__ import annotations

import logging
import time as _time
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EdgeScheduler:
    """边缘任务调度器。

    根据节点资源状态和任务需求，将计算任务分配到合适的边缘节点，
    实现负载均衡和资源优化。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.scheduling_policy = self.config.get("scheduling_policy", "greedy")
        self.max_load_threshold = self.config.get("max_load_threshold", 0.9)

    def schedule(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行边缘任务调度。

        Args:
            params: 调度参数字典，包含：
                - tasks: 待调度任务列表，每个任务包含\n
                    {"id": str, "cpu_required": float, "memory_required": float, "priority": int}。
                - nodes: 可用节点列表，每个节点包含\n
                    {"id": str, "cpu_capacity": float,
                     "memory_capacity": float, "current_load": float}。
                - scheduling_policy: 调度策略，\n
                    "greedy"/"round_robin"/"least_loaded"/"priority"，默认 "greedy"。

        Returns:
            调度结果字典，包含：
                - schedule: 任务分配方案。
                - resource_allocation: 资源分配详情。
                - utilization: 资源利用率。
        """
        np.random.seed(42)

        tasks = params.get("tasks", [])
        nodes = params.get("nodes", [])
        scheduling_policy = params.get("scheduling_policy", self.scheduling_policy)

        t_start = _time.perf_counter()

        if not tasks or not nodes:
            return {
                "schedule": {},
                "resource_allocation": {},
                "utilization": {"avg_cpu": 0.0, "avg_memory": 0.0},
            }

        # 初始化节点状态
        node_states = {}
        for node in nodes:
            nid = node["id"]
            node_states[nid] = {
                "cpu_capacity": node["cpu_capacity"],
                "memory_capacity": node["memory_capacity"],
                "cpu_used": node.get("current_load", 0.0) * node["cpu_capacity"],
                "memory_used": 0.0,
                "assigned_tasks": [],
            }

        schedule: dict[str, str] = {}
        resource_allocation: dict[str, list[dict[str, Any]]] = {}

        # 按优先级排序任务
        sorted_tasks = sorted(tasks, key=lambda t: t.get("priority", 0), reverse=True)

        # 节点轮转索引（用于 round_robin）
        node_ids = [n["id"] for n in nodes]
        rr_index = 0

        for task in sorted_tasks:
            task_id = task["id"]
            cpu_req = task.get("cpu_required", 1.0)
            mem_req = task.get("memory_required", 1.0)

            if scheduling_policy == "greedy":
                # 贪心：选择剩余资源最多的节点
                best_node = max(
                    node_ids,
                    # fmt: off
                    key=lambda nid: (
                        node_states[nid]["cpu_capacity"]
                        - node_states[nid]["cpu_used"]
                    ),
                    # fmt: on
                )
            elif scheduling_policy == "round_robin":
                # 轮转
                best_node = node_ids[rr_index % len(node_ids)]
                rr_index += 1
            elif scheduling_policy == "least_loaded":
                # 最少负载
                best_node = min(
                    node_ids,
                    # fmt: off
                    key=lambda nid: (
                        node_states[nid]["cpu_used"]
                        / max(node_states[nid]["cpu_capacity"], 1)
                    ),
                    # fmt: on
                )
            elif scheduling_policy == "priority":
                # 优先级匹配：高优先级任务分配给负载低的节点
                best_node = min(
                    node_ids,
                    key=lambda nid: node_states[nid]["cpu_used"],
                )
            else:
                best_node = node_ids[0]

            # 检查资源是否足够
            state = node_states[best_node]
            remaining_cpu = state["cpu_capacity"] - state["cpu_used"]
            remaining_mem = state["memory_capacity"] - state["memory_used"]

            if remaining_cpu >= cpu_req and remaining_mem >= mem_req:
                schedule[task_id] = best_node
                state["cpu_used"] += cpu_req
                state["memory_used"] += mem_req
                state["assigned_tasks"].append(task_id)

                if best_node not in resource_allocation:
                    resource_allocation[best_node] = []
                resource_allocation[best_node].append(
                    {
                        "task_id": task_id,
                        "cpu_allocated": cpu_req,
                        "memory_allocated": mem_req,
                    }
                )
            else:
                schedule[task_id] = "unassigned"

        # 计算资源利用率
        cpu_utils = []
        mem_utils = []
        for nid, state in node_states.items():
            cpu_util = state["cpu_used"] / max(state["cpu_capacity"], 1)
            mem_util = state["memory_used"] / max(state["memory_capacity"], 1)
            cpu_utils.append(cpu_util)
            mem_utils.append(mem_util)

        t_end = _time.perf_counter()
        schedule_time = (t_end - t_start) * 1000

        return {
            "schedule": schedule,
            "resource_allocation": resource_allocation,
            "utilization": {
                "avg_cpu": round(float(np.mean(cpu_utils)), 4),
                "avg_memory": round(float(np.mean(mem_utils)), 4),
                "max_cpu": round(float(np.max(cpu_utils)), 4),
                "max_memory": round(float(np.max(mem_utils)), 4),
                "n_assigned": sum(1 for v in schedule.values() if v != "unassigned"),
                "n_unassigned": sum(1 for v in schedule.values() if v == "unassigned"),
            },
            "scheduling_policy": scheduling_policy,
            "schedule_time_ms": round(schedule_time, 3),
        }

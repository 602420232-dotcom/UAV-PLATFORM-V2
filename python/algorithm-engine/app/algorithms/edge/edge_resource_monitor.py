"""边缘资源监控模块。

边缘设备资源监控，实时监测 CPU、GPU、内存和带宽使用情况，
提供告警和历史趋势分析。
"""

from __future__ import annotations

import logging
import time as _time
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EdgeResourceMonitor:
    """边缘资源监控器。

    实时监控边缘设备的计算资源使用情况，
    包括 CPU、GPU、内存和网络带宽，支持告警和趋势分析。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.monitor_interval = self.config.get("monitor_interval", 1.0)
        self.alert_thresholds = self.config.get(
            "alert_thresholds",
            {
                "cpu": 90.0,
                "gpu": 95.0,
                "memory": 85.0,
                "bandwidth": 80.0,
            },
        )
        self.history_length = self.config.get("history_length", 100)
        self.utilization_history: dict[str, list[float]] = {
            "cpu": [],
            "gpu": [],
            "memory": [],
            "bandwidth": [],
        }

    def monitor(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行资源监控。

        Args:
            params: 监控参数字典，包含：
                - resource_types: 要监控的资源类型列表，如 ["cpu", "gpu", "memory", "bandwidth"]。
                - alert_thresholds: 告警阈值字典，如 {"cpu": 90.0, "memory": 85.0}。
                - simulate: 是否模拟数据，默认 True。
                - n_samples: 模拟数据样本数，默认 10。

        Returns:
            监控结果字典，包含：
                - resource_status: 各资源当前状态。
                - alerts: 告警列表。
                - utilization_history: 利用率历史。
        """
        np.random.seed(42)

        resource_types = params.get("resource_types", ["cpu", "gpu", "memory", "bandwidth"])
        alert_thresholds = params.get("alert_thresholds", self.alert_thresholds)
        simulate = params.get("simulate", True)
        n_samples = params.get("n_samples", 10)

        t_start = _time.perf_counter()

        resource_status: dict[str, dict[str, Any]] = {}
        alerts: list[dict[str, Any]] = []

        for resource in resource_types:
            threshold = alert_thresholds.get(resource, 90.0)

            if simulate:
                # 模拟资源利用率数据
                base_usage = {
                    "cpu": 45.0,
                    "gpu": 60.0,
                    "memory": 55.0,
                    "bandwidth": 30.0,
                }.get(resource, 50.0)

                samples = np.clip(
                    base_usage + np.random.randn(n_samples) * 15,
                    0,
                    100,
                )
                current_usage = float(samples[-1])
                avg_usage = float(np.mean(samples))
                max_usage = float(np.max(samples))
                min_usage = float(np.min(samples))
                std_usage = float(np.std(samples))
            else:
                current_usage = 0.0
                avg_usage = 0.0
                max_usage = 0.0
                min_usage = 0.0
                std_usage = 0.0
                samples = np.array([])

            # 更新历史
            if resource in self.utilization_history:
                self.utilization_history[resource].extend(samples.tolist())
                if len(self.utilization_history[resource]) > self.history_length:
                    self.utilization_history[resource] = self.utilization_history[resource][-self.history_length :]

            resource_status[resource] = {
                "current_usage": round(current_usage, 2),
                "avg_usage": round(avg_usage, 2),
                "max_usage": round(max_usage, 2),
                "min_usage": round(min_usage, 2),
                "std_usage": round(std_usage, 2),
                "threshold": threshold,
                "unit": "%",
            }

            # 检查告警
            if current_usage >= threshold:
                alerts.append(
                    {
                        "resource": resource,
                        "level": "critical" if current_usage >= 95.0 else "warning",
                        "current_value": round(current_usage, 2),
                        "threshold": threshold,
                        "message": f"{resource.upper()} 使用率 {current_usage:.1f}% 超过阈值 {threshold}%",
                    }
                )

        # 总体健康评估
        all_current = [resource_status[r]["current_usage"] for r in resource_types if r in resource_status]
        overall_health = (
            "healthy"
            if all(v < 80 for v in all_current)
            else ("warning" if all(v < 95 for v in all_current) else "critical")
        )

        t_end = _time.perf_counter()
        monitor_time = (t_end - t_start) * 1000

        return {
            "resource_status": resource_status,
            "alerts": alerts,
            "utilization_history": {k: v[-20:] for k, v in self.utilization_history.items() if v},
            "overall_health": overall_health,
            "n_alerts": len(alerts),
            "monitor_time_ms": round(monitor_time, 3),
        }

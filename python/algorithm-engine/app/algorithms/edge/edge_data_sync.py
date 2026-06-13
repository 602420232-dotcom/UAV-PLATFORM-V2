"""边云数据同步模块。

边缘与云端数据同步，支持增量同步与冲突解决，
确保边云数据一致性。
"""

from __future__ import annotations

import hashlib
import logging
import time as _time
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EdgeDataSync:
    """边云数据同步器。

    管理边缘设备与云端之间的数据同步，
    支持增量同步、冲突检测与解决。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.sync_mode = self.config.get("sync_mode", "incremental")
        self.conflict_resolution = self.config.get("conflict_resolution", "timestamp")
        self.last_sync_timestamp = self.config.get("last_sync_timestamp", 0.0)

    def sync(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行边云数据同步。

        Args:
            params: 同步参数字典，包含：
                - edge_data: 边缘端数据，字典形式 {key: {"value": Any, "timestamp": float, "hash": str}}。
                - cloud_data: 云端数据，字典形式同上。
                - sync_mode: 同步模式，"full"/"incremental"，默认 "incremental"。
                - conflict_resolution: 冲突解决策略，\n
                    "timestamp"/"edge_wins"/"cloud_wins"/"merge"，默认 "timestamp"。

        Returns:
            同步结果字典，包含：
                - sync_result: 同步后的合并数据。
                - data_volume: 数据传输量（字节）。
                - latency: 同步延迟（毫秒）。
        """
        np.random.seed(42)

        edge_data = params.get("edge_data", {})
        cloud_data = params.get("cloud_data", {})
        sync_mode = params.get("sync_mode", self.sync_mode)
        conflict_resolution = params.get("conflict_resolution", self.conflict_resolution)

        t_start = _time.perf_counter()

        sync_result: dict[str, dict[str, Any]] = {}
        conflicts: list[dict[str, Any]] = []
        uploaded_keys: list[str] = []
        downloaded_keys: list[str] = []
        total_bytes = 0

        # 收集所有键
        all_keys = set(list(edge_data.keys()) + list(cloud_data.keys()))

        for key in all_keys:
            edge_entry = edge_data.get(key)
            cloud_entry = cloud_data.get(key)

            if edge_entry and not cloud_entry:
                # 仅边缘有：上传到云端
                sync_result[key] = {
                    "value": edge_entry["value"],
                    "source": "edge",
                    "timestamp": edge_entry.get("timestamp", 0.0),
                }
                uploaded_keys.append(key)
                total_bytes += len(str(edge_entry["value"]))

            elif cloud_entry and not edge_entry:
                # 仅云端有：下载到边缘
                sync_result[key] = {
                    "value": cloud_entry["value"],
                    "source": "cloud",
                    "timestamp": cloud_entry.get("timestamp", 0.0),
                }
                downloaded_keys.append(key)
                total_bytes += len(str(cloud_entry["value"]))

            else:
                # 两端都有：检查是否需要同步
                edge_ts = edge_entry.get("timestamp", 0.0)
                cloud_ts = cloud_entry.get("timestamp", 0.0)

                if sync_mode == "incremental":
                    if edge_ts > cloud_ts:
                        # 边缘更新：上传
                        sync_result[key] = {
                            "value": edge_entry["value"],
                            "source": "edge",
                            "timestamp": edge_ts,
                        }
                        uploaded_keys.append(key)
                        total_bytes += len(str(edge_entry["value"]))
                    elif cloud_ts > edge_ts:
                        # 云端更新：下载
                        sync_result[key] = {
                            "value": cloud_entry["value"],
                            "source": "cloud",
                            "timestamp": cloud_ts,
                        }
                        downloaded_keys.append(key)
                        total_bytes += len(str(cloud_entry["value"]))
                    else:
                        # 时间戳相同：无冲突
                        sync_result[key] = {
                            "value": edge_entry["value"],
                            "source": "both",
                            "timestamp": edge_ts,
                        }
                else:
                    # 全量同步：总是使用最新数据
                    if edge_ts >= cloud_ts:
                        sync_result[key] = {
                            "value": edge_entry["value"],
                            "source": "edge",
                            "timestamp": edge_ts,
                        }
                    else:
                        sync_result[key] = {
                            "value": cloud_entry["value"],
                            "source": "cloud",
                            "timestamp": cloud_ts,
                        }

                # 冲突检测
                edge_hash = edge_entry.get("hash", self._compute_hash(edge_entry["value"]))
                cloud_hash = cloud_entry.get("hash", self._compute_hash(cloud_entry["value"]))
                if edge_hash != cloud_hash and edge_ts == cloud_ts:
                    conflict = {
                        "key": key,
                        "edge_timestamp": edge_ts,
                        "cloud_timestamp": cloud_ts,
                        "resolution": conflict_resolution,
                    }
                    conflicts.append(conflict)

                    # 冲突解决
                    if conflict_resolution == "edge_wins":
                        sync_result[key]["value"] = edge_entry["value"]
                        sync_result[key]["source"] = "edge"
                    elif conflict_resolution == "cloud_wins":
                        sync_result[key]["value"] = cloud_entry["value"]
                        sync_result[key]["source"] = "cloud"
                    elif conflict_resolution == "merge":
                        sync_result[key]["value"] = {
                            "edge": edge_entry["value"],
                            "cloud": cloud_entry["value"],
                            "merged": True,
                        }
                        sync_result[key]["source"] = "merged"

        t_end = _time.perf_counter()
        latency = (t_end - t_start) * 1000

        return {
            "sync_result": sync_result,
            "data_volume": total_bytes,
            "latency": round(latency, 3),
            "sync_mode": sync_mode,
            "conflict_resolution": conflict_resolution,
            "n_uploaded": len(uploaded_keys),
            "n_downloaded": len(downloaded_keys),
            "n_conflicts": len(conflicts),
            "conflicts": conflicts,
            "uploaded_keys": uploaded_keys,
            "downloaded_keys": downloaded_keys,
        }

    @staticmethod
    def _compute_hash(value: Any) -> str:
        """计算值的哈希。"""
        value_str = str(value).encode("utf-8")
        return hashlib.md5(value_str).hexdigest()

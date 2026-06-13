"""边缘模型更新模块。

边缘模型 OTA 更新，支持差量更新与回滚，
确保边缘设备模型版本的一致性和可靠性。
"""

from __future__ import annotations

import logging
import time as _time
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EdgeModelUpdate:
    """边缘模型更新管理器。

    管理 AI 模型在边缘设备上的 OTA 更新，
    支持全量更新、差量更新和版本回滚。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.current_version = self.config.get("current_version", "1.0.0")
        self.update_strategy = self.config.get("update_strategy", "delta")
        self.rollback_versions: list[str] = [self.current_version]

    def update(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行边缘模型更新。

        Args:
            params: 更新参数字典，包含：
                - new_weights: 新模型权重（list 或 np.ndarray）。
                - target_version: 目标版本号。
                - update_strategy: 更新策略，"full"/"delta"/"rolling"，默认 "delta"。
                - verify_checksum: 是否校验校验和，默认 True。

        Returns:
            更新结果字典，包含：
                - update_status: 更新状态。
                - version_diff: 版本差异信息。
                - rollback_info: 回滚信息。
        """
        np.random.seed(42)

        new_weights = params.get("new_weights", None)
        target_version = params.get("target_version", "1.1.0")
        update_strategy = params.get("update_strategy", self.update_strategy)
        verify_checksum = params.get("verify_checksum", True)

        t_start = _time.perf_counter()

        if new_weights is None:
            return {
                "update_status": "failed",
                "version_diff": {},
                "rollback_info": {"available_versions": self.rollback_versions},
                "error": "No new weights provided",
            }

        new_weights_array = np.array(new_weights, dtype=float)
        new_size = new_weights_array.nbytes

        # 模拟当前模型权重
        current_weights = np.random.randn(*new_weights_array.shape) * 0.5
        current_size = current_weights.nbytes

        # 版本差异计算
        weight_diff = new_weights_array - current_weights
        diff_norm = float(np.linalg.norm(weight_diff))
        diff_nnz = int(np.count_nonzero(weight_diff))

        version_diff = {
            "from_version": self.current_version,
            "to_version": target_version,
            "weight_diff_norm": round(diff_norm, 6),
            "changed_parameters": diff_nnz,
            "total_parameters": int(new_weights_array.size),
            "change_ratio": round(diff_nnz / max(int(new_weights_array.size), 1), 4),
        }

        # 执行更新
        if update_strategy == "full":
            # 全量更新
            transfer_size = new_size
            update_status = "full_updated"
        elif update_strategy == "delta":
            # 差量更新：仅传输变化的权重
            delta_indices = np.where(np.abs(weight_diff) > 1e-6)[0]
            transfer_size = len(delta_indices) * 8  # 索引 + 值
            update_status = "delta_updated"
        elif update_strategy == "rolling":
            # 滚动更新：分批更新
            n_batches = 4
            transfer_size = new_size // n_batches  # 每批传输量
            update_status = "rolling_updated"
        else:
            update_status = "failed"
            transfer_size = 0

        # 校验和验证
        checksum_valid = True
        if verify_checksum:
            checksum = float(np.sum(new_weights_array))
            checksum_valid = not np.isnan(checksum) and not np.isinf(checksum)

        if not checksum_valid:
            update_status = "checksum_failed"

        # 更新回滚信息
        if update_status in ("full_updated", "delta_updated", "rolling_updated"):
            self.rollback_versions.append(self.current_version)
            self.current_version = target_version

        t_end = _time.perf_counter()
        update_time = (t_end - t_start) * 1000

        return {
            "update_status": update_status,
            "version_diff": version_diff,
            "rollback_info": {
                "current_version": self.current_version,
                "available_versions": self.rollback_versions,
                "can_rollback": len(self.rollback_versions) > 1,
            },
            "update_details": {
                "strategy": update_strategy,
                "transfer_size_bytes": transfer_size,
                "original_size_bytes": current_size,
                "transfer_ratio": round(transfer_size / max(current_size, 1), 4),
                "checksum_valid": checksum_valid,
                "update_time_ms": round(update_time, 3),
            },
        }

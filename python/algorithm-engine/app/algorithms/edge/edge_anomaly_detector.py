"""边缘异常检测器模块。

边缘设备运行异常检测，基于统计方法识别异常行为，
保障边缘计算系统的稳定运行。
"""

from __future__ import annotations

import logging
import time as _time
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EdgeAnomalyDetector:
    """边缘异常检测器。

    基于统计方法检测边缘设备的运行异常，
    包括 Z-score、IQR 和移动平均等检测方法。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.detection_method = self.config.get("detection_method", "zscore")
        self.zscore_threshold = self.config.get("zscore_threshold", 3.0)
        self.iqr_factor = self.config.get("iqr_factor", 1.5)
        self.window_size = self.config.get("window_size", 20)
        self.baseline_stats: dict[str, dict[str, float]] = {}

    def detect(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行异常检测。

        Args:
            params: 检测参数字典，包含：
                - metrics: 指标数据，字典形式 {"metric_name": {"values": list, "timestamps": list}}。
                - detection_method: 检测方法，"zscore"/"iqr"/"moving_average"/"ensemble"，默认 "zscore"。
                - zscore_threshold: Z-score 阈值，默认 3.0。
                - iqr_factor: IQR 倍数因子，默认 1.5。
                - window_size: 滑动窗口大小，默认 20。

        Returns:
            检测结果字典，包含：
                - anomalies: 检测到的异常列表。
                - anomaly_scores: 各数据点的异常分数。
                - normal_range: 正常范围。
        """
        np.random.seed(42)

        metrics = params.get("metrics", {})
        detection_method = params.get("detection_method", self.detection_method)
        zscore_threshold = params.get("zscore_threshold", self.zscore_threshold)
        iqr_factor = params.get("iqr_factor", self.iqr_factor)
        window_size = params.get("window_size", self.window_size)

        t_start = _time.perf_counter()

        all_anomalies: list[dict[str, Any]] = []
        all_scores: dict[str, list[float]] = {}
        normal_ranges: dict[str, dict[str, float]] = {}

        for metric_name, metric_data in metrics.items():
            values = np.array(metric_data.get("values", []), dtype=float)
            timestamps = metric_data.get("timestamps", list(range(len(values))))

            if len(values) < 3:
                continue

            scores = np.zeros(len(values))
            anomaly_indices = []

            if detection_method == "zscore":
                # Z-score 方法
                mean = float(np.mean(values))
                std = float(np.std(values))
                if std > 0:
                    z_scores = (values - mean) / std
                    scores = np.abs(z_scores)
                    anomaly_indices = np.where(scores > zscore_threshold)[0].tolist()
                normal_range = {
                    "lower": round(mean - zscore_threshold * std, 4),
                    "upper": round(mean + zscore_threshold * std, 4),
                    "mean": round(mean, 4),
                    "std": round(std, 4),
                }

            elif detection_method == "iqr":
                # IQR 方法
                q1 = float(np.percentile(values, 25))
                q3 = float(np.percentile(values, 75))
                iqr = q3 - q1
                lower_bound = q1 - iqr_factor * iqr
                upper_bound = q3 + iqr_factor * iqr

                for i, v in enumerate(values):
                    if v < lower_bound or v > upper_bound:
                        anomaly_indices.append(i)
                        # IQR 异常分数：偏离边界的程度
                        if v < lower_bound:
                            scores[i] = (lower_bound - v) / max(iqr, 1e-8)
                        else:
                            scores[i] = (v - upper_bound) / max(iqr, 1e-8)

                normal_range = {
                    "lower": round(lower_bound, 4),
                    "upper": round(upper_bound, 4),
                    "q1": round(q1, 4),
                    "q3": round(q3, 4),
                    "iqr": round(iqr, 4),
                }

            elif detection_method == "moving_average":
                # 滑动窗口移动平均方法
                if len(values) >= window_size:
                    window = np.ones(window_size) / window_size
                    moving_avg = np.convolve(values, window, mode="valid")
                    residuals = np.abs(values[window_size - 1 :] - moving_avg)
                    residual_std = float(np.std(residuals)) if len(residuals) > 1 else 1.0
                    if residual_std > 0:
                        scores[window_size - 1 :] = residuals / residual_std
                    anomaly_indices = np.where(scores > zscore_threshold)[0].tolist()

                mean = float(np.mean(values))
                std = float(np.std(values))
                normal_range = {
                    "lower": round(mean - 2 * std, 4),
                    "upper": round(mean + 2 * std, 4),
                    "mean": round(mean, 4),
                    "std": round(std, 4),
                    "window_size": window_size,
                }

            elif detection_method == "ensemble":
                # 集成方法：综合 Z-score 和 IQR
                mean = float(np.mean(values))
                std = float(np.std(values))
                q1 = float(np.percentile(values, 25))
                q3 = float(np.percentile(values, 75))
                iqr = q3 - q1

                z_scores = np.zeros(len(values))
                iqr_scores = np.zeros(len(values))

                if std > 0:
                    z_scores = np.abs((values - mean) / std)
                if iqr > 0:
                    lower_b = q1 - iqr_factor * iqr
                    upper_b = q3 + iqr_factor * iqr
                    for i, v in enumerate(values):
                        if v < lower_b:
                            iqr_scores[i] = (lower_b - v) / iqr
                        elif v > upper_b:
                            iqr_scores[i] = (v - upper_b) / iqr

                scores = 0.5 * z_scores + 0.5 * iqr_scores
                anomaly_indices = np.where(scores > zscore_threshold)[0].tolist()

                normal_range = {
                    "lower": round(mean - zscore_threshold * std, 4),
                    "upper": round(mean + zscore_threshold * std, 4),
                    "mean": round(mean, 4),
                    "std": round(std, 4),
                }

            else:
                mean = float(np.mean(values))
                std = float(np.std(values))
                normal_range = {
                    "lower": round(mean - 3 * std, 4),
                    "upper": round(mean + 3 * std, 4),
                }

            # 记录异常
            for idx in anomaly_indices:
                all_anomalies.append(
                    {
                        "metric": metric_name,
                        "index": int(idx),
                        "timestamp": timestamps[idx] if idx < len(timestamps) else None,
                        "value": round(float(values[idx]), 4),
                        "score": round(float(scores[idx]), 4),
                        "method": detection_method,
                    }
                )

            all_scores[metric_name] = scores.tolist()
            normal_ranges[metric_name] = normal_range

        t_end = _time.perf_counter()
        detect_time = (t_end - t_start) * 1000

        return {
            "anomalies": all_anomalies,
            "anomaly_scores": all_scores,
            "normal_range": normal_ranges,
            "detection_method": detection_method,
            "n_anomalies": len(all_anomalies),
            "n_metrics": len(metrics),
            "detect_time_ms": round(detect_time, 3),
        }

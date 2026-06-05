"""
性能指标模块
提供性能监控、指标计算等功能
"""

import logging
import numpy as np
import psutil
import os
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """
    性能指标收集器
    """

    def __init__(self):
        self.start_time = time.time()
        self.process = psutil.Process(os.getpid())
        self.metrics = {}

    def start(self):
        """开始计时"""
        self.start_time = time.time()

    def stop(self):
        """停止计时并收集指标"""
        elapsed_time = time.time() - self.start_time
        self.metrics['execution_time_seconds'] = elapsed_time

        try:
            memory_info = self.process.memory_info()
            self.metrics['memory_usage_mb'] = memory_info.rss / 1024 / 1024
            self.metrics['cpu_usage_percent'] = self.process.cpu_percent(interval=0.1)
        except Exception as e:
            logger.warning(f"获取系统指标失败: {e}")

        return self.metrics

    def get_metrics(self) -> Dict[str, Any]:
        """获取当前指标"""
        return self.metrics.copy()


class DataQualityMetrics:
    """
    数据质量指标计算
    """

    @staticmethod
    def calculate_mean(data: np.ndarray) -> float:
        """计算平均值"""
        return float(np.mean(data))

    @staticmethod
    def calculate_std(data: np.ndarray) -> float:
        """计算标准差"""
        return float(np.std(data))

    @staticmethod
    def calculate_min(data: np.ndarray) -> float:
        """计算最小值"""
        return float(np.min(data))

    @staticmethod
    def calculate_max(data: np.ndarray) -> float:
        """计算最大值"""
        return float(np.max(data))

    @staticmethod
    def calculate_range(data: np.ndarray) -> float:
        """计算值域"""
        return float(np.max(data) - np.min(data))

    @staticmethod
    def calculate_valid_ratio(data: np.ndarray) -> float:
        """计算有效值比例"""
        valid_count = np.sum(np.isfinite(data))
        return float(valid_count / data.size)

    @staticmethod
    def calculate_outlier_ratio(data: np.ndarray, threshold: float = 3.0) -> float:
        """计算异常值比例"""
        mean = np.mean(data)
        std = np.std(data)
        outliers = np.abs(data - mean) > threshold * std
        return float(np.sum(outliers) / data.size)

    @staticmethod
    def calculate_correlation(data1: np.ndarray, data2: np.ndarray) -> float:
        """计算相关系数"""
        if data1.shape != data2.shape:
            logger.error("数据形状不匹配")
            return 0.0

        return float(np.corrcoef(data1.flatten(), data2.flatten())[0, 1])

    @staticmethod
    def compute_all(data: np.ndarray, name: str = 'data') -> Dict[str, Any]:
        """计算所有质量指标"""
        return {
            f'{name}_mean': DataQualityMetrics.calculate_mean(data),
            f'{name}_std': DataQualityMetrics.calculate_std(data),
            f'{name}_min': DataQualityMetrics.calculate_min(data),
            f'{name}_max': DataQualityMetrics.calculate_max(data),
            f'{name}_range': DataQualityMetrics.calculate_range(data),
            f'{name}_valid_ratio': DataQualityMetrics.calculate_valid_ratio(data),
            f'{name}_outlier_ratio': DataQualityMetrics.calculate_outlier_ratio(data)
        }


class AssimilationMetrics:
    """
    同化结果指标计算
    """

    @staticmethod
    def calculate_analysis_improvement(background: np.ndarray, analysis: np.ndarray) -> float:
        """计算分析场改进度"""
        bg_std = np.std(background)
        analysis_std = np.std(analysis)

        if bg_std == 0:
            return 0.0

        return float((bg_std - analysis_std) / bg_std)

    @staticmethod
    def calculate_spread_reduction(background: np.ndarray, analysis: np.ndarray) -> float:
        """计算方差减少率"""
        bg_var = np.var(background)
        analysis_var = np.var(analysis)

        if bg_var == 0:
            return 0.0

        return float((bg_var - analysis_var) / bg_var)

    @staticmethod
    def calculate_observation_impact(observations: np.ndarray, analysis: np.ndarray,
                                     obs_locations: np.ndarray) -> float:
        """计算观测影响"""
        if len(observations) == 0:
            return 0.0

        # 简单计算：分析场与观测值的相关性
        obs_values = observations
        # 从分析场插值到观测位置
        from ..adapters.grid import grid_to_points
        analysis_at_obs = grid_to_points(analysis, obs_locations)

        if len(obs_values) != len(analysis_at_obs):
            return 0.0

        return float(np.corrcoef(obs_values, analysis_at_obs)[0, 1])

    @staticmethod
    def compute_all(background: np.ndarray, analysis: np.ndarray, variance: np.ndarray,
                    observations: Optional[np.ndarray] = None,
                    obs_locations: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """计算所有同化指标"""
        improvement = AssimilationMetrics.calculate_analysis_improvement(
            background, analysis)
        spread = AssimilationMetrics.calculate_spread_reduction(
            background, analysis)
        metrics = {
            'analysis_improvement': improvement,
            'spread_reduction': spread,
            'mean_analysis': float(np.mean(analysis)),
            'mean_variance': float(np.mean(variance)),
            'max_variance': float(np.max(variance)),
            'min_variance': float(np.min(variance))
        }

        if observations is not None and obs_locations is not None:
            metrics['observation_impact'] = AssimilationMetrics.calculate_observation_impact(
                observations, analysis, obs_locations
            )

        return metrics


def generate_performance_report(metrics: Dict[str, Any]) -> str:
    """生成性能报告字符串"""
    report = [
        "="*60,
        "性能监控报告",
        "="*60
    ]

    for key, value in metrics.items():
        if isinstance(value, float):
            report.append(f"{key}: {value:.2f}")
        else:
            report.append(f"{key}: {value}")

    report.append("="*60)
    return "\n".join(report)

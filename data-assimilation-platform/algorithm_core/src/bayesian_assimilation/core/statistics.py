"""
统计工具模块
提供协方差、相关系数等统计功能
"""

import logging
import numpy as np
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class CovarianceOperator:
    """
    协方差算子
    """

    @staticmethod
    def compute_covariance(data: np.ndarray) -> np.ndarray:
        """
        计算协方差矩阵

        Args:
            data: 数据矩阵 (n_samples, n_features)

        Returns:
            协方差矩阵
        """
        if data.ndim == 1:
            data = data.reshape(-1, 1)

        n_samples = data.shape[0]
        mean = np.mean(data, axis=0)
        centered = data - mean

        return np.dot(centered.T, centered) / (n_samples - 1)

    @staticmethod
    def compute_correlation(data: np.ndarray) -> np.ndarray:
        """
        计算相关系数矩阵

        Args:
            data: 数据矩阵 (n_samples, n_features)

        Returns:
            相关系数矩阵
        """
        cov = CovarianceOperator.compute_covariance(data)
        std = np.std(data, axis=0)

        # 避免除以零
        std[std == 0] = 1e-10

        return cov / np.outer(std, std)

    @staticmethod
    def gaussian_covariance(length_scale: float, grid_shape: tuple) -> np.ndarray:
        """
        生成高斯协方差矩阵

        Args:
            length_scale: 相关长度
            grid_shape: 网格形状

        Returns:
            协方差矩阵
        """
        nx, ny, nz = grid_shape
        n_points = nx * ny * nz

        # 创建坐标网格
        x = np.linspace(0, 1, nx)
        y = np.linspace(0, 1, ny)
        z = np.linspace(0, 1, nz)

        xx, yy, zz = np.meshgrid(x, y, z, indexing='ij')
        coords = np.vstack([xx.ravel(), yy.ravel(), zz.ravel()]).T

        # 计算距离矩阵
        distance = np.zeros((n_points, n_points))
        for i in range(n_points):
            for j in range(n_points):
                distance[i, j] = np.linalg.norm(coords[i] - coords[j])

        # 高斯协方差函数
        return np.exp(-distance**2 / (2 * length_scale**2))

    @staticmethod
    def localize_covariance(covariance: np.ndarray, localization_radius: float,
                           grid_shape: tuple) -> np.ndarray:
        """
        本地化协方差矩阵

        Args:
            covariance: 原始协方差矩阵
            localization_radius: 本地化半径
            grid_shape: 网格形状

        Returns:
            本地化后的协方差矩阵
        """
        nx, ny, nz = grid_shape
        n_points = nx * ny * nz

        # 创建坐标网格
        x = np.linspace(0, 1, nx)
        y = np.linspace(0, 1, ny)
        z = np.linspace(0, 1, nz)

        xx, yy, zz = np.meshgrid(x, y, z, indexing='ij')
        coords = np.vstack([xx.ravel(), yy.ravel(), zz.ravel()]).T

        # 计算本地化函数
        localization = np.ones((n_points, n_points))
        for i in range(n_points):
            for j in range(n_points):
                distance = np.linalg.norm(coords[i] - coords[j])
                if distance > localization_radius:
                    # 使用 Gaspari-Cohn 本地化函数
                    r = distance / localization_radius
                    if r <= 1:
                        localization[i, j] = ((-0.25 * r + 0.5) * r + 0.625) * r**2 - 0.875 * r + 1.0
                    elif r <= 2:
                        localization[i, j] = ((1/12 * r - 0.5) * r + 0.625) * r**2 + \
                                            (5/3 * r - 5.0) * r + 4.0/3
                    else:
                        localization[i, j] = 0.0

        return covariance * localization


class StatisticalMetrics:
    """
    统计指标计算
    """

    @staticmethod
    def mean(data: np.ndarray, axis: Optional[int] = None) -> float:
        """计算均值"""
        return float(np.mean(data, axis=axis))

    @staticmethod
    def variance(data: np.ndarray, axis: Optional[int] = None) -> float:
        """计算方差"""
        return float(np.var(data, axis=axis))

    @staticmethod
    def standard_deviation(data: np.ndarray, axis: Optional[int] = None) -> float:
        """计算标准差"""
        return float(np.std(data, axis=axis))

    @staticmethod
    def skewness(data: np.ndarray) -> float:
        """计算偏度"""
        mean = np.mean(data)
        std = np.std(data)

        if std == 0:
            return 0.0

        return float(np.mean(((data - mean) / std)**3))

    @staticmethod
    def kurtosis(data: np.ndarray) -> float:
        """计算峰度"""
        mean = np.mean(data)
        std = np.std(data)

        if std == 0:
            return 0.0

        return float(np.mean(((data - mean) / std)**4)) - 3

    @staticmethod
    def percentile(data: np.ndarray, q: float) -> float:
        """计算分位数"""
        return float(np.percentile(data, q))

    @staticmethod
    def median(data: np.ndarray) -> float:
        """计算中位数"""
        return float(np.median(data))

    @staticmethod
    def iqr(data: np.ndarray) -> float:
        """计算四分位距"""
        q25 = np.percentile(data, 25)
        q75 = np.percentile(data, 75)
        return float(q75 - q25)


class EnsembleStatistics:
    """
    集合统计工具
    """

    @staticmethod
    def ensemble_mean(ensemble: np.ndarray) -> np.ndarray:
        """计算集合均值"""
        return np.mean(ensemble, axis=0)

    @staticmethod
    def ensemble_spread(ensemble: np.ndarray) -> np.ndarray:
        """计算集合标准差"""
        return np.std(ensemble, axis=0)

    @staticmethod
    def ensemble_variance(ensemble: np.ndarray) -> np.ndarray:
        """计算集合方差"""
        return np.var(ensemble, axis=0)

    @staticmethod
    def ensemble_covariance(ensemble: np.ndarray) -> np.ndarray:
        """计算集合协方差矩阵"""
        n_members = ensemble.shape[0]
        mean = EnsembleStatistics.ensemble_mean(ensemble)

        # 将集合展平
        flat_ensemble = ensemble.reshape(n_members, -1)
        flat_mean = mean.flatten()

        centered = flat_ensemble - flat_mean
        return np.dot(centered.T, centered) / (n_members - 1)

    @staticmethod
    def rank_histogram(ensemble: np.ndarray, observations: np.ndarray) -> np.ndarray:
        """
        计算秩直方图

        Args:
            ensemble: 集合数据 (n_members, ...)
            observations: 观测数据

        Returns:
            秩直方图
        """
        n_members = ensemble.shape[0]
        ranks = np.zeros(len(observations))

        for i, obs in enumerate(observations):
            # 将观测值插入集合
            combined = np.concatenate([ensemble[:, i].ravel(), [obs]])
            ranks[i] = np.sum(combined < obs)

        # 计算直方图
        hist, _ = np.histogram(ranks, bins=n_members + 1, range=(-0.5, n_members + 0.5))
        return hist


def compute_statistics(data: np.ndarray) -> Dict[str, Any]:
    """
    计算数据的基本统计信息

    Args:
        data: 输入数据

    Returns:
        统计信息字典
    """
    return {
        'mean': StatisticalMetrics.mean(data),
        'variance': StatisticalMetrics.variance(data),
        'std': StatisticalMetrics.standard_deviation(data),
        'min': float(np.min(data)),
        'max': float(np.max(data)),
        'median': StatisticalMetrics.median(data),
        'skewness': StatisticalMetrics.skewness(data),
        'kurtosis': StatisticalMetrics.kurtosis(data),
        'iqr': StatisticalMetrics.iqr(data),
        'q10': StatisticalMetrics.percentile(data, 10),
        'q90': StatisticalMetrics.percentile(data, 90),
        'n_samples': int(data.size)
    }

"""
网格处理模块
提供网格插值、重采样等功能
"""

import logging
import numpy as np
from scipy import interpolate
from typing import Dict, Any, List, Tuple, Optional, Union

logger = logging.getLogger(__name__)


class GridAdapter:
    """
    网格适配器
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.default_method: str = self.config.get('interpolation_method', 'linear')

    def interpolate(self, data: np.ndarray, new_shape: Tuple[int, ...],
                   method: Optional[str] = None) -> np.ndarray:
        """
        插值数据到新网格

        Args:
            data: 原始数据
            new_shape: 新网格形状
            method: 插值方法 ('linear', 'nearest', 'cubic')

        Returns:
            插值后的数据
        """
        try:
            method = method or self.default_method
            method = method if method else 'linear'

            if data.ndim != len(new_shape):
                logger.error(f"数据维度 ({data.ndim}) 与目标形状维度 ({len(new_shape)}) 不匹配")
                return data

            if data.ndim == 3:
                return self._interpolate_3d(data, new_shape, method)
            elif data.ndim == 2:
                return self._interpolate_2d(data, new_shape, method)
            else:
                logger.error(f"不支持的维度: {data.ndim}")
                return data

        except Exception as e:
            logger.error(f"插值失败: {e}")
            return data

    def _interpolate_3d(self, data: np.ndarray, new_shape: Tuple[int, ...],
                        method: str) -> np.ndarray:
        """
        3D数据插值
        """
        nx, ny, nz = data.shape
        new_nx, new_ny, new_nz = new_shape[0], new_shape[1], new_shape[2]

        # 创建坐标
        x = np.linspace(0, 1, nx)
        y = np.linspace(0, 1, ny)
        z = np.linspace(0, 1, nz)

        new_x = np.linspace(0, 1, new_nx)
        new_y = np.linspace(0, 1, new_ny)
        new_z = np.linspace(0, 1, new_nz)

        # 创建插值器
        interp = interpolate.RegularGridInterpolator(
            (x, y, z), data, method=method, bounds_error=False, fill_value=0
        )

        # 创建新网格坐标
        new_coords = np.meshgrid(new_x, new_y, new_z, indexing='ij')
        new_points = np.vstack([coord.ravel() for coord in new_coords]).T

        # 插值
        result = interp(new_points).reshape(new_shape)
        return result

    def _interpolate_2d(self, data: np.ndarray, new_shape: Tuple[int, ...],
                        method: str) -> np.ndarray:
        """
        2D数据插值
        """
        nx, ny = data.shape
        new_nx, new_ny = new_shape[0], new_shape[1]

        # 创建坐标
        x = np.linspace(0, 1, nx)
        y = np.linspace(0, 1, ny)

        # 创建新网格坐标
        new_x = np.linspace(0, 1, new_nx)
        new_y = np.linspace(0, 1, new_ny)

        # 使用 RegularGridInterpolator 替代 interp2d（scipy 1.12+ 兼容性）
        interp = interpolate.RegularGridInterpolator(
            (x, y), data, method=method, bounds_error=False, fill_value=0
        )

        # 创建新网格坐标点
        new_coords = np.meshgrid(new_x, new_y, indexing='ij')
        new_points = np.vstack([coord.ravel() for coord in new_coords]).T

        # 插值
        result = interp(new_points).reshape(new_shape)
        return result

    def resample(self, data: np.ndarray, factor: float) -> np.ndarray:
        """
        重采样数据

        Args:
            data: 原始数据
            factor: 重采样因子

        Returns:
            重采样后的数据
        """
        try:
            new_shape = tuple(int(s * factor) for s in data.shape)
            return self.interpolate(data, new_shape)
        except Exception as e:
            logger.error(f"重采样失败: {e}")
            return data


def interpolate_data(data: np.ndarray, new_shape: Tuple[int, ...],
                    method: Optional[str] = 'linear') -> np.ndarray:
    """
    插值数据到新网格

    Args:
        data: 原始数据
        new_shape: 新网格形状
        method: 插值方法

    Returns:
        插值后的数据
    """
    adapter = GridAdapter()
    return adapter.interpolate(data, new_shape, method)


def resample_data(data: np.ndarray, factor: float) -> np.ndarray:
    """
    重采样数据

    Args:
        data: 原始数据
        factor: 重采样因子

    Returns:
        重采样后的数据
    """
    adapter = GridAdapter()
    return adapter.resample(data, factor)


def grid_to_points(grid_data: np.ndarray, points: np.ndarray) -> np.ndarray:
    """
    将网格数据插值到点

    Args:
        grid_data: 网格数据
        points: 点坐标 (N, 3)

    Returns:
        点上的数据值
    """
    try:
        if grid_data.ndim != 3:
            logger.error(f"网格数据必须是3D: {grid_data.ndim}")
            return np.zeros(len(points))

        nx, ny, nz = grid_data.shape

        # 创建坐标
        x = np.linspace(0, 1, nx)
        y = np.linspace(0, 1, ny)
        z = np.linspace(0, 1, nz)

        # 归一化点坐标
        normalized_points = points.copy()
        normalized_points[:, 0] = (points[:, 0] - points[:, 0].min()) / \
                               (points[:, 0].max() - points[:, 0].min() + 1e-10)
        normalized_points[:, 1] = (points[:, 1] - points[:, 1].min()) / \
                               (points[:, 1].max() - points[:, 1].min() + 1e-10)
        normalized_points[:, 2] = (points[:, 2] - points[:, 2].min()) / \
                               (points[:, 2].max() - points[:, 2].min() + 1e-10)

        # 创建插值器
        interp = interpolate.RegularGridInterpolator(
            (x, y, z), grid_data, method='linear', bounds_error=False, fill_value=0
        )

        # 插值
        result = interp(normalized_points)
        return result

    except Exception as e:
        logger.error(f"网格转点失败: {e}")
        return np.zeros(len(points))


def points_to_grid(points: np.ndarray, values: np.ndarray,
                  grid_shape: Tuple[int, int, int]) -> np.ndarray:
    """
    将点数据转换为网格

    Args:
        points: 点坐标 (N, 3)
        values: 点值 (N, )
        grid_shape: 网格形状

    Returns:
        网格数据
    """
    try:
        nx, ny, nz = grid_shape
        grid = np.zeros(grid_shape)

        # 归一化点坐标到网格索引
        x_indices = ((points[:, 0] - points[:, 0].min()) / \
                    (points[:, 0].max() - points[:, 0].min() + 1e-10) * (nx - 1)).astype(int)
        y_indices = ((points[:, 1] - points[:, 1].min()) / \
                    (points[:, 1].max() - points[:, 1].min() + 1e-10) * (ny - 1)).astype(int)
        z_indices = ((points[:, 2] - points[:, 2].min()) / \
                    (points[:, 2].max() - points[:, 2].min() + 1e-10) * (nz - 1)).astype(int)

        # 确保索引在有效范围内
        x_indices = np.clip(x_indices, 0, nx - 1)
        y_indices = np.clip(y_indices, 0, ny - 1)
        z_indices = np.clip(z_indices, 0, nz - 1)

        # 填充网格
        grid[x_indices, y_indices, z_indices] = values

        return grid

    except Exception as e:
        logger.error(f"点转网格失败: {e}")
        return np.zeros(grid_shape)

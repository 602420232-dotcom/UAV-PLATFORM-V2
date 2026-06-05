"""
观测算子模块
实现各种观测算子（H矩阵）的构建和操作
"""

import os
import sys

SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import numpy as np  # noqa: E402
from scipy.sparse import csr_matrix  # noqa: E402
from typing import Tuple  # noqa: E402
import logging  # noqa: E402

logger = logging.getLogger(__name__)


class ObservationOperator:
    """
    观测算子基类
    """

    def __init__(self, grid_shape: Tuple[int, int, int], resolution: float):
        self.grid_shape = grid_shape
        self.resolution = resolution
        self.nx, self.ny, self.nz = grid_shape

    def build(self, obs_locations: np.ndarray) -> csr_matrix:
        """
        构建观测算子矩阵

        Args:
            obs_locations: 观测位置数组 (n_obs, 3)

        Returns:
            H: 观测算子矩阵 (n_obs, n_grid)
        """
        raise NotImplementedError("子类必须实现 build 方法")

    def apply(self, state: np.ndarray, obs_locations: np.ndarray) -> np.ndarray:
        """
        应用观测算子

        Args:
            state: 状态向量
            obs_locations: 观测位置

        Returns:
            观测值预测
        """
        raise NotImplementedError("子类必须实现 apply 方法")


class NearestNeighborOperator(ObservationOperator):
    """
    最近邻观测算子
    将观测位置映射到最近的网格点
    """

    def build(self, obs_locations: np.ndarray) -> csr_matrix:
        """构建最近邻观测算子"""
        n_obs = len(obs_locations)
        n_total = self.nx * self.ny * self.nz

        rows = []
        cols = []
        vals = []

        for i, (x, y, z) in enumerate(obs_locations):
            ix = int(np.clip(x / self.resolution, 0, self.nx - 1))
            iy = int(np.clip(y / self.resolution, 0, self.ny - 1))
            iz = int(np.clip(z / self.resolution, 0, self.nz - 1))
            idx = ix * self.ny * self.nz + iy * self.nz + iz
            rows.append(i)
            cols.append(idx)
            vals.append(1.0)

        return csr_matrix((vals, (rows, cols)), shape=(n_obs, n_total))

    def apply(self, state: np.ndarray, obs_locations: np.ndarray) -> np.ndarray:
        """应用最近邻插值"""
        result = []
        state_3d = state.reshape(self.grid_shape)

        for x, y, z in obs_locations:
            ix = int(np.clip(x / self.resolution, 0, self.nx - 1))
            iy = int(np.clip(y / self.resolution, 0, self.ny - 1))
            iz = int(np.clip(z / self.resolution, 0, self.nz - 1))
            result.append(state_3d[ix, iy, iz])

        return np.array(result)


class BilinearOperator(ObservationOperator):
    """
    双线性插值观测算子
    使用双线性插值计算观测值
    """

    def build(self, obs_locations: np.ndarray) -> csr_matrix:
        """构建双线性观测算子"""
        n_obs = len(obs_locations)
        n_total = self.nx * self.ny * self.nz

        rows = []
        cols = []
        vals = []

        for i, (x, y, z) in enumerate(obs_locations):
            ix = int(np.clip(x / self.resolution, 0, self.nx - 2))
            iy = int(np.clip(y / self.resolution, 0, self.ny - 2))
            iz = int(np.clip(z / self.resolution, 0, self.nz - 2))

            dx = (x - ix * self.resolution) / self.resolution
            dy = (y - iy * self.resolution) / self.resolution
            dz = (z - iz * self.resolution) / self.resolution

            weights = [
                (1 - dx) * (1 - dy) * (1 - dz),
                dx * (1 - dy) * (1 - dz),
                (1 - dx) * dy * (1 - dz),
                dx * dy * (1 - dz),
                (1 - dx) * (1 - dy) * dz,
                dx * (1 - dy) * dz,
                (1 - dx) * dy * dz,
                dx * dy * dz
            ]

            offsets = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0),
                       (0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1)]

            for (di, dj, dk), w in zip(offsets, weights):
                if w > 1e-6:
                    idx = (ix + di) * self.ny * self.nz + (iy + dj) * self.nz + (iz + dk)
                    rows.append(i)
                    cols.append(idx)
                    vals.append(w)

        return csr_matrix((vals, (rows, cols)), shape=(n_obs, n_total))

    def apply(self, state: np.ndarray, obs_locations: np.ndarray) -> np.ndarray:
        """应用双线性插值"""
        result = []
        state_3d = state.reshape(self.grid_shape)

        for x, y, z in obs_locations:
            ix = int(np.clip(x / self.resolution, 0, self.nx - 2))
            iy = int(np.clip(y / self.resolution, 0, self.ny - 2))
            iz = int(np.clip(z / self.resolution, 0, self.nz - 2))

            dx = (x - ix * self.resolution) / self.resolution
            dy = (y - iy * self.resolution) / self.resolution
            dz = (z - iz * self.resolution) / self.resolution

            val = (
                state_3d[ix, iy, iz] * (1 - dx) * (1 - dy) * (1 - dz) +
                state_3d[ix + 1, iy, iz] * dx * (1 - dy) * (1 - dz) +
                state_3d[ix, iy + 1, iz] * (1 - dx) * dy * (1 - dz) +
                state_3d[ix + 1, iy + 1, iz] * dx * dy * (1 - dz) +
                state_3d[ix, iy, iz + 1] * (1 - dx) * (1 - dy) * dz +
                state_3d[ix + 1, iy, iz + 1] * dx * (1 - dy) * dz +
                state_3d[ix, iy + 1, iz + 1] * (1 - dx) * dy * dz +
                state_3d[ix + 1, iy + 1, iz + 1] * dx * dy * dz
            )
            result.append(val)

        return np.array(result)


class GaussianOperator(ObservationOperator):
    """
    高斯加权观测算子
    使用高斯核函数加权周围网格点
    """

    def __init__(self, grid_shape: Tuple[int, int, int], resolution: float, sigma: float = 50.0):
        super().__init__(grid_shape, resolution)
        self.sigma = sigma

    def build(self, obs_locations: np.ndarray) -> csr_matrix:
        """构建高斯加权观测算子"""
        n_obs = len(obs_locations)
        n_total = self.nx * self.ny * self.nz

        rows = []
        cols = []
        vals = []

        half_width = int(self.sigma / self.resolution) + 1

        for i, (x, y, z) in enumerate(obs_locations):
            ix_center = int(x / self.resolution)
            iy_center = int(y / self.resolution)
            iz_center = int(z / self.resolution)

            for di in range(-half_width, half_width + 1):
                for dj in range(-half_width, half_width + 1):
                    for dk in range(-half_width, half_width + 1):
                        ix = ix_center + di
                        iy = iy_center + dj
                        iz = iz_center + dk

                        if 0 <= ix < self.nx and 0 <= iy < self.ny and 0 <= iz < self.nz:
                            dist_sq = (di * self.resolution)**2 + \
                                (dj * self.resolution)**2 + \
                                (dk * self.resolution)**2
                            weight = np.exp(-dist_sq / (2 * self.sigma**2))

                            if weight > 1e-6:
                                idx = ix * self.ny * self.nz + \
                                    iy * self.nz + iz
                                rows.append(i)
                                cols.append(idx)
                                vals.append(weight)

        return csr_matrix((vals, (rows, cols)), shape=(n_obs, n_total))

    def apply(self, state: np.ndarray, obs_locations: np.ndarray) -> np.ndarray:
        """应用高斯加权"""
        result = []
        state_3d = state.reshape(self.grid_shape)
        half_width = int(self.sigma / self.resolution) + 1

        for x, y, z in obs_locations:
            ix_center = int(x / self.resolution)
            iy_center = int(y / self.resolution)
            iz_center = int(z / self.resolution)

            val = 0.0
            total_weight = 0.0

            for di in range(-half_width, half_width + 1):
                for dj in range(-half_width, half_width + 1):
                    for dk in range(-half_width, half_width + 1):
                        ix = ix_center + di
                        iy = iy_center + dj
                        iz = iz_center + dk

                        if 0 <= ix < self.nx and 0 <= iy < self.ny and 0 <= iz < self.nz:
                            dist_sq = (di * self.resolution)**2 + \
                                (dj * self.resolution)**2 + \
                                (dk * self.resolution)**2
                            weight = np.exp(-dist_sq / (2 * self.sigma**2))
                            val += state_3d[ix, iy, iz] * weight
                            total_weight += weight

            if total_weight > 0:
                val /= total_weight
            result.append(val)

        return np.array(result)


class OperatorFactory:
    """
    观测算子工厂类
    根据名称创建不同类型的观测算子
    """

    @staticmethod
    def create(
        operator_type: str,
        grid_shape: Tuple[int, int, int],
        resolution: float,
        **kwargs
    ) -> ObservationOperator:
        """
        创建观测算子

        Args:
            operator_type: 算子类型 ('nearest', 'bilinear', 'gaussian')
            grid_shape: 网格形状
            resolution: 分辨率
            **kwargs: 额外参数

        Returns:
            观测算子实例
        """
        operator_type = operator_type.lower()

        if operator_type == 'nearest':
            return NearestNeighborOperator(grid_shape, resolution)
        elif operator_type == 'bilinear':
            return BilinearOperator(grid_shape, resolution)
        elif operator_type == 'gaussian':
            sigma = kwargs.get('sigma', 50.0)
            return GaussianOperator(grid_shape, resolution, sigma)
        else:
            raise ValueError(f"未知的观测算子类型: {operator_type}")


# 便捷函数


def build_observation_operator(
    obs_locations: np.ndarray,
    grid_shape: Tuple[int, int, int],
    resolution: float,
    method: str = 'bilinear'


) -> csr_matrix:
    """
    构建观测算子矩阵

    Args:
        obs_locations: 观测位置
        grid_shape: 网格形状
        resolution: 分辨率
        method: 插值方法

    Returns:
        H: 观测算子矩阵
    """
    operator = OperatorFactory.create(method, grid_shape, resolution)
    return operator.build(obs_locations)


def apply_observation_operator(
    state: np.ndarray,
    obs_locations: np.ndarray,
    grid_shape: Tuple[int, int, int],
    resolution: float,
    method: str = 'bilinear'


) -> np.ndarray:
    """
    应用观测算子

    Args:
        state: 状态向量
        obs_locations: 观测位置
        grid_shape: 网格形状
        resolution: 分辨率
        method: 插值方法

    Returns:
        预测观测值
    """
    operator = OperatorFactory.create(method, grid_shape, resolution)
    return operator.apply(state, obs_locations)

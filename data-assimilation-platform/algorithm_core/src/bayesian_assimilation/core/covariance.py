"""
协方差计算模块
整合后的协方差实现
"""

import numpy as np
from scipy.sparse import csr_matrix
from typing import Tuple, Optional
import numba
from numba import jit, prange


class SparseBackgroundCovariance:
    """
    稀疏背景协方差（从文档1提取）
    """

    def __init__(self, grid_shape: Tuple[int, int, int], resolution: float,
                 error_scale: float = 1.5, correlation_length: float = 100.0):
        self.nx, self.ny, self.nz = grid_shape
        self.resolution = resolution
        self.error_scale = error_scale
        self.correlation_length = correlation_length
        self.variance = np.ones(np.prod(grid_shape)) * (error_scale ** 2)

    def apply(self, x: np.ndarray) -> np.ndarray:
        """应用协方差算子"""
        x_3d = x.reshape((self.nx, self.ny, self.nz))
        y_3d = np.zeros_like(x_3d)

        kernel_size = 3
        half_k = kernel_size // 2

        for i in range(self.nx):
            for j in range(self.ny):
                for k in range(self.nz):
                    weight_sum = 0
                    value_sum = 0

                    for di in range(-half_k, half_k + 1):
                        for dj in range(-half_k, half_k + 1):
                            for dk in range(-half_k, half_k + 1):
                                ni = i + di
                                nj = j + dj
                                nk = k + dk

                                if 0 <= ni < self.nx and 0 <= nj < self.ny and 0 <= nk < self.nz:
                                    distance = np.sqrt(
                                        (di*self.resolution)**2 +
                                        (dj*self.resolution)**2 +
                                        (dk*self.resolution)**2
                                    )
                                    weight = np.exp(-(distance / self.correlation_length)**2)

                                    value_sum += weight * x_3d[ni, nj, nk]
                                    weight_sum += weight

                    if weight_sum > 0:
                        y_3d[i, j, k] = value_sum / weight_sum

        y_flat = y_3d.flatten() * self.variance
        return y_flat

    def apply_inverse(self, x: np.ndarray, preconditioner: Optional[np.ndarray] = None) -> np.ndarray:
        """应用协方差逆的近似"""
        if preconditioner is None:
            preconditioner = 1.0 / (self.variance + 1e-6)
        return x * preconditioner


@jit(nopython=True, parallel=True, fastmath=True)
def numba_apply_covariance_3d(x_3d, variance, nx, ny, nz, alpha):
    """Numba加速的3D协方差应用（从文档2提取）"""
    y_3d = np.zeros_like(x_3d)

    for i in prange(nx):
        for j in range(ny):
            for k in range(nz):
                val = x_3d[i, j, k] * (1 - alpha)**3

                if i > 0:
                    val += x_3d[i-1, j, k] * alpha * (1 - alpha)**2
                if i < nx-1:
                    val += x_3d[i+1, j, k] * alpha * (1 - alpha)**2
                if j > 0:
                    val += x_3d[i, j-1, k] * alpha * (1 - alpha)**2
                if j < ny-1:
                    val += x_3d[i, j+1, k] * alpha * (1 - alpha)**2
                if k > 0:
                    val += x_3d[i, j, k-1] * alpha * (1 - alpha)**2
                if k < nz-1:
                    val += x_3d[i, j, k+1] * alpha * (1 - alpha)**2

                y_3d[i, j, k] = val

    y_flat = y_3d.reshape(-1) * variance
    return y_flat


class FastSparseBackgroundCovariance:
    """
    高性能稀疏背景协方差（从文档2、4提取）
    """

    def __init__(self, grid_shape, resolution, error_scale=1.0, correlation_length=50.0):
        self.nx, self.ny, self.nz = grid_shape
        self.resolution = resolution
        self.alpha = np.exp(-resolution / correlation_length)
        self.var_scale = error_scale**2
        self.variance = np.ones(np.prod(grid_shape)) * self.var_scale

    def apply(self, x):
        """应用协方差算子"""
        x_3d = x.reshape(self.nx, self.ny, self.nz)

        # 使用Numba加速
        y_flat = numba_apply_covariance_3d(
            x_3d, self.variance,
            self.nx, self.ny, self.nz,
            self.alpha
        )

        return y_flat

    def apply_inverse(self, x):
        """应用协方差逆的近似"""
        return x / (self.var_scale + 1e-6)

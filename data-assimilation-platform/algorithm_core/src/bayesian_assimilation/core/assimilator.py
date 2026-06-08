# algorithm_core/src/bayesian_assimilation/core/assimilator.py
# 贝叶斯同化核心实现

import os
import sys

SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import numpy as np  # noqa: E402
import logging  # noqa: E402
from typing import Optional, Tuple  # noqa: E402

from bayesian_assimilation.utils.config import AssimilationConfig, BaseConfig  # noqa: E402
from bayesian_assimilation.core.base import AssimilationBase  # noqa: E402

from scipy.interpolate import RegularGridInterpolator  # noqa: E402
from scipy.sparse import lil_matrix  # noqa: E402

logger = logging.getLogger(__name__)


class BayesianAssimilator(AssimilationBase):
    """
    贝叶斯同化器
    实现基础的贝叶斯数据同化算法
    """

    analysis_field: Optional[np.ndarray]
    variance_field: Optional[np.ndarray]

    def __init__(self, config: Optional[BaseConfig] = None) -> None:
        super().__init__(config)
        self.config = config or AssimilationConfig()
        self.analysis_field = None
        self.variance_field = None
        self.resolution: float = getattr(self.config, 'target_resolution', 50.0)

    def assimilate(self,
                   background: np.ndarray,
                   observations: np.ndarray,
                   obs_locations: np.ndarray,
                   obs_errors: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        执行贝叶斯同化

        Args:
            background: 背景场 (nx, ny, nz)
            observations: 观测数据 (n_obs, )
            obs_locations: 观测位置 (n_obs, 3)
            obs_errors: 观测误差 (n_obs, )

        Returns:
            analysis: 分析场 (nx, ny, nz)
            variance: 方差场 (nx, ny, nz)
        """
        return self.assimilate_3dvar(background, observations, obs_locations, obs_errors)

    def assimilate_3dvar(self,
                         background: np.ndarray,
                         observations: np.ndarray,
                         obs_locations: np.ndarray,
                         obs_errors: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        3DVAR同化（从文档3）- 优化版本

        Args:
            background: 背景场 (nx, ny, nz)
            observations: 观测值 (n_obs, )
            obs_locations: 观测位置 (n_obs, 3)
            obs_errors: 观测误差 (n_obs, )

        Returns:
            analysis: 分析场 (nx, ny, nz)
            variance: 方差场 (nx, ny, nz)
        """
        nx, ny, nz = background.shape
        n_total = nx * ny * nz  # noqa: F841

        xb = background.flatten()

        H = self._build_observation_operator_sparse(obs_locations, nx, ny, nz)
        n_obs = len(observations)

        if obs_errors is None:
            obs_errors = np.ones(n_obs) * self.config.observation_error_scale

        R_inv_diag = 1.0 / (obs_errors ** 2 + 1e-6)

        B_inv_diag = np.full_like(xb, 1.0 / (self.config.background_error_scale ** 2 + 1e-6))

        Hy = H @ xb
        residual = observations - Hy
        R_inv_residual = R_inv_diag * residual
        HTR_inv_residual = H.T @ R_inv_residual

        rhs = B_inv_diag * xb + HTR_inv_residual

        A_diag = B_inv_diag.copy()
        if hasattr(H, 'getrow'):
            for i in range(len(R_inv_diag)):
                row = H.getrow(i)  # type: ignore
                if row.nnz > 0:
                    col_idx = row.indices[0]
                    A_diag[col_idx] += R_inv_diag[i]
        else:
            for i in range(len(R_inv_diag)):
                row_data = H[i].toarray().flatten() if hasattr(H[i], 'toarray') else H[i]
                col_idx = np.argmax(row_data)
                A_diag[col_idx] += R_inv_diag[i]

        xa = rhs / A_diag

        variance = 1.0 / (A_diag + 1e-6)

        analysis = xa.reshape((nx, ny, nz))
        variance_field = variance.reshape((nx, ny, nz))

        self.analysis_field = analysis
        self.variance_field = variance_field
        self.grid_shape = (nx, ny, nz)

        return analysis, variance_field

    def _build_observation_operator_simple(self, obs_locations, nx, ny, nz):
        """简单观测算子(从文档3)"""
        n_obs = len(obs_locations)
        n_total = nx * ny * nz

        H = np.zeros((n_obs, n_total))

        for i, (ix, iy, iz) in enumerate(obs_locations):
            ix = int(np.clip(ix, 0, nx - 1))
            iy = int(np.clip(iy, 0, ny - 1))
            iz = int(np.clip(iz, 0, nz - 1))
            idx = ix * ny * nz + iy * nz + iz
            H[i, idx] = 1.0

        return H

    def _build_observation_operator_sparse(self, obs_locations, nx, ny, nz):  # type: ignore
        """稀疏观测算子(优化版本)"""
        n_obs = len(obs_locations)
        n_total = nx * ny * nz

        H = lil_matrix((n_obs, n_total))

        for i, (x, y, z) in enumerate(obs_locations):
            ix = int(np.clip(x / self.resolution, 0, nx - 1))
            iy = int(np.clip(y / self.resolution, 0, ny - 1))
            iz = int(np.clip(z / self.resolution, 0, nz - 1))
            idx = ix * ny * nz + iy * nz + iz
            H[i, idx] = 1.0

        return H.tocsr()

    def get_stats(self):
        """获取统计信息"""
        stats = {
            'grid_shape': self.grid_shape,
            'resolution': self.resolution,
            'analysis_mean': (
                np.mean(self.analysis_field) if self.analysis_field is not None
                else None
            ),
            'variance_mean': (
                np.mean(self.variance_field) if self.variance_field is not None
                else None
            )
        }
        return stats

    def interpolate_to_path_grid(
            self,
            target_resolution: float = 10.0,
            method: str = 'linear') -> np.ndarray:
        """
        将方差场插值到路径规划栅格

        Args:
            target_resolution: 目标分辨率（米）
            method: 插值方法，'linear'或'nearest'

        Returns:
            降尺度后的方差场
        """
        if self.variance_field is None:
            raise ValueError("先执行同化计算")

        nx, ny, nz = self.variance_field.shape

        x_src = np.arange(nx) * self.resolution
        y_src = np.arange(ny) * self.resolution
        z_src = np.arange(nz) * self.resolution

        nx_new = int(nx * self.resolution / target_resolution)
        ny_new = int(ny * self.resolution / target_resolution)
        nz_new = int(nz * self.resolution / target_resolution)

        x_dst = np.linspace(0, x_src[-1], nx_new)
        y_dst = np.linspace(0, y_src[-1], ny_new)
        z_dst = np.linspace(0, z_src[-1], nz_new)

        interpolator = RegularGridInterpolator(
            (x_src, y_src, z_src),
            self.variance_field,
            method=method,
            bounds_error=False,
            fill_value=np.nan
        )

        xx, yy, zz = np.meshgrid(x_dst, y_dst, z_dst, indexing='ij')
        points = np.stack([xx.ravel(), yy.ravel(), zz.ravel()], axis=-1)

        variance_interp = interpolator(points).reshape(xx.shape)

        if np.any(np.isnan(variance_interp)):
            logger.warning(f"插值结果包含 {np.sum(np.isnan(variance_interp))} 个NaN值，使用最近邻填充")

            nearest_interpolator = RegularGridInterpolator(
                (x_src, y_src, z_src),
                self.variance_field,
                method='nearest',
                bounds_error=False,
                fill_value=float(np.nanmean(self.variance_field))
            )

            nan_mask = np.isnan(variance_interp)
            variance_interp[nan_mask] = nearest_interpolator(
                points[np.any(np.isnan(points), axis=1)]
            )

        logger.info(f"方差场降尺度: {self.resolution}m → {target_resolution}m, "
                    f"新维度: {variance_interp.shape}, 方法: {method}")

        return variance_interp

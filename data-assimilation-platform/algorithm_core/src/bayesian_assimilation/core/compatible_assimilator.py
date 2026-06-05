"""
兼容性同化器（从文档4提取）
不爆内存、自动兼容、稳定运行的版本
"""

import os
import sys

SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import numpy as np
from scipy.sparse import diags, csr_matrix
from scipy.sparse.linalg import LinearOperator, cg
import logging
from typing import Optional, Tuple, List
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

logger = logging.getLogger(__name__)

from bayesian_assimilation.utils.config import CompatibleConfig
from bayesian_assimilation.core.base import AssimilationBase


class CompatibleAssimilator(AssimilationBase):
    """
    兼容性同化器（从文档4提取）
    保证稳定运行，不爆内存
    """

    def __init__(self, config: Optional[CompatibleConfig] = None):
        super().__init__(config or CompatibleConfig())
        self.resolution: float = 50.0
        self.grid_shape: Optional[Tuple[int, int, int]] = None

    def initialize_grid_safe(self, domain_size: Optional[Tuple[float, float, float]] = None):
        """安全初始化网格"""
        if domain_size is None:
            if hasattr(self.config, 'domain_size') and self.config.domain_size is not None:  # type: ignore
                domain_size = self.config.domain_size  # type: ignore
            else:
                domain_size = (1000.0, 1000.0, 100.0)

        if isinstance(domain_size, tuple) and len(domain_size) >= 3:
            x_len, y_len, z_len = domain_size[:3]
        else:
            x_len, y_len, z_len = 1000.0, 1000.0, 100.0

        max_points = 4_000_000
        vol = x_len * y_len * z_len
        self.resolution = float((vol / max_points) ** (1/3))

        min_res = 1.0
        max_res = 100.0
        if hasattr(self.config, 'min_resolution') and self.config.min_resolution is not None:  # type: ignore
            min_res = float(self.config.min_resolution)  # type: ignore
        if hasattr(self.config, 'max_resolution') and self.config.max_resolution is not None:  # type: ignore
            max_res = float(self.config.max_resolution)  # type: ignore

        self.resolution = float(np.clip(self.resolution, min_res, max_res))

        self.nx = int(x_len / self.resolution) + 1
        self.ny = int(y_len / self.resolution) + 1
        self.nz = int(z_len / self.resolution) + 1
        self.grid_shape = (self.nx, self.ny, self.nz)

        logger.info(f"安全网格: {self.nx}x{self.ny}x{self.nz} 分辨率={self.resolution:.1f}m")
        return self.grid_shape

    def assimilate_safe(self, bg, obs, obs_loc, obs_err=None):
        """安全同化"""
        if self.grid_shape is None:
            self.initialize_grid_safe()

        logger.info("开始安全同化 ...")
        return self._assimilate_cpu_safe(bg, obs, obs_loc, obs_err)

    def _assimilate_cpu_safe(self, bg, obs, obs_loc, obs_err):
        """CPU安全同化"""
        if self.grid_shape is None:
            self.initialize_grid_safe()
        assert self.grid_shape is not None, "grid_shape must be initialized before assimilation"
        if obs is None or obs_loc is None:
            logger.warning("观测数据或位置为 None，返回背景场")
            return bg, np.zeros_like(bg)

        if len(obs) == 0 or len(obs_loc) == 0:
            logger.warning("观测数据或位置为空，返回背景场")
            return bg, np.zeros_like(bg)

        nx, ny, nz = self.grid_shape
        n_total = nx * ny * nz
        xb = bg.ravel()

        H = self._build_obs_op_safe(obs_loc)

        bg_error_scale = 1.5
        corr_length = 50.0
        if hasattr(self.config, 'background_error_scale') and self.config.background_error_scale is not None:
            bg_error_scale = float(self.config.background_error_scale)
        if hasattr(self.config, 'correlation_length') and self.config.correlation_length is not None:
            corr_length = float(self.config.correlation_length)

        cov = FastSparseBackgroundCovariance(
            self.grid_shape, self.resolution,
            bg_error_scale,
            corr_length
        )

        def apply_inverse(x):
            return cov.apply_inverse(x)

        Binv = LinearOperator((n_total, n_total), matvec=apply_inverse)  # type: ignore

        obs_err_scale = 0.8
        if hasattr(self.config, 'observation_error_scale') and self.config.observation_error_scale is not None:
            obs_err_scale = float(self.config.observation_error_scale)

        if obs_err is None:
            obs_err = np.full(len(obs), obs_err_scale)

        Rinv_diag = 1.0 / (obs_err**2 + 1e-6)
        Rinv = diags(Rinv_diag)

        def hessian(x):
            return Binv.matvec(x) + H.T @ (Rinv @ (H @ x))

        b = Binv.matvec(xb) + H.T @ (Rinv @ obs)
        A = LinearOperator((n_total, n_total), matvec=hessian)  # type: ignore

        max_iter = 200
        cg_tol = 1e-5
        if hasattr(self.config, 'max_cg_iterations') and self.config.max_cg_iterations is not None:
            max_iter = int(self.config.max_cg_iterations)
        if hasattr(self.config, 'cg_tolerance') and self.config.cg_tolerance is not None:
            cg_tol = float(self.config.cg_tolerance)

        xa, _ = cg(A, b, x0=xb, maxiter=max_iter, atol=cg_tol)

        var = np.full(n_total, bg_error_scale**2)

        analysis = xa.reshape(nx, ny, nz)
        variance = var.reshape(nx, ny, nz)

        self.analysis_field = analysis
        self.variance_field = variance

        logger.info(f"安全同化完成，分析形状={analysis.shape}")
        return analysis, variance

    def _build_obs_op_safe(self, obs_loc):
        """安全观测算子"""
        if self.grid_shape is None:
            self.initialize_grid_safe()
        assert self.grid_shape is not None, "grid_shape must be initialized before building observation operator"
        if obs_loc is None or len(obs_loc) == 0:
            nx, ny, nz = self.grid_shape
            n_obs = 1
            return csr_matrix(([], ([], [])), shape=(n_obs, nx*ny*nz))

        nx, ny, nz = self.grid_shape
        rows, cols, vals = [], [], []

        for i, (x, y, z) in enumerate(obs_loc):
            ix = min(max(0, int(x/self.resolution)), nx-2)
            iy = min(max(0, int(y/self.resolution)), ny-2)
            iz = min(max(0, int(z/self.resolution)), nz-2)

            dx = (x - ix*self.resolution)/self.resolution
            dy = (y - iy*self.resolution)/self.resolution
            dz = (z - iz*self.resolution)/self.resolution

            w = [
                (1-dx)*(1-dy)*(1-dz), dx*(1-dy)*(1-dz),
                (1-dx)*dy*(1-dz), dx*dy*(1-dz),
                (1-dx)*(1-dy)*dz, dx*(1-dy)*dz,
                (1-dx)*dy*dz, dx*dy*dz
            ]

            for (di, dj, dk, ww) in [(0, 0, 0, w[0]), (1, 0, 0, w[1]),
                                  (0, 1, 0, w[2]), (1, 1, 0, w[3]),
                                  (0, 0, 1, w[4]), (1, 0, 1, w[5]),
                                  (0, 1, 1, w[6]), (1, 1, 1, w[7])]:
                if ww > 1e-6:
                    idx = (ix+di)*(ny*nz)+(iy+dj)*nz+(iz+dk)
                    rows.append(i)
                    cols.append(int(idx))
                    vals.append(ww)

        n_obs = len(obs_loc)
        return csr_matrix((vals, (rows, cols)), shape=(n_obs, nx*ny*nz))

    def assimilate_3dvar(self, background, observations, obs_locations, obs_errors=None):
        """3DVAR同化接口"""
        return self.assimilate_safe(background, observations, obs_locations, obs_errors)

    def assimilate(self, background, observations, obs_locations, obs_errors=None):
        """执行同化"""
        return self.assimilate_safe(background, observations, obs_locations, obs_errors)


class FastSparseBackgroundCovariance:
    """高性能稀疏背景协方差"""

    def __init__(self, grid_shape, resolution, error_scale=1.0, correlation_length=50.0):
        self.nx, self.ny, self.nz = grid_shape
        self.resolution = resolution
        self.alpha = np.exp(-resolution / correlation_length)
        self.var_scale = error_scale**2
        self.variance = np.ones(np.prod(grid_shape)) * self.var_scale

    def apply(self, x):
        """应用协方差算子"""
        x_3d = x.reshape(self.nx, self.ny, self.nz)
        y_3d = np.zeros_like(x_3d)

        alpha = self.alpha
        for i in range(self.nx):
            for j in range(self.ny):
                for k in range(self.nz):
                    val = x_3d[i, j, k] * (1 - alpha)**3

                    if i > 0:
                        val += x_3d[i-1, j, k] * alpha * (1 - alpha)**2
                    if i < self.nx-1:
                        val += x_3d[i+1, j, k] * alpha * (1 - alpha)**2
                    if j > 0:
                        val += x_3d[i, j-1, k] * alpha * (1 - alpha)**2
                    if j < self.ny-1:
                        val += x_3d[i, j+1, k] * alpha * (1 - alpha)**2
                    if k > 0:
                        val += x_3d[i, j, k-1] * alpha * (1 - alpha)**2
                    if k < self.nz-1:
                        val += x_3d[i, j, k+1] * alpha * (1 - alpha)**2

                    y_3d[i, j, k] = val

        return y_3d.reshape(-1) * self.variance

    def apply_inverse(self, x):
        """应用协方差逆的近似"""
        return x / (self.var_scale + 1e-6)

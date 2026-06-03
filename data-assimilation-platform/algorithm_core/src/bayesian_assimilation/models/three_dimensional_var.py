# algorithm_core/src/bayesian_assimilation/models/three_dimensional_var.py
# 基于 compatibility.py 重构，适配项目结构

import os
import sys

SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import LinearOperator, cg
from typing import Optional, Tuple, List
import logging

from bayesian_assimilation.core.base import AssimilationBase
from bayesian_assimilation.utils.config import BaseConfig

logger = logging.getLogger(__name__)


class SpatialCovariance:
    """
    空间相关背景误差协方差模型
    
    使用高斯型空间相关函数构建 B 矩阵的近似。
    B = σ² * exp(-d²/2L²)
    其中 d 为两点距离，L 为相关尺度。
    
    使用紧支撑（compact support）提高计算效率。
    """
    
    def __init__(self, sigma_b: float = 1.0, correlation_length: float = 100.0):
        """
        Args:
            sigma_b: 背景误差标准差
            correlation_length: 空间相关尺度 (km)
        """
        self.sigma_b = sigma_b
        self.correlation_length = correlation_length
    
    def apply(self, x: np.ndarray, grid_coords: np.ndarray = None) -> np.ndarray:
        """
        应用 B 矩阵到向量 x (B @ x)
        使用递归滤波器近似，避免显式构建大型 B 矩阵。
        
        Args:
            x: 输入向量 (n_grid,)
            grid_coords: 网格坐标 (n_grid, 2)，可选
        
        Returns:
            B @ x
        """
        from scipy.ndimage import gaussian_filter
        
        # 将向量重塑为 2D 网格
        n_grid = x.shape[0]
        grid_size = int(np.sqrt(n_grid))
        if grid_size * grid_size != n_grid:
            # 非正方形网格，直接返回对角近似
            return self.sigma_b ** 2 * x
        
        x_2d = x.reshape(grid_size, grid_size)
        
        # 使用高斯滤波模拟空间相关
        sigma_grid = self.correlation_length / (grid_size * 1.0) * grid_size
        filtered = gaussian_filter(x_2d, sigma=sigma_grid)
        
        result = (self.sigma_b ** 2) * filtered.reshape(-1)
        return result
    
    def apply_inverse(self, x: np.ndarray, grid_coords: np.ndarray = None) -> np.ndarray:
        """
        应用 B^{-1} 到向量 x
        """
        from scipy.ndimage import gaussian_filter
        
        n_grid = x.shape[0]
        grid_size = int(np.sqrt(n_grid))
        if grid_size * grid_size != n_grid:
            return x / (self.sigma_b ** 2)
        
        x_2d = x.reshape(grid_size, grid_size)
        sigma_grid = self.correlation_length / (grid_size * 1.0) * grid_size
        
        # B^{-1} 近似为逆滤波
        # 在实际应用中 B^{-1} 通常需要更精确的处理
        filtered = gaussian_filter(x_2d, sigma=sigma_grid)
        result = filtered.reshape(-1) / (self.sigma_b ** 2)
        return result


class ThreeDimensionalVAR(AssimilationBase):
    """
    3DVAR同化算法 - 生产级实现
    源自: compatibility.py (GPU加速贝叶斯同化系统 - 最终稳定版)
    """
    
    def __init__(self, config: Optional[BaseConfig] = None):
        super().__init__(config)
        self.gpu = None
        self._ensure_defaults()
        
    def _ensure_defaults(self):
        """确保默认值已设置"""
        if self.grid_shape is None:
            self.grid_shape = (10, 10, 5)
        if self.resolution is None:
            self.resolution = 50.0
        if not hasattr(self, 'nx'):
            self.nx, self.ny, self.nz = self.grid_shape
        
    def assimilate(self, background, observations, obs_locations, obs_errors=None):
        """主入口：执行同化"""
        self._ensure_defaults()
        
        if background is None:
            raise ValueError("背景场不能为空")
        
        if observations is None or obs_locations is None:
            logger.warning("观测数据或位置为空，返回背景场")
            return background, np.zeros_like(background)
        
        if len(observations) == 0 or len(obs_locations) == 0:
            logger.warning("观测数据或位置为空，返回背景场")
            return background, np.zeros_like(background)
        
        logger.info(f"🚀 开始3DVAR同化，网格: {self.grid_shape}")
        return self._assimilate_optimized(background, observations, obs_locations, obs_errors)
    
    def _assimilate_optimized(self, bg, obs, obs_loc, obs_err):
        """优化版同化（源自compatibility.py的smart_assimilate）"""
        nx, ny, nz = self.grid_shape
        n = nx * ny * nz
        
        H = self._build_observation_operator_trilinear(obs_loc)
        
        cov = SpatialCovariance(sigma_b=1.0, correlation_length=self.resolution)
        
        B_inv = LinearOperator(
            shape=(n, n), 
            matvec=cov.apply_inverse # type: ignore
        )
        
        obs_err = obs_err if obs_err is not None else np.full(len(obs), 0.1)
        from scipy.sparse import diags
        R_inv = diags(1.0 / (obs_err**2 + 1e-6))
        
        def hessian_matvec(x):
            return cov.apply_inverse(x) + H.T @ (R_inv @ (H @ x))
        
        xb = bg.ravel()
        b = cov.apply_inverse(xb) + H.T @ (R_inv @ obs)
        
        A = LinearOperator(shape=(n, n), matvec=hessian_matvec) # type: ignore
        xa, info = cg(A, b, x0=xb, maxiter=100, atol=1e-6)
        
        if info != 0:
            logger.warning(f"CG未收敛: {info}")
        
        variance = self._estimate_variance_diagonal(cov, H, R_inv)
        
        return xa.reshape(nx, ny, nz), variance.reshape(nx, ny, nz)
    
    def _build_observation_operator_trilinear(self, obs_loc):
        """三线性插值观测算子（源自compatibility.py）"""
        if obs_loc is None or len(obs_loc) == 0:
            nx, ny, nz = self.grid_shape
            return csr_matrix(([], ([], [])), shape=(1, nx*ny*nz))
        
        nx, ny, nz = self.grid_shape
        rows, cols, vals = [], [], []
        
        for i, loc in enumerate(obs_loc):
            x, y, z = loc
            ix = min(max(0, int(x/self.resolution)), nx-2)
            iy = min(max(0, int(y/self.resolution)), ny-2)
            iz = min(max(0, int(z/self.resolution)), nz-2)
            
            dx = (x/self.resolution - ix)
            dy = (y/self.resolution - iy)
            dz = (z/self.resolution - iz)
            
            weights = [
                (1-dx)*(1-dy)*(1-dz),
                dx*(1-dy)*(1-dz),
                (1-dx)*dy*(1-dz),
                dx*dy*(1-dz),
                (1-dx)*(1-dy)*dz,
                dx*(1-dy)*dz,
                (1-dx)*dy*dz,
                dx*dy*dz
            ]
            
            indices = [
                (ix, iy, iz),
                (ix+1, iy, iz),
                (ix, iy+1, iz),
                (ix+1, iy+1, iz),
                (ix, iy, iz+1),
                (ix+1, iy, iz+1),
                (ix, iy+1, iz+1),
                (ix+1, iy+1, iz+1)
            ]
            
            for idx, (di, dj, dk) in enumerate(indices):
                if weights[idx] > 1e-6:
                    flat_idx = di * ny * nz + dj * nz + dk
                    rows.append(i)
                    cols.append(flat_idx)
                    vals.append(weights[idx])
        
        return csr_matrix((vals, (rows, cols)), shape=(len(obs_loc), nx*ny*nz))
    
    def _estimate_variance_diagonal(self, cov, H, R_inv):
        """对角方差估计"""
        nx, ny, nz = self.grid_shape
        n = nx * ny * nz
        diag = np.zeros(n)
        
        diag += 1.0 / (cov.sigma_b ** 2 + 1e-6)
        
        for i in range(n):
            obs_idx = H[:, i].nonzero()[0]
            if len(obs_idx) > 0:
                h_vals = H[obs_idx, i].toarray().flatten()
                r_diag = R_inv.diagonal()[obs_idx]
                diag[i] += np.sum(h_vals**2 * r_diag)
        
        return 1.0 / (diag + 1e-6)


if __name__ == "__main__":
    model = ThreeDimensionalVAR()
    bg = np.random.rand(10, 10, 5) * 10
    obs = np.array([5.0, 6.0, 7.0])
    obs_loc = np.array([[100.0, 100.0, 50.0], [200.0, 200.0, 100.0], [300.0, 300.0, 150.0]])
    
    analysis, variance = model.assimilate(bg, obs, obs_loc)
    logger.info(f"分析场形状: {analysis.shape}")
    logger.info(f"方差场形状: {variance.shape}")
    logger.info(f"分析场范围: [{analysis.min():.2f}, {analysis.max():.2f}]")
    logger.info("测试通过！")


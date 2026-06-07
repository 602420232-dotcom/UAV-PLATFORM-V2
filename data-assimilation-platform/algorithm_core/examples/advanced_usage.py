"""
高级用法示例：优化版贝叶斯同化方差场计算模块
支持3DVAR和EnKF两种同化方案，针对大规模计算优化
与项目结构完全适配的版本
"""

import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.sparse import diags, csr_matrix
from scipy.sparse.linalg import LinearOperator, cg
from scipy import ndimage
from dataclasses import dataclass
from typing import Optional, Tuple, List
import logging
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

# 设置与项目一致的日志格式


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('assimilation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class AssimilationConfig:
    """同化配置参数"""
    method: str = "3DVAR"  # "3DVAR" 或 "EnKF"
    ensemble_size: int = 30  # EnKF集合成员数
    grid_resolution: float = 1.0  # 米，与路径规划栅格对齐
    update_interval: int = 300  # 秒，5分钟更新
    variance_threshold: float = 2.0  # 方差阈值，触发重规划

    # 误差协方差参数
    background_error_scale: float = 1.0  # 背景场误差尺度
    observation_error_scale: float = 0.5  # 观测误差尺度
    correlation_length: float = 100.0  # 空间相关尺度（米）

    # 优化参数
    use_sparse: bool = True  # 使用稀疏矩阵
    max_cg_iterations: int = 10000  # 共轭梯度最大迭代次数
    cg_tolerance: float = 1e-10  # 共轭梯度收敛容差

    # 输出设置
    output_dir: str = "results"  # 输出目录
    save_results: bool = True  # 是否保存结果


class SparseBackgroundCovariance:
    """
    稀疏背景误差协方差类
    使用递归滤波器或稀疏矩阵近似B矩阵，避免存储稠密矩阵
    """

    def __init__(self, grid_shape: Tuple[int, int, int], resolution: float,
                 error_scale: float = 1.5, correlation_length: float = 100.0):
        """
        初始化稀疏背景协方差

        Args:
            grid_shape: 网格形状 (nx, ny, nz)
            resolution: 网格分辨率（米）
            error_scale: 误差尺度
            correlation_length: 相关长度（米）
        """
        self.nx, self.ny, self.nz = grid_shape
        self.resolution = resolution
        self.error_scale = error_scale
        self.correlation_length = correlation_length

        # 计算相关半径（网格点数）
        self.correlation_radius = int(correlation_length / resolution)

        # 预计算相关权重
        self._compute_correlation_weights()

        # 对角线方差
        self.variance = np.ones(np.prod(grid_shape)) * (error_scale ** 2)

    def _compute_correlation_weights(self):
        """计算空间相关权重（高斯相关函数）"""
        # 使用指数衰减相关函数
        self.local_correlation = np.exp(-(self.resolution / self.correlation_length) ** 2)

    def apply(self, x: np.ndarray) -> np.ndarray:
        """
        应用背景误差协方差算子：y = B * x
        使用局部相关近似，避免显式存储矩阵

        Args:
            x: 输入向量

        Returns:
            y: 输出向量
        """
        # 重塑为三维数组
        x_3d = x.reshape((self.nx, self.ny, self.nz))
        y_3d = np.zeros_like(x_3d)

        # 应用局部相关（使用向量化优化）
        kernel_size = 3
        half_k = kernel_size // 2

        # 预计算距离权重
        distances = np.sqrt(
            np.arange(-half_k, half_k + 1)[:, None, None]**2 +
            np.arange(-half_k, half_k + 1)[None, :, None]**2 +
            np.arange(-half_k, half_k + 1)[None, None, :]**2
        ) * self.resolution

        weights = np.exp(-(distances / self.correlation_length) ** 2)
        weights = weights / np.sum(weights)  # 归一化

        # 使用卷积加速
        for i in range(half_k, self.nx - half_k):
            for j in range(half_k, self.ny - half_k):
                for k in range(half_k, self.nz - half_k):
                    # 提取局部块
                    local_block = x_3d[i-half_k:i+half_k+1, j-half_k:j+half_k+1, k-half_k:k+half_k+1]
                    y_3d[i, j, k] = np.sum(local_block * weights)

        # 添加方差缩放
        y_flat = y_3d.flatten() * self.variance
        return y_flat

    def apply_inverse(self, x: np.ndarray, preconditioner: Optional[np.ndarray] = None) -> np.ndarray:
        """
        应用背景误差协方差逆的近似：y ≈ B^{-1} * x
        使用对角矩阵近似逆
        """
        if preconditioner is None:
            preconditioner = 1.0 / (self.variance + 1e-6)

        return x * preconditioner

    def to_sparse_matrix(self) -> csr_matrix:
        """
        将协方差转换为稀疏矩阵（用于调试或小规模问题）
        注意：对于大网格，这会占用大量内存
        """
        n_total = self.nx * self.ny * self.nz
        data = []
        rows = []
        cols = []

        kernel_size = 3
        half_k = kernel_size // 2

        for idx in range(n_total):
            # 将一维索引转换为三维索引
            i = idx // (self.ny * self.nz)
            j = (idx // self.nz) % self.ny
            k = idx % self.nz

            for di in range(-half_k, half_k + 1):
                for dj in range(-half_k, half_k + 1):
                    for dk in range(-half_k, half_k + 1):
                        ni = i + di
                        nj = j + dj
                        nk = k + dk

                        if 0 <= ni < self.nx and 0 <= nj < self.ny and 0 <= nk < self.nz:
                            n_idx = ni * (self.ny * self.nz) + nj * self.nz + nk

                            # 计算距离和权重
                            distance = np.sqrt(
                                (di*self.resolution)**2 +
                                (dj*self.resolution)**2 +
                                (dk*self.resolution)**2
                            )
                            weight = np.exp(-(distance / self.correlation_length)**2)

                            data.append(weight * self.variance[idx])
                            rows.append(idx)
                            cols.append(n_idx)

        # 创建CSR稀疏矩阵
        B_sparse = csr_matrix((data, (rows, cols)), shape=(n_total, n_total))

        return B_sparse


class OptimizedBayesianAssimilation:
    """
    优化后的贝叶斯同化核心类
    针对大规模计算优化的实现
    """

    def __init__(self, config: Optional[AssimilationConfig] = None):
        self.config = config or AssimilationConfig()
        self.grid_shape = None
        self.background_covariance = None
        self.variance_field = None
        self.analysis_field = None

        # 性能统计
        self.stats = {
            'assimilation_time': 0.0,
            'cg_iterations': 0,
            'memory_usage_mb': 0.0
        }

    def initialize_grid(self, domain_size: Tuple[float, float, float],
                       resolution: Optional[float] = None):
        """
        初始化计算网格

        Args:
            domain_size: (x_len, y_len, z_len) 单位：米
            resolution: 栅格分辨率，默认使用config中的值
        """
        res = resolution or self.config.grid_resolution
        self.nx = int(domain_size[0] / res) + 1
        self.ny = int(domain_size[1] / res) + 1
        self.nz = int(domain_size[2] / res) + 1
        self.grid_shape = (self.nx, self.ny, self.nz)
        self.resolution = res

        # 网格坐标
        self.x_coords = np.linspace(0, domain_size[0], self.nx)
        self.y_coords = np.linspace(0, domain_size[1], self.ny)
        self.z_coords = np.linspace(0, domain_size[2], self.nz)

        logger.info(f"初始化网格: {self.nx}×{self.ny}×{self.nz}, "
                   f"分辨率: {res}m, 总网格点: {self.nx*self.ny*self.nz:,}")

        # 构建优化的背景误差协方差
        self._build_background_covariance_optimized()

    def _build_background_covariance_optimized(self):
        """构建优化的背景误差协方差（使用稀疏/隐式表示）"""
        logger.info("构建优化的背景误差协方差...")
        if self.grid_shape is None:
            raise RuntimeError("网格尚未初始化，请先调用 initialize_grid()")

        if self.config.use_sparse:
            # 使用稀疏协方差算子
            self.background_covariance = SparseBackgroundCovariance(
                grid_shape=self.grid_shape,
                resolution=self.resolution,
                error_scale=self.config.background_error_scale,
                correlation_length=self.config.correlation_length
            )
            logger.info(f"使用稀疏背景协方差，相关长度: {self.config.correlation_length}m")
        else:
            # 回退到对角矩阵（小规模问题）
            n_total = self.nx * self.ny * self.nz
            variance = np.ones(n_total) * (self.config.background_error_scale ** 2)
            self.background_covariance = diags(variance, format='csr')
            logger.info(f"使用对角背景协方差，维度: {n_total}×{n_total}")

    def _bilinear_interpolation_weights(self, x: float, y: float, z: float) -> Tuple[List[int], List[float]]:
        """
        计算三线性插值权重

        Args:
            x, y, z: 观测点坐标（网格坐标）

        Returns:
            indices: 邻近网格点的一维索引列表
            weights: 对应的权重列表
        """
        # 找到最近的网格点索引
        ix = np.searchsorted(self.x_coords, x) - 1
        iy = np.searchsorted(self.y_coords, y) - 1
        iz = np.searchsorted(self.z_coords, z) - 1

        # 确保在边界内
        ix = max(0, min(ix, self.nx - 2))
        iy = max(0, min(iy, self.ny - 2))
        iz = max(0, min(iz, self.nz - 2))

        # 计算插值权重
        dx = (x - self.x_coords[ix]) / (self.x_coords[ix+1] - self.x_coords[ix]) if ix < self.nx - 1 else 0.0
        dy = (y - self.y_coords[iy]) / (self.y_coords[iy+1] - self.y_coords[iy]) if iy < self.ny - 1 else 0.0
        dz = (z - self.z_coords[iz]) / (self.z_coords[iz+1] - self.z_coords[iz]) if iz < self.nz - 1 else 0.0

        # 八个顶点的权重
        weights: List[float] = [
            float((1-dx)*(1-dy)*(1-dz)),  # 000
            float(dx*(1-dy)*(1-dz)),  # 100
            float((1-dx)*dy*(1-dz)),  # 010
            float(dx*dy*(1-dz)),  # 110
            float((1-dx)*(1-dy)*dz),  # 001
            float(dx*(1-dy)*dz),  # 101
            float((1-dx)*dy*dz),  # 011
            float(dx*dy*dz)               # 111
        ]

        # 对应的网格点索引
        indices: List[int] = []
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    ni = ix + i
                    nj = iy + j
                    nk = iz + k
                    if ni < self.nx and nj < self.ny and nk < self.nz:
                        idx = ni * (self.ny * self.nz) + nj * self.nz + nk
                        indices.append(int(idx))
                    else:
                        indices.append(-1)  # 无效索引

        return indices, weights

    def _build_observation_operator_optimized(self, obs_locations: np.ndarray) -> csr_matrix:
        """
        构建优化的观测算子H（三线性插值）
        使用稀疏矩阵存储

        Args:
            obs_locations: 观测位置，形状 (n_obs, 3)，每行是(x, y, z)坐标

        Returns:
            H: 稀疏观测算子矩阵
        """
        n_obs = len(obs_locations)
        n_total = self.nx * self.ny * self.nz

        # 使用列表构建稀疏矩阵
        row_indices = []
        col_indices = []
        values = []

        for obs_idx, (x, y, z) in enumerate(obs_locations):
            # 计算插值权重
            indices, weights = self._bilinear_interpolation_weights(x, y, z)

            for idx, weight in zip(indices, weights):
                if idx != -1 and weight > 1e-6:  # 忽略极小权重和无效索引
                    row_indices.append(obs_idx)
                    col_indices.append(idx)
                    values.append(weight)

        # 创建稀疏CSR矩阵
        H = csr_matrix((values, (row_indices, col_indices)), shape=(n_obs, n_total))

        logger.info(f"构建观测算子: {n_obs}个观测点，稀疏度: {H.nnz/(n_obs*n_total)*100:.4f}%")

        return H

    def _apply_hessian(self, x: np.ndarray, B_inv,
                      H: csr_matrix, R_inv) -> np.ndarray:
        """
        计算Hessian矩阵应用：Hx = (B^{-1} + H^T R^{-1} H) x
        用于共轭梯度法
        """
        # 第一部分: B^{-1} x
        if isinstance(B_inv, LinearOperator):
            B_inv_x = B_inv.matvec(x)
        elif hasattr(B_inv, 'dot'):
            B_inv_x = B_inv.dot(x)
        else:
            B_inv_x = np.asarray(B_inv) @ x

        # 第二部分: H^T R^{-1} H x
        Hx = H.dot(x)
        R_inv_Hx = R_inv.dot(Hx)
        Ht_R_inv_Hx = H.T.dot(R_inv_Hx)

        return B_inv_x + Ht_R_inv_Hx

    def assimilate_3dvar_optimized(self,
                                 background_field: np.ndarray,
                                 observations: np.ndarray,
                                 obs_locations: np.ndarray,
                                 obs_errors: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        优化版3DVAR同化算法
        使用共轭梯度法求解，避免显式矩阵求逆
        """
        start_time = datetime.now()
        if self.grid_shape is None:
            raise RuntimeError("网格尚未初始化，请先调用 initialize_grid()")

        nx, ny, nz = self.grid_shape
        n_total = nx * ny * nz

        # 将背景场展平
        xb = background_field.flatten()

        # 构建观测算子
        H = self._build_observation_operator_optimized(obs_locations)
        n_obs = len(observations)

        # 构建观测误差协方差R
        if obs_errors is None:
            obs_errors = np.ones(n_obs) * self.config.observation_error_scale

        diags(obs_errors ** 2, format='csr')
        R_inv = diags(1.0 / (obs_errors ** 2 + 1e-6), format='csr')

        # 构建背景误差协方差逆的线性算子
        if self.background_covariance is None:
            raise RuntimeError("背景误差协方差未初始化")

        if isinstance(self.background_covariance, SparseBackgroundCovariance):
            bg_cov = self.background_covariance

            def matvec_B_inv(x: np.ndarray) -> np.ndarray:
                return bg_cov.apply_inverse(x)

            B_inv = LinearOperator(
                shape=(n_total, n_total),
                matvec=matvec_B_inv,  # type: ignore
                dtype=np.float64
            )
        elif hasattr(self.background_covariance, 'power'):
            B_inv = self.background_covariance.power(-1)
        else:
            raise TypeError(f"不支持的背景协方差类型: {type(self.background_covariance)}")

        # 构建右侧向量: b = B^{-1} xb + H^T R^{-1} y
        y = observations

        if isinstance(B_inv, LinearOperator):
            B_inv_xb = B_inv.matvec(xb)
        else:
            B_inv_xb = B_inv.dot(xb)

        R_inv_y = R_inv.dot(y)
        Ht_R_inv_y = H.T.dot(R_inv_y)
        b = B_inv_xb + Ht_R_inv_y

        # 定义Hessian矩阵的线性算子

        def hessian_matvec(x):
            return self._apply_hessian(x, B_inv, H, R_inv)

        A = LinearOperator(
            shape=(n_total, n_total),
            matvec=hessian_matvec,  # type: ignore
            dtype=np.float64
        )

        # 使用共轭梯度法求解线性系统: A xa = b
        logger.info("开始共轭梯度求解...")
        xa, info = cg(A, b, x0=xb,
                     maxiter=self.config.max_cg_iterations,
                     rtol=self.config.cg_tolerance)

        if info != 0:
            if info > 0:
                logger.warning(f"共轭梯度法在{info}次迭代后未收敛")
            else:
                logger.error(f"共轭梯度法出错，错误代码: {info}")

        # 计算分析场误差方差（近似）
        variance = self._estimate_analysis_variance(B_inv, H, R_inv)

        # 重塑为三维场
        analysis_field = xa.reshape((nx, ny, nz))
        variance_field = variance.reshape((nx, ny, nz))

        self.analysis_field = analysis_field
        self.variance_field = variance_field

        # 性能统计
        elapsed = (datetime.now() - start_time).total_seconds()
        self.stats['assimilation_time'] = elapsed
        self.stats['cg_iterations'] = info if info > 0 else self.config.max_cg_iterations

        logger.info(f"3DVAR同化完成，观测数: {n_obs}, "
                   f"CG迭代: {self.stats['cg_iterations']}, "
                   f"耗时: {elapsed:.2f}秒, "
                   f"平均方差: {np.mean(variance):.3f}")

        return analysis_field, variance_field

    def _estimate_analysis_variance(self, B_inv, H, R_inv) -> np.ndarray:
        """
        估计分析误差方差（近似）
        使用对角占优近似
        """
        n_total = B_inv.shape[0] if hasattr(B_inv, 'shape') else self.nx * self.ny * self.nz

        # 方法1: 使用对角占优近似
        diag_approx = np.zeros(n_total)

        # 背景项对角线
        if isinstance(self.background_covariance, SparseBackgroundCovariance):
            diag_approx += 1.0 / (self.background_covariance.variance + 1e-6)
        elif hasattr(B_inv, 'diagonal'):
            diag_approx += B_inv.diagonal()
        else:
            diag_approx += 1.0 / (self.config.background_error_scale ** 2 + 1e-6)

        # 观测项对角线: diag(H^T R^{-1} H)
        # 向量化计算
        for i in range(n_total):
            obs_indices = H[:, i].nonzero()[0]
            if len(obs_indices) > 0:
                H_values = H[obs_indices, i].toarray().flatten()
                R_diag_values = R_inv.diagonal()[obs_indices]
                diag_approx[i] += np.sum(H_values ** 2 * R_diag_values)

        # 方差 ≈ 1 / 对角线元素
        variance = 1.0 / (diag_approx + 1e-6)

        return variance

    def _gaspari_cohn(self, r: float, c: float) -> float:
        """Gaspari-Cohn局部化函数"""
        r_abs = abs(r) / c
        if r_abs <= 1:
            return 1 - 5/3*r_abs**2 + 5/8*r_abs**3 + 1/2*r_abs**4 - 1/4*r_abs**5
        elif r_abs <= 2:
            return 4 - 5*r_abs + 5/3*r_abs**2 + 5/8*r_abs**3 - 1/2*r_abs**4 + 1/12*r_abs**5 - 2/(3*r_abs)
        else:
            return 0

    def assimilate_enkf_localized(self,
                                ensemble_forecasts: List[np.ndarray],
                                observations: np.ndarray,
                                obs_locations: np.ndarray,
                                obs_errors: Optional[np.ndarray] = None,
                                localization_radius: float = 200.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        局部化集合卡尔曼滤波(EnKF)
        使用协方差局部化减少采样误差
        """
        start_time = datetime.now()
        if self.grid_shape is None:
            raise RuntimeError("网格尚未初始化，请先调用 initialize_grid()")

        nx, ny, nz = self.grid_shape
        N = len(ensemble_forecasts)  # 集合成员数

        # 集合矩阵 X_f: (n_grid, N)
        X_f = np.array([ens.flatten() for ens in ensemble_forecasts]).T
        n_grid = X_f.shape[0]

        # 集合均值
        x_mean = np.mean(X_f, axis=1, keepdims=True)

        # 集合扰动矩阵
        X_pert = X_f - x_mean

        # 构建观测算子
        H = self._build_observation_operator_optimized(obs_locations)
        n_obs = len(observations)

        # 观测误差协方差
        if obs_errors is None:
            obs_errors = np.ones(n_obs) * self.config.observation_error_scale
        R = np.diag(obs_errors ** 2)

        # 计算网格点和观测点的物理坐标
        grid_points = np.array(np.meshgrid(
            np.arange(nx),
            np.arange(ny),
            np.arange(nz),
            indexing='ij'
        )).reshape(3, -1).T

        grid_points_phys = grid_points * self.resolution
        obs_points_phys = obs_locations

        # 局部化矩阵 - 使用向量化计算
        logger.info("计算局部化权重...")

        # 计算所有网格点到所有观测点的距离
        distances = np.sqrt(
            np.sum((grid_points_phys[:, np.newaxis, :] - obs_points_phys[np.newaxis, :, :])**2, axis=2)
        )

        # 计算局部化权重
        localization_matrix = np.zeros((n_grid, n_obs))
        for i in range(n_grid):
            for j in range(n_obs):
                localization_matrix[i, j] = self._gaspari_cohn(distances[i, j], localization_radius)

        # 计算集合样本协方差
        Pf = (X_pert @ X_pert.T) / (N - 1)

        # 计算卡尔曼增益 (使用局部化)
        HPfH = H @ Pf @ H.T

        # 应用局部化到 HPfH
        HPfH_localized = np.zeros_like(HPfH)
        for i in range(n_obs):
            for j in range(n_obs):
                obs_distance = np.linalg.norm(obs_points_phys[i] - obs_points_phys[j])
                localization_ij = self._gaspari_cohn(float(obs_distance), localization_radius)
                HPfH_localized[i, j] = HPfH[i, j] * localization_ij

        # 计算逆矩阵
        inv_matrix = np.linalg.inv(HPfH_localized + R)

        # 计算 Pf H^T
        PfH = Pf @ H.T

        # 应用局部化到 PfH
        PfH_localized = PfH * localization_matrix

        # 计算卡尔曼增益
        K = PfH_localized @ inv_matrix

        # 更新每个集合成员
        X_a = np.zeros_like(X_f)

        for i in range(N):
            # 观测扰动
            obs_pert = np.random.normal(0, obs_errors)
            y_i = observations + obs_pert

            # 计算创新向量
            innovation = y_i - H @ X_f[:, i]

            # 分析场更新
            X_a[:, i] = X_f[:, i] + K @ innovation

        # 计算分析场统计
        analysis_mean = np.mean(X_a, axis=1).reshape((nx, ny, nz))
        variance_field = np.var(X_a, axis=1).reshape((nx, ny, nz))

        self.analysis_field = analysis_mean
        self.variance_field = variance_field

        # 性能统计
        elapsed = (datetime.now() - start_time).total_seconds()
        self.stats['assimilation_time'] = elapsed

        logger.info(f"局部化EnKF完成，集合大小: {N}, "
                   f"局部化半径: {localization_radius}m, "
                   f"耗时: {elapsed:.2f}秒, "
                   f"平均方差: {np.mean(variance_field):.3f}")

        return analysis_mean, variance_field

    def interpolate_to_path_grid(self,
                                target_resolution: float = 10.0,
                                method: str = 'linear') -> np.ndarray:
        """
        将方差场插值到路径规划栅格
        """
        if self.variance_field is None:
            raise ValueError("先执行同化计算")

        nx, ny, nz = self.variance_field.shape

        # 创建源网格坐标
        x_src = np.arange(nx) * self.resolution
        y_src = np.arange(ny) * self.resolution
        z_src = np.arange(nz) * self.resolution

        # 创建目标网格
        nx_new = int(nx * self.resolution / target_resolution)
        ny_new = int(ny * self.resolution / target_resolution)
        nz_new = int(nz * self.resolution / target_resolution)

        x_dst = np.linspace(0, x_src[-1], nx_new)
        y_dst = np.linspace(0, y_src[-1], ny_new)
        z_dst = np.linspace(0, z_src[-1], nz_new)

        # 使用RegularGridInterpolator进行三维插值
        interpolator = RegularGridInterpolator(
            (x_src, y_src, z_src),
            self.variance_field,
            method=method,
            bounds_error=False,
            fill_value=np.nan
        )

        # 生成目标网格点
        xx, yy, zz = np.meshgrid(x_dst, y_dst, z_dst, indexing='ij')
        points = np.stack([xx.ravel(), yy.ravel(), zz.ravel()], axis=-1)

        # 插值
        variance_interp = interpolator(points).reshape(xx.shape)

        # 处理边界外的点
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
            variance_interp[nan_mask] = nearest_interpolator(points[np.any(np.isnan(points), axis=1)])

        logger.info(f"方差场降尺度: {self.resolution}m → {target_resolution}m, "
                   f"新维度: {variance_interp.shape}, 方法: {method}")

        return variance_interp

    def detect_risk_mutation_optimized(self,
                                     previous_variance: np.ndarray,
                                     current_variance: np.ndarray,
                                     threshold_multiplier: float = 3.0,
                                     min_risk_area: int = 10) -> Tuple[np.ndarray, dict]:
        """
        优化版风险突变检测
        """
        # 确保形状一致
        assert previous_variance.shape == current_variance.shape, "方差场形状不一致"

        # 计算相对变化
        epsilon = 1e-6
        relative_change = np.abs(current_variance - previous_variance) / (previous_variance + epsilon)

        # 绝对阈值
        absolute_threshold = self.config.variance_threshold

        # 检测风险区域
        risk_mask = (relative_change > threshold_multiplier) | (current_variance > absolute_threshold)

        # 形态学操作：移除小区域
        if min_risk_area > 1:
            # 标记连通区域
            labeled_array, num_features = ndimage.label(risk_mask)  # type: ignore

            # 统计每个区域大小
            region_sizes = ndimage.sum(risk_mask, labeled_array, range(1, num_features + 1))

            # 创建掩码，只保留足够大的区域
            large_regions_mask = np.zeros_like(risk_mask, dtype=bool)
            for i, size in enumerate(region_sizes):
                if size >= min_risk_area:
                    large_regions_mask[labeled_array == (i + 1)] = True

            risk_mask = large_regions_mask

        # 计算风险统计
        n_risk_cells = np.sum(risk_mask)
        total_cells = risk_mask.size
        risk_percentage = n_risk_cells / total_cells * 100

        if n_risk_cells > 0:
            avg_risk_variance = np.mean(current_variance[risk_mask])
            max_risk_variance = np.max(current_variance[risk_mask])
        else:
            avg_risk_variance = 0
            max_risk_variance = 0

        risk_stats = {
            'n_risk_cells': int(n_risk_cells),
            'risk_percentage': float(risk_percentage),
            'avg_risk_variance': float(avg_risk_variance),
            'max_risk_variance': float(max_risk_variance),
            'total_cells': int(total_cells)
        }

        if n_risk_cells > 0:
            logger.info(f"风险统计: {n_risk_cells} 个栅格 ({risk_percentage:.1f}%), 平均方差: {avg_risk_variance:.3f}")
        else:
            logger.info("未检测到高风险区域")

        return risk_mask, risk_stats

    def export_variance_field(self,
                             filename: str = "variance_field.npy",
                             format: str = "numpy",
                             output_dir: Optional[str] = None) -> str:
        """
        导出方差场
        """
        if self.variance_field is None:
            raise ValueError("没有可导出的方差场数据")

        # 确定输出目录
        if output_dir is None:
            output_dir = self.config.output_dir

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 构建完整路径
        filepath = os.path.join(output_dir, filename)

        try:
            if format.lower() == "numpy":
                np.save(filepath, self.variance_field)
                logger.info(f"方差场已保存为NumPy文件: {filepath}")

            elif format.lower() == "text":
                np.savetxt(filepath, self.variance_field.flatten())
                logger.info(f"方差场已保存为文本文件: {filepath}")

            elif format.lower() == "binary":
                with open(filepath, 'wb') as f:
                    self.variance_field.tofile(f)
                logger.info(f"方差场已保存为二进制文件: {filepath}")

            else:
                logger.warning(f"不支持的文件格式: {format}，使用NumPy格式")
                np.save(filepath, self.variance_field)

            return filepath

        except Exception as e:
            logger.error(f"保存方差场失败: {e}")
            raise

    def get_performance_stats(self) -> dict:
        """获取性能统计"""
        if self.grid_shape is not None:
            n_total = np.prod(self.grid_shape)
            self.stats['grid_points'] = int(n_total)
            self.stats['grid_shape'] = self.grid_shape

        return self.stats.copy()


def demo_3dvar():
    """3DVAR演示"""
    logger.info("="*60)
    logger.info("3DVAR同化演示")
    logger.info("="*60)

    # 初始化同化系统
    config = AssimilationConfig(
        method="3DVAR",
        grid_resolution=50.0,
        background_error_scale=1.5,
        observation_error_scale=0.8,
        correlation_length=100.0,
        use_sparse=True,
        max_cg_iterations=500,
        cg_tolerance=1e-3,  # 适当放宽容差以平衡精度和速度
        output_dir="results/3dvar_demo"
    )

    assimilation = OptimizedBayesianAssimilation(config)

    # 初始化1000m×1000m×200m的空域，50m分辨率
    assimilation.initialize_grid((1000, 1000, 200), resolution=50)

    if assimilation.grid_shape is None:
        raise RuntimeError("网格未初始化")

    nx, ny, nz = assimilation.grid_shape
    logger.info(f"网格形状: ({nx}, {ny}, {nz})")

    # 创建有空间相关性的背景场
    x, y, z = np.meshgrid(
        np.linspace(0, 1000, nx),
        np.linspace(0, 1000, ny),
        np.linspace(0, 200, nz),
        indexing='ij'
    )

    # 模拟风场：基本风速 + 涡旋
    background = 5.0 + 2.0 * np.sin(2*np.pi*x/500) * np.cos(2*np.pi*y/500)
    logger.info(f"背景场范围: [{background.min():.2f}, {background.max():.2f}] m/s")

    # 模拟观测数据 (10个随机分布的气象站)
    np.random.seed(42)
    n_obs = 10
    observations = []
    obs_locations = []

    for i in range(n_obs):
        # 随机位置
        obs_x = np.random.uniform(0, 1000)
        obs_y = np.random.uniform(0, 1000)
        obs_z = np.random.uniform(0, 200)

        # 在真实值上添加观测误差
        true_value = 5.0 + 2.0 * np.sin(2*np.pi*obs_x/500) * np.cos(2*np.pi*obs_y/500)
        obs_value = true_value + np.random.normal(0, 0.5)

        observations.append(obs_value)
        obs_locations.append([obs_x, obs_y, obs_z])

    observations = np.array(observations)
    obs_locations = np.array(obs_locations)

    logger.info(f"生成 {n_obs} 个观测点")
    logger.info(f"观测值范围: [{observations.min():.2f}, {observations.max():.2f}] m/s")

    # 执行优化版3DVAR同化
    try:
        analysis, variance = assimilation.assimilate_3dvar_optimized(
            background, observations, obs_locations
        )

        logger.info(f"分析场范围: [{analysis.min():.2f}, {analysis.max():.2f}] m/s")
        logger.info(f"方差场范围: [{variance.min():.4f}, {variance.max():.4f}]")

        # 风险突变检测演示
        # 注意：演示中使用人为构造的previous_variance，实际业务中应使用历史方差场
        # 当前设置：previous比current高10%，用于模拟方差下降场景
        # 由于previous_variance > current_variance，大部分区域会触发"高风险"检测
        # 这是演示数据特性，实际业务中应使用真实的历史方差数据
        previous_variance = variance * 1.1  # 模拟历史较高的方差
        risk_mask, risk_stats = assimilation.detect_risk_mutation_optimized(
            previous_variance, variance,
            threshold_multiplier=2.0,
            min_risk_area=10
        )

        # 降尺度到10m分辨率
        variance_high_res = assimilation.interpolate_to_path_grid(target_resolution=10.0)
        logger.info(f"降尺度后方差场形状: {variance_high_res.shape}")

        # 导出数据
        if config.save_results:
            assimilation.export_variance_field(
                "variance_field_optimized.npy",
                format="numpy"
            )

        # 显示性能统计
        stats = assimilation.get_performance_stats()
        logger.info(f"性能统计: {stats}")

        return {
            'analysis': analysis,
            'variance': variance,
            'variance_high_res': variance_high_res,
            'risk_stats': risk_stats,
            'performance': stats
        }

    except Exception as e:
        logger.error(f"3DVAR同化过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def demo_enkf():
    """EnKF演示"""
    logger.info("\n" + "="*60)
    logger.info("EnKF同化演示")
    logger.info("="*60)

    # 初始化同化系统
    config = AssimilationConfig(
        method="EnKF",
        grid_resolution=50.0,
        background_error_scale=1.5,
        observation_error_scale=0.8,
        correlation_length=100.0,
        ensemble_size=20,
        output_dir="results/enkf_demo"
    )

    assimilation = OptimizedBayesianAssimilation(config)

    # 初始化网格
    assimilation.initialize_grid((1000, 1000, 200), resolution=50)

    if assimilation.grid_shape is None:
        raise RuntimeError("网格未初始化")

    nx, ny, nz = assimilation.grid_shape

    # 创建背景场
    x, y, z = np.meshgrid(
        np.linspace(0, 1000, nx),
        np.linspace(0, 1000, ny),
        np.linspace(0, 200, nz),
        indexing='ij'
    )

    background = 5.0 + 2.0 * np.sin(2*np.pi*x/500) * np.cos(2*np.pi*y/500)

    # 模拟观测数据
    np.random.seed(42)
    n_obs = 10
    observations = []
    obs_locations = []

    for i in range(n_obs):
        obs_x = np.random.uniform(0, 1000)
        obs_y = np.random.uniform(0, 1000)
        obs_z = np.random.uniform(0, 200)

        true_value = 5.0 + 2.0 * np.sin(2*np.pi*obs_x/500) * np.cos(2*np.pi*obs_y/500)
        obs_value = true_value + np.random.normal(0, 0.5)

        observations.append(obs_value)
        obs_locations.append([obs_x, obs_y, obs_z])

    observations = np.array(observations)
    obs_locations = np.array(obs_locations)

    # 生成集合预报
    ensemble_size = 20
    ensemble_forecasts = []

    for i in range(ensemble_size):
        perturbation = np.random.normal(0, 0.5, (nx, ny, nz))
        member = background + perturbation
        ensemble_forecasts.append(member)

    # 执行局部化EnKF
    try:
        analysis_enkf, variance_enkf = assimilation.assimilate_enkf_localized(
            ensemble_forecasts, observations, obs_locations,
            localization_radius=150.0
        )

        logger.info(f"EnKF分析场范围: [{analysis_enkf.min():.2f}, {analysis_enkf.max():.2f}] m/s")
        logger.info(f"EnKF方差场范围: [{variance_enkf.min():.4f}, {variance_enkf.max():.4f}]")

        # 导出数据
        if config.save_results:
            assimilation.export_variance_field(
                "variance_field_enkf.npy",
                format="numpy"
            )

        return {
            'analysis': analysis_enkf,
            'variance': variance_enkf
        }

    except Exception as e:
        logger.error(f"EnKF同化过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    logger.info("贝叶斯同化系统 - 高级用法演示")
    logger.info("="*60)

    # 运行3DVAR演示
    result_3dvar = demo_3dvar()

    # 运行EnKF演示
    result_enkf = demo_enkf()

    logger.info("\n" + "="*60)
    logger.info("演示完成！")

    return {
        '3dvar': result_3dvar,
        'enkf': result_enkf
    }


if __name__ == "__main__":
    # 运行演示
    results = main()

    # 保存结果摘要
    if results['3dvar'] or results['enkf']:
        summary = {
            'timestamp': datetime.now().isoformat(),
            '3dvar_completed': results['3dvar'] is not None,
            'enkf_completed': results['enkf'] is not None,
        }

        if results['3dvar']:
            summary['3dvar_stats'] = results['3dvar'].get('performance', {})

        import json
        with open('results/demo_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info("结果摘要已保存: results/demo_summary.json")

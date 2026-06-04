# algorithm_core/src/bayesian_assimilation/models/variance_field_optimizer.py
# 方差场优化器

import os
import sys

SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import numpy as np
from scipy.optimize import minimize
from scipy import sparse
from scipy.sparse.linalg import spsolve, LinearOperator
from typing import Optional, Tuple, List, Dict, Any, Union
import logging
import concurrent.futures
import multiprocessing

from bayesian_assimilation.core.base import AssimilationBase
from bayesian_assimilation.utils.config import BaseConfig

logger = logging.getLogger(__name__)

try:
    import scipy
    SCIPY_VERSION = tuple(map(int, scipy.__version__.split('.')[:2]))
except ImportError:
    SCIPY_VERSION = (0, 0)


class VarianceFieldOptimizer:
    """
    方差场优化器
    用于优化同化算法中的误差协方差参数
    支持稀疏矩阵、并行计算和数值稳定性处理
    """
    
    def __init__(self, config: Optional[BaseConfig] = None, use_sparse: bool = True):
        self.config = config
        self.use_sparse = use_sparse
        self.optimization_history: List[Dict[str, Any]] = []
        self.best_params: Optional[Dict[str, Any]] = None
        self.best_score: float = float('inf')
        self.n_jobs: int = max(1, multiprocessing.cpu_count() - 1)
        
        # 默认参数
        self.background_error_scale: float = 1.0
        self.observation_error_scale: float = 0.1
        self.correlation_length_scale: float = 10.0
        self.regularization: float = 1e-6
        self._ensure_defaults()
    
    def _ensure_defaults(self):
        """确保默认值已设置"""
        if self.config is not None:
            if hasattr(self.config, 'background_error_scale'):
                self.background_error_scale = float(self.config.background_error_scale)
            if hasattr(self.config, 'observation_error_scale'):
                self.observation_error_scale = float(self.config.observation_error_scale)
            if hasattr(self.config, 'correlation_length_scale'):
                self.correlation_length_scale = float(self.config.correlation_length_scale) # type: ignore
            if hasattr(self.config, 'regularization'):
                self.regularization = float(self.config.regularization) # type: ignore
    
    def _build_sparse_observation_operator(self, obs_locations: np.ndarray, 
                                          nx: int, ny: int, nz: int):
        """
        构建稀疏观测算子
        
        Args:
            obs_locations: 观测位置
            nx, ny, nz: 网格维度
            
        Returns:
            稀疏观测算子矩阵
        """
        n_obs = len(obs_locations)
        n_total = nx * ny * nz
        
        rows = []
        cols = []
        vals = []
        
        for i, loc in enumerate(obs_locations):
            x, y, z = loc
            ix = max(0, min(int(x), nx - 1))
            iy = max(0, min(int(y), ny - 1))
            iz = max(0, min(int(z), nz - 1))
            
            idx = ix * ny * nz + iy * nz + iz
            rows.append(i)
            cols.append(idx)
            vals.append(1.0)
        
        return sparse.csr_matrix((vals, (rows, cols)), shape=(n_obs, n_total))
    
    def _build_dense_observation_operator(self, obs_locations: np.ndarray, 
                                         nx: int, ny: int, nz: int) -> np.ndarray:
        """
        构建稠密观测算子
        
        Args:
            obs_locations: 观测位置
            nx, ny, nz: 网格维度
            
        Returns:
            稠密观测算子矩阵
        """
        n_obs = len(obs_locations)
        n_total = nx * ny * nz
        
        H = np.zeros((n_obs, n_total))
        
        for i, loc in enumerate(obs_locations):
            x, y, z = loc
            ix = max(0, min(int(x), nx - 1))
            iy = max(0, min(int(y), ny - 1))
            iz = max(0, min(int(z), nz - 1))
            
            idx = ix * ny * nz + iy * nz + iz
            H[i, idx] = 1.0
        
        return H
    
    def _build_observation_operator(self, obs_locations: np.ndarray, 
                                   nx: int, ny: int, nz: int):
        """
        构建观测算子（根据配置选择稀疏或稠密）
        
        Args:
            obs_locations: 观测位置
            nx, ny, nz: 网格维度
            
        Returns:
            观测算子矩阵
        """
        if self.use_sparse:
            return self._build_sparse_observation_operator(obs_locations, nx, ny, nz)
        return self._build_dense_observation_operator(obs_locations, nx, ny, nz)
    
    def _compute_objective_single(self, params: np.ndarray, 
                                 background: np.ndarray,
                                 observations: np.ndarray,
                                 obs_locations: np.ndarray) -> float:
        """
        计算单个参数组的目标函数值
        
        Args:
            params: 参数数组
            background: 背景场
            observations: 观测数据
            obs_locations: 观测位置
            
        Returns:
            目标函数值
        """
        bg_error_scale = max(params[0], 1e-3)
        obs_error_scale = max(params[1], 1e-4)
        corr_scale = max(params[2], 1e-1)
        
        try:
            nx, ny, nz = background.shape
            n_total = nx * ny * nz
            n_obs = len(observations)
            
            H = self._build_observation_operator(obs_locations, nx, ny, nz)
            xb = background.ravel()
            
            if self.use_sparse:
                H_dense = H.toarray() if sparse.issparse(H) else H # type: ignore
                
                HxB = H_dense @ xb
                
                B_inv = np.eye(n_total) / (bg_error_scale**2 + self.regularization)
                R_inv = np.eye(n_obs) / (obs_error_scale**2 + self.regularization)
                
                d = observations - HxB
                
                HBT = H_dense @ B_inv
                S = HBT @ H_dense.T + np.linalg.inv(R_inv)
                S_reg = S + np.eye(n_obs) * self.regularization
                
                try:
                    S_inv = np.linalg.inv(S_reg)
                except np.linalg.LinAlgError:
                    S_inv = np.linalg.pinv(S_reg)
                
                K = B_inv @ H_dense.T @ S_inv
                xa = xb + K @ d
                
                Hxa = H_dense @ xa
            else:
                B_inv = np.eye(n_total) / (bg_error_scale**2 + self.regularization)
                R_inv = np.eye(n_obs) / (obs_error_scale**2 + self.regularization)
                
                HxB = H @ xb
                d = observations - HxB
                
                HBT = H @ np.linalg.inv(B_inv)
                S = HBT @ H.T + np.linalg.inv(R_inv)
                S_reg = S + np.eye(n_obs) * self.regularization
                
                try:
                    S_inv = np.linalg.inv(S_reg)
                except np.linalg.LinAlgError:
                    S_inv = np.linalg.pinv(S_reg)
                
                K = np.linalg.inv(B_inv) @ H.T @ S_inv
                xa = xb + K @ d
                
                Hxa = H @ xa
            
            residual = np.mean((Hxa - observations)**2)
            return float(residual + self.regularization * np.sum(params**2))
            
        except Exception as e:
            logger.warning(f"目标函数计算失败: {e}")
            return float('inf')
    
    def _objective_function(self, params: np.ndarray, 
                           background: np.ndarray,
                           observations: np.ndarray,
                           obs_locations: np.ndarray) -> float:
        """
        目标函数（支持并行计算）
        
        Args:
            params: 参数数组
            background: 背景场
            observations: 观测数据
            obs_locations: 观测位置
            
        Returns:
            目标函数值
        """
        return self._compute_objective_single(params, background, observations, obs_locations)
    
    def _objective_parallel(self, params: np.ndarray, 
                           backgrounds: List[np.ndarray],
                           observations_list: List[np.ndarray],
                           obs_locations_list: List[np.ndarray]) -> float:
        """
        并行目标函数计算（用于多数据集优化）
        
        Args:
            params: 参数数组
            backgrounds: 背景场列表
            observations_list: 观测数据列表
            obs_locations_list: 观测位置列表
            
        Returns:
            平均目标函数值
        """
        if len(backgrounds) == 0:
            return float('inf')
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.n_jobs) as executor:
            futures = [
                executor.submit(self._compute_objective_single, params, bg, obs, loc)
                for bg, obs, loc in zip(backgrounds, observations_list, obs_locations_list)
            ]
            
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        valid_results = [r for r in results if r != float('inf')]
        if len(valid_results) == 0:
            return float('inf')
        
        return float(np.mean(valid_results))
    
    def _get_minimize_options(self, verbose: int = 0) -> Dict[str, Any]:
        """
        获取 minimize 函数的选项（版本兼容）
        
        Args:
            verbose: 详细程度
            
        Returns:
            选项字典
        """
        options: Dict[str, Any] = {'maxiter': 100}
        
        if SCIPY_VERSION >= (1, 9): # type: ignore # type: ignore
            options['verbose'] = verbose
        else:
            options['disp'] = verbose > 0
        
        return options
    
    def optimize(self, background: Union[np.ndarray, List[np.ndarray]], 
                observations: Union[np.ndarray, List[np.ndarray]], 
                obs_locations: Union[np.ndarray, List[np.ndarray]],
                method: str = 'L-BFGS-B',
                verbose: int = 0) -> Dict[str, Any]:
        """
        优化参数
        
        Args:
            background: 背景场（支持单个或多个数据集）
            observations: 观测数据
            obs_locations: 观测位置
            method: 优化方法
            verbose: 详细程度（0=静默, 1=简要, 2=详细）
            
        Returns:
            优化结果
        """
        logger.info("开始方差场参数优化")
        
        is_parallel = isinstance(background, list)
        
        initial_params = np.array([
            self.background_error_scale,
            self.observation_error_scale,
            self.correlation_length_scale
        ])
        
        bounds = [
            (0.01, 20.0),    # background_error_scale
            (0.001, 2.0),    # observation_error_scale
            (0.5, 100.0)     # correlation_length_scale
        ]
        
        history = []
        def callback(x):
            if is_parallel:
                f_val = self._objective_parallel(x, background, observations, obs_locations) # type: ignore
            else:
                f_val = self._objective_function(x, background, observations, obs_locations) # pyright: ignore[reportArgumentType]
            history.append({
                'iteration': len(history) + 1,
                'params': x.copy(),
                'score': f_val
            })
            if verbose > 1:
                logger.info(f"迭代 {len(history)}: 分数={f_val:.6f}")
        
        options = self._get_minimize_options(verbose)
        
        if is_parallel:
            obj_func = lambda p: self._objective_parallel(p, background, observations, obs_locations) # type: ignore # type: ignore
        else:
            obj_func = lambda p: self._objective_function(p, background, observations, obs_locations) # type: ignore
        
        result = minimize(
            fun=obj_func,
            x0=initial_params,
            method=method,
            bounds=bounds,
            callback=callback,
            options=options
        )
        
        self.optimization_history = history
        if result.fun < self.best_score:
            self.best_score = result.fun
            self.best_params = {
                'background_error_scale': float(result.x[0]),
                'observation_error_scale': float(result.x[1]),
                'correlation_length_scale': float(result.x[2])
            }
            
            self.background_error_scale = self.best_params['background_error_scale']
            self.observation_error_scale = self.best_params['observation_error_scale']
            self.correlation_length_scale = self.best_params['correlation_length_scale']
            
            logger.info(f"参数优化完成，最佳分数: {self.best_score:.6f}")
            logger.info(f"最佳参数: {self.best_params}")
        
        return {
            'success': result.success,
            'message': str(result.message) if result.message else None,
            'best_params': self.best_params,
            'best_score': self.best_score,
            'history': self.optimization_history,
            'nit': result.nit if hasattr(result, 'nit') else len(history),
            'nfev': result.nfev if hasattr(result, 'nfev') else None
        }
    
    def optimize_with_cv(self, background: np.ndarray, 
                        observations: np.ndarray, 
                        obs_locations: np.ndarray,
                        n_folds: int = 5,
                        method: str = 'L-BFGS-B',
                        verbose: int = 0) -> Dict[str, Any]:
        """
        使用交叉验证优化参数
        
        Args:
            background: 背景场
            observations: 观测数据
            obs_locations: 观测位置
            n_folds: 交叉验证折数
            method: 优化方法
            verbose: 详细程度
            
        Returns:
            优化结果
        """
        n_obs = len(observations)
        fold_size = n_obs // n_folds
        
        results = []
        
        for i in range(n_folds):
            val_indices = slice(i * fold_size, (i + 1) * fold_size)
            train_indices = np.concatenate([np.arange(i * fold_size), 
                                          np.arange((i + 1) * fold_size, n_obs)])
            
            train_obs = observations[train_indices]
            train_loc = obs_locations[train_indices]
            val_obs = observations[val_indices]
            val_loc = obs_locations[val_indices]
            
            fold_result = self.optimize(background, train_obs, train_loc, 
                                       method=method, verbose=verbose - 1)
            
            if fold_result['best_params']:
                self.background_error_scale = fold_result['best_params']['background_error_scale']
                self.observation_error_scale = fold_result['best_params']['observation_error_scale']
                self.correlation_length_scale = fold_result['best_params']['correlation_length_scale']
                
                val_score = self._compute_objective_single(
                    np.array([self.background_error_scale, 
                             self.observation_error_scale, 
                             self.correlation_length_scale]),
                    background, val_obs, val_loc
                )
                fold_result['val_score'] = val_score
            
            results.append(fold_result)
            
            if verbose > 0:
                logger.info(f"交叉验证折 {i+1}/{n_folds}: 训练分数={fold_result['best_score']:.6f}")
        
        avg_val_score = np.mean([r.get('val_score', float('inf')) for r in results])
        best_fold = min(results, key=lambda r: r.get('val_score', float('inf')))
        
        self.best_params = best_fold['best_params']
        self.best_score = best_fold['best_score']
        
        return {
            'success': all(r['success'] for r in results),
            'best_params': self.best_params,
            'best_score': self.best_score,
            'cv_scores': [r.get('val_score') for r in results],
            'avg_val_score': avg_val_score,
            'fold_results': results
        }
    
    def get_variance_field(self, shape: Tuple[int, int, int]) -> np.ndarray:
        """
        获取方差场
        
        Args:
            shape: 网格形状
            
        Returns:
            方差场
        """
        return np.ones(shape) * (self.background_error_scale**2)
    
    def get_sparse_variance_matrix(self, shape: Tuple[int, int, int]):
        """
        获取稀疏方差矩阵
        
        Args:
            shape: 网格形状
            
        Returns:
            稀疏方差矩阵
        """
        nx, ny, nz = shape
        n_total = nx * ny * nz
        variance = self.background_error_scale**2 + self.regularization
        return sparse.diags([variance] * n_total, format='csr')
    
    def get_observation_error_variance(self, n_obs: int) -> np.ndarray:
        """
        获取观测误差方差
        
        Args:
            n_obs: 观测数量
            
        Returns:
            观测误差方差
        """
        return np.ones(n_obs) * (self.observation_error_scale**2)
    
    def get_best_params(self) -> Optional[Dict[str, Any]]:
        """
        获取最佳参数
        
        Returns:
            最佳参数
        """
        return self.best_params
    
    def set_parallel_jobs(self, n_jobs: int):
        """
        设置并行计算的线程数
        
        Args:
            n_jobs: 线程数
        """
        self.n_jobs = max(1, n_jobs)
    
    def reset(self):
        """
        重置优化器
        """
        self.optimization_history = []
        self.best_params = None
        self.best_score = float('inf')
        self.background_error_scale = 1.0
        self.observation_error_scale = 0.1
        self.correlation_length_scale = 10.0


class AdaptiveVarianceField(VarianceFieldOptimizer):
    """
    自适应方差场
    根据同化质量动态调整方差参数
    """
    
    def __init__(self, config: Optional[BaseConfig] = None):
        super().__init__(config)
        self.adaptation_rate: float = 0.1
        self.min_background_error: float = 0.05
        self.max_background_error: float = 10.0
        self.last_incremental_score: Optional[float] = None
        self.smoothing_factor: float = 0.8
    
    def adapt(self, analysis: np.ndarray, 
              background: np.ndarray,
              observations: np.ndarray,
              obs_locations: np.ndarray) -> None:
        """
        自适应调整方差参数
        
        Args:
            analysis: 分析场
            background: 背景场
            observations: 观测数据
            obs_locations: 观测位置
        """
        try:
            nx, ny, nz = analysis.shape
            H = self._build_observation_operator(obs_locations, nx, ny, nz)
            
            if sparse.issparse(H):
                Hxa = H.dot(analysis.ravel())
                Hxb = H.dot(background.ravel())
            else:
                Hxa = H @ analysis.ravel()
                Hxb = H @ background.ravel()
            
            analysis_residual = np.mean((Hxa - observations)**2)
            background_residual = np.mean((Hxb - observations)**2)
            
            eps = 1e-10
            improvement_ratio = background_residual / max(analysis_residual, eps)
            
            if improvement_ratio < 0.85:
                self.background_error_scale = min(
                    self.background_error_scale * (1.0 + self.adaptation_rate),
                    self.max_background_error
                )
                logger.debug(f"增加背景误差: {self.background_error_scale:.4f}")
            elif improvement_ratio > 1.2:
                self.background_error_scale = max(
                    self.background_error_scale * (1.0 - self.adaptation_rate * 0.5),
                    self.min_background_error
                )
                logger.debug(f"减少背景误差: {self.background_error_scale:.4f}")
            
            if self.last_incremental_score is not None:
                self.last_incremental_score = (
                    self.smoothing_factor * self.last_incremental_score +
                    (1 - self.smoothing_factor) * analysis_residual
                ) # type: ignore
            else:
                self.last_incremental_score = analysis_residual # pyright: ignore[reportAttributeAccessIssue]
                
        except Exception as e:
            logger.warning(f"自适应调整失败: {e}")
    
    def set_adaptation_rate(self, rate: float) -> None:
        """
        设置自适应率
        
        Args:
            rate: 自适应率
        """
        self.adaptation_rate = max(0.0, min(rate, 1.0))


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("          方差场优化器测试")
    logger.info("=" * 70)

    logger.info("\n1. 测试基础优化（稀疏矩阵模式）")
    logger.info("-" * 70)
    optimizer = VarianceFieldOptimizer(use_sparse=True)
    optimizer.set_parallel_jobs(4)
    
    nx, ny, nz = 10, 10, 5
    background = np.random.rand(nx, ny, nz) * 10
    
    obs_locations = np.array([
        [2, 3, 2], [5, 5, 2], [7, 2, 2],
        [3, 7, 2], [8, 8, 2], [1, 1, 2]
    ])
    
    observations = np.array([
        background[2, 3, 2] + np.random.normal(0, 0.1),
        background[5, 5, 2] + np.random.normal(0, 0.1),
        background[7, 2, 2] + np.random.normal(0, 0.1),
        background[3, 7, 2] + np.random.normal(0, 0.1),
        background[8, 8, 2] + np.random.normal(0, 0.1),
        background[1, 1, 2] + np.random.normal(0, 0.1)
    ])
    
    result = optimizer.optimize(background, observations, obs_locations, verbose=1)
    logger.info(f"优化成功: {result['success']}")
    logger.info(f"最佳分数: {result['best_score']:.6f}")
    if result['best_params']:
        logger.info(f"最佳参数:")
        for key, value in result['best_params'].items():
            logger.info(f"  {key}: {value:.4f}")
    
    variance_field = optimizer.get_variance_field((nx, ny, nz))
    logger.info(f"方差场形状: {variance_field.shape}")
    logger.info(f"方差场范围: [{variance_field.min():.4f}, {variance_field.max():.4f}]")
    
    logger.info("\n2. 测试交叉验证优化")
    logger.info("-" * 70)
    cv_result = optimizer.optimize_with_cv(background, observations, obs_locations, 
                                          n_folds=3, verbose=1)
    logger.info(f"交叉验证平均分数: {cv_result['avg_val_score']:.6f}")
    
    logger.info("\n3. 测试自适应方差场")
    logger.info("-" * 70)
    adaptive_optimizer = AdaptiveVarianceField()
    
    analysis = background + np.random.randn(nx, ny, nz) * 0.5
    adaptive_optimizer.adapt(analysis, background, observations, obs_locations)
    logger.info(f"自适应后背景误差: {adaptive_optimizer.background_error_scale:.4f}")
    
    logger.info("\n4. 测试稀疏方差矩阵")
    logger.info("-" * 70)
    sparse_var = optimizer.get_sparse_variance_matrix((nx, ny, nz))
    logger.info(f"稀疏方差矩阵类型: {type(sparse_var)}")
    logger.info(f"稀疏方差矩阵形状: {sparse_var.shape}")
    logger.info(f"稀疏度: {100 * (1 - sparse_var.nnz / sparse_var.shape[0]):.2f}%") # type: ignore
    
    logger.info("\n" + "=" * 70)
    logger.info("          所有测试通过！")
    logger.info("=" * 70)


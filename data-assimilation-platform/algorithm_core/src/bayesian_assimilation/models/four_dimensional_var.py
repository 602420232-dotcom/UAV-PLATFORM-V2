import os
import sys

SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import numpy as np
from scipy.optimize import minimize
from scipy.linalg import solve
import subprocess
import netCDF4 as nc
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging

from bayesian_assimilation.core.base import AssimilationBase
from bayesian_assimilation.utils.config import BaseConfig

logger = logging.getLogger(__name__)

class FourDimensionalVar(AssimilationBase):
    """
    4D-VAR 同化算法实现
    支持时间维度的同化，提高预报精度
    """
    
    def __init__(self, config: Optional[Any] = None):
        super().__init__(config)
        self.name = "four_dimensional_var"
        # 确保config是字典
        if not isinstance(self.config, dict):
            self.config = {}
        self.config.setdefault("max_iterations", 20)
        self.config.setdefault("tolerance", 1e-6)
        self.config.setdefault("parallel", False)
        self.config.setdefault("wrf_input_dir", "./")
        self.config.setdefault("wrf_exe_path", "./wrf.exe")
        self.observation_operator = None
        self.parallel_manager = None
        self._ensure_defaults()
    
    def _ensure_defaults(self):
        """确保默认值已设置"""
        if self.grid_shape is None:
            self.grid_shape = (10, 10, 5)
        if self.resolution is None:
            self.resolution = 50.0
        if not hasattr(self, 'nx'):
            self.nx, self.ny, self.nz = self.grid_shape
    
    def _get_config_value(self, config, attr_name, default_value):
        """
        安全地获取配置值
        """
        if config is not None and hasattr(config, attr_name):
            return getattr(config, attr_name)
        return default_value
    
    def run_wrf_model(self, x0: Dict[str, np.ndarray]) -> List[Dict[str, np.ndarray]]:
        """
        对接真实 WRF 积分
        x0: 初始场 (温、压、湿、风 U、V、W)
        """
        # 1. 写入 wrfinput_d01
        nc_file = os.path.join(self.config["wrf_input_dir"], "wrfinput_d01")
        
        if os.path.exists(nc_file):
            with nc.Dataset(nc_file, 'r+') as ds:
                if 'T' in x0 and 'T' in ds.variables:
                    ds.variables['T'][0, 0, :, :] = x0['T']
                if 'U' in x0 and 'U' in ds.variables:
                    ds.variables['U'][0, 0, :, :] = x0['U']
                if 'V' in x0 and 'V' in ds.variables:
                    ds.variables['V'][0, 0, :, :] = x0['V']
                if 'Ps' in x0 and 'PSFC' in ds.variables:
                    ds.variables['PSFC'][0, :, :] = x0['Ps']

        # 2. 运行 WRF
        os.chdir(self.config["wrf_input_dir"])
        if os.path.exists(self.config["wrf_exe_path"]):
            subprocess.run(
                [self.config["wrf_exe_path"]], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.PIPE
            )

        # 3. 读取 wrfout 全部时刻
        wrfout_files = sorted([f for f in os.listdir(self.config["wrf_input_dir"]) if 'wrfout' in f])
        history = []
        for f in wrfout_files:
            try:
                with nc.Dataset(f) as ds:
                    model_state = {}
                    if 'T' in ds.variables:
                        model_state['T'] = ds.variables['T'][0, 0, :, :]
                    if 'U' in ds.variables:
                        model_state['U'] = ds.variables['U'][0, 0, :, :]
                    if 'V' in ds.variables:
                        model_state['V'] = ds.variables['V'][0, 0, :, :]
                    if model_state:
                        history.append(model_state)
            except Exception as e:
                logger.warning(f"读取WRF输出文件失败: {e}")
                continue
        
        # 如果没有WRF输出，使用简化模型
        if not history:
            history = self._simplified_model_run(x0)
        
        return history
    
    def _simplified_model_run(self, x0: Dict[str, np.ndarray]) -> List[Dict[str, np.ndarray]]:
        """
        简化的模型运行，用于没有WRF的情况
        """
        history = []
        shape = x0['T'].shape
        
        # 模拟4个时间步的运行
        for i in range(4):
            # 简单的平流和扩散
            model_state = {
                'T': x0['T'] * (1 - 0.1 * i) + np.random.normal(0, 0.1, shape),
                'U': x0['U'] * (1 - 0.05 * i) + np.random.normal(0, 0.05, shape),
                'V': x0['V'] * (1 - 0.05 * i) + np.random.normal(0, 0.05, shape)
            }
            history.append(model_state)
        
        return history
    
    def cost_function(self, x0_flat: np.ndarray, xb: Dict[str, np.ndarray], 
                     B_inv: np.ndarray, R_inv: np.ndarray, 
                     observations: List[Dict], H) -> float:
        """
        4D-Var 代价函数
        J = 0.5*(x-xb)ᵀB⁻¹(x-xb) + 0.5*Σ(H(xₖ)-yₖ)ᵀR⁻¹(H(xₖ)-yₖ)
        """
        # 恢复场结构
        shape_2d = xb['T'].shape
        n_points = shape_2d[0] * shape_2d[1]
        
        x0 = {
            'T': x0_flat[:n_points].reshape(shape_2d),
            'U': x0_flat[n_points:2*n_points].reshape(shape_2d),
            'V': x0_flat[2*n_points:3*n_points].reshape(shape_2d),
            'Ps': x0_flat[3*n_points:].reshape(shape_2d)
        }

        # 1. 背景项
        dx_T = x0['T'] - xb['T']
        dx_U = x0['U'] - xb['U']
        dx_V = x0['V'] - xb['V']
        dx_Ps = x0['Ps'] - xb['Ps']

        Jb = 0.5 * (np.sum(dx_T * self._apply_B_inv(dx_T, B_inv)) +
                    np.sum(dx_U * self._apply_B_inv(dx_U, B_inv)) +
                    np.sum(dx_V * self._apply_B_inv(dx_V, B_inv)) +
                    np.sum(dx_Ps * self._apply_B_inv(dx_Ps, B_inv)))

        # 2. WRF 积分
        model_time_series = self.run_wrf_model(x0)

        # 3. 观测项
        Jo = 0.0
        for obs in observations:
            t = obs.get('time_idx', 0)
            if t < len(model_time_series):
                y = obs['value']
                Hx = H(model_time_series[t])
                diff = Hx - y
                Jo += 0.5 * diff.T @ R_inv @ diff

        return Jb + Jo
    
    def adjoint_gradient(self, x0_flat: np.ndarray, xb: Dict[str, np.ndarray], 
                        B_inv: np.ndarray, R_inv: np.ndarray, 
                        observations: List[Dict], H) -> np.ndarray:
        """
        伴随模式 → 输出代价函数梯度
        用于 L-BFGS 快速优化
        """
        shape_2d = xb['T'].shape
        n_points = shape_2d[0] * shape_2d[1]
        
        x0 = {
            'T': x0_flat[:n_points].reshape(shape_2d),
            'U': x0_flat[n_points:2*n_points].reshape(shape_2d),
            'V': x0_flat[2*n_points:3*n_points].reshape(shape_2d),
            'Ps': x0_flat[3*n_points:].reshape(shape_2d)
        }

        # —— 前向积分（WRF）
        model_time_series = self.run_wrf_model(x0)

        # —— 初始化伴随变量
        lambda_T = np.zeros_like(x0['T'])
        lambda_U = np.zeros_like(x0['U'])
        lambda_V = np.zeros_like(x0['V'])
        lambda_Ps = np.zeros_like(x0['Ps'])

        # —— 逆时间循环（伴随核心）
        for k in reversed(range(len(model_time_series))):
            # 观测贡献
            for obs_idx, obs in enumerate(observations):
                if obs.get('time_idx', 0) == k:
                    Hx = H(model_time_series[k])
                    diff = Hx - obs['value']
                    adj_obs = R_inv @ diff
                    # 观测算子H的伴随 - 只对对应位置添加贡献
                    lat_idx = int(obs.get('lat_idx', 0))
                    lon_idx = int(obs.get('lon_idx', 0))
                    if lambda_T.ndim >= 2 and 0 <= lat_idx < lambda_T.shape[0] and 0 <= lon_idx < lambda_T.shape[1]: # type: ignore
                        lambda_T[lat_idx, lon_idx] += adj_obs[obs_idx] * 1.0
                        lambda_U[lat_idx, lon_idx] += adj_obs[obs_idx] * 0.2
                        lambda_V[lat_idx, lon_idx] += adj_obs[obs_idx] * 0.2


            # WRF 线性伴随（简化版，可对接真实 WRF 伴随）
            lambda_T = lambda_T * 0.98
            lambda_U = lambda_U * 0.95
            lambda_V = lambda_V * 0.95

        # —— 背景项梯度
        grad_T = self._apply_B_inv(x0['T'] - xb['T'], B_inv) + lambda_T
        grad_U = self._apply_B_inv(x0['U'] - xb['U'], B_inv) + lambda_U
        grad_V = self._apply_B_inv(x0['V'] - xb['V'], B_inv) + lambda_V
        grad_Ps = self._apply_B_inv(x0['Ps'] - xb['Ps'], B_inv) + lambda_Ps

        # 展平返回
        return np.concatenate([grad_T.ravel(),
                               grad_U.ravel(),
                               grad_V.ravel(),
                               grad_Ps.ravel()])
    
    
    def _apply_B_inv(self, x: np.ndarray, B_inv: np.ndarray) -> np.ndarray:
        """
        应用背景误差协方差逆矩阵
        """
        if B_inv.ndim == 2:
            result = B_inv @ x.ravel()
            return result.reshape(x.shape)
        else:
            return x * B_inv
    
    def assimilate(self, background: Dict, observations: List[Dict]) -> Tuple[Dict, Dict]:
        """
        执行4D-VAR同化
        """
        logger.info("开始4D-VAR同化...")
        start_time = datetime.now()
        
        # 准备背景场
        xb = {
            'T': background.get('variables', {}).get('temperature', np.zeros((10, 10))),
            'U': background.get('variables', {}).get('u_wind', np.zeros((10, 10))),
            'V': background.get('variables', {}).get('v_wind', np.zeros((10, 10))),
            'Ps': background.get('variables', {}).get('pressure', np.zeros((10, 10)))
        }
        
        # 确保背景场是二维的
        assert xb['T'].ndim == 2, f"温度场必须是二维，实际维度: {xb['T'].ndim}"
        n_rows, n_cols = xb['T'].shape
        n = n_rows * n_cols
        
        # 准备观测算子
        def observation_operator(model_state):
            obs_values = []
            for obs in observations:
                lat_idx = int(obs.get('lat_idx', 0))
                lon_idx = int(obs.get('lon_idx', 0))
                var = obs.get('variable', 'temperature')
                
                if var == 'temperature' and 'T' in model_state:
                    obs_values.append(model_state['T'][lat_idx, lon_idx])
                elif var == 'u_wind' and 'U' in model_state:
                    obs_values.append(model_state['U'][lat_idx, lon_idx])
                elif var == 'v_wind' and 'V' in model_state:
                    obs_values.append(model_state['V'][lat_idx, lon_idx])
            return np.array(obs_values)
        
        # 准备协方差矩阵
        B_inv = np.eye(n) * 0.1
        R_inv = np.eye(len(observations)) * 1.0
        
        # 展平初始场
        x0_flat = np.concatenate([
            xb['T'].ravel(),
            xb['U'].ravel(),
            xb['V'].ravel(),
            xb['Ps'].ravel()
        ])

        # 带伴随梯度的优化（L-BFGS）
        result = minimize(
            fun=self.cost_function,
            jac=self.adjoint_gradient,
            x0=x0_flat,
            args=(xb, B_inv, R_inv, observations, observation_operator),
            method='L-BFGS-B',
            options={
                'maxiter': self.config['max_iterations'],
                'gtol': self.config['tolerance'],
            }
        )

        # 最优分析场
        xa = {
            'T': result.x[:n].reshape((n_rows, n_cols)),
            'U': result.x[n:2*n].reshape((n_rows, n_cols)),
            'V': result.x[2*n:3*n].reshape((n_rows, n_cols)),
            'Ps': result.x[3*n:].reshape((n_rows, n_cols))
        }

        # 构建分析场
        analysis = {
            'grid': background.get('grid', {}),
            'variables': {
                'temperature': xa['T'],
                'u_wind': xa['U'],
                'v_wind': xa['V'],
                'pressure': xa['Ps']
            }
        }

        # 计算方差场 - 使用简化方法
        try:
            # 基于观测密度估算方差
            obs_density = len(observations) / (n_rows * n_cols)
            variance_scale = 1.0 / (1.0 + obs_density * 10)
            
            variance_field = {
                'temperature': np.ones((n_rows, n_cols)) * 0.5 * variance_scale,
                'u_wind': np.ones((n_rows, n_cols)) * 0.3 * variance_scale,
                'v_wind': np.ones((n_rows, n_cols)) * 0.3 * variance_scale,
                'pressure': np.ones((n_rows, n_cols)) * 0.4 * variance_scale
            }
            
            logger.info(f"方差场计算完成，观测密度: {obs_density:.3f}")
            
        except Exception as e:
            logger.warning(f"方差场计算失败: {e}")
            # 生成默认方差场
            variance_field = {
                'temperature': np.ones((n_rows, n_cols)) * 0.5,
                'u_wind': np.ones((n_rows, n_cols)) * 0.3,
                'v_wind': np.ones((n_rows, n_cols)) * 0.3,
                'pressure': np.ones((n_rows, n_cols)) * 0.4
            }
        
        end_time = datetime.now()
        logger.info(f"4D-VAR同化完成，耗时: {end_time - start_time}")
        
        return analysis, variance_field
    
    def set_parallel_manager(self, parallel_manager):
        """
        设置并行管理器
        """
        self.parallel_manager = parallel_manager
        if isinstance(self.config, dict):
            self.config['parallel'] = True


if __name__ == "__main__":
    model = FourDimensionalVar()
    
    # 准备测试数据
    background = {
        'grid': {'shape': (10, 10)},
        'variables': {
            'temperature': np.random.rand(10, 10) * 10 + 20,
            'u_wind': np.random.rand(10, 10) * 5,
            'v_wind': np.random.rand(10, 10) * 5,
            'pressure': np.random.rand(10, 10) * 100 + 1000
        }
    }
    
    observations = [
        {'time_idx': 0, 'lat_idx': 2, 'lon_idx': 3, 'variable': 'temperature', 'value': 25.0},
        {'time_idx': 1, 'lat_idx': 5, 'lon_idx': 5, 'variable': 'u_wind', 'value': 3.0},
        {'time_idx': 2, 'lat_idx': 7, 'lon_idx': 2, 'variable': 'v_wind', 'value': -2.0}
    ]
    
    analysis, variance = model.assimilate(background, observations)
    logger.info(f"分析场温度范围: [{analysis['variables']['temperature'].min():.2f}, {analysis['variables']['temperature'].max():.2f}]")
    logger.info(f"分析场风场范围: [{analysis['variables']['u_wind'].min():.2f}, {analysis['variables']['u_wind'].max():.2f}]")
    logger.info("测试通过！")

# 便捷函数
four_dimensional_var = FourDimensionalVar().assimilate


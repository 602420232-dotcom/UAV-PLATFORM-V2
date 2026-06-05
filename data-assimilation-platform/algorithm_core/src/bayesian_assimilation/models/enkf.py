# algorithm_core/src/bayesian_assimilation/models/enkf.py
# EnKF同化算法实现

import os
import sys

SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import numpy as np  # noqa: E402
from typing import Optional  # noqa: E402
import logging  # noqa: E402

from bayesian_assimilation.core.base import AssimilationBase  # noqa: E402
from bayesian_assimilation.utils.config import BaseConfig  # noqa: E402

logger = logging.getLogger(__name__)


class EnKF(AssimilationBase):
    """
    集合卡尔曼滤波(EnKF)同化算法
    适合非线性系统和复杂观测场景
    """

    def __init__(self, config: Optional[BaseConfig] = None):
        super().__init__(config)
        self.ensemble_size = self._get_config_value(config, 'ensemble_size', 30)
        self.background_error_scale = self._get_config_value(config, 'background_error_scale', 1.0)
        self.observation_error_scale = self._get_config_value(
            config, 'observation_error_scale', 0.1)
        self._ensure_defaults()

    def _get_config_value(self, config, attr_name, default_value):
        """
        安全地获取配置值
        """
        if config is not None and hasattr(config, attr_name):
            return getattr(config, attr_name)
        return default_value

    def _ensure_defaults(self):
        """确保默认值已设置"""
        if self.grid_shape is None:
            self.grid_shape = (10, 10, 5)
        if self.resolution is None:
            self.resolution = 50.0
        if not hasattr(self, 'nx'):
            self.nx, self.ny, self.nz = self.grid_shape

    def assimilate(self, background, observations, obs_locations, obs_errors=None):
        """
        执行EnKF同化

        Args:
            background: 背景场
            observations: 观测数据
            obs_locations: 观测位置
            obs_errors: 观测误差

        Returns:
            analysis: 分析场
            variance: 方差场
        """
        self._ensure_defaults()

        if background is None:
            raise ValueError("背景场不能为空")

        if observations is None or obs_locations is None:
            logger.warning("观测数据或位置为空，返回背景场")
            return background, np.zeros_like(background)

        if len(observations) == 0 or len(obs_locations) == 0:
            logger.warning("观测数据或位置为空，返回背景场")
            return background, np.zeros_like(background)

        logger.info(f"🚀 开始EnKF同化，网格: {self.grid_shape}, 集合大小: {self.ensemble_size}")
        return self._assimilate_ensemble(background, observations, obs_locations, obs_errors)

    def _assimilate_ensemble(self, bg, obs, obs_loc, obs_err):
        """
        执行集合卡尔曼滤波
        """
        nx, ny, nz = self.grid_shape
        n = nx * ny * nz  # noqa: F841
        n_obs = len(obs)

        # 生成集合
        ensemble = self._generate_ensemble(bg)

        # 构建观测算子
        H = self._build_observation_operator(obs_loc)

        # 观测误差协方差
        obs_err = obs_err or np.full(n_obs, self.observation_error_scale)
        R = np.diag(obs_err**2)
        R_inv = np.diag(1.0 / (obs_err**2 + 1e-6))  # noqa: F841

        # 计算集合均值和协方差
        xb_mean = np.mean(ensemble, axis=0)
        xb_prime = ensemble - xb_mean

        # 计算观测空间的集合
        yb = H @ ensemble.T
        yb_mean = np.mean(yb, axis=1)
        yb_prime = yb - yb_mean[:, np.newaxis]

        # 计算卡尔曼增益
        Pyy = (yb_prime @ yb_prime.T) / (self.ensemble_size - 1) + R
        Pxy = (xb_prime.T @ yb_prime.T) / (self.ensemble_size - 1)

        try:
            K = Pxy @ np.linalg.inv(Pyy)
        except np.linalg.LinAlgError:
            # 处理奇异矩阵
            K = Pxy @ np.linalg.pinv(Pyy)

        # 计算分析场
        innovation = obs - yb_mean
        xa_mean = xb_mean + K @ innovation

        # 更新集合 - 为每个集合成员添加创新
        xa_ensemble = np.zeros_like(ensemble)
        for i in range(self.ensemble_size):
            obs_perturb = obs + np.random.normal(0, np.sqrt(np.diag(R)), n_obs)
            innovation_i = obs_perturb - yb[:, i]
            xa_ensemble[i] = ensemble[i] + K @ innovation_i

        # 计算分析误差方差
        xa_prime = xa_ensemble - xa_mean  # noqa: F841
        variance = np.var(xa_ensemble, axis=0)

        self.analysis = xa_mean.reshape(nx, ny, nz)
        self.variance = variance.reshape(nx, ny, nz)

        return self.analysis, self.variance

    def _generate_ensemble(self, bg):
        """
        生成初始集合
        """
        nx, ny, nz = self.grid_shape
        n = nx * ny * nz

        # 展平背景场
        bg_flat = bg.ravel()

        # 生成集合
        ensemble = np.zeros((self.ensemble_size, n))
        for i in range(self.ensemble_size):
            # 添加随机扰动
            perturbation = np.random.normal(0, self.background_error_scale, n)
            ensemble[i] = bg_flat + perturbation

        return ensemble

    def _build_observation_operator(self, obs_loc):
        """
        构建观测算子
        """
        if obs_loc is None or len(obs_loc) == 0:
            nx, ny, nz = self.grid_shape
            return np.zeros((1, nx * ny * nz))

        nx, ny, nz = self.grid_shape
        n_obs = len(obs_loc)

        H = np.zeros((n_obs, nx * ny * nz))

        for i, (x, y, z) in enumerate(obs_loc):
            # 找到最近的网格点
            ix = min(max(0, int(x/self.resolution)), nx-1)
            iy = min(max(0, int(y/self.resolution)), ny-1)
            iz = min(max(0, int(z/self.resolution)), nz-1)

            idx = ix * ny * nz + iy * nz + iz
            H[i, idx] = 1.0

        return H


if __name__ == "__main__":
    model = EnKF()
    bg = np.random.rand(10, 10, 5) * 10
    obs = np.array([5.0, 6.0, 7.0])
    obs_loc = np.array([[100.0, 100.0, 50.0], [200.0, 200.0, 100.0], [300.0, 300.0, 150.0]])

    analysis, variance = model.assimilate(bg, obs, obs_loc)
    logger.info(f"分析场形状: {analysis.shape}")
    logger.info(f"方差场形状: {variance.shape}")
    logger.info(f"分析场范围: [{analysis.min():.2f}, {analysis.max():.2f}]")
    logger.info("测试通过！")

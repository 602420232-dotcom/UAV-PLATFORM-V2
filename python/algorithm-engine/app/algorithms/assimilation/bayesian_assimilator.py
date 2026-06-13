"""贝叶斯同化器算法。

使用贝叶斯框架融合先验（背景场）和似然（观测信息）：
- 假设高斯似然函数
- 计算后验均值和方差
- 通过贝叶斯更新实现最优估计
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class BayesianAssimilator:
    """贝叶斯同化器。

    在贝叶斯框架下，将背景场作为先验分布，将观测作为似然信息，
    通过贝叶斯定理计算后验分布的均值（分析场）和方差。

    对于高斯假设：
        后验均值 = (sigma_y^2 * x_b + sigma_b^2 * y) / (sigma_b^2 + sigma_y^2)
        后验方差 = sigma_b^2 * sigma_y^2 / (sigma_b^2 + sigma_y^2)

    参数:
        prior_confidence: 先验置信度，控制背景误差方差的缩放（默认 1.0）
        likelihood_sigma: 似然标准差，控制观测误差大小（默认 0.5）
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.prior_confidence: float = self.config.get("prior_confidence", 1.0)
        self.likelihood_sigma: float = self.config.get("likelihood_sigma", 0.5)
        self.grid_shape: tuple[int, ...] = self.config.get("grid_shape", (10, 10, 5))
        self.background_error_scale: float = self.config.get("background_error_scale", 1.0)
        self.influence_radius: int = self.config.get("influence_radius", 3)

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行贝叶斯同化。

        Args:
            params: 包含以下键的字典：
                - background_field: 背景场（numpy array）
                - observations: 观测列表，每个元素为含 position/value 的字典

        Returns:
            包含 analysis_field（分析场列表格式）及贝叶斯诊断信息的字典。
        """
        background = np.asarray(params.get("background_field", np.zeros(self.grid_shape)))
        observations = params.get("observations", [])

        if background.ndim == 0:
            background = background.reshape(1)

        shape = background.shape
        n = background.size
        xb = background.flatten()

        logger.info(
            "开始贝叶斯同化，网格大小: %s，观测数量: %d，先验置信度: %.2f",
            shape,
            len(observations),
            self.prior_confidence,
        )

        # ---- 先验参数 ----
        prior_mean = xb.copy()
        prior_sigma = self.background_error_scale / max(self.prior_confidence, 1e-6)
        prior_var = prior_sigma ** 2

        # ---- 似然参数 ----
        likelihood_var = self.likelihood_sigma ** 2

        # ---- 对每个网格点应用贝叶斯更新 ----
        posterior_mean = prior_mean.copy()
        posterior_var = np.ones(n) * prior_var

        # 构建观测位置和值的数组
        obs_positions = []
        obs_values = []
        for obs in observations:
            pos = obs.get("position", [0] * len(shape))
            obs_positions.append(np.array(pos, dtype=float))
            obs_values.append(obs.get("value", 0.0))

        if len(obs_positions) > 0:
            obs_arr = np.array(obs_positions)
            obs_val_arr = np.array(obs_values)

            # 遍历所有网格点
            for idx in range(n):
                grid_pos = np.array(self._index_to_position(idx, shape), dtype=float)

                # 找到影响范围内的观测
                distances = np.sqrt(np.sum((obs_arr - grid_pos) ** 2, axis=1))
                mask = distances <= self.influence_radius

                if np.any(mask):
                    local_obs = obs_val_arr[mask]
                    local_dist = distances[mask]

                    # 距离权重（越近权重越大）
                    scale = max(self.influence_radius * 0.5, 1e-6)
                    weights = np.exp(-0.5 * (local_dist / scale) ** 2)
                    weights = weights / max(weights.sum(), 1e-10)

                    # 加权观测值
                    y_eff = np.sum(weights * local_obs)

                    # 有效观测方差（考虑距离衰减）
                    effective_likelihood_var = likelihood_var / max(weights.sum(), 1e-10)

                    # 贝叶斯更新
                    posterior_var[idx] = (
                        prior_var * effective_likelihood_var
                        / (prior_var + effective_likelihood_var)
                    )
                    posterior_mean[idx] = (
                        effective_likelihood_var * prior_mean[idx]
                        + prior_var * y_eff
                    ) / (prior_var + effective_likelihood_var)

        analysis = posterior_mean.reshape(shape)
        posterior_std = np.sqrt(posterior_var).reshape(shape)

        # 诊断统计
        mean_posterior_var = float(np.mean(posterior_var))
        max_posterior_var = float(np.max(posterior_var))

        logger.info(
            "贝叶斯同化完成，后验方差均值: %.4f，后验方差最大值: %.4f",
            mean_posterior_var,
            max_posterior_var,
        )

        return {
            "analysis_field": analysis.tolist(),
            "posterior_std": posterior_std.tolist(),
            "mean_posterior_variance": mean_posterior_var,
            "max_posterior_variance": max_posterior_var,
            "prior_confidence": self.prior_confidence,
            "likelihood_sigma": self.likelihood_sigma,
            "grid_shape": list(shape),
            "num_observations": len(observations),
        }

    def _index_to_position(self, idx, shape):
        """将一维索引转换为多维网格位置。"""
        pos = []
        remaining = idx
        for i in range(len(shape) - 1, -1, -1):
            pos.append(remaining % shape[i])
            remaining = remaining // shape[i]
        pos.reverse()
        return pos

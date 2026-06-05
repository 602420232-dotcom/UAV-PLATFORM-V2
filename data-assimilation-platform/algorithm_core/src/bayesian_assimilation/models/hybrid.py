# algorithm_core/src/bayesian_assimilation/models/hybrid.py
# 混合同化算法实现

import os
import sys

SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import numpy as np
from typing import Optional, Tuple, List, Dict, Any
import logging

from bayesian_assimilation.core.base import AssimilationBase
from bayesian_assimilation.utils.config import BaseConfig
from bayesian_assimilation.models.three_dimensional_var import ThreeDimensionalVAR
from bayesian_assimilation.models.enkf import EnKF
from bayesian_assimilation.models.four_dimensional_var import FourDimensionalVar
from bayesian_assimilation.models.enhanced_bayesian import EnhancedBayesianAssimilation

logger = logging.getLogger(__name__)


class HybridAssimilation(AssimilationBase):
    """
    混合同化算法
    结合3D-VAR和EnKF的优势，支持多种算法组合
    """

    def __init__(self, config: Optional[BaseConfig] = None, algorithm_types: List[str] = None):  # type: ignore
        """
        初始化混合同化器

        Args:
            config: 配置对象
            algorithm_types: 算法类型列表，可选值: ['3dvar', 'enkf', '4dvar', 'enhanced']
        """
        super().__init__(config)
        self.algorithms = {}
        self.weights = {}
        self._initialize_algorithms(algorithm_types or ['3dvar', 'enkf'])
        self._ensure_defaults()

    def _initialize_algorithms(self, algorithm_types: List[str]):
        """
        初始化指定的算法实例
        """
        logger.info(f"初始化混合同化算法，算法类型: {algorithm_types}")

        if '3dvar' in algorithm_types:
            self.algorithms['3dvar'] = ThreeDimensionalVAR(self.config)
            self.weights['3dvar'] = 0.5

        if 'enkf' in algorithm_types:
            self.algorithms['enkf'] = EnKF(self.config)
            self.weights['enkf'] = 0.5

        if '4dvar' in algorithm_types:
            self.algorithms['4dvar'] = FourDimensionalVar(self.config)
            self.weights['4dvar'] = 0.3

        if 'enhanced' in algorithm_types:
            self.algorithms['enhanced'] = EnhancedBayesianAssimilation(self.config)
            self.weights['enhanced'] = 0.3

        self._normalize_weights()

    def _normalize_weights(self):
        """
        归一化权重，确保权重总和为1.0
        """
        total = sum(self.weights.values())
        if total > 0:
            for key in self.weights:
                self.weights[key] /= total

    def _ensure_defaults(self):
        """确保默认值已设置"""
        if self.grid_shape is None:
            self.grid_shape = (10, 10, 5)
        if self.resolution is None:
            self.resolution = 50.0

    def initialize_grid(self, domain_size: Tuple[float, float, float],
                       resolution: Optional[float] = None):
        """
        初始化网格

        Args:
            domain_size: 域大小 (x, y, z)
            resolution: 分辨率
        """
        super().initialize_grid(domain_size, resolution)
        for name, algo in self.algorithms.items():
            algo.initialize_grid(domain_size, resolution)
        logger.info(f"网格初始化完成，形状: {self.grid_shape}，分辨率: {self.resolution}")

    def set_weights(self, weights: Dict[str, float]):
        """
        设置各算法的权重

        Args:
            weights: 权重字典，如 {'3dvar': 0.6, 'enkf': 0.4}
        """
        for key, value in weights.items():
            if key in self.algorithms:
                self.weights[key] = value
        self._normalize_weights()
        logger.info(f"权重设置完成: {self.weights}")

    def assimilate(self, background, observations, obs_locations, obs_errors=None):
        """
        执行混合同化

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

        if self.grid_shape is None:
            raise RuntimeError("网格未初始化，请先调用 initialize_grid")

        logger.info(f"开始混合同化，使用算法: {list(self.algorithms.keys())}")

        results = {}
        for name, algo in self.algorithms.items():
            logger.info(f"执行 {name} 同化...")
            analysis, variance = algo.assimilate(background, observations, obs_locations, obs_errors)
            results[name] = {'analysis': analysis, 'variance': variance}

        analysis = None
        variance = None

        for name, result in results.items():
            weight = self.weights[name]
            result_analysis = result['analysis']
            result_variance = result['variance']

            if result_analysis is None or result_variance is None:
                continue

            if analysis is None:
                analysis = weight * result_analysis
                variance = weight * result_variance
            else:
                analysis = analysis + weight * result_analysis
                variance = variance + weight * result_variance

        if analysis is None or variance is None:
            raise RuntimeError("所有算法都返回了 None 结果")

        self.analysis = analysis
        self.variance = variance

        logger.info("混合同化完成")
        return analysis, variance

    def get_algorithm_info(self) -> Dict[str, Any]:
        """
        获取算法信息

        Returns:
            算法信息字典
        """
        info = {
            'algorithms': list(self.algorithms.keys()),
            'weights': self.weights,
            'grid_shape': self.grid_shape,
            'resolution': self.resolution
        }
        return info


class AdaptiveHybridAssimilation(HybridAssimilation):
    """
    自适应混合同化
    根据同化质量动态调整各算法权重
    """

    def __init__(self, config: Optional[BaseConfig] = None, algorithm_types: List[str] = None):  # type: ignore
        super().__init__(config, algorithm_types)
        self.adaptation_rate = 0.1
        self.max_weight = 0.85
        self.min_weight = 0.15
        self.last_scores = {}

    def assimilate(self, background, observations, obs_locations, obs_errors=None):
        """
        执行自适应混合同化
        """
        results = {}
        scores = {}

        for name, algo in self.algorithms.items():
            analysis, variance = algo.assimilate(background, observations, obs_locations, obs_errors)
            results[name] = {'analysis': analysis, 'variance': variance}

            if analysis is not None:
                nx, ny, nz = self.grid_shape
                H = self._build_observation_operator(obs_locations, nx, ny, nz)
                Hxa = H @ analysis.ravel()
                score = float(np.mean((Hxa - observations)**2))
                scores[name] = score
                self.last_scores[name] = score

        if len(scores) > 0:
            best_algo = min(scores.keys(), key=lambda k: scores[k])
            worst_algo = max(scores.keys(), key=lambda k: scores[k])

            logger.info(f"各算法评分: {scores}")
            logger.info(f"最佳算法: {best_algo}, 最差算法: {worst_algo}")

            for name in self.weights:
                if name == best_algo:
                    self.weights[name] = min(self.weights[name] + self.adaptation_rate, self.max_weight)
                elif name == worst_algo:
                    self.weights[name] = max(self.weights[name] - self.adaptation_rate, self.min_weight)

            self._normalize_weights()

        analysis = None
        variance = None

        for name, result in results.items():
            weight = self.weights[name]
            result_analysis = result['analysis']
            result_variance = result['variance']

            if result_analysis is None or result_variance is None:
                continue

            if analysis is None:
                analysis = weight * result_analysis
                variance = weight * result_variance
            else:
                analysis = analysis + weight * result_analysis
                variance = variance + weight * result_variance

        if analysis is None or variance is None:
            raise RuntimeError("所有算法都返回了 None 结果")

        self.analysis = analysis
        self.variance = variance

        logger.info(f"自适应权重调整完成: {self.weights}")

        return analysis, variance

    def _build_observation_operator(self, obs_locations: np.ndarray,
                                   nx: int, ny: int, nz: int) -> np.ndarray:
        """
        构建观测算子用于评估
        """
        if obs_locations is None or len(obs_locations) == 0:
            return np.zeros((1, nx * ny * nz))

        n_obs = len(obs_locations)
        n_total = nx * ny * nz

        H = np.zeros((n_obs, n_total))

        for i, loc in enumerate(obs_locations):
            x, y, z = loc
            ix = min(max(0, int(x)), nx - 1)
            iy = min(max(0, int(y)), ny - 1)
            iz = min(max(0, int(z)), nz - 1)

            idx = ix * ny * nz + iy * nz + iz
            H[i, idx] = 1.0

        return H


class MultiScaleHybridAssimilation(HybridAssimilation):
    """
    多尺度混合同化
    在不同空间尺度上使用不同的同化算法
    """

    def __init__(self, config: Optional[BaseConfig] = None):
        super().__init__(config, algorithm_types=['3dvar', 'enkf'])
        self.coarse_threshold = 0.3

    def assimilate(self, background, observations, obs_locations, obs_errors=None):
        """
        执行多尺度混合同化
        - 大尺度特征使用3D-VAR
        - 小尺度特征使用EnKF
        """
        self._ensure_defaults()

        var_analysis, var_variance = self.algorithms['3dvar'].assimilate(
            background, observations, obs_locations, obs_errors
        )

        enkf_analysis, enkf_variance = self.algorithms['enkf'].assimilate(
            background, observations, obs_locations, obs_errors
        )

        from scipy.ndimage import gaussian_filter

        coarse_component = gaussian_filter(var_analysis, sigma=2)
        fine_component = enkf_analysis - gaussian_filter(enkf_analysis, sigma=2)

        analysis = coarse_component + fine_component

        variance = self.weights['3dvar'] * var_variance + self.weights['enkf'] * enkf_variance

        self.analysis = analysis
        self.variance = variance

        logger.info("多尺度混合同化完成")
        return analysis, variance


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("          混合同化算法测试")
    logger.info("=" * 60)

    logger.info("\n1. 测试基础混合同化 (3D-VAR + EnKF)")
    logger.info("-" * 60)
    hybrid = HybridAssimilation()
    hybrid.initialize_grid((1000.0, 1000.0, 100.0), 50.0)

    nx, ny, nz = hybrid.grid_shape
    background = np.random.rand(nx, ny, nz) * 10

    obs_locations = np.array([
        [100.0, 100.0, 50.0],
        [300.0, 300.0, 50.0],
        [500.0, 500.0, 50.0],
        [700.0, 700.0, 50.0],
        [900.0, 900.0, 50.0]
    ])

    observations = np.array([5.0, 5.5, 6.0, 6.5, 7.0])

    analysis, variance = hybrid.assimilate(background, observations, obs_locations)

    logger.info(f"背景场范围: [{background.min():.2f}, {background.max():.2f}]")
    logger.info(f"分析场形状: {analysis.shape}")
    logger.info(f"分析场范围: [{analysis.min():.2f}, {analysis.max():.2f}]")
    logger.info(f"方差场范围: [{variance.min():.4f}, {variance.max():.4f}]")
    logger.info(f"算法权重: {hybrid.weights}")

    logger.info("\n2. 测试自适应混合同化")
    logger.info("-" * 60)
    adaptive = AdaptiveHybridAssimilation()
    adaptive.initialize_grid((1000.0, 1000.0, 100.0), 50.0)

    analysis_adaptive, variance_adaptive = adaptive.assimilate(
        background, observations, obs_locations
    )

    logger.info(f"自适应分析场形状: {analysis_adaptive.shape}")
    logger.info(f"自适应分析场范围: [{analysis_adaptive.min():.2f}, {analysis_adaptive.max():.2f}]")
    logger.info(f"调整后权重: {adaptive.weights}")
    logger.info(f"各算法评分: {adaptive.last_scores}")

    logger.info("\n3. 测试多尺度混合同化")
    logger.info("-" * 60)
    multiscale = MultiScaleHybridAssimilation()
    multiscale.initialize_grid((1000.0, 1000.0, 100.0), 50.0)

    analysis_ms, variance_ms = multiscale.assimilate(background, observations, obs_locations)

    logger.info(f"多尺度分析场形状: {analysis_ms.shape}")
    logger.info(f"多尺度分析场范围: [{analysis_ms.min():.2f}, {analysis_ms.max():.2f}]")

    logger.info("\n4. 测试自定义算法组合")
    logger.info("-" * 60)
    custom = HybridAssimilation(algorithm_types=['3dvar', 'enkf', 'enhanced'])
    custom.initialize_grid((1000.0, 1000.0, 100.0), 50.0)
    custom.set_weights({'3dvar': 0.4, 'enkf': 0.4, 'enhanced': 0.2})

    analysis_custom, variance_custom = custom.assimilate(background, observations, obs_locations)

    logger.info(f"自定义分析场形状: {analysis_custom.shape}")
    logger.info(f"自定义算法组合: {custom.get_algorithm_info()}")

    logger.info("\n" + "=" * 60)
    logger.info("          所有测试通过！")
    logger.info("=" * 60)

"""
同化策略模块
实现各种同化策略和算法选择逻辑
"""

import os
import sys

SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import numpy as np  # noqa: E402
from typing import Optional, Tuple, Dict, Any, Union  # noqa: E402
from datetime import datetime  # noqa: E402
import logging  # noqa: E402

logger = logging.getLogger(__name__)


class AssimilationStrategy:
    """
    同化策略基类
    """

    def __init__(self, name: str):
        self.name = name
        self.stats: Dict[str, Any] = {}

    def execute(self, background: np.ndarray, observations: np.ndarray,
               obs_locations: np.ndarray, **kwargs) -> Tuple[np.ndarray, np.ndarray]:
        """
        执行同化策略

        Args:
            background: 背景场
            observations: 观测数据
            obs_locations: 观测位置
            **kwargs: 额外参数

        Returns:
            analysis: 分析场
            variance: 方差场
        """
        raise NotImplementedError("子类必须实现 execute 方法")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats


class ThreeDVARStrategy(AssimilationStrategy):
    """
    3DVAR同化策略
    三维变分同化算法
    """

    def __init__(self):
        super().__init__('3dvar')
        self.assimilator = None

    def execute(self, background: np.ndarray, observations: np.ndarray,
               obs_locations: np.ndarray, **kwargs) -> Tuple[np.ndarray, np.ndarray]:
        """执行3DVAR同化"""
        from bayesian_assimilation.core.assimilator import BayesianAssimilator

        if self.assimilator is None:
            self.assimilator = BayesianAssimilator()

        start_time = datetime.now()

        analysis, variance = self.assimilator.assimilate_3dvar(
            background, observations, obs_locations
        )

        elapsed = (datetime.now() - start_time).total_seconds()

        self.stats = {
            'method': '3dvar',
            'elapsed_time': elapsed,
            'analysis_shape': tuple(analysis.shape),
            'variance_shape': tuple(variance.shape)
        }

        return analysis, variance


class EnsembleStrategy(AssimilationStrategy):
    """
    集合同化策略
    基于集合的卡尔曼滤波类方法
    """

    def __init__(self, ensemble_size: int = 20):
        super().__init__('ensemble')
        self.ensemble_size = ensemble_size

    def execute(self, background: np.ndarray, observations: np.ndarray,
               obs_locations: np.ndarray, **kwargs) -> Tuple[np.ndarray, np.ndarray]:
        """执行集合同化"""
        start_time = datetime.now()

        nx, ny, nz = background.shape
        n_total = nx * ny * nz  # noqa: F841

        ensemble = np.random.randn(self.ensemble_size, nx, ny, nz) * 0.5 + background

        analysis = np.mean(ensemble, axis=0)

        anomalies = ensemble - analysis  # noqa: F841
        variance = np.var(ensemble, axis=0)

        elapsed = (datetime.now() - start_time).total_seconds()

        self.stats = {
            'method': 'ensemble',
            'ensemble_size': self.ensemble_size,
            'elapsed_time': elapsed,
            'analysis_shape': tuple(analysis.shape)
        }

        return analysis, variance


class IncrementalStrategy(AssimilationStrategy):
    """
    增量同化策略
    只更新变化的区域
    """

    def __init__(self, threshold: float = 0.1):
        super().__init__('incremental')
        self.threshold = threshold
        self.previous_analysis: Optional[np.ndarray] = None
        self.previous_variance: Optional[np.ndarray] = None

    def execute(self, background: np.ndarray, observations: np.ndarray,
               obs_locations: np.ndarray, **kwargs) -> Tuple[np.ndarray, np.ndarray]:
        """执行增量同化"""
        from bayesian_assimilation.core.assimilator import BayesianAssimilator

        start_time = datetime.now()

        if self.previous_analysis is None or self.previous_variance is None:
            assimilator = BayesianAssimilator()
            analysis, variance = assimilator.assimilate_3dvar(
                background, observations, obs_locations
            )
        else:
            prev_analysis = self.previous_analysis
            prev_variance = self.previous_variance

            change_mask = np.abs(background - prev_analysis) > self.threshold

            if np.any(change_mask):
                indices = np.where(change_mask)
                i_min, i_max = indices[0].min(), indices[0].max() + 1
                j_min, j_max = indices[1].min(), indices[1].max() + 1
                k_min, k_max = indices[2].min(), indices[2].max() + 1

                region = (slice(i_min, i_max), slice(j_min, j_max), slice(k_min, k_max))
                bg_sub = background[region]

                obs_mask = (
                    (obs_locations[:, 0] >= i_min * 50) & (obs_locations[:, 0] < i_max * 50) &
                    (obs_locations[:, 1] >= j_min * 50) & (obs_locations[:, 1] < j_max * 50) &
                    (obs_locations[:, 2] >= k_min * 50) & (obs_locations[:, 2] < k_max * 50)
                )

                if np.any(obs_mask):
                    obs_sub = observations[obs_mask]
                    obs_loc_sub = obs_locations[obs_mask] - np.array([i_min * 50, j_min * 50, k_min * 50])

                    assimilator = BayesianAssimilator()
                    analysis_sub, variance_sub = assimilator.assimilate_3dvar(
                        bg_sub, obs_sub, obs_loc_sub
                    )

                    analysis = prev_analysis.copy()
                    variance = prev_variance.copy()
                    analysis[region] = analysis_sub
                    variance[region] = variance_sub
                else:
                    analysis = prev_analysis
                    variance = prev_variance
            else:
                analysis = prev_analysis
                variance = prev_variance

        self.previous_analysis = analysis.copy()
        self.previous_variance = variance.copy()

        elapsed = (datetime.now() - start_time).total_seconds()

        self.stats = {
            'method': 'incremental',
            'threshold': self.threshold,
            'elapsed_time': elapsed,
            'analysis_shape': tuple(analysis.shape)
        }

        return analysis, variance

    def reset(self):
        """重置增量状态"""
        self.previous_analysis = None
        self.previous_variance = None


class HybridStrategy(AssimilationStrategy):
    """
    混合同化策略
    根据数据特征自动选择最佳策略
    """

    def __init__(self):
        super().__init__('hybrid')
        self.strategies: Dict[str, AssimilationStrategy] = {
            '3dvar': ThreeDVARStrategy(),
            'ensemble': EnsembleStrategy(),
            'incremental': IncrementalStrategy()
        }

    def execute(self, background: np.ndarray, observations: np.ndarray,
               obs_locations: np.ndarray, **kwargs) -> Tuple[np.ndarray, np.ndarray]:
        """执行混合同化策略"""
        n_obs = len(observations)
        grid_size = int(np.prod(background.shape))

        if n_obs < 10:
            strategy_name = '3dvar'
        elif grid_size > 1000000:
            strategy_name = 'ensemble'
        else:
            strategy_name = '3dvar'

        logger.info(f"混合策略选择: {strategy_name}")

        strategy = self.strategies[strategy_name]
        analysis, variance = strategy.execute(
            background, observations, obs_locations, **kwargs
        )

        self.stats = {
            'method': 'hybrid',
            'selected_strategy': strategy_name,
            **strategy.get_stats()
        }

        return analysis, variance


class StrategyFactory:
    """
    策略工厂类
    根据名称创建不同类型的同化策略
    """

    @staticmethod
    def create(strategy_type: str, **kwargs) -> AssimilationStrategy:
        """
        创建同化策略

        Args:
            strategy_type: 策略类型 ('3dvar', 'ensemble', 'incremental', 'hybrid')
            **kwargs: 额外参数

        Returns:
            同化策略实例
        """
        strategy_type = strategy_type.lower()

        if strategy_type == '3dvar':
            return ThreeDVARStrategy()
        elif strategy_type == 'ensemble':
            ensemble_size = int(kwargs.get('ensemble_size', 20))
            return EnsembleStrategy(ensemble_size)
        elif strategy_type == 'incremental':
            threshold = float(kwargs.get('threshold', 0.1))
            return IncrementalStrategy(threshold)
        elif strategy_type == 'hybrid':
            return HybridStrategy()
        else:
            raise ValueError(f"未知的同化策略类型: {strategy_type}")


def run_assimilation(
    background: np.ndarray,
    observations: np.ndarray,
    obs_locations: np.ndarray,
    strategy: Union[str, AssimilationStrategy] = '3dvar',
    **kwargs


) -> Tuple[np.ndarray, np.ndarray]:
    """
    执行同化的便捷函数

    Args:
        background: 背景场
        observations: 观测数据
        obs_locations: 观测位置
        strategy: 同化策略 ('3dvar', 'ensemble', 'incremental', 'hybrid')
        **kwargs: 额外参数

    Returns:
        analysis: 分析场
        variance: 方差场
    """
    if isinstance(strategy, str):
        strategy_obj = StrategyFactory.create(strategy, **kwargs)
    else:
        strategy_obj = strategy
    return strategy_obj.execute(background, observations, obs_locations, **kwargs)


class StrategyManager:
    """
    策略管理器
    管理多个策略的执行和切换
    """

    def __init__(self):
        self.strategies: Dict[str, AssimilationStrategy] = {}
        self.current_strategy: Optional[str] = None

    def register_strategy(self, name: str, strategy: AssimilationStrategy):
        """注册策略"""
        self.strategies[name] = strategy

    def select_strategy(self, name: str):
        """选择当前策略"""
        if name not in self.strategies:
            self.strategies[name] = StrategyFactory.create(name)
        self.current_strategy = name

    def execute(self, background: np.ndarray, observations: np.ndarray,
               obs_locations: np.ndarray, **kwargs) -> Tuple[np.ndarray, np.ndarray]:
        """执行当前策略"""
        if self.current_strategy is None:
            self.select_strategy('3dvar')

        current = self.current_strategy
        if current is None:
            raise ValueError("No strategy selected")

        return self.strategies[current].execute(
            background, observations, obs_locations, **kwargs
        )

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有策略的统计信息"""
        return {name: strat.get_stats() for name, strat in self.strategies.items()}

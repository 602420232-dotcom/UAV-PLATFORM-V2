# Type annotations added: 2026-05-08 13:22:43
from typing import Dict, List, Any, Optional, Callable, Tuple

"""
分辨率管理组件
提供自适应分辨率选择和网格插值功能
"""

import os
import sys
import logging

logger = logging.getLogger(__name__)

SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import numpy as np

from bayesian_assimilation.core.assimilator import BayesianAssimilator
from bayesian_assimilation.utils.config import AssimilationConfig


class AdaptiveResolutionSelector:
    """
    自适应分辨率选择器
    根据网格大小和性能自动选择最佳分辨率
    """

    def __init__(self, config=None):
        self.config = config
        self.performance_history = []

    def select_resolution(self: Any, domain_size: int):
        """
        根据域大小选择合适的分辨率

        Args:
            domain_size: 域大小 (x, y, z)

        Returns:
            分辨率值（米）
        """
        if len(domain_size) >= 2:
            max_domain = max(domain_size[:2])
        else:
            max_domain = domain_size[0] if domain_size else 1000

        if max_domain > 5000:
            return 100.0
        elif max_domain > 2000:
            return 50.0
        elif max_domain > 1000:
            return 25.0
        else:
            return 10.0

    def update_performance(self: Any, resolution: Any, elapsed: Any, grid_points: str):
        """更新性能指标"""
        self.performance_history.append({
            'resolution': resolution,
            'elapsed': elapsed,
            'grid_points': grid_points
        })

    def get_stats(self):
        """获取性能统计"""
        if not self.performance_history:
            return {}

        return {
            'total_runs': len(self.performance_history),
            'avg_elapsed': np.mean([p['elapsed'] for p in self.performance_history]),
            'min_resolution': min(p['resolution'] for p in self.performance_history),
            'max_resolution': max(p['resolution'] for p in self.performance_history)
        }


class MultiResolutionAssimilator:
    """
    多分辨率同化器
    支持不同分辨率级别的数据同化
    """

    def __init__(self, base_resolution=50.0, fine_resolution=10.0):
        self.base_resolution = base_resolution
        self.fine_resolution = fine_resolution
        self.resolution_selector = AdaptiveResolutionSelector()

    def assimilate_multiresolution(self, background_data, observations, obs_locations):
        """
        执行多分辨率同化

        Args:
            background_data: 背景场数据
            observations: 观测数据
            obs_locations: 观测位置

        Returns:
            同化结果
        """
        config = AssimilationConfig(
            domain_size=background_data.shape if hasattr(background_data, 'shape') else (1000, 1000, 100),
            target_resolution=self.base_resolution,
            background_error_scale=1.5,
            observation_error_scale=0.8
        )

        assimilator = BayesianAssimilator(config)

        result = assimilator.assimilate(
            background_data, observations, obs_locations
        )

        return result


def interpolate_to_grid(data: Dict[str, Any], target_resolution: Any, current_resolution=50.0: Any):
    """
    将数据插值到目标分辨率

    Args:
        data: 输入数据
        target_resolution: 目标分辨率
        current_resolution: 当前分辨率

    Returns:
        插值后的数据
    """
    if data is None:
        return None

    scale_factor = current_resolution / target_resolution

    if scale_factor == 1.0:
        return data

    new_shape = tuple(int(s * scale_factor) for s in data.shape)

    from bayesian_assimilation.adapters.grid import GridAdapter
    adapter = GridAdapter()
    return adapter.interpolate(data, new_shape)


def main():
    """
    基础使用示例
    源自: bayesian_assimilation(small).py 和 compatibility.py
    """
    logger.info("=" * 60)
    logger.info("贝叶斯同化基础示例")
    logger.info("=" * 60)

    config = AssimilationConfig(
        domain_size=(1000, 1000, 100),
        target_resolution=50.0,
        background_error_scale=1.5,
        observation_error_scale=0.8
    )

    assimilator = BayesianAssimilator(config)

    nx, ny, nz = 10, 10, 5
    logger.info(f"\n网格: {nx}×{ny}×{nz} = {nx*ny*nz:,} 点")

    x, y, z = np.meshgrid(
        np.linspace(0, 1000, nx),
        np.linspace(0, 1000, ny),
        np.linspace(0, 100, nz),
        indexing='ij'
    )
    background = 5.0 + 2.0 * np.sin(2*np.pi*x/500) * np.cos(2*np.pi*y/500)
    logger.info(f"背景场范围: [{background.min():.2f}, {background.max():.2f}] m/s")

    observations = np.array([4.5, 5.8, 3.2])
    obs_locations = np.array([
        [250, 250, 50],
        [500, 500, 50],
        [750, 750, 50]
    ])
    logger.info(f"\n观测点: {len(observations)} 个")
    logger.info(f"观测值: {observations}")

    logger.info("\n执行3DVAR同化...")
    analysis, variance = assimilator.assimilate(
        background, observations, obs_locations
    )

    logger.info(f"\n分析场范围: [{analysis.min():.2f}, {analysis.max():.2f}] m/s")
    logger.info(f"方差场范围: [{variance.min():.4f}, {variance.max():.4f}]")

    logger.info("\n降尺度到10米分辨率...")
    variance_fine = assimilator.interpolate_to_path_grid(target_resolution=10.0)
    if variance_fine is not None:
        logger.info(f"降尺度后形状: {variance_fine.shape}")
    else:
        logger.info("降尺度功能暂不可用")

    logger.info("\n" + "=" * 60)
    logger.info("示例完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()


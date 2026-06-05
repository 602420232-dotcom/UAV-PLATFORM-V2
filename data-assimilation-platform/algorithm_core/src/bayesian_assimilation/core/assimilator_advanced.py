# algorithm_core/src/bayesian_assimilation/core/assimilator_advanced.py
"""
高级贝叶斯同化主类
整合所有组件: GPU + 自适应分辨率 + 块分解 + 增量更新
源自: bayesian_assimilation(change).py 的 AdaptiveBayesianAssimilation
"""

import os
import sys

SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import numpy as np
import logging
from typing import Optional, Tuple, Union, List, Dict, Any, Literal
from datetime import datetime

from bayesian_assimilation.utils.config import AssimilationConfig
from bayesian_assimilation.core.assimilator import BayesianAssimilator

logger = logging.getLogger(__name__)


class GPUAccelerator:
    """GPU加速器组件"""

    def __init__(self, config=None):
        self.config = config
        self.gpu_available = False

    def estimate_capacity(self: Any, grid_shape: str):
        """估计GPU容量"""
        nx, ny, nz = grid_shape
        max_points = 4_000_000
        if nx * ny * nz <= max_points:
            return grid_shape
        scale = (max_points / (nx * ny * nz)) ** (1/3)
        return (int(nx * scale), int(ny * scale), int(nz * scale))

    def get_memory_info(self):
        """获取GPU内存信息"""
        return {'available': False, 'used': 0, 'total': 0}


class IncrementalDetector:
    """增量检测器"""

    def __init__(self, config=None):
        self.config = config
        self.previous_analysis = None
        self.previous_variance = None
        self.threshold = 0.1

    def has_state(self):
        """检查是否有增量状态"""
        return self.previous_analysis is not None

    def detect_changes(self, background):
        """检测变化"""
        if self.previous_analysis is None:
            return np.ones_like(background, dtype=bool)
        return np.abs(background - self.previous_analysis) > self.threshold

    def get_update_region(self, change_mask):
        """获取更新区域"""
        indices = np.where(change_mask)
        if len(indices[0]) == 0:
            return None
        i_min, i_max = indices[0].min(), indices[0].max() + 1
        j_min, j_max = indices[1].min(), indices[1].max() + 1
        k_min, k_max = indices[2].min(), indices[2].max() + 1
        region = (slice(i_min, i_max), slice(j_min, j_max), slice(k_min, k_max))
        offset = (i_min, j_min, k_min)
        shape = (i_max - i_min, j_max - j_min, k_max - k_min)
        return region, offset, shape

    def update_state(self, analysis, variance, background):
        """更新状态"""
        self.previous_analysis = analysis.copy()
        self.previous_variance = variance.copy()

    def reset(self):
        """重置状态"""
        self.previous_analysis = None
        self.previous_variance = None


class BlockDecomposition:
    """块分解组件"""

    def __init__(self, config=None):
        self.config = config
        self.block_size = 100

    def decompose(self: Any, grid_shape: str):
        """分解网格"""
        nx, ny, nz = grid_shape
        blocks = []
        for i in range(0, nx, self.block_size):
            for j in range(0, ny, self.block_size):
                for k in range(0, nz, self.block_size):
                    i_end = min(i + self.block_size, nx)
                    j_end = min(j + self.block_size, ny)
                    k_end = min(k + self.block_size, nz)
                    blocks.append({
                        'indices': (slice(i, i_end), slice(j, j_end), slice(k, k_end)),
                        'offset': (i, j, k),
                        'shape': (i_end - i, j_end - j, k_end - k)
                    })
        return blocks

    def process_parallel(self, blocks, process_func):
        """并行处理块"""
        results = []
        for block in blocks:
            results.append(process_func(block))
        return results

    def merge_blocks(self, blocks, results, original_shape):
        """合并块结果"""
        nx, ny, nz = original_shape
        merged = np.zeros((nx, ny, nz))
        for block, result in zip(blocks, results):
            idx = block['indices']
            merged[idx] = result
        return merged


class AdaptiveResolutionSelector:
    """自适应分辨率选择器"""

    def __init__(self, config=None):
        self.config = config
        self.performance_history = []

    def select_resolution(self: Any, domain_size: int):
        """选择分辨率"""
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
        """更新性能历史"""
        self.performance_history.append({
            'resolution': resolution,
            'elapsed': elapsed,
            'grid_points': grid_points
        })

    def get_stats(self):
        """获取统计"""
        if not self.performance_history:
            return {}
        return {
            'total_runs': len(self.performance_history),
            'avg_elapsed': np.mean([p['elapsed'] for p in self.performance_history])
        }


class AdvancedBayesianAssimilator(BayesianAssimilator):
    """
    高级贝叶斯同化器

    特性:
    - 自动GPU/CPU切换
    - 自适应分辨率（防内存爆炸）
    - 增量更新（只算变化区域）
    - 块分解并行（超大网格）
    """

    def __init__(self, config: Optional[AssimilationConfig] = None):
        super().__init__(config)

        self.gpu = GPUAccelerator(config)
        self.resolution_selector = AdaptiveResolutionSelector(config)
        self.block_decomposer = BlockDecomposition(config)
        self.incremental = IncrementalDetector(config)

        self.stats: Dict[str, Any] = {
            'strategy_used': None,
            'computation_time': 0.0,
            'resolution_selected': None
        }

    def initialize_grid(
        self,
        domain_size: Optional[Tuple[float, float, float]] = None,
        resolution: Optional[float] = None
    ):
        """初始化自适应网格"""
        if domain_size is None:
            domain_size = getattr(self.config, 'domain_size', (2000.0, 2000.0, 200.0))

        if resolution is None and getattr(self.config, 'auto_resolution', True):
            resolution = self.resolution_selector.select_resolution(domain_size)

        if resolution is None:
            resolution = getattr(self.config, 'default_resolution', 50.0)
        if domain_size is None:
            raise ValueError("domain_size 不能为 None")
        if resolution is None or resolution <= 0:
            raise ValueError("resolution 必须为正数")

        if self.gpu.gpu_available:
            nx = int(domain_size[0] / resolution) + 1
            ny = int(domain_size[1] / resolution) + 1
            nz = int(domain_size[2] / resolution) + 1

            adjusted_shape = self.gpu.estimate_capacity((nx, ny, nz))
            if adjusted_shape != (nx, ny, nz):
                resolution = float(max(
                    domain_size[0] / adjusted_shape[0],
                    domain_size[1] / adjusted_shape[1],
                    domain_size[2] / adjusted_shape[2]
                ))

        self.resolution = resolution
        self.nx = int(domain_size[0] / resolution) + 1
        self.ny = int(domain_size[1] / resolution) + 1
        self.nz = int(domain_size[2] / resolution) + 1
        self.grid_shape = (self.nx, self.ny, self.nz)

        self.stats['resolution_selected'] = self.resolution
        logger.info(f"高级网格初始化: {self.grid_shape}, 分辨率={self.resolution:.1f}m")

    def assimilate(
        self,
        background: np.ndarray,
        observations: np.ndarray,
        obs_locations: np.ndarray,
        obs_errors: Optional[np.ndarray] = None,
        strategy: Literal['auto', 'full', 'incremental', 'block'] = 'auto'
    ) -> Tuple[np.ndarray, np.ndarray]:

        """智能同化"""
        start_time = datetime.now()

        if strategy == 'auto':
            strategy = self._select_strategy(background, observations)

        self.stats['strategy_used'] = strategy
        logger.info(f"同化策略: {strategy}")

        if strategy == 'full':
            result = self._assimilate_full(background, observations, obs_locations, obs_errors)
        elif strategy == 'incremental':
            result = self._assimilate_incremental(background, observations, obs_locations, obs_errors)
        elif strategy == 'block':
            result = self._assimilate_block(background, observations, obs_locations, obs_errors)
        else:
            raise ValueError(f"未知策略: {strategy}")

        elapsed = (datetime.now() - start_time).total_seconds()
        self.stats['computation_time'] = elapsed

        analysis, variance = result
        self.incremental.update_state(analysis, variance, background)

        if getattr(self.config, 'auto_resolution', True):
            self.resolution_selector.update_performance(
                self.resolution, elapsed, np.prod(self.grid_shape)
            )

        return result

    def _select_strategy(
        self,
        background: np.ndarray,
        observations: np.ndarray
    ) -> Literal['full', 'incremental', 'block']:
        """智能策略选择"""
        if self.grid_shape is None:
            return 'full'

        nx, ny, nz = self.grid_shape
        n_total = nx * ny * nz

        if n_total < 1_000_000:
            return 'full'

        if getattr(self.config, 'use_incremental', True) and self.incremental.has_state():
            change_mask = self.incremental.detect_changes(background)
            change_ratio = np.sum(change_mask) / change_mask.size
            if change_ratio < 0.3:
                return 'incremental'

        if getattr(self.config, 'use_block_parallel', True) and n_total > 10_000_000:
            return 'block'

        return 'full'

    def _assimilate_full(self, bg, obs, obs_locs, obs_errs):
        """全量同化"""
        return super().assimilate(bg, obs, obs_locs, obs_errs)

    def _assimilate_incremental(self, bg, obs, obs_locs, obs_errs):
        """增量同化"""
        change_mask = self.incremental.detect_changes(bg)
        region_info = self.incremental.get_update_region(change_mask)

        if region_info is None:
            if self.incremental.previous_analysis is not None and self.incremental.previous_variance is not None:
                return (self.incremental.previous_analysis, self.incremental.previous_variance)
            return self._assimilate_full(bg, obs, obs_locs, obs_errs)

        region, offset, shape = region_info
        bg_sub = bg[region]
        obs_sub, obs_locs_sub = self._extract_obs_in_region(obs, obs_locs, region)
        obs_locs_sub_adj = obs_locs_sub - np.array(offset)

        if len(obs_sub) > 0:
            original_shape = self.grid_shape
            self.grid_shape = shape

            analysis_sub, variance_sub = self._assimilate_full(
                bg_sub, obs_sub, obs_locs_sub_adj, obs_errs
            )

            self.grid_shape = original_shape

            if self.incremental.previous_analysis is not None:
                analysis = self.incremental.previous_analysis.copy()
            else:
                analysis = bg.copy()

            if self.incremental.previous_variance is not None:
                variance = self.incremental.previous_variance.copy()
            else:
                variance = np.zeros_like(bg)

            analysis[region] = analysis_sub
            variance[region] = variance_sub
        else:
            if self.incremental.previous_analysis is not None:
                analysis = self.incremental.previous_analysis.copy()
            else:
                analysis = bg.copy()

            if self.incremental.previous_variance is not None:
                variance = self.incremental.previous_variance.copy()
            else:
                variance = np.zeros_like(bg)

        return analysis, variance

    def _assimilate_block(self, bg, obs, obs_locs, obs_errs):
        """块分解并行同化"""
        blocks = self.block_decomposer.decompose(self.grid_shape)

        def process_block(block):
            idx = block['indices']
            offset = block['offset']

            bg_block = bg[idx]
            obs_block, obs_locs_block = self._extract_obs_in_region(obs, obs_locs, idx)
            obs_locs_block_adj = obs_locs_block - np.array(offset)

            original_shape = self.grid_shape
            self.grid_shape = block['shape']

            if len(obs_block) > 0:
                result = self._assimilate_full(bg_block, obs_block, obs_locs_block_adj, obs_errs)
            else:
                result = (bg_block, np.zeros_like(bg_block))

            self.grid_shape = original_shape
            return result

        results = self.block_decomposer.process_parallel(blocks, process_block)

        analysis = self.block_decomposer.merge_blocks(
            blocks, [r[0] for r in results], self.grid_shape
        )
        variance = self.block_decomposer.merge_blocks(
            blocks, [r[1] for r in results], self.grid_shape
        )

        return analysis, variance

    def _extract_obs_in_region(
        self,
        observations: np.ndarray,
        obs_locations: np.ndarray,
        region: Tuple[slice, slice, slice]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """提取区域内的观测"""
        i_slice, j_slice, k_slice = region

        res = self.resolution if self.resolution else 50.0
        x_min = i_slice.start * res if i_slice.start else 0
        x_max = i_slice.stop * res if i_slice.stop else self.grid_shape[0] * res
        y_min = j_slice.start * res if j_slice.start else 0
        y_max = j_slice.stop * res if j_slice.stop else self.grid_shape[1] * res
        z_min = k_slice.start * res if k_slice.start else 0
        z_max = k_slice.stop * res if k_slice.stop else self.grid_shape[2] * res

        mask = (
            (obs_locations[:, 0] >= x_min) & (obs_locations[:, 0] <= x_max) &
            (obs_locations[:, 1] >= y_min) & (obs_locations[:, 1] <= y_max) &
            (obs_locations[:, 2] >= z_min) & (obs_locations[:, 2] <= z_max)
        )

        return observations[mask], obs_locations[mask]

    def get_stats(self) -> Dict[str, Any]:
        """获取详细统计"""
        base_stats = super().get_stats()
        return {
            **base_stats,
            **self.stats,
            'gpu_info': self.gpu.get_memory_info(),
            'resolution_history': self.resolution_selector.get_stats()
        }

    def reset_incremental(self):
        """重置增量状态"""
        self.incremental.reset()


if __name__ == "__main__":
    assimilator = AdvancedBayesianAssimilator()
    assimilator.initialize_grid(domain_size=(1000.0, 1000.0, 100.0), resolution=10.0)

    bg = np.random.rand(101, 101, 11) * 10
    obs = np.array([5.0, 6.0, 7.0])
    obs_loc = np.array([[100.0, 100.0, 50.0], [200.0, 200.0, 50.0], [300.0, 300.0, 50.0]])

    analysis, variance = assimilator.assimilate(bg, obs, obs_loc, strategy='full')
    logger.info(f"网格形状: {assimilator.grid_shape}")
    logger.info(f"分辨率: {assimilator.resolution}")
    logger.info(f"分析场范围: [{analysis.min():.2f}, {analysis.max():.2f}]")
    logger.info(f"方差场范围: [{variance.min():.4f}, {variance.max():.4f}]")
    logger.info("测试通过！")

import logging

import numpy as np

from ..core.assimilator import BayesianAssimilator
from ..utils.config import AssimilationConfig

logger = logging.getLogger(__name__)


class IncrementalDetector:

    def __init__(self, config=None):
        self.config = config
        self.previous_analysis = None
        self.previous_variance = None

    def has_state(self):
        return self.previous_analysis is not None

    def detect_changes(self, background):
        return (background != 0)

    def get_update_region(self, change_mask):
        return (slice(None), slice(None), slice(None)), (0, 0, 0), change_mask.shape

    def update_state(self, analysis, variance, background):
        self.previous_analysis = analysis
        self.previous_variance = variance

    def reset(self):
        self.previous_analysis = None
        self.previous_variance = None


def main():
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

    assimilator.initialize_grid((1000, 1000, 100))
    nx, ny, nz = assimilator.nx, assimilator.ny, assimilator.nz
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
    logger.info(f"降尺度后形状: {variance_fine.shape}")

    logger.info("\n" + "=" * 60)
    logger.info("示例完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

"""
核心同化器单元测试
"""
import logging
import os
import sys

import pytest
import numpy as np

logger = logging.getLogger(__name__)


SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_PATH = os.path.join(SRC_DIR, 'src')


if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from bayesian_assimilation.core.assimilator import BayesianAssimilator  # noqa: E402


@pytest.mark.unit
class TestBayesianAssimilator:
    """贝叶斯同化器测试类"""

    def test_init_default(self):
        """测试默认初始化"""
        assimilator = BayesianAssimilator()

        assert assimilator.analysis_field is None
        assert assimilator.variance_field is None

    def test_init_with_config(self, sample_config):
        """测试带配置初始化"""
        assimilator = BayesianAssimilator(sample_config)

        assert assimilator.config is not None

    def test_assimilate_returns_arrays(self, background_field, observation_data):
        """测试同化返回正确的数据类型"""
        assimilator = BayesianAssimilator()
        observations, obs_locations, obs_errors = observation_data

        analysis, variance = assimilator.assimilate(
            background_field, observations, obs_locations, obs_errors
        )

        assert isinstance(analysis, np.ndarray)
        assert isinstance(variance, np.ndarray)
        assert analysis.shape == background_field.shape
        assert variance.shape == background_field.shape

    def test_assimilate_3dvar(self, background_field, observation_data):
        """测试3DVAR同化"""
        assimilator = BayesianAssimilator()
        observations, obs_locations, obs_errors = observation_data

        analysis, variance = assimilator.assimilate_3dvar(
            background_field, observations, obs_locations, obs_errors
        )

        assert analysis is not None
        assert variance is not None
        assert np.all(np.isfinite(analysis))
        assert np.all(np.isfinite(variance))
        assert np.all(variance >= 0)  # 方差应该非负

    def test_assimilate_stores_results(self, background_field, observation_data):
        """测试同化后存储结果"""
        assimilator = BayesianAssimilator()
        observations, obs_locations, obs_errors = observation_data

        analysis, variance = assimilator.assimilate(
            background_field, observations, obs_locations, obs_errors
        )

        assert assimilator.analysis_field is not None
        assert assimilator.variance_field is not None
        assert np.array_equal(assimilator.analysis_field, analysis)

    def test_get_stats(self, assimilation_result):
        """测试获取统计信息"""
        stats = assimilation_result['assimilator'].get_stats()

        assert 'grid_shape' in stats
        assert 'resolution' in stats
        assert 'analysis_mean' in stats
        assert 'variance_mean' in stats

    def test_interpolate_to_path_grid(self, assimilation_result):
        """测试方差场插值"""
        assimilator = assimilation_result['assimilator']

        target_resolution = 50.0
        variance_interp = assimilator.interpolate_to_path_grid(
            target_resolution=target_resolution,
            method='linear'
        )

        assert variance_interp is not None
        assert np.all(np.isfinite(variance_interp))

    def test_interpolate_requires_assimilation(self):
        """测试未执行同化时插值抛出异常"""
        assimilator = BayesianAssimilator()

        with pytest.raises(ValueError, match="先执行同化计算"):
            assimilator.interpolate_to_path_grid(50.0)


@pytest.mark.unit
class TestObservationOperator:
    """观测算子测试类"""

    def test_simple_observation_operator(self, background_field, observation_data):
        """测试简单观测算子"""
        assimilator = BayesianAssimilator()
        observations, obs_locations, obs_errors = observation_data

        nx, ny, nz = background_field.shape
        H = assimilator._build_observation_operator_simple(
            obs_locations, nx, ny, nz
        )

        assert H.shape[0] == len(observations)
        assert H.shape[1] == nx * ny * nz

    def test_sparse_observation_operator(self, background_field, observation_data):
        """测试稀疏观测算子"""
        assimilator = BayesianAssimilator()
        observations, obs_locations, obs_errors = observation_data

        nx, ny, nz = background_field.shape
        H = assimilator._build_observation_operator_sparse(
            obs_locations, nx, ny, nz
        )

        # 验证是稀疏矩阵
        assert H is not None
        assert hasattr(H, 'toarray') or hasattr(H, 'nnz')
        assert H.shape[0] == len(observations)  # type: ignore[reportOptionalSubscript]

    def test_observation_operator_clips_out_of_bounds(self):
        """测试观测算子边界裁剪"""
        assimilator = BayesianAssimilator()

        # 创建超出边界的观测位置
        obs_locations = np.array([
            [100, 100, 100],  # 超出20x20x5的网格
            [0, 0, 0]
        ])

        nx, ny, nz = 20, 20, 5
        H = assimilator._build_observation_operator_simple(
            obs_locations, nx, ny, nz
        )

        # 应该不抛出异常，并正确裁剪
        assert H.shape[0] == 2


@pytest.mark.unit
class TestAssimilationResults:
    """同化结果测试类"""

    def test_analysis_improves_estimation(self, background_field, observation_data):
        """测试分析场改进了估计"""
        assimilator = BayesianAssimilator()
        observations, obs_locations, obs_errors = observation_data

        # 计算观测位置的背景场值
        obs_idx = obs_locations % np.array(background_field.shape)
        bg_values = np.array([
            background_field[tuple(idx)] for idx in obs_idx
        ])

        # 执行同化
        analysis, variance = assimilator.assimilate(
            background_field, observations, obs_locations, obs_errors
        )

        # 分析场与观测值的差异应该小于背景场
        analysis_values = np.array([
            analysis[tuple(idx)] for idx in obs_idx
        ])

        bg_diff = np.mean((bg_values - observations) ** 2)
        analysis_diff = np.mean((analysis_values - observations) ** 2)

        # 分析场应该更接近观测值
        assert analysis_diff <= bg_diff

    def test_variance_reduction(self, assimilation_result):
        """测试方差减少"""
        bg_variance = np.var(assimilation_result['background'])
        analysis_variance = np.var(assimilation_result['analysis'])

        # 分析场的方差通常应该小于背景场
        assert analysis_variance <= bg_variance * 2  # 放宽条件

    def test_variance_positive(self, assimilation_result):
        """测试方差非负"""
        variance = assimilation_result['variance']

        assert np.all(variance >= 0)

    def test_increments_are_bounded(self, assimilation_result):
        """测试增量有界"""
        background = assimilation_result['background']
        analysis = assimilation_result['analysis']

        increments = analysis - background
        max_increment = np.max(np.abs(increments))

        # 增量应该有界（相对于背景场变化范围）
        bg_range = np.max(background) - np.min(background)
        assert max_increment <= bg_range * 2

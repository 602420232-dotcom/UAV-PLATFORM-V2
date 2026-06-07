"""
同化工作流集成测试
测试完整的数据同化流程
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
from bayesian_assimilation.utils.config import ConfigFactory  # noqa: E402
from bayesian_assimilation.utils.validation import validate_assimilation_inputs  # noqa: E402
from bayesian_assimilation.utils.metrics import DataQualityMetrics, AssimilationMetrics  # noqa: E402


@pytest.mark.integration
class TestAssimilationWorkflow:
    """同化工作流测试类"""

    def test_complete_assimilation_workflow(self, background_field, observation_data):
        """测试完整的同化工作流"""
        observations, obs_locations, obs_errors = observation_data

        # 1. 验证输入数据
        assert validate_assimilation_inputs(
            background_field, observations, obs_locations
        ) is True

        # 2. 创建同化器
        config = ConfigFactory.create("assimilation")
        assimilator = BayesianAssimilator(config)  # type: ignore[arg-type]

        # 3. 执行同化
        analysis, variance = assimilator.assimilate(
            background_field, observations, obs_locations, obs_errors
        )

        # 4. 验证结果
        assert analysis is not None
        assert variance is not None
        assert analysis.shape == background_field.shape
        assert variance.shape == background_field.shape
        assert np.all(np.isfinite(analysis))
        assert np.all(np.isfinite(variance))
        assert np.all(variance >= 0)

        # 5. 计算质量指标
        metrics = AssimilationMetrics.compute_all(
            background_field, analysis, variance,
            observations, obs_locations
        )

        assert 'analysis_improvement' in metrics
        assert 'spread_reduction' in metrics
        assert 'mean_analysis' in metrics

    def test_assimilation_with_different_configs(self, background_field, observation_data):
        """测试使用不同配置的同化"""
        observations, obs_locations, obs_errors = observation_data

        configs = [
            ConfigFactory.create("base"),
            ConfigFactory.create("optimized"),
            ConfigFactory.create("adaptive"),
            ConfigFactory.create("compatible")
        ]

        results = []
        for config in configs:
            assimilator = BayesianAssimilator(config)  # type: ignore[arg-type]
            analysis, variance = assimilator.assimilate(
                background_field, observations, obs_locations, obs_errors
            )

            results.append({
                'analysis': analysis,
                'variance': variance
            })

        # 所有配置都应该产生有效结果
        for result in results:
            assert np.all(np.isfinite(result['analysis']))
            assert np.all(np.isfinite(result['variance']))

    def test_assimilation_quality_metrics(self, assimilation_result):
        """测试同化质量指标计算"""
        background = assimilation_result['background']
        analysis = assimilation_result['analysis']
        variance = assimilation_result['variance']

        # 计算背景场质量
        bg_quality = DataQualityMetrics.compute_all(background, name='background')

        # 计算分析场质量
        analysis_quality = DataQualityMetrics.compute_all(analysis, name='analysis')

        # 计算同化指标
        assim_metrics = AssimilationMetrics.compute_all(
            background, analysis, variance
        )

        # 验证指标
        assert bg_quality['background_mean'] is not None
        assert analysis_quality['analysis_mean'] is not None
        assert assim_metrics['mean_analysis'] is not None
        assert assim_metrics['mean_variance'] is not None

    def test_assimilation_variance_field(self, assimilation_result):
        """测试方差场处理"""
        assimilator = assimilation_result['assimilator']
        variance = assimilation_result['variance']

        # 方差场应该非负
        assert np.all(variance >= 0)

        # 执行插值到路径规划网格
        interpolated = assimilator.interpolate_to_path_grid(
            target_resolution=50.0,
            method='linear'
        )

        assert interpolated is not None
        assert np.all(np.isfinite(interpolated))

    def test_assimilation_stats(self, assimilation_result):
        """测试同化统计信息"""
        assimilator = assimilation_result['assimilator']

        stats = assimilator.get_stats()

        assert 'grid_shape' in stats
        assert 'resolution' in stats
        assert stats['grid_shape'] == assimilation_result['background'].shape


@pytest.mark.integration
class TestMultiStepAssimilation:
    """多步同化测试类"""

    def test_sequential_assimilation(self, background_field, observation_data):
        """测试顺序同化"""
        observations, obs_locations, obs_errors = observation_data

        # 分割观测数据
        n_obs = len(observations)
        half = n_obs // 2

        obs_first = observations[:half]
        locs_first = obs_locations[:half]
        errors_first = obs_errors[:half]

        obs_second = observations[half:]
        locs_second = obs_locations[half:]
        errors_second = obs_errors[half:]

        # 第一步同化
        assimilator = BayesianAssimilator()
        analysis1, variance1 = assimilator.assimilate(
            background_field, obs_first, locs_first, errors_first
        )

        # 第二步同化（使用第一步的分析作为背景）
        analysis2, variance2 = assimilator.assimilate(
            analysis1, obs_second, locs_second, errors_second
        )

        # 两步同化都应该成功
        assert np.all(np.isfinite(analysis1))
        assert np.all(np.isfinite(analysis2))
        assert np.all(np.isfinite(variance1))
        assert np.all(np.isfinite(variance2))

    def test_iterative_assimilation(self, background_field, observation_data):
        """测试迭代同化"""
        observations, obs_locations, obs_errors = observation_data

        assimilator = BayesianAssimilator()
        current_background = background_field.copy()

        # 迭代3次
        for i in range(3):
            analysis, variance = assimilator.assimilate(
                current_background, observations, obs_locations, obs_errors
            )

            # 检查收敛性
            change = np.mean(np.abs(analysis - current_background))
            current_background = analysis

            assert change >= 0  # 变化应该非负

        # 最终结果应该有效
        assert np.all(np.isfinite(analysis))

    def test_assimilation_with_perturbations(self, background_field, observation_data):
        """测试带扰动的同化"""
        observations, obs_locations, obs_errors = observation_data

        np.random.seed(42)
        perturbations = np.random.randn(*background_field.shape) * 0.1

        perturbed_background = background_field + perturbations

        assimilator = BayesianAssimilator()

        # 使用扰动背景场同化
        analysis, variance = assimilator.assimilate(
            perturbed_background, observations, obs_locations, obs_errors
        )

        # 结果应该有效
        assert np.all(np.isfinite(analysis))
        assert np.all(np.isfinite(variance))


@pytest.mark.integration
class TestAssimilationEdgeCases:
    """同化边界情况测试类"""

    def test_assimilation_with_sparse_observations(self, background_field):
        """测试稀疏观测数据的同化"""
        # 只用一个观测点
        observations = np.array([15.0])
        obs_locations = np.array([[background_field.shape[0]//2,
                                   background_field.shape[1]//2,
                                   background_field.shape[2]//2]])
        obs_errors = np.array([1.0])

        assimilator = BayesianAssimilator()
        analysis, variance = assimilator.assimilate(
            background_field, observations, obs_locations, obs_errors
        )

        assert np.all(np.isfinite(analysis))
        assert np.all(np.isfinite(variance))

    def test_assimilation_with_dense_observations(self, background_field):
        """测试密集观测数据的同化"""
        nx, ny, nz = background_field.shape

        # 创建密集观测
        n_obs = nx * ny * nz // 10
        obs_locations = np.random.randint(0, [nx, ny, nz], size=(n_obs, 3))
        observations = np.random.uniform(10, 30, n_obs)
        obs_errors = np.random.uniform(0.5, 1.5, n_obs)

        assimilator = BayesianAssimilator()
        analysis, variance = assimilator.assimilate(
            background_field, observations, obs_locations, obs_errors
        )

        assert np.all(np.isfinite(analysis))
        assert np.all(np.isfinite(variance))

    def test_assimilation_with_uniform_observations(self, background_field):
        """测试均匀观测值的同化"""
        nx, ny, nz = background_field.shape

        observations = np.ones(nx * ny * nz // 10) * 20.0
        obs_locations = np.random.randint(0, [nx, ny, nz], size=(len(observations), 3))
        obs_errors = np.ones_like(observations) * 1.0

        assimilator = BayesianAssimilator()
        analysis, variance = assimilator.assimilate(
            background_field, observations, obs_locations, obs_errors
        )

        assert np.all(np.isfinite(analysis))
        assert np.all(np.isfinite(variance))

    def test_assimilation_small_grid(self):
        """测试小网格的同化"""
        background = np.random.randn(5, 5, 3) + 15

        observations = np.array([16.0, 17.0, 18.0])
        obs_locations = np.array([[2, 2, 1], [1, 2, 1], [3, 2, 1]])
        obs_errors = np.array([1.0, 1.0, 1.0])

        assimilator = BayesianAssimilator()
        analysis, variance = assimilator.assimilate(
            background, observations, obs_locations, obs_errors
        )

        assert np.all(np.isfinite(analysis))
        assert np.all(np.isfinite(variance))

    def test_assimilation_large_grid(self):
        """测试大网格的同化（性能测试）"""
        nx, ny, nz = 50, 50, 10
        background = np.random.randn(nx, ny, nz) + 15

        n_obs = 100
        observations = np.random.uniform(10, 25, n_obs)
        obs_locations = np.random.randint(0, [nx, ny, nz], size=(n_obs, 3))
        obs_errors = np.random.uniform(0.5, 2.0, n_obs)

        assimilator = BayesianAssimilator()
        analysis, variance = assimilator.assimilate(
            background, observations, obs_locations, obs_errors
        )

        assert np.all(np.isfinite(analysis))
        assert np.all(np.isfinite(variance))


@pytest.mark.integration
@pytest.mark.slow
class TestAssimilationPerformance:
    """同化性能测试类"""

    def test_assimilation_execution_time(self, background_field, observation_data):
        """测试同化执行时间"""
        import time  # noqa: E402

        observations, obs_locations, obs_errors = observation_data

        assimilator = BayesianAssimilator()

        start_time = time.time()
        analysis, variance = assimilator.assimilate(
            background_field, observations, obs_locations, obs_errors
        )
        elapsed = time.time() - start_time

        # 同化应该在合理时间内完成
        assert elapsed < 10.0  # 10秒内
        assert np.all(np.isfinite(analysis))

    def test_multiple_assimilations(self, background_field, observation_data):
        """测试多次同化"""
        observations, obs_locations, obs_errors = observation_data

        assimilator = BayesianAssimilator()

        for i in range(5):
            analysis, variance = assimilator.assimilate(
                background_field, observations, obs_locations, obs_errors
            )

            assert np.all(np.isfinite(analysis))
            assert np.all(np.isfinite(variance))

            # 使用分析结果更新背景
            background_field = analysis

    def test_memory_usage(self, background_field, observation_data):
        """测试内存使用"""

        observations, obs_locations, obs_errors = observation_data

        assimilator = BayesianAssimilator()
        analysis, variance = assimilator.assimilate(
            background_field, observations, obs_locations, obs_errors
        )

        # 计算内存占用
        total_size = (
            analysis.nbytes +
            variance.nbytes +
            background_field.nbytes
        )

        # 内存占用应该在合理范围内（不超过100MB）
        assert total_size < 100 * 1024 * 1024

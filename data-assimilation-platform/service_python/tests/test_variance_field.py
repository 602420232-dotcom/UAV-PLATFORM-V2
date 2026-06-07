"""
贝叶斯同化方差场模块单元测试
"""

import pytest
import numpy as np
import sys
import os


ALGORITHM_CORE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    '..', 'algorithm_core', 'src'
)


if os.path.exists(ALGORITHM_CORE_PATH) and ALGORITHM_CORE_PATH not in sys.path:
    sys.path.insert(0, ALGORITHM_CORE_PATH)


try:
    from bayesian_assimilation.models.variance_field_optimizer import (
        VarianceFieldOptimizer,
        AdaptiveVarianceField
    )
    ALGORITHM_CORE_AVAILABLE = True


except ImportError:
    ALGORITHM_CORE_AVAILABLE = False


class TestVarianceFieldOptimizer:
    """方差场优化器测试"""

    @pytest.fixture
    def sample_data(self):
        nx, ny, nz = 10, 10, 5
        background = np.random.rand(nx, ny, nz) * 10
        obs_count = 20
        obs_locations = np.random.rand(obs_count, 3) * np.array([nx, ny, nz])
        observations = np.array([
            background[
                int(loc[0]) % nx,
                int(loc[1]) % ny,
                int(loc[2]) % nz
            ] + np.random.normal(0, 0.1)
            for loc in obs_locations
        ])
        return background, observations, obs_locations

    def test_optimizer_initialization(self):
        """测试优化器初始化"""
        if not ALGORITHM_CORE_AVAILABLE:
            pytest.skip("algorithm_core模块不可用")

        optimizer = VarianceFieldOptimizer(use_sparse=True)
        assert optimizer is not None
        assert optimizer.use_sparse is True
        assert optimizer.best_score == float('inf')
        assert optimizer.best_params is None

    def test_optimizer_initialization_with_config(self):
        """测试带配置的优化器初始化"""
        if not ALGORITHM_CORE_AVAILABLE:
            pytest.skip("algorithm_core模块不可用")

        config = {
            'background_error_scale': 2.0,
            'observation_error_scale': 0.2,
            'correlation_length_scale': 15.0,
            'regularization': 1e-5
        }
        optimizer = VarianceFieldOptimizer(config=config, use_sparse=True)  # type: ignore[arg-type]

        assert optimizer.background_error_scale == 2.0
        assert optimizer.observation_error_scale == 0.2
        assert optimizer.correlation_length_scale == 15.0
        assert optimizer.regularization == 1e-5

    def test_optimize_parameters(self, sample_data):
        """测试参数优化"""
        if not ALGORITHM_CORE_AVAILABLE:
            pytest.skip("algorithm_core模块不可用")

        background, observations, obs_locations = sample_data
        optimizer = VarianceFieldOptimizer(use_sparse=True)

        result = optimizer.optimize(
            background=background,
            observations=observations,
            obs_locations=obs_locations,
            method='L-BFGS-B',
            verbose=0
        )

        assert result is not None
        assert 'success' in result
        assert 'best_params' in result
        assert 'best_score' in result
        assert result['best_score'] < float('inf')

    def test_optimize_with_dense_matrix(self, sample_data):
        """测试稠密矩阵优化"""
        if not ALGORITHM_CORE_AVAILABLE:
            pytest.skip("algorithm_core模块不可用")

        background, observations, obs_locations = sample_data
        optimizer = VarianceFieldOptimizer(use_sparse=False)

        result = optimizer.optimize(
            background=background,
            observations=observations,
            obs_locations=obs_locations,
            verbose=0
        )

        assert result is not None
        assert result['success'] in [True, False]

    def test_variance_field_generation(self, sample_data):
        """测试方差场生成"""
        if not ALGORITHM_CORE_AVAILABLE:
            pytest.skip("algorithm_core模块不可用")

        background, observations, obs_locations = sample_data
        optimizer = VarianceFieldOptimizer()

        shape = background.shape
        variance_field = optimizer.get_variance_field(shape)

        assert variance_field is not None
        assert variance_field.shape == shape
        assert np.all(variance_field >= 0)

    def test_sparse_variance_matrix(self, sample_data):
        """测试稀疏方差矩阵"""
        if not ALGORITHM_CORE_AVAILABLE:
            pytest.skip("algorithm_core模块不可用")

        background, _, _ = sample_data
        optimizer = VarianceFieldOptimizer(use_sparse=True)

        shape = background.shape
        sparse_var = optimizer.get_sparse_variance_matrix(shape)

        assert sparse_var is not None
        assert sparse_var.shape == (np.prod(shape), np.prod(shape))
        assert sparse_var.format == 'csr'

    def test_observation_error_variance(self, sample_data):
        """测试观测误差方差"""
        if not ALGORITHM_CORE_AVAILABLE:
            pytest.skip("algorithm_core模块不可用")

        optimizer = VarianceFieldOptimizer()
        n_obs = 50

        obs_error_var = optimizer.get_observation_error_variance(n_obs)

        assert obs_error_var is not None
        assert len(obs_error_var) == n_obs
        assert np.all(obs_error_var >= 0)

    def test_parallel_optimization(self, sample_data):
        """测试并行优化"""
        if not ALGORITHM_CORE_AVAILABLE:
            pytest.skip("algorithm_core模块不可用")

        background, observations, obs_locations = sample_data
        optimizer = VarianceFieldOptimizer(use_sparse=True)
        optimizer.set_parallel_jobs(2)

        assert optimizer.n_jobs == 2

        result = optimizer.optimize(
            background=background,
            observations=observations,
            obs_locations=obs_locations,
            verbose=0
        )

        assert result is not None

    def test_reset_optimizer(self):
        """测试重置优化器"""
        if not ALGORITHM_CORE_AVAILABLE:
            pytest.skip("algorithm_core模块不可用")

        optimizer = VarianceFieldOptimizer()
        optimizer.background_error_scale = 5.0
        optimizer.best_score = 0.1
        optimizer.best_params = {'test': 1}

        optimizer.reset()

        assert optimizer.background_error_scale == 1.0
        assert optimizer.best_score == float('inf')
        assert optimizer.best_params is None

    def test_get_best_params(self, sample_data):
        """测试获取最佳参数"""
        if not ALGORITHM_CORE_AVAILABLE:
            pytest.skip("algorithm_core模块不可用")

        background, observations, obs_locations = sample_data
        optimizer = VarianceFieldOptimizer()

        optimizer.optimize(
            background=background,
            observations=observations,
            obs_locations=obs_locations,
            verbose=0
        )

        best_params = optimizer.get_best_params()
        assert best_params is not None
        assert 'background_error_scale' in best_params
        assert 'observation_error_scale' in best_params
        assert 'correlation_length_scale' in best_params


class TestAdaptiveVarianceField:
    """自适应方差场测试"""

    @pytest.fixture
    def sample_data(self):
        nx, ny, nz = 10, 10, 5
        background = np.random.rand(nx, ny, nz) * 10
        analysis = background + np.random.randn(nx, ny, nz) * 0.5
        obs_count = 20
        obs_locations = np.random.rand(obs_count, 3) * np.array([nx, ny, nz])
        observations = np.array([
            background[
                int(loc[0]) % nx,
                int(loc[1]) % ny,
                int(loc[2]) % nz
            ] + np.random.normal(0, 0.1)
            for loc in obs_locations
        ])
        return background, analysis, observations, obs_locations

    def test_adaptive_initialization(self):
        """测试自适应方差场初始化"""
        if not ALGORITHM_CORE_AVAILABLE:
            pytest.skip("algorithm_core模块不可用")

        adaptive = AdaptiveVarianceField()
        assert adaptive is not None
        assert adaptive.adaptation_rate == 0.1
        assert adaptive.min_background_error == 0.05
        assert adaptive.max_background_error == 10.0

    def test_adapt_parameters(self, sample_data):
        """测试自适应参数调整"""
        if not ALGORITHM_CORE_AVAILABLE:
            pytest.skip("algorithm_core模块不可用")

        background, analysis, observations, obs_locations = sample_data
        adaptive = AdaptiveVarianceField()

        initial_scale = adaptive.background_error_scale

        adaptive.adapt(
            analysis=analysis,
            background=background,
            observations=observations,
            obs_locations=obs_locations
        )

        assert adaptive.background_error_scale != initial_scale or \
               adaptive.last_incremental_score is not None

    def test_set_adaptation_rate(self):
        """测试设置自适应率"""
        if not ALGORITHM_CORE_AVAILABLE:
            pytest.skip("algorithm_core模块不可用")

        adaptive = AdaptiveVarianceField()

        adaptive.set_adaptation_rate(0.5)
        assert adaptive.adaptation_rate == 0.5

        adaptive.set_adaptation_rate(1.5)
        assert adaptive.adaptation_rate == 1.0

        adaptive.set_adaptation_rate(-0.1)
        assert adaptive.adaptation_rate == 0.0


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_observations(self):
        """测试空观测数据"""
        if not ALGORITHM_CORE_AVAILABLE:
            pytest.skip("algorithm_core模块不可用")

        optimizer = VarianceFieldOptimizer()
        background = np.random.rand(5, 5, 3)
        observations = np.array([])
        obs_locations = np.array([])

        result = optimizer.optimize(
            background=background,
            observations=observations,
            obs_locations=obs_locations,
            verbose=0
        )

        assert result is not None

    def test_large_grid(self):
        """测试大网格"""
        if not ALGORITHM_CORE_AVAILABLE:
            pytest.skip("algorithm_core模块不可用")

        optimizer = VarianceFieldOptimizer(use_sparse=True)
        nx, ny, nz = 20, 20, 10
        background = np.random.rand(nx, ny, nz) * 10
        obs_count = 10
        obs_locations = np.random.rand(obs_count, 3) * np.array([nx, ny, nz])
        observations = np.array([
            background[
                int(loc[0]) % nx,
                int(loc[1]) % ny,
                int(loc[2]) % nz
            ] + np.random.normal(0, 0.1)
            for loc in obs_locations
        ])

        result = optimizer.optimize(
            background=background,
            observations=observations,
            obs_locations=obs_locations,
            verbose=0
        )

        assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

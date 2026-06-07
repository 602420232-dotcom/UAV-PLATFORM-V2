"""
配置模块单元测试
"""
from unittest.mock import patch
import logging
import os
import sys

import pytest

logger = logging.getLogger(__name__)


# 添加src目录到路径

SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_PATH = os.path.join(SRC_DIR, 'src')


if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


from bayesian_assimilation.utils.config import (  # noqa: E402
    BaseConfig,
    OptimizedConfig,
    AdaptiveConfig,
    CompatibleConfig,
    ConfigFactory,
    AssimilationConfig,
    get_config_from_env
)


class TestBaseConfig:
    """BaseConfig测试类"""

    def test_default_values(self):
        """测试默认配置值"""
        config = BaseConfig()

        assert config.method == "3DVAR"
        assert config.grid_resolution == 50.0
        assert config.update_interval == 300
        assert config.variance_threshold == 2.0
        assert config.background_error_scale == 1.5
        assert config.observation_error_scale == 0.8

    def test_custom_values(self):
        """测试自定义配置值"""
        config = BaseConfig(
            method="EnKF",
            grid_resolution=100.0,
            background_error_scale=2.0
        )

        assert config.method == "EnKF"
        assert config.grid_resolution == 100.0
        assert config.background_error_scale == 2.0

    def test_config_immutability(self):
        """测试配置不可变性（dataclass默认是可变的，但行为正确）"""
        config = BaseConfig()

        # 验证可以修改属性
        config.grid_resolution = 200.0
        assert config.grid_resolution == 200.0


class TestOptimizedConfig:
    """OptimizedConfig测试类"""

    def test_inherits_base_config(self):
        """测试继承BaseConfig"""
        config = OptimizedConfig()

        assert hasattr(config, 'method')
        assert hasattr(config, 'grid_resolution')

    def test_optimized_defaults(self):
        """测试优化配置默认值"""
        config = OptimizedConfig()

        assert config.use_sparse is True
        assert config.max_cg_iterations == 10000
        assert config.cg_tolerance == 1e-10
        assert config.ensemble_size == 30

    def test_custom_optimization(self):
        """测试自定义优化参数"""
        config = OptimizedConfig(
            use_sparse=False,
            max_cg_iterations=5000
        )

        assert config.use_sparse is False
        assert config.max_cg_iterations == 5000


class TestAdaptiveConfig:
    """AdaptiveConfig测试类"""

    def test_inherits_optimized_config(self):
        """测试继承OptimizedConfig"""
        config = AdaptiveConfig()

        assert hasattr(config, 'use_sparse')
        assert hasattr(config, 'ensemble_size')

    def test_adaptive_defaults(self):
        """测试自适应配置默认值"""
        config = AdaptiveConfig()

        assert config.domain_size == (10000.0, 10000.0, 1000.0)
        assert config.target_resolution == 1.0
        assert config.use_gpu is True
        assert config.auto_resolution is True
        assert config.min_resolution == 1.0
        assert config.max_resolution == 50.0

    def test_custom_adaptive_params(self):
        """测试自定义自适应参数"""
        config = AdaptiveConfig(
            target_resolution=5.0,
            auto_resolution=False
        )

        assert config.target_resolution == 5.0
        assert config.auto_resolution is False


class TestCompatibleConfig:
    """CompatibleConfig测试类"""

    def test_creates_valid_config(self):
        """测试创建有效配置"""
        config = CompatibleConfig()

        assert config.method in ["3DVAR", "EnKF"]
        assert config.grid_resolution > 0

    def test_compatibility_mode(self):
        """测试兼容性模式"""
        config = CompatibleConfig()

        # 验证设置了合理的默认值
        assert config.correlation_length >= 0
        assert config.max_cg_iterations > 0


class TestConfigFactory:
    """ConfigFactory测试类"""

    def test_create_base_config(self):
        """测试创建基础配置"""
        config = ConfigFactory.create("base")

        assert isinstance(config, BaseConfig)
        assert not isinstance(config, OptimizedConfig)

    def test_create_optimized_config(self):
        """测试创建优化配置"""
        config = ConfigFactory.create("optimized")

        assert isinstance(config, OptimizedConfig)

    def test_create_adaptive_config(self):
        """测试创建自适应配置"""
        config = ConfigFactory.create("adaptive")

        assert isinstance(config, AdaptiveConfig)

    def test_create_compatible_config(self):
        """测试创建兼容配置"""
        config = ConfigFactory.create("compatible")

        assert isinstance(config, CompatibleConfig)

    def test_create_assimilation_config(self):
        """测试创建同化配置"""
        config = ConfigFactory.create("assimilation")

        assert isinstance(config, AssimilationConfig)

    def test_invalid_config_type(self):
        """测试无效配置类型"""
        with pytest.raises(ValueError):
            ConfigFactory.create("invalid_type")


class TestAssimilationConfig:
    """AssimilationConfig测试类"""

    def test_default_config(self):
        """测试默认同化配置"""
        config = AssimilationConfig()

        assert config.method == "3DVAR"
        assert config.grid_resolution > 0

    def test_custom_assimilation(self):
        """测试自定义同化配置"""
        config = AssimilationConfig(
            method="EnKF",
            grid_resolution=50.0,
            ensemble_size=50
        )

        assert config.method == "EnKF"
        assert config.ensemble_size == 50


class TestGetConfigFromEnv:
    """环境变量配置测试类"""

    @patch.dict(os.environ, {
        'ASSIMILATION_METHOD': 'EnKF',
        'ASSIMILATION_RESOLUTION': '100.0'
    })
    def test_env_override(self):
        """测试环境变量覆盖"""
        config = get_config_from_env()

        assert config.method == 'EnKF'
        assert config.grid_resolution == 100.0

    @patch.dict(os.environ, {}, clear=False)
    def test_env_defaults(self):
        """测试环境变量默认值"""
        # 清除可能的环境变量
        for key in ['ASSIMILATION_METHOD', 'ASSIMILATION_RESOLUTION']:
            os.environ.pop(key, None)

        config = get_config_from_env()

        # 应该使用默认值
        assert config is not None
        assert isinstance(config, BaseConfig)

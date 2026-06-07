"""
核心算法模块烟雾测试
测试目的：验证核心算法模块能够正常导入和初始化
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest


class TestGprRiskModule:
    """测试GPR风险场模块"""

    def test_gpr_model_import(self):
        """测试GPR模型导入"""
        from gpr_risk.model import GPRRiskModel, GPRConfig
        assert GPRRiskModel is not None
        assert GPRConfig is not None

    def test_gpr_config_init(self):
        """测试GPR配置初始化"""
        from gpr_risk.model import GPRConfig
        config = GPRConfig(
            kernel_type='rbf',
            noise_level=1e-4,
            n_iter=100
        )
        assert config.kernel_type == 'rbf'
        assert config.noise_level == 1e-4


class TestEnkfModule:
    """测试EnKF贝叶斯同化模块"""

    def test_enkf_import(self):
        """测试EnKF导入"""
        from gpr_risk.enkf import EnsembleKalmanFilter, EnKFConfig
        assert EnsembleKalmanFilter is not None
        assert EnKFConfig is not None

    def test_enkf_config_init(self):
        """测试EnKF配置初始化"""
        from gpr_risk.enkf import EnKFConfig
        config = EnKFConfig(
            ensemble_size=50,
            inflation_factor=1.05,
            observation_noise=0.1
        )
        assert config.ensemble_size == 50
        assert config.inflation_factor == 1.05


class TestPathPlanningModule:
    """测试路径规划模块"""

    def test_planner_import(self):
        """测试路径规划器导入"""
        from path_planning.planner import GPRPathPlanner, PlannerConfig
        assert GPRPathPlanner is not None
        assert PlannerConfig is not None

    def test_cost_function_import(self):
        """测试代价函数导入"""
        from path_planning.cost_function import RiskCostFunction, CostConfig
        assert RiskCostFunction is not None
        assert CostConfig is not None

    def test_constants_import(self):
        """测试坐标系常量"""
        from path_planning.planner import GRID_EXTENT_KM, GRID_RESOLUTION_KM, GRID_OFFSET_KM
        assert GRID_EXTENT_KM == 150.0
        assert GRID_RESOLUTION_KM == 1.0
        assert GRID_OFFSET_KM == 75.0


class TestUnetModule:
    """测试U-Net降尺度模块"""

    def test_unet_import(self):
        """测试U-Net模型导入"""
        from unet_downscaler.model import UNetDownscaler
        assert UNetDownscaler is not None


class TestCnnCorrectorModule:
    """测试CNN-LSTM时序订正模块"""

    def test_cnn_corrector_import(self):
        """测试CNN订正器导入"""
        from cnn_corrector.model import CNNLSTMCorrector
        assert CNNLSTMCorrector is not None


class TestActiveObsModule:
    """测试主动观测模块"""

    def test_bayesian_observer_import(self):
        """测试贝叶斯观测器导入"""
        from active_obs.bayesian_observer import BayesianObserver
        assert BayesianObserver is not None


class TestMultiUavModule:
    """测试多无人机模块"""

    def test_conflict_resolver_import(self):
        """测试冲突消解器导入"""
        from multi_uav.conflict_resolver import ConflictResolver
        assert ConflictResolver is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

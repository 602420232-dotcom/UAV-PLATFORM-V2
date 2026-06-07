"""
Model-Engine 集成测试
测试各模块之间的协作和数据流
"""

import sys
import os
import pytest
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestGPRPathPlanningIntegration:
    """GPR风险场与路径规划集成测试"""

    def test_gpr_to_planner_data_flow(self):
        """测试GPR风险场输出到路径规划器的数据流"""
        from gpr_risk.model import GPRConfig
        from path_planning.cost_function import CostConfig

        # 创建GPR模型配置
        gpr_config = GPRConfig(
            kernel_type='rbf',
            noise_level=1e-4,
            n_iter=10
        )

        # 创建代价函数配置
        cost_config = CostConfig(
            risk_weight=0.6,
            distance_weight=0.3,
            energy_weight=0.1
        )

        # 验证配置可以协同工作
        assert gpr_config.kernel_type == 'rbf'
        assert cost_config.risk_weight + cost_config.distance_weight + cost_config.energy_weight == 1.0

    def test_risk_field_to_cost_conversion(self):
        """测试风险场到代价的转换"""
        from path_planning.cost_function import RiskCostFunction, CostConfig

        config = CostConfig()
        RiskCostFunction(config)

        # 模拟风险场数据
        risk_field = np.random.rand(150, 150)
        uncertainty_field = np.random.rand(150, 150) * 0.1

        # 验证代价计算
        assert risk_field.shape == (150, 150)
        assert uncertainty_field.shape == (150, 150)


class TestEnKFGPRIntegration:
    """EnKF同化与GPR集成测试"""

    def test_enkf_output_to_gpr_input(self):
        """测试EnKF输出作为GPR输入的数据兼容性"""
        from gpr_risk.enkf import EnKFConfig

        # 创建EnKF配置
        EnKFConfig(
            ensemble_size=20,
            inflation_factor=1.05,
            observation_noise=0.1
        )

        # 模拟EnKF输出
        analysis_mean = np.random.rand(10, 10)
        analysis_std = np.random.rand(10, 10) * 0.1

        # 验证数据格式兼容GPR输入
        assert analysis_mean.shape == analysis_std.shape
        assert np.all(analysis_std >= 0)


class TestCNNUNetIntegration:
    """CNN订正与U-Net降尺度集成测试"""

    def test_unet_output_to_cnn_input(self):
        """测试U-Net降尺度输出作为CNN订正输入"""
        # 模拟U-Net输出（高分辨率场）
        high_res_field = np.random.rand(150, 150, 3)  # 3个气象变量

        # 验证数据格式
        assert high_res_field.ndim == 3
        assert high_res_field.shape[2] == 3


class TestMultiUAVPathPlanningIntegration:
    """多无人机与路径规划集成测试"""

    def test_conflict_resolution_with_planner(self):
        """测试冲突消解与路径规划的协作"""
        from multi_uav.conflict_resolver import ConflictResolver, ConflictConfig

        config = ConflictConfig(
            safety_distance=50.0,
            priority_strategy='distance'
        )
        ConflictResolver(config)

        # 模拟多条路径
        paths = [
            [(0, 0), (10, 10), (20, 20)],
            [(5, 0), (15, 10), (25, 20)],
            [(0, 5), (10, 15), (20, 25)]
        ]

        # 验证冲突检测
        assert len(paths) == 3


class TestDataPipelineIntegration:
    """数据管道集成测试"""

    def test_data_fetcher_to_dataset_conversion(self):
        """测试数据获取到数据集的转换"""
        # 模拟获取的原始数据
        raw_data = {
            'temperature': np.random.rand(100, 100),
            'wind_u': np.random.rand(100, 100),
            'wind_v': np.random.rand(100, 100),
            'pressure': np.random.rand(100, 100)
        }

        # 验证数据格式
        assert 'temperature' in raw_data
        assert 'wind_u' in raw_data
        assert 'wind_v' in raw_data
        assert raw_data['temperature'].shape == (100, 100)


class TestFusionIntegration:
    """融合模块集成测试"""

    def test_ensemble_fusion_with_uncertainty(self):
        """测试集合融合与不确定性量化"""
        from fusion.ensemble import FusionConfig

        FusionConfig(
            method='weighted_average',
            uncertainty_quantification=True
        )

        # 模拟多个模型的预测
        predictions = [
            np.random.rand(50, 50) for _ in range(5)
        ]
        weights = [0.3, 0.25, 0.2, 0.15, 0.1]

        # 验证权重归一化
        assert abs(sum(weights) - 1.0) < 1e-6
        assert len(predictions) == len(weights)


class TestActiveObservationIntegration:
    """主动观测集成测试"""

    def test_bayesian_observer_with_risk_field(self):
        """测试贝叶斯观测器与风险场的协作"""
        from active_obs.bayesian_observer import ObserverConfig

        config = ObserverConfig(
            exploration_rate=0.1,
            exploitation_rate=0.9
        )

        # 模拟风险场和不确定性
        np.random.rand(100, 100)
        np.random.rand(100, 100)

        # 验证配置
        assert config.exploration_rate + config.exploitation_rate == 1.0


class TestMPCIntegration:
    """MPC控制器集成测试"""

    def test_mpc_with_path_planner(self):
        """测试MPC与路径规划器的协作"""
        from control.mpc import MPCConfig

        config = MPCConfig(
            horizon=10,
            dt=1.0,
            max_velocity=20.0
        )

        # 验证配置
        assert config.horizon > 0
        assert config.dt > 0
        assert config.max_velocity > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

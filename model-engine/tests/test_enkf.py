"""EnKF 同化测试"""
import numpy as np
from gpr_risk.enkf import EnsembleKalmanFilter


def test_enkf_generate_ensemble():
    enkf = EnsembleKalmanFilter(n_ensemble=20)
    mean = np.random.randn(6, 50, 50) * 0.1
    log_var = np.random.randn(6, 50, 50) * 0.1
    ensemble = enkf.generate_ensemble(mean, log_var)
    assert ensemble.shape == (20, 6, 50, 50)
    # 集合均值应接近原始均值
    assert abs(ensemble.mean() - mean.mean()) < 0.5


def test_enkf_assimilate():
    enkf = EnsembleKalmanFilter(n_ensemble=20)
    H, W = 10, 10
    mean = np.zeros((6, H, W))
    log_var = np.ones((6, H, W)) * (-2)

    # 从均值为0的分布采样集合
    ensemble = enkf.generate_ensemble(mean, log_var)

    # 虚拟观测 (真值在中心点 = 1.0)
    observations = np.array([1.0])
    obs_positions = np.array([[5, 5]])

    analysis, analysis_mean, analysis_var = enkf.assimilate(
        ensemble, observations, obs_positions
    )

    assert analysis.shape == (20, 6, H, W)
    assert analysis_mean.shape == (6, H, W)
    assert analysis_var.shape == (6, H, W)

    # 同化后中心点应接近观测值 1.0
    assert abs(analysis_mean[0, 5, 5] - 1.0) < 0.5


def test_enkf_uncertainty_reduction():
    """同化后不确定性应下降"""
    enkf = EnsembleKalmanFilter(n_ensemble=50)
    H, W = 10, 10
    mean = np.zeros((1, H, W))
    log_var = np.ones((1, H, W)) * (-1)
    ensemble = enkf.generate_ensemble(mean, log_var)

    prior_var = ensemble.var(axis=0).mean()

    # 多个观测点
    observations = np.ones(3)
    obs_positions = np.array([[2, 2], [5, 5], [8, 8]])

    _, _, post_var = enkf.assimilate(ensemble, observations, obs_positions)

    # 后验方差应小于先验方差
    reduction = enkf.uncertainty_reduction(prior_var, post_var)
    assert reduction > 0, f"不确定性应下降, 实际: 先验={prior_var:.4f}, 后验={post_var.mean():.4f}"

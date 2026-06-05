"""GPR 风险场测试"""
import torch
from gpr_risk.model import GPRiskEstimator, compute_risk_score


def test_gpr_fit_predict():
    est = GPRiskEstimator()
    residual = torch.randn(1, 6, 50, 50) * 0.1
    est.fit(residual)
    risk = est.risk_field((150, 150), device="cpu")
    assert risk.shape == (1, 150, 150)
    assert not torch.isnan(risk).any()


def test_risk_score():
    mean = torch.randn(1, 6, 10, 10)
    var = torch.rand(1, 10, 10) * 0.5
    risk = compute_risk_score(mean, var)
    assert risk.shape == (1, 10, 10)
    assert (risk >= 0).all()

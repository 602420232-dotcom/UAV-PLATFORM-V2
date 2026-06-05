"""概率 U-Net 测试"""
import torch
from unet_downscaler.probabilistic import ProbabilisticUNet, negative_log_likelihood, crps_score


def test_probabilistic_output_shape():
    model = ProbabilisticUNet()
    x = torch.randn(2, 6, 50, 50)
    mean, log_var = model(x)
    assert mean.shape == (2, 6, 150, 150)
    assert log_var.shape == (2, 6, 150, 150)


def test_log_var_constrained():
    model = ProbabilisticUNet()
    x = torch.randn(2, 6, 50, 50)
    _, log_var = model(x)
    # log_var 被约束在 [-5, 5]
    assert log_var.min() >= -5.1
    assert log_var.max() <= 5.1


def test_nll_loss():
    model = ProbabilisticUNet()
    x = torch.randn(2, 6, 50, 50)
    target = torch.randn(2, 6, 150, 150)
    mean, log_var = model(x)
    loss = negative_log_likelihood(mean, log_var, target)
    assert loss > 0
    assert torch.isfinite(loss)


def test_crps_score():
    model = ProbabilisticUNet()
    x = torch.randn(2, 6, 50, 50)
    target = torch.randn(2, 6, 150, 150)
    mean, log_var = model(x)
    crps = crps_score(mean, log_var, target)
    assert crps > 0
    assert torch.isfinite(crps)


def test_perfect_prediction():
    """完美预测应该给出很小的 NLL"""
    mean = torch.zeros(1, 1, 10, 10)
    log_var = torch.ones(1, 1, 10, 10) * (-5)  # 方差极小
    target = torch.zeros(1, 1, 10, 10)
    loss = negative_log_likelihood(mean, log_var, target)
    assert loss < 1.0

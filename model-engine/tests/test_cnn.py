"""CNN 订正器测试"""
import torch
from cnn_corrector.model import CNNCorrector, CNNConfig, SpatialCorrector


def test_cnn_forward():
    model = CNNCorrector()
    x = torch.randn(2, 1, 11, 50, 50)  # (B, T, C, H, W)
    dem = torch.randn(2, 1, 50, 50)
    out = model(x, dem)
    assert out.shape == (2, 6, 50, 50), f"Expected (2,6,50,50), got {out.shape}"


def test_spatial_only():
    spatial = SpatialCorrector(CNNConfig())
    x = torch.randn(2, 11, 50, 50)
    dem = torch.randn(2, 1, 50, 50)
    out = spatial(x, dem)
    assert out.shape == (2, 6, 50, 50)


def test_single_frame():
    """单帧输入 (无时序维度)"""
    model = CNNCorrector()
    x = torch.randn(2, 11, 50, 50)
    dem = torch.randn(2, 1, 50, 50)
    out = model(x, dem)
    assert out.shape == (2, 6, 50, 50)


def test_cnn_device():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = CNNCorrector().to(device)
    x = torch.randn(1, 11, 50, 50).to(device)
    dem = torch.randn(1, 1, 50, 50).to(device)
    out = model(x, dem)
    assert out.device.type == device

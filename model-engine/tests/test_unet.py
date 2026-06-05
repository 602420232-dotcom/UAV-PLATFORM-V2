"""U-Net 降尺度测试"""
import torch
from unet_downscaler.model import UNetDownscaler, UNetConfig


def test_unet_forward():
    model = UNetDownscaler()
    x = torch.randn(2, 6, 50, 50)
    out = model(x)
    assert out.shape == (2, 6, 150, 150), f"Expected (2,6,150,150), got {out.shape}"


def test_unet_with_obs():
    """带观测同化"""
    model = UNetDownscaler(UNetConfig(use_attention=True))
    x = torch.randn(2, 6, 50, 50)
    obs = torch.randn(2, 4, 50, 50)
    mask = (torch.rand(2, 1, 50, 50) > 0.9).float()
    out = model(x, obs, mask)
    assert out.shape == (2, 6, 150, 150)


def test_unet_device():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = UNetDownscaler().to(device)
    x = torch.randn(1, 6, 50, 50).to(device)
    out = model(x)
    assert out.device.type == device

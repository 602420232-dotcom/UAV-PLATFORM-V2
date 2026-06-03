"""
概率 U-Net — 论文核心模型

与确定性 U-Net 的区别:
  输出从 (B, C, H, W) 变成 (B, C, H, W) × 2 = [mean, log_var]
  损失从 MSE 变成 负对数似然 (NLL)

这样模型不仅告诉你"明天下雨"，还告诉你"我有 80% 把握"。
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from dataclasses import dataclass, field
from typing import Optional, Tuple

from unet_downscaler.model import UNetConfig, DoubleConv, Down, Up, SpatialObsEncoder


class ProbabilisticUNet(nn.Module):
    """
    概率 U-Net
    
    输出:
      mean:   (B, C, H, W)  — 预报均值
      log_var: (B, C, H, W) — 对数方差 (取 exp 得方差)
    
    用法:
        model = ProbabilisticUNet()
        mean, log_var = model(x)
        # 采样: sample = mean + torch.exp(0.5 * log_var) * torch.randn_like(mean)
    """

    def __init__(self, config: Optional[UNetConfig] = None):
        super().__init__()
        self.config = config or UNetConfig()
        c = self.config

        # 编码器 (与确定性 U-Net 共享)
        self.inc = DoubleConv(c.in_channels, c.base_channels)

        self.downs = nn.ModuleList()
        self.ups = nn.ModuleList()
        ch = c.base_channels
        skip_channels = [ch]
        for i in range(c.depth):
            self.downs.append(Down(ch, ch * 2))
            ch *= 2
            skip_channels.append(ch)

        self.bottleneck = DoubleConv(ch, ch * 2)
        ch *= 2

        for i in range(c.depth):
            skip_ch = skip_channels[-(i + 1)]
            self.ups.append(Up(ch, skip_ch // 2, use_attn=c.use_attention))
            ch = skip_ch // 2

        # 观测编码器
        if c.use_attention:
            self.obs_encoder = SpatialObsEncoder(c.obs_channels)

        # 上采样到目标分辨率 (3×)
        self.final_upsample = nn.Sequential(
            nn.ConvTranspose2d(c.base_channels, c.base_channels,
                               kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(c.base_channels, c.base_channels // 2,
                               kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
        )

        # 【关键改动】输出两个分支: mean 和 log_var
        self.mean_head = nn.Conv2d(c.base_channels // 2, c.out_channels, kernel_size=3, padding=1)
        self.log_var_head = nn.Conv2d(c.base_channels // 2, c.out_channels, kernel_size=3, padding=1)

    def forward(self, x: torch.Tensor,
                obs: Optional[torch.Tensor] = None,
                obs_mask: Optional[torch.Tensor] = None
                ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns:
            mean:   (B, 6, 150, 150) 预报均值
            log_var: (B, 6, 150, 150) 对数方差
        """
        x1 = self.inc(x)
        skips = [x1]
        for down in self.downs:
            skips.append(down(skips[-1]))
        x = self.bottleneck(skips[-1])

        for i, up in enumerate(self.ups):
            skip = skips[-(i + 2)]
            x = up(x, skip)

        x = self.final_upsample(x)
        mean = self.mean_head(x)
        log_var = self.log_var_head(x)

        # 约束 log_var 范围 (-5, 5) → 方差范围 (0.007, 148)
        log_var = torch.tanh(log_var / 5) * 5

        return mean, log_var


# ── 概率模型的损失函数 ──────────────────────────

def negative_log_likelihood(mean: torch.Tensor, log_var: torch.Tensor,
                            target: torch.Tensor) -> torch.Tensor:
    """
    负对数似然损失

    NLL = 0.5 × Σ( (y - μ)²/σ² + log σ² )

    当预测完全准确 (mean ≈ target, var ≈ 0) 时，NLL → -∞
    但实际训练中 var 不会为 0，因为 log_var 被约束在 [-5, 5]
    """
    var = torch.exp(log_var.clamp(min=-5, max=5))  # σ²
    mse = ((target - mean) ** 2) / var              # (y-μ)²/σ²
    return (0.5 * mse + 0.5 * log_var).mean()


def crps_score(mean: torch.Tensor, log_var: torch.Tensor,
               target: torch.Tensor, n_samples: int = 100) -> torch.Tensor:
    """
    CRPS (Continuous Ranked Probability Score)
    概率预报的评估指标，同时考虑精度和校准度

    值越小越好。CRPS=0 表示完美预报。
    """
    std = torch.exp(0.5 * log_var)
    # 标准化误差
    z = (target - mean) / (std + 1e-8)
    # 标准正态的 PDF 和 CDF
    pdf = torch.exp(-0.5 * z**2) / torch.sqrt(2 * torch.tensor(torch.pi))
    cdf = 0.5 * (1 + torch.erf(z / torch.sqrt(torch.tensor(2.0))))
    # CRPS 近似公式
    crps = std * (z * (2 * cdf - 1) + 2 * pdf - 1 / torch.sqrt(torch.tensor(torch.pi)))
    return crps.mean()

"""
U-Net 物理降尺度模型
3km → 1km 超分辨率 + 多源同化

输入: 订正后粗网格 (3km, 50×50)
输出: 精细预报 (1km, 150×150)

多源同化: 站点观测 + 无人机观测 通过注意力门注入
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from dataclasses import dataclass, field
from typing import Tuple, Optional, List


@dataclass
class UNetConfig:
    """U-Net 配置"""
    in_channels: int = 6            # 订正后变量数
    out_channels: int = 6
    base_channels: int = 64
    depth: int = 4                  # 下采样层数
    kernel_size: int = 3
    scale_factor: int = 3           # 3km → 1km
    use_attention: bool = True
    obs_channels: int = 4           # 站点/无人机观测通道
    dropout: float = 0.05


class DoubleConv(nn.Module):
    """(Conv3×3 → BN → ReLU) × 2"""
    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.conv(x)


class AttentionGate(nn.Module):
    """注意力门 — 用于多源观测同化"""
    def __init__(self, F_g: int, F_l: int, F_int: int):
        super().__init__()
        self.W_g = nn.Sequential(
            nn.Conv2d(F_g, F_int, kernel_size=1), nn.BatchNorm2d(F_int))
        self.W_x = nn.Sequential(
            nn.Conv2d(F_l, F_int, kernel_size=1), nn.BatchNorm2d(F_int))
        self.psi = nn.Sequential(
            nn.Conv2d(F_int, 1, kernel_size=1), nn.BatchNorm2d(1), nn.Sigmoid())

    def forward(self, g, x):
        return x * self.psi(F.relu(self.W_g(g) + self.W_x(x)))


class SpatialObsEncoder(nn.Module):
    """稀疏站点/无人机观测 → 稠密场编码"""
    def __init__(self, obs_channels: int):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(obs_channels, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
        )

    def forward(self, sparse_obs: torch.Tensor,
                mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            sparse_obs: (B, C_obs, H, W) — 观测稀疏场（多数为 NaN）
            mask: (B, 1, H, W) — 观测有效掩码
        Returns:
            obs_feat: (B, 32, H, W)
        """
        if mask is not None:
            sparse_obs = sparse_obs * mask
        return self.encoder(sparse_obs)


class Down(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.pool = nn.MaxPool2d(2)
        self.conv = DoubleConv(in_ch, out_ch)

    def forward(self, x):
        return self.conv(self.pool(x))


class Up(nn.Module):
    def __init__(self, in_ch, out_ch, use_attn=False, gate_ch=None):
        super().__init__()
        self.up = nn.ConvTranspose2d(in_ch, in_ch // 2, kernel_size=2, stride=2)
        self.conv = DoubleConv(in_ch // 2 + (gate_ch or in_ch // 2), out_ch)
        self.use_attn = use_attn
        if use_attn:
            self.attn = AttentionGate(in_ch // 2, gate_ch or in_ch // 2, in_ch // 4)

    def forward(self, x, skip, obs_feat=None):
        x = self.up(x)
        if self.use_attn and obs_feat is not None:
            skip = self.attn(x, skip) + skip  # 注意力 + 残差
        # 处理尺寸不匹配
        diff_y = skip.size(2) - x.size(2)
        diff_x = skip.size(3) - x.size(3)
        x = F.pad(x, [diff_x // 2, diff_x - diff_x // 2,
                      diff_y // 2, diff_y - diff_y // 2])
        return self.conv(torch.cat([x, skip], dim=1))


class UNetDownscaler(nn.Module):
    """
    U-Net 3km → 1km 降尺度
    可选: 多源观测同化 (注意力门)
    """
    def __init__(self, config: Optional[UNetConfig] = None):
        super().__init__()
        self.config = config or UNetConfig()
        c = self.config

        # 观测编码器
        if c.use_attention:
            self.obs_encoder = SpatialObsEncoder(c.obs_channels)

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
            self.ups.append(Up(ch, skip_ch // 2, use_attn=c.use_attention,
                               gate_ch=skip_ch if i == c.depth - 1 else None))
            ch = skip_ch // 2

        # 上采样到目标分辨率 (3×)
        self.final_upsample = nn.Sequential(
            nn.ConvTranspose2d(c.base_channels, c.base_channels,
                               kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(c.base_channels, c.base_channels // 2,
                               kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(c.base_channels // 2, c.out_channels, kernel_size=3, padding=1),
        )

    def forward(self, x: torch.Tensor,
                obs: Optional[torch.Tensor] = None,
                obs_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            x: 订正后粗网格 (B, 6, 50, 50)
            obs: 站点/无人机观测稀疏场 (B, 4, 50, 50) — optional
            obs_mask: 观测有效掩码 (B, 1, 50, 50)
        Returns:
            fine: (B, 6, 150, 150)
        """
        # 观测编码
        obs_feat = None
        if self.config.use_attention and obs is not None:
            obs_feat = self.obs_encoder(obs, obs_mask)

        x1 = self.inc(x)             # 64
        skips = [x1]
        for down in self.downs:
            skips.append(down(skips[-1]))

        x = self.bottleneck(skips[-1])

        for i, up in enumerate(self.ups):
            skip = skips[-(i + 2)]
            x = up(x, skip, obs_feat if i == self.config.depth - 1 else None)

        return self.final_upsample(x)

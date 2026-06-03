"""
CNN 空间订正 + LSTM 时序订正
输入: 粗网格预报 (3km) + DEM + 站点观测
输出: 误差订正后的精细场, 剔除异常格点

架构:
  粗网格 + DEM ──→ 浅层 CNN ──→ ConvLSTM ──→ 订正后场
                      ↑                        ↑
                  天资/风雷                 站点观测
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from dataclasses import dataclass
from typing import Tuple, Optional, List


@dataclass
class CNNConfig:
    """CNN 订正器配置"""
    in_channels: int = 12         # 6 (surface) + 5 (pressure levels) + 1 (DEM)
    hidden_channels: List[int] = None
    out_channels: int = 6         # 订正后: u10, v10, t2m, rh2m, ps, blh
    kernel_size: int = 3
    dropout: float = 0.1
    grid_size: Tuple[int, int] = (50, 50)  # 粗网格
    lstm_hidden: int = 64
    lstm_layers: int = 2

    def __post_init__(self):
        if self.hidden_channels is None:
            self.hidden_channels = [32, 64, 128]


class SpatialCorrector(nn.Module):
    """
    浅层 CNN 空间订正
    结构: Conv3×3 → ReLU → Conv3×3 → ReLU → Conv1×1
    """
    def __init__(self, config: CNNConfig):
        super().__init__()
        cfg = config
        in_ch = cfg.in_channels

        # DEM 编码
        self.dem_encoder = nn.Sequential(
            nn.Conv2d(1, 8, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.Conv2d(8, 8, kernel_size=3, padding=1),
            nn.ReLU(),
        )

        # 主分支
        layers = []
        self.skip_channels = []
        for ch in cfg.hidden_channels:
            layers.extend([
                nn.Conv2d(in_ch, ch, kernel_size=cfg.kernel_size, padding=cfg.kernel_size // 2),
                nn.BatchNorm2d(ch),
                nn.ReLU(),
                nn.Dropout2d(cfg.dropout),
            ])
            self.skip_channels.append(ch)
            in_ch = ch

        layers.append(nn.Conv2d(in_ch, cfg.out_channels, kernel_size=1))
        self.conv_blocks = nn.ModuleList(layers)

        # 残差连接
        self.skip_convs = nn.ModuleList([
            nn.Conv2d(8 + cfg.hidden_channels[0], ch, kernel_size=1)
            for ch in cfg.hidden_channels
        ])

    def forward(self, x: torch.Tensor, dem: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: 粗网格预报 (B, 11, H, W) — 不含DEM
            dem: DEM高程 (B, 1, H, W)
        Returns:
            corrected: 订正后场 (B, 6, H, W)
        """
        dem_feat = self.dem_encoder(dem)
        x = torch.cat([x, dem_feat], dim=1)  # (B, 19, H, W)
        for i, layer in enumerate(self.conv_blocks):
            x = layer(x)
        return x


class LSTMTemporalCorrector(nn.Module):
    """
    ConvLSTM 时序订正
    利用多时刻预报的时序一致性进一步抑制异常
    """
    def __init__(self, input_dim: int = 6, hidden_dim: int = 64,
                 kernel_size: int = 3, num_layers: int = 2):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.kernel_size = kernel_size

        self.convlstm = nn.ModuleList([
            nn.Conv2d(input_dim if i == 0 else hidden_dim,
                      hidden_dim, kernel_size, padding=kernel_size // 2)
            for i in range(num_layers)
        ])
        self.convlstm_h = nn.ModuleList([
            nn.Conv2d(hidden_dim, hidden_dim, kernel_size, padding=kernel_size // 2)
            for _ in range(num_layers)
        ])
        self.convlstm_c = nn.ModuleList([
            nn.Conv2d(hidden_dim, hidden_dim, kernel_size, padding=kernel_size // 2)
            for _ in range(num_layers)
        ])
        self.output_conv = nn.Conv2d(hidden_dim, input_dim, kernel_size=1)

    def forward(self, seq: torch.Tensor) -> torch.Tensor:
        """
        Args:
            seq: 时间序列 (B, T, C, H, W)
        Returns:
            订正后单帧 (B, C, H, W)
        """
        B, T, C, H, W = seq.shape
        h = [torch.zeros(B, self.hidden_dim, H, W, device=seq.device)
             for _ in range(len(self.convlstm))]
        c = [torch.zeros(B, self.hidden_dim, H, W, device=seq.device)
             for _ in range(len(self.convlstm))]

        for t in range(T):
            x = seq[:, t]
            for layer in range(len(self.convlstm)):
                gate = torch.sigmoid(self.convlstm[layer](x) + self.convlstm_h[layer](h[layer]))
                c[layer] = gate * c[layer] + (1 - gate) * torch.tanh(
                    self.convlstm[layer](x) + self.convlstm_h[layer](h[layer])
                )
                h[layer] = gate * torch.tanh(c[layer])
                x = h[layer]

        return self.output_conv(h[-1])


class CNNCorrector(nn.Module):
    """
    完整订正器: CNN 空间 + LSTM 时序
    """
    def __init__(self, config: Optional[CNNConfig] = None):
        super().__init__()
        self.config = config or CNNConfig()
        self.spatial = SpatialCorrector(self.config)
        self.temporal = LSTMTemporalCorrector(
            input_dim=self.config.out_channels,
            hidden_dim=self.config.lstm_hidden,
            kernel_size=self.config.kernel_size,
            num_layers=self.config.lstm_layers,
        )

    def forward(self, x: torch.Tensor, dem: torch.Tensor,
                return_seq: bool = False) -> torch.Tensor:
        """
        Args:
            x: 输入 (B, T, 11, H, W) 或 (B, 11, H, W)
            dem: DEM (B, 1, H, W)
        Returns:
            corrected: (B, 6, H, W)
        """
        if x.dim() == 4:
            x = x.unsqueeze(1)  # (B, 1, C, H, W)
        B, T, C, H, W = x.shape

        # 空间订正每帧
        spatial_out = []
        for t in range(T):
            corrected = self.spatial(x[:, t], dem)
            spatial_out.append(corrected)
        spatial_seq = torch.stack(spatial_out, dim=1)  # (B, T, 6, H, W)

        # 时序订正
        final = self.temporal(spatial_seq)
        return final if not return_seq else (final, spatial_seq)

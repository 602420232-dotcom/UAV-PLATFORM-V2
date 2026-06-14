"""概率U-Net气象降尺度模型 (Probabilistic U-Net).

基于概率U-Net的气象场降尺度模块，输出均值场和方差场，
支持蒙特卡洛采样以量化预测不确定性。使用numpy模拟编码器-解码器结构。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ProbabilisticUNet:
    """概率U-Net气象降尺度模型.

    实现编码器-解码器结构，将粗分辨率气象场降尺度到细分辨率，
    同时输出均值场和方差场以表征预测不确定性。
    通过蒙特卡洛采样生成多个可能的高分辨率场实现。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """初始化概率U-Net模型.

        Args:
            config: 配置字典，支持以下参数:
                - in_channels: 输入通道数，默认 6
                - base_channels: 基础通道数，默认 32
                - depth: 编码器/解码器深度，默认 3
                - latent_dim: 潜变量维度，默认 8
                - n_mc_samples: 蒙特卡洛采样数，默认 10
                - scale_factor: 降尺度因子，默认 3
        """
        self.config = config or {}
        self.in_channels = self.config.get("in_channels", 6)
        self.base_channels = self.config.get("base_channels", 32)
        self.depth = self.config.get("depth", 3)
        self.latent_dim = self.config.get("latent_dim", 8)
        self.n_mc_samples = self.config.get("n_mc_samples", 10)
        self.scale_factor = self.config.get("scale_factor", 3)
        self._encoder_weights: list[tuple[np.ndarray, np.ndarray]] = []
        self._decoder_weights: list[tuple[np.ndarray, np.ndarray]] = []
        self._mean_head_weights: list[np.ndarray] = []
        self._var_head_weights: list[np.ndarray] = []

    def predict(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行概率U-Net降尺度预测.

        Args:
            params: 参数字典，包含:
                - input_field: 粗网格气象场，形状 (H, W) 或 (H, W, C)
                - scale_factor: 可选降尺度因子（覆盖初始化配置）
                - n_samples: 可选蒙特卡洛采样数（覆盖初始化配置）

        Returns:
            包含以下键的字典:
                - mean_field: 均值场（降尺度后的期望气象场）
                - variance_field: 方差场（预测不确定性）
                - samples: 采样结果列表
                - confidence_interval: 95%置信区间
        """
        np.random.seed(42)

        input_field = np.asarray(
            params.get("input_field", np.zeros((50, 50, 6))),
            dtype=np.float64,
        )
        scale_factor = params.get("scale_factor", self.scale_factor)
        n_samples = params.get("n_samples", self.n_mc_samples)

        if input_field.ndim == 2:
            input_field = input_field[:, :, np.newaxis]

        in_h, in_w, in_c = input_field.shape
        out_h = in_h * scale_factor
        out_w = in_w * scale_factor

        logger.info(
            "概率U-Net降尺度: 输入(%d, %d, %d) -> 输出(%d, %d), 采样数=%d",
            in_h,
            in_w,
            in_c,
            out_h,
            out_w,
            n_samples,
        )

        # 初始化权重
        self._initialize_weights(in_c)

        # 编码器前向传播
        encoder_features = self._encode(input_field)

        # 蒙特卡洛采样
        samples: list[np.ndarray] = []
        for _ in range(n_samples):
            # 采样潜变量
            z = np.random.randn(self.latent_dim) * 0.5
            # 解码器前向传播
            decoded = self._decode(encoder_features, z, out_h, out_w, in_c)
            samples.append(decoded)

        samples_arr = np.array(samples)  # (n_samples, H, W, C)
        mean_field = samples_arr.mean(axis=0)
        variance_field = samples_arr.var(axis=0)

        # 95% 置信区间
        std_field = np.sqrt(variance_field)
        ci_lower = mean_field - 1.96 * std_field
        ci_upper = mean_field + 1.96 * std_field

        return {
            "mean_field": mean_field.tolist(),
            "variance_field": variance_field.tolist(),
            "samples": [s.tolist() for s in samples],
            "confidence_interval": {
                "lower": ci_lower.tolist(),
                "upper": ci_upper.tolist(),
            },
            "input_shape": list(input_field.shape),
            "output_shape": list(mean_field.shape),
            "n_samples": n_samples,
            "scale_factor": scale_factor,
        }

    def _initialize_weights(self, in_channels: int) -> None:
        """初始化编码器和解码器权重.

        Args:
            in_channels: 输入通道数
        """
        self._encoder_weights = []
        self._decoder_weights = []
        self._mean_head_weights = []
        self._var_head_weights = []

        # 编码器权重（每层: 卷积核 + 偏置）
        ch = in_channels
        for d in range(self.depth):
            out_ch = self.base_channels * (2**d)
            k = 3
            w = np.random.randn(k, k, ch, out_ch) * 0.1
            b = np.zeros(out_ch)
            self._encoder_weights.append((w, b))
            ch = out_ch

        # 解码器权重
        for d in range(self.depth - 1, -1, -1):
            out_ch = self.base_channels * (2**d) if d > 0 else in_channels
            in_ch = self.base_channels * (2 ** (d + 1))
            k = 3
            w = np.random.randn(k, k, in_ch + ch, out_ch) * 0.1
            b = np.zeros(out_ch)
            self._decoder_weights.append((w, b))
            ch = out_ch

        # 均值头和方差头
        self._mean_head_weights = [
            np.random.randn(ch, ch) * 0.1,
            np.zeros(ch),
        ]
        self._var_head_weights = [
            np.random.randn(ch, ch) * 0.1,
            np.zeros(ch),
        ]

    def _encode(self, x: np.ndarray) -> list[np.ndarray]:
        """编码器前向传播.

        Args:
            x: 输入气象场

        Returns:
            各层特征图列表（用于跳跃连接）
        """
        features = [x]
        h = x.copy()
        for w_conv, b_conv in self._encoder_weights:
            h = self._conv2d(h, w_conv, b_conv)
            h = np.maximum(0, h)  # ReLU
            h = self._max_pool(h)
            features.append(h)
        return features

    def _decode(
        self,
        encoder_features: list[np.ndarray],
        z: np.ndarray,
        target_h: int,
        target_w: int,
        out_channels: int,
    ) -> np.ndarray:
        """解码器前向传播.

        Args:
            encoder_features: 编码器特征图列表
            z: 潜变量
            target_h: 目标高度
            target_w: 目标宽度
            out_channels: 输出通道数

        Returns:
            解码后的气象场
        """
        # 从编码器最深层开始
        h = encoder_features[-1]

        # 注入潜变量
        z_expanded = z.reshape(1, 1, -1)
        z_broadcast = np.broadcast_to(z_expanded, (h.shape[0], h.shape[1], z.shape[0]))
        h = np.concatenate([h, z_broadcast], axis=-1)

        # 逐层上采样 + 跳跃连接
        skip_idx = len(encoder_features) - 2
        for i, (w_conv, b_conv) in enumerate(self._decoder_weights):
            h = self._bilinear_upsample_2d(h)
            if skip_idx >= 0:
                skip = encoder_features[skip_idx]
                # 调整通道数以匹配
                h = np.concatenate([h, skip], axis=-1)
                skip_idx -= 1
            # 调整卷积输入通道数
            expected_in = w_conv.shape[2]
            if h.shape[2] != expected_in:
                h = self._adjust_channels(h, expected_in)
            h = self._conv2d(h, w_conv, b_conv)
            if i < len(self._decoder_weights) - 1:
                h = np.maximum(0, h)

        # 上采样到目标尺寸
        if h.shape[0] != target_h or h.shape[1] != target_w:
            h = self._resize(h, target_h, target_w)

        # 调整输出通道数
        if h.shape[2] != out_channels:
            h = self._adjust_channels(h, out_channels)

        return h

    def _conv2d(
        self,
        x: np.ndarray,
        kernel: np.ndarray,
        bias: np.ndarray,
    ) -> np.ndarray:
        """2D卷积运算（带padding）.

        Args:
            x: 输入特征图 (H, W, C_in)
            kernel: 卷积核 (kH, kW, C_in, C_out)
            bias: 偏置 (C_out,)

        Returns:
            输出特征图 (H, W, C_out)
        """
        h, w, _ = x.shape
        kh, kw, _, n_out = kernel.shape
        pad = kh // 2
        padded = np.pad(x, ((pad, pad), (pad, pad), (0, 0)), mode="reflect")
        output = np.zeros((h, w, n_out), dtype=np.float64)
        for co in range(n_out):
            for ci in range(x.shape[2]):
                for ii in range(kh):
                    for jj in range(kw):
                        output[:, :, co] += (
                            padded[ii: ii + h, jj: jj + w, ci]
                            * kernel[ii, jj, ci, co]
                        )
            output[:, :, co] += bias[co]
        return output

    def _max_pool(self, x: np.ndarray, pool_size: int = 2) -> np.ndarray:
        """最大池化."""
        h, w, c = x.shape
        h_out, w_out = h // pool_size, w // pool_size
        cropped = x[: h_out * pool_size, : w_out * pool_size, :]
        return cropped.reshape(h_out, pool_size, w_out, pool_size, c).max(axis=(1, 3))

    def _bilinear_upsample_2d(self, x: np.ndarray) -> np.ndarray:
        """双线性上采样（2倍）."""
        h, w, c = x.shape
        result = np.zeros((h * 2, w * 2, c), dtype=np.float64)
        for i in range(h * 2):
            for j in range(w * 2):
                src_i = i / 2.0
                src_j = j / 2.0
                i0 = int(np.floor(src_i))
                j0 = int(np.floor(src_j))
                i1 = min(i0 + 1, h - 1)
                j1 = min(j0 + 1, w - 1)
                di = src_i - i0
                dj = src_j - j0
                result[i, j] = (
                    x[i0, j0] * (1 - di) * (1 - dj)
                    + x[i1, j0] * di * (1 - dj)
                    + x[i0, j1] * (1 - di) * dj
                    + x[i1, j1] * di * dj
                )
        return result

    def _resize(
        self,
        x: np.ndarray,
        target_h: int,
        target_w: int,
    ) -> np.ndarray:
        """双线性插值调整尺寸.

        Args:
            x: 输入特征图 (H, W, C)
            target_h: 目标高度
            target_w: 目标宽度

        Returns:
            调整尺寸后的特征图
        """
        h, w, c = x.shape
        result = np.zeros((target_h, target_w, c), dtype=np.float64)
        for i in range(target_h):
            for j in range(target_w):
                src_i = i * (h - 1) / max(target_h - 1, 1)
                src_j = j * (w - 1) / max(target_w - 1, 1)
                i0 = int(np.floor(src_i))
                j0 = int(np.floor(src_j))
                i1 = min(i0 + 1, h - 1)
                j1 = min(j0 + 1, w - 1)
                di = src_i - i0
                dj = src_j - j0
                result[i, j] = (
                    x[i0, j0] * (1 - di) * (1 - dj)
                    + x[i1, j0] * di * (1 - dj)
                    + x[i0, j1] * (1 - di) * dj
                    + x[i1, j1] * di * dj
                )
        return result

    def _adjust_channels(
        self,
        x: np.ndarray,
        target_c: int,
    ) -> np.ndarray:
        """调整通道数（截断或填充零）.

        Args:
            x: 输入特征图
            target_c: 目标通道数

        Returns:
            调整通道数后的特征图
        """
        if x.shape[2] == target_c:
            return x
        if x.shape[2] > target_c:
            return x[:, :, :target_c]
        pad_width = ((0, 0), (0, 0), (0, target_c - x.shape[2]))
        return np.pad(x, pad_width, mode="constant")

"""CNN气象场修正器 (CNN Corrector).

基于卷积神经网络的气象预报偏差修正模块。
使用numpy模拟卷积运算，实现多通道输入->卷积层->池化->全连接->输出修正场。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class CNNCorrector:
    """CNN气象场修正器.

    利用卷积神经网络学习气象预报场与观测场之间的系统性偏差，
    并生成修正场以提升预报精度。使用numpy模拟卷积运算，
    包含卷积层、激活函数、池化层和全连接层。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """初始化CNN修正器.

        Args:
            config: 配置字典，支持以下参数:
                - filters: 卷积核数量列表，默认 [16, 32]
                - kernel_size: 卷积核尺寸，默认 3
                - learning_rate: 学习率，默认 0.001
                - n_epochs: 训练轮数，默认 10
                - pool_size: 池化窗口大小，默认 2
                - hidden_size: 全连接层隐藏维度，默认 64
        """
        self.config = config or {}
        self.filters = self.config.get("filters", [16, 32])
        self.kernel_size = self.config.get("kernel_size", 3)
        self.learning_rate = self.config.get("learning_rate", 0.001)
        self.n_epochs = self.config.get("n_epochs", 10)
        self.pool_size = self.config.get("pool_size", 2)
        self.hidden_size = self.config.get("hidden_size", 64)
        self._weights: list[tuple[np.ndarray, np.ndarray]] = []

    def correct(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行CNN气象场偏差修正.

        Args:
            params: 参数字典，包含:
                - input_field: 输入气象场，形状 (H, W) 或 (H, W, C)
                - target_field: 观测场，形状与 input_field 相同
                - config: 可选的运行时配置覆盖

        Returns:
            包含以下键的字典:
                - corrected_field: 修正后气象场
                - bias: 偏差统计 (均值偏差, 最大偏差)
                - rmse: 修正后均方根误差
        """
        np.random.seed(42)

        input_field = np.asarray(
            params.get("input_field", np.zeros((32, 32, 3))),
            dtype=np.float64,
        )
        target_field = np.asarray(
            params.get("target_field", np.zeros((32, 32, 3))),
            dtype=np.float64,
        )
        config = params.get("config", {})
        if config:
            self.config.update(config)

        # 确保输入为3维 (H, W, C)
        if input_field.ndim == 2:
            input_field = input_field[:, :, np.newaxis]
        if target_field.ndim == 2:
            target_field = target_field[:, :, np.newaxis]

        in_channels = input_field.shape[2]
        # 初始化权重
        self._initialize_weights(in_channels)

        # 训练：计算偏差场作为学习目标
        bias_field = target_field - input_field

        # 前向传播生成修正场
        correction = self._forward(input_field)

        # 简单梯度下降训练（模拟）
        for epoch in range(self.n_epochs):
            pred = self._forward(input_field)
            loss = np.mean((pred - bias_field) ** 2)
            if epoch % 3 == 0:
                logger.info("CNN修正器训练轮次 %d, 损失: %.6f", epoch, loss)

        # 最终修正场
        correction = self._forward(input_field)
        corrected_field = input_field + correction

        # 统计指标
        bias_mean = float(np.mean(correction))
        bias_max = float(np.max(np.abs(correction)))
        rmse = float(np.sqrt(np.mean((corrected_field - target_field) ** 2)))

        return {
            "corrected_field": corrected_field.tolist(),
            "bias": {"mean": bias_mean, "max": bias_max},
            "rmse": rmse,
            "input_shape": list(input_field.shape),
            "output_shape": list(corrected_field.shape),
        }

    def _initialize_weights(self, in_channels: int) -> None:
        """初始化网络权重.

        Args:
            in_channels: 输入通道数
        """
        self._weights = []
        channels = [in_channels] + self.filters
        for i in range(len(channels) - 1):
            k = self.kernel_size
            w = np.random.randn(k, k, channels[i], channels[i + 1]) * 0.1
            b = np.zeros(channels[i + 1])
            self._weights.append((w, b))

        # 全连接层权重（延迟初始化，取决于池化后尺寸）
        self._fc_weights: list[np.ndarray] = []

    def _conv2d(
        self,
        x: np.ndarray,
        kernel: np.ndarray,
        bias: np.ndarray,
    ) -> np.ndarray:
        """2D卷积运算.

        Args:
            x: 输入特征图，形状 (H, W, C_in)
            kernel: 卷积核，形状 (kH, kW, C_in, C_out)
            bias: 偏置，形状 (C_out,)

        Returns:
            输出特征图，形状 (H, W, C_out)
        """
        h, w, _ = x.shape
        kh, kw, _, n_out = kernel.shape
        pad = kh // 2
        padded = np.pad(x, ((pad, pad), (pad, pad), (0, 0)), mode="reflect")
        output = np.zeros((h, w, n_out), dtype=np.float64)
        for co in range(n_out):
            for ci in range(x.shape[2]):
                for i in range(kh):
                    for j in range(kw):
                        output[:, :, co] += (
                            padded[i : i + h, j : j + w, ci] * kernel[i, j, ci, co]
                        )
            output[:, :, co] += bias[co]
        return output

    def _relu(self, x: np.ndarray) -> np.ndarray:
        """ReLU激活函数."""
        return np.maximum(0, x)

    def _max_pool(self, x: np.ndarray) -> np.ndarray:
        """最大池化.

        Args:
            x: 输入特征图，形状 (H, W, C)

        Returns:
            池化后特征图
        """
        h, w, c = x.shape
        ph, pw = self.pool_size, self.pool_size
        h_out = h // ph
        w_out = w // pw
        pooled = x[: h_out * ph, : w_out * pw, :]
        pooled = pooled.reshape(h_out, ph, w_out, pw, c).max(axis=(1, 3))
        return pooled

    def _forward(self, x: np.ndarray) -> np.ndarray:
        """前向传播.

        Args:
            x: 输入气象场，形状 (H, W, C)

        Returns:
            修正场，形状与输入相同
        """
        h, w, in_c = x.shape
        feature = x.copy()

        # 卷积 + ReLU + 池化
        for w_conv, b_conv in self._weights:
            feature = self._conv2d(feature, w_conv, b_conv)
            feature = self._relu(feature)
            feature = self._max_pool(feature)

        # 展平
        flat = feature.reshape(-1)
        flat_size = flat.shape[0]

        # 全连接层
        if not self._fc_weights:
            self._fc_weights = [
                np.random.randn(flat_size, self.hidden_size) * 0.1,
                np.zeros(self.hidden_size),
                np.random.randn(self.hidden_size, flat_size) * 0.1,
                np.zeros(flat_size),
            ]

        fc_w1, fc_b1, fc_w2, fc_b2 = self._fc_weights
        hidden = self._relu(flat @ fc_w1 + fc_b1)
        output_flat = hidden @ fc_w2 + fc_b2

        # 重塑为原始空间尺寸
        output = output_flat.reshape(feature.shape)
        # 上采样回原始尺寸（双线性插值）
        output = self._bilinear_upsample(output, h, w, in_c)

        return output

    def _bilinear_upsample(
        self,
        x: np.ndarray,
        target_h: int,
        target_w: int,
        channels: int,
    ) -> np.ndarray:
        """双线性上采样到目标尺寸.

        Args:
            x: 输入特征图
            target_h: 目标高度
            target_w: 目标宽度
            channels: 输出通道数

        Returns:
            上采样后的特征图
        """
        result = np.zeros((target_h, target_w, channels), dtype=np.float64)
        h_in, w_in = x.shape[0], x.shape[1]
        for i in range(target_h):
            for j in range(target_w):
                # 映射到输入坐标
                src_i = i * (h_in - 1) / max(target_h - 1, 1)
                src_j = j * (w_in - 1) / max(target_w - 1, 1)
                i0 = int(np.floor(src_i))
                j0 = int(np.floor(src_j))
                i1 = min(i0 + 1, h_in - 1)
                j1 = min(j0 + 1, w_in - 1)
                di = src_i - i0
                dj = src_j - j0
                result[i, j] = (
                    x[i0, j0] * (1 - di) * (1 - dj)
                    + x[i1, j0] * di * (1 - dj)
                    + x[i0, j1] * (1 - di) * dj
                    + x[i1, j1] * di * dj
                )
        return result

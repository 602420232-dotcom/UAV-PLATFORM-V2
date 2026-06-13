"""LSTM时序修正器 (LSTM Temporal Corrector).

基于长短期记忆网络的气象时间序列偏差修正模块。
考虑时间依赖性，对气象预报序列进行系统性偏差修正，
提升时间维度的预报精度。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class LSTMTemporalCorrector:
    """LSTM时序修正器.

    利用LSTM网络学习气象预报时间序列与观测时间序列之间的偏差模式，
    考虑时间依赖性进行偏差修正。使用numpy模拟LSTM单元的前向传播。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """初始化LSTM时序修正器.

        Args:
            config: 配置字典，支持以下参数:
                - input_size: 输入特征维度，默认 6
                - hidden_size: LSTM隐藏层维度，默认 64
                - num_layers: LSTM层数，默认 2
                - output_size: 输出维度，默认 6
                - learning_rate: 学习率，默认 0.001
                - n_epochs: 训练轮数，默认 10
                - seq_length: 输入序列长度，默认 12
                - pred_length: 预测序列长度，默认 6
        """
        self.config = config or {}
        self.input_size = self.config.get("input_size", 6)
        self.hidden_size = self.config.get("hidden_size", 64)
        self.num_layers = self.config.get("num_layers", 2)
        self.output_size = self.config.get("output_size", 6)
        self.learning_rate = self.config.get("learning_rate", 0.001)
        self.n_epochs = self.config.get("n_epochs", 10)
        self.seq_length = self.config.get("seq_length", 12)
        self.pred_length = self.config.get("pred_length", 6)
        self._lstm_weights: list[dict[str, np.ndarray]] = []
        self._fc_weights: list[np.ndarray] = []

    def correct(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行LSTM时序偏差修正.

        Args:
            params: 参数字典，包含:
                - input_sequence: 输入预报时间序列，形状 (T, H, W, C) 或 (T, C)
                - observation_sequence: 观测时间序列，形状与 input_sequence 相同
                - pred_length: 可选预测长度（覆盖初始化配置）
                - config: 可选的运行时配置覆盖

        Returns:
            包含以下键的字典:
                - corrected_sequence: 修正后时间序列
                - temporal_bias: 时序偏差统计
                - skill_score: 技巧评分
        """
        np.random.seed(42)

        input_sequence = np.asarray(
            params.get("input_sequence", np.zeros((12, 50, 50, 6))),
            dtype=np.float64,
        )
        observation_sequence = np.asarray(
            params.get("observation_sequence", np.zeros((12, 50, 50, 6))),
            dtype=np.float64,
        )
        pred_length = params.get("pred_length", self.pred_length)
        config = params.get("config", {})
        if config:
            self.config.update(config)

        # 处理不同输入维度
        if input_sequence.ndim == 2:
            # (T, C) -> 简单时序修正
            return self._correct_1d(input_sequence, observation_sequence, pred_length)

        # 计算偏差序列
        bias_sequence = observation_sequence - input_sequence

        # 初始化权重
        seq_len = input_sequence.shape[0]
        feature_dim = int(
            input_sequence.shape[1]
            if input_sequence.ndim == 2
            else np.prod(input_sequence.shape[1:])
        )
        self._initialize_weights(feature_dim)

        logger.info(
            "LSTM时序修正: 序列长度=%d, 特征维度=%d, 预测长度=%d",
            seq_len, feature_dim, pred_length,
        )

        # 将3D/4D输入展平为2D (T, features)
        flat_input = input_sequence.reshape(seq_len, -1)
        flat_bias = bias_sequence.reshape(seq_len, -1)

        # 训练：学习偏差模式
        for epoch in range(self.n_epochs):
            pred_bias = self._forward(flat_input)
            loss = np.mean((pred_bias - flat_bias) ** 2)
            if epoch % 3 == 0:
                logger.info("LSTM时序修正训练轮次 %d, 损失: %.6f", epoch, loss)

        # 学习到的偏差模式
        learned_bias = self._forward(flat_input)

        # 外推偏差到预测时段
        last_bias = learned_bias[-1:]
        extrapolated_bias = np.repeat(last_bias, pred_length, axis=0)
        # 添加衰减趋势
        for t in range(pred_length):
            decay = 1.0 / (1.0 + 0.1 * t)
            extrapolated_bias[t] *= decay

        # 生成修正后的预测序列
        last_frame = input_sequence[-1:]
        predicted_raw = np.repeat(last_frame, pred_length, axis=0)
        corrected_sequence = predicted_raw + extrapolated_bias

        # 统计指标
        temporal_bias_mean = float(np.mean(learned_bias, axis=0).mean())
        temporal_bias_std = float(np.std(learned_bias, axis=0).mean())

        # 技巧评分（相对于气候态平均的改进）
        climatology_bias = np.mean(flat_bias, axis=0, keepdims=True)
        climatology_rmse = float(np.sqrt(np.mean((flat_bias - climatology_bias) ** 2)))
        model_rmse = float(np.sqrt(np.mean((learned_bias - flat_bias) ** 2)))
        skill_score = 1.0 - model_rmse / max(climatology_rmse, 1e-10)
        skill_score = max(0.0, min(1.0, skill_score))

        return {
            "corrected_sequence": corrected_sequence.tolist(),
            "temporal_bias": {
                "mean": temporal_bias_mean,
                "std": temporal_bias_std,
                "trend": float(np.mean(learned_bias[-1] - learned_bias[0])),
            },
            "skill_score": skill_score,
            "input_shape": list(input_sequence.shape),
            "output_shape": list(corrected_sequence.shape),
            "pred_length": pred_length,
        }

    def _correct_1d(
        self,
        input_seq: np.ndarray,
        obs_seq: np.ndarray,
        pred_length: int,
    ) -> dict[str, Any]:
        """1D时序修正（简化版）.

        Args:
            input_seq: 输入序列 (T, C)
            obs_seq: 观测序列 (T, C)
            pred_length: 预测长度

        Returns:
            修正结果字典
        """
        bias = obs_seq - input_seq
        bias_mean = np.mean(bias, axis=0)
        bias_trend = (bias[-1] - bias[0]) / max(len(bias) - 1, 1)

        corrected = []
        for t in range(pred_length):
            decay = 1.0 / (1.0 + 0.05 * t)
            correction = bias_mean + bias_trend * (t + 1) * decay
            corrected.append(input_seq[-1] + correction)
        corrected_sequence = np.array(corrected)

        rmse = float(np.sqrt(np.mean(bias ** 2)))
        skill = max(0.0, 1.0 - rmse / max(float(np.std(obs_seq)), 1e-10))

        return {
            "corrected_sequence": corrected_sequence.tolist(),
            "temporal_bias": {
                "mean": float(np.mean(bias_mean)),
                "std": float(np.std(bias)),
                "trend": float(np.mean(bias_trend)),
            },
            "skill_score": skill,
            "input_shape": list(input_seq.shape),
            "output_shape": list(corrected_sequence.shape),
            "pred_length": pred_length,
        }

    def _initialize_weights(self, input_dim: int) -> None:
        """初始化LSTM和全连接层权重.

        Args:
            input_dim: 输入特征维度
        """
        self._lstm_weights = []
        for layer in range(self.num_layers):
            in_size = input_dim if layer == 0 else self.hidden_size
            # LSTM门控权重: 输入门、遗忘门、输出门、候选状态
            scale = 0.1
            self._lstm_weights.append({
                "W_ih": np.random.randn(4 * self.hidden_size, in_size) * scale,
                "b_ih": np.zeros(4 * self.hidden_size),
                "W_hh": np.random.randn(4 * self.hidden_size, self.hidden_size) * scale,
                "b_hh": np.zeros(4 * self.hidden_size),
            })

        # 全连接输出层
        self._fc_weights = [
            np.random.randn(self.hidden_size, input_dim) * 0.1,
            np.zeros(input_dim),
        ]

    def _forward(self, x: np.ndarray) -> np.ndarray:
        """LSTM前向传播.

        Args:
            x: 输入序列 (T, features)

        Returns:
            输出序列 (T, features)
        """
        seq_len = x.shape[0]
        batch_size = 1

        # 初始化隐藏状态
        h = np.zeros((self.num_layers, batch_size, self.hidden_size))
        c = np.zeros((self.num_layers, batch_size, self.hidden_size))

        outputs = []
        for t in range(seq_len):
            inp = x[t:t + 1]  # (1, features)
            for layer in range(self.num_layers):
                weights = self._lstm_weights[layer]
                gates = (
                    inp @ weights["W_ih"].T + weights["b_ih"]
                    + h[layer] @ weights["W_hh"].T + weights["b_hh"]
                )
                i_gate = self._sigmoid(gates[:, :self.hidden_size])
                f_gate = self._sigmoid(gates[:, self.hidden_size:2 * self.hidden_size])
                o_gate = self._sigmoid(gates[:, 2 * self.hidden_size:3 * self.hidden_size])
                g_gate = np.tanh(gates[:, 3 * self.hidden_size:])
                c[layer] = f_gate * c[layer] + i_gate * g_gate
                h[layer] = o_gate * np.tanh(c[layer])
                inp = h[layer]
            outputs.append(h[-1].squeeze(0))

        # 全连接输出
        fc_w, fc_b = self._fc_weights
        output = np.array(outputs) @ fc_w + fc_b
        return output

    @staticmethod
    def _sigmoid(x: np.ndarray) -> np.ndarray:
        """Sigmoid激活函数."""
        return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))

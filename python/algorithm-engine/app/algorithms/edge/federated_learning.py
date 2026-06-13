"""Federated Learning for Edge Devices.

Migrated from: edge-cloud-coordinator/federated_learning.py

Supports FedAvg and FedProx aggregation strategies.
Enhanced with async aggregation, differential privacy, and communication compression.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class FederatedLearner:
    """Federated Learning orchestrator.

    Supports FedAvg and FedProx aggregation strategies for
    distributed model training across edge devices.
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.strategy = self.config.get("strategy", "fedavg")
        self.n_clients = self.config.get("n_clients", 5)
        self.n_rounds = self.config.get("n_rounds", 10)
        self.learning_rate = self.config.get("learning_rate", 0.01)
        self.proximal_mu = self.config.get("proximal_mu", 0.01)
        self.global_model: Optional[np.ndarray] = None

    def train(self, params: dict[str, Any]) -> dict[str, Any]:
        """Run federated learning training.

        Args:
            params: Dictionary containing:
                - client_updates: list of client model weight updates
                - strategy: "fedavg" or "fedprox"
                - n_rounds: number of aggregation rounds

        Returns:
            Dictionary with global model, training metrics,
            and convergence info.
        """
        client_updates = params.get("client_updates", [])
        strategy = params.get("strategy", self.strategy)
        n_rounds = params.get("n_rounds", self.n_rounds)

        if not client_updates:
            return {"error": "No client updates provided", "global_model": None}

        # Initialize global model from first client
        self.global_model = np.array(client_updates[0], dtype=float)
        history = []

        for round_idx in range(n_rounds):
            # Simulate client updates
            aggregated = self._aggregate(client_updates, strategy)
            self.global_model = aggregated

            loss = float(np.random.rand() * 0.5)  # Simulated loss
            history.append({"round": round_idx + 1, "loss": loss})

        global_model_list = None
        if self.global_model is not None:
            global_model_list = self.global_model.tolist()

        return {
            "global_model": global_model_list,
            "strategy": strategy,
            "n_rounds": n_rounds,
            "n_clients": len(client_updates),
            "history": history,
            "final_loss": history[-1]["loss"] if history else None,
        }

    def _aggregate(self, client_updates, strategy):
        """Aggregate client model updates."""
        if strategy == "fedavg":
            return self._fedavg(client_updates)
        elif strategy == "fedprox":
            return self._fedprox(client_updates)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _fedavg(self, client_updates):
        """Federated Averaging: simple mean of client models."""
        return np.mean([np.array(u, dtype=float) for u in client_updates], axis=0)

    def _fedprox(self, client_updates):
        """FedProx: proximal term regularization."""
        avg = self._fedavg(client_updates)
        if self.global_model is not None:
            proximal_term = self.proximal_mu * (avg - self.global_model)
            avg = avg - proximal_term
        return avg

    # ------------------------------------------------------------------
    # 增强联邦学习方法
    # ------------------------------------------------------------------

    def async_aggregate(self, params: dict[str, Any]) -> dict[str, Any]:
        """异步联邦聚合。

        允许节点在不同时间提交模型更新，使用时间衰减加权。
        越早提交的更新权重越低，越新的更新权重越高，以反映
        数据分布的时效性。

        Args:
            params: 异步聚合参数字典，包含：
                - client_updates: 客户端更新列表，每个元素为字典：
                  {"weights": list, "timestamp": float, "client_id": str}。
                  timestamp 为相对于参考时间的偏移量（秒）。
                - decay_factor: 时间衰减因子，默认 0.95。
                  值越接近 1 表示衰减越慢，旧更新保留更多权重。

        Returns:
            异步聚合结果字典，包含：
                - global_weights: 聚合后的全局模型权重列表。
                - participating_clients: 参与聚合的客户端 ID 列表。
                - aggregation_time: 聚合耗时（毫秒）。
                - n_participants: 参与客户端数量。
                - time_span: 更新时间跨度（秒）。
        """
        import time as _time

        t_start = _time.perf_counter()

        client_updates = params.get("client_updates", [])
        decay_factor = params.get("decay_factor", 0.95)

        if not client_updates:
            return {
                "global_weights": None,
                "participating_clients": [],
                "aggregation_time": 0.0,
                "n_participants": 0,
                "time_span": 0.0,
            }

        # 提取时间戳并归一化（以最旧的时间戳为基准）
        timestamps = np.array([u["timestamp"] for u in client_updates], dtype=float)
        weights_arrays = [np.array(u["weights"], dtype=float) for u in client_updates]
        client_ids = [u.get("client_id", f"client_{i}") for i, u in enumerate(client_updates)]

        t_min = timestamps.min()
        t_max = timestamps.max()
        time_span = float(t_max - t_min)

        # 计算时间衰减权重：w_i = decay_factor^((t_max - t_i) / tau)
        # tau 为归一化时间尺度，避免衰减过快
        tau = max(time_span, 1.0)
        decay_weights = np.array([
            decay_factor ** ((t_max - ts) / tau) for ts in timestamps
        ])
        decay_weights /= decay_weights.sum()  # 归一化

        # 加权聚合
        global_weights = np.zeros_like(weights_arrays[0])
        for w_arr, dw in zip(weights_arrays, decay_weights):
            global_weights += dw * w_arr

        aggregation_time = (_time.perf_counter() - t_start) * 1000

        return {
            "global_weights": global_weights.tolist(),
            "participating_clients": client_ids,
            "aggregation_time": round(aggregation_time, 3),
            "n_participants": len(client_updates),
            "time_span": round(time_span, 4),
        }

    def differential_privacy(self, params: dict[str, Any]) -> dict[str, Any]:
        """差分隐私保护。

        在模型更新上应用梯度裁剪和高斯噪声注入，满足 (epsilon, delta)
        差分隐私保证。

        Args:
            params: 差分隐私参数字典，包含：
                - model_update: 模型更新权重（list 或 np.ndarray）。
                - epsilon: 隐私预算 epsilon，默认 1.0。值越小隐私保护越强。
                - delta: 隐私预算 delta，默认 1e-5。
                - clip_norm: 梯度裁剪范数，默认 1.0。

        Returns:
            差分隐私处理结果字典，包含：
                - noisy_update: 加噪后的模型更新列表。
                - privacy_budget_used: 已使用的隐私预算 {"epsilon", "delta"}。
                - clip_applied: 是否执行了裁剪。
                - clip_norm_applied: 实际裁剪后的范数。
                - noise_scale: 噪声标准差。
        """
        model_update = params.get("model_update", [])
        epsilon = params.get("epsilon", 1.0)
        delta = params.get("delta", 1e-5)
        clip_norm = params.get("clip_norm", 1.0)

        update = np.array(model_update, dtype=float)

        if update.size == 0:
            return {
                "noisy_update": [],
                "privacy_budget_used": {"epsilon": 0.0, "delta": 0.0},
                "clip_applied": False,
                "clip_norm_applied": 0.0,
                "noise_scale": 0.0,
            }

        # 步骤 1：梯度裁剪
        original_norm = float(np.linalg.norm(update))
        clip_applied = original_norm > clip_norm

        if clip_applied:
            update = update * (clip_norm / original_norm)
        actual_norm = float(np.linalg.norm(update))

        # 步骤 2：计算高斯噪声标准差
        # sigma = clip_norm * sqrt(2 * ln(1.25 / delta)) / epsilon
        noise_scale = clip_norm * math.sqrt(2.0 * math.log(1.25 / delta)) / epsilon

        # 步骤 3：注入高斯噪声
        noise = np.random.normal(0, noise_scale, size=update.shape)
        noisy_update = update + noise

        return {
            "noisy_update": noisy_update.tolist(),
            "privacy_budget_used": {"epsilon": epsilon, "delta": delta},
            "clip_applied": clip_applied,
            "clip_norm_applied": round(actual_norm, 6),
            "noise_scale": round(noise_scale, 6),
        }

    def communication_efficient(self, params: dict[str, Any]) -> dict[str, Any]:
        """通信压缩：Top-K 稀疏化 + 量化。

        对模型更新进行 Top-K 稀疏化（仅保留绝对值最大的 K 个元素），
        然后对保留的值进行指数量化以减少通信开销。

        Args:
            params: 通信压缩参数字典，包含：
                - model_update: 模型更新权重（list 或 np.ndarray）。
                - compression_ratio: 压缩比率，默认 0.1。
                  表示仅保留 10% 的参数。
                - quantize_bits: 量化比特数，默认 8。

        Returns:
            通信压缩结果字典，包含：
                - compressed_update: 压缩后的模型更新列表（稀疏表示）。
                - compression_ratio_achieved: 实际达到的压缩比率。
                - bytes_saved: 节省的字节数（估算）。
                - n_total: 原始参数总数。
                - n_nonzero: 压缩后非零参数数量。
                - quantize_bits: 使用的量化比特数。
        """
        model_update = params.get("model_update", [])
        compression_ratio = params.get("compression_ratio", 0.1)
        quantize_bits = params.get("quantize_bits", 8)

        update = np.array(model_update, dtype=float)

        if update.size == 0:
            return {
                "compressed_update": [],
                "compression_ratio_achieved": 0.0,
                "bytes_saved": 0,
                "n_total": 0,
                "n_nonzero": 0,
                "quantize_bits": quantize_bits,
            }

        n_total = update.size
        k = max(1, int(n_total * compression_ratio))

        # Top-K 稀疏化：保留绝对值最大的 K 个元素
        flat = update.flatten()
        threshold = np.sort(np.abs(flat))[-k] if k < n_total else 0.0
        mask = np.abs(flat) >= threshold

        # 如果超过 K 个元素等于阈值，随机截断
        indices_above = np.where(np.abs(flat) > threshold)[0]
        indices_at = np.where(np.abs(flat) == threshold)[0]
        if len(indices_above) + len(indices_at) > k:
            n_keep_at = k - len(indices_above)
            if n_keep_at > 0:
                keep_at = np.random.choice(indices_at, size=n_keep_at, replace=False)
                selected_indices = np.concatenate([indices_above, keep_at])
            else:
                selected_indices = indices_above
        else:
            selected_indices = np.concatenate([indices_above, indices_at])

        # 量化
        max_val = float(np.max(np.abs(flat[selected_indices]))) if len(selected_indices) > 0 else 1.0
        if max_val == 0:
            max_val = 1.0
        quant_levels = 2 ** (quantize_bits - 1) - 1  # 有符号量化
        quantized = np.round(flat[selected_indices] / max_val * quant_levels) / quant_levels * max_val

        # 构建稀疏表示
        compressed = np.zeros_like(flat)
        compressed[selected_indices] = quantized
        compressed_update = compressed.reshape(update.shape)

        n_nonzero = int(np.count_nonzero(compressed))
        actual_ratio = n_nonzero / n_total if n_total > 0 else 0.0

        # 字节数估算：原始 float64 vs 量化后
        original_bytes = n_total * 8  # float64
        compressed_bytes = n_nonzero * (quantize_bits // 8 + 4)  # 量化值 + 索引
        bytes_saved = max(0, original_bytes - compressed_bytes)

        return {
            "compressed_update": compressed_update.tolist(),
            "compression_ratio_achieved": round(actual_ratio, 4),
            "bytes_saved": bytes_saved,
            "n_total": n_total,
            "n_nonzero": n_nonzero,
            "quantize_bits": quantize_bits,
        }

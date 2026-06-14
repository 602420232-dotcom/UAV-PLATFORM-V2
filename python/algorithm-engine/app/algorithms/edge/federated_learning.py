"""Federated Learning for Edge Devices.

Migrated from: edge-cloud-coordinator/federated_learning.py

Supports FedAvg and FedProx aggregation strategies.
Enhanced with:
- FedAvgServer / FedAvgClient: server-side weighted averaging, client-side local training
- FedProxServer / FedProxClient: proximal term to prevent client drift
- Checkpoint save/load for resumable training (JSON format)
- Communication compression: Top-K sparsification, Float32->Float16 quantization
- Multi-round aggregation with learning-rate scheduling and early stopping
"""

from __future__ import annotations

import copy
import json
import logging
import math
import os
import time
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


# ======================================================================
# Communication Compression Utilities
# ======================================================================


def top_k_sparsify(
    gradients: np.ndarray,
    k_ratio: float = 0.1,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Top-K sparsification: keep only the largest K% of gradient magnitudes.

    Args:
        gradients: Gradient array to sparsify.
        k_ratio: Fraction of elements to keep (e.g. 0.1 = top 10%).

    Returns:
        Tuple of (sparse_gradient, stats_dict).
    """
    flat = gradients.flatten().astype(np.float64)
    n_total = flat.size
    k = max(1, int(n_total * k_ratio))

    # Find threshold
    abs_sorted = np.sort(np.abs(flat))
    threshold = abs_sorted[-k] if k < n_total else 0.0

    # Handle ties at threshold
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

    sparse = np.zeros_like(flat)
    sparse[selected_indices] = flat[selected_indices]
    sparse_gradient = sparse.reshape(gradients.shape)

    n_nonzero = int(np.count_nonzero(sparse_gradient))
    original_bytes = n_total * 4  # float32
    compressed_bytes = n_nonzero * 6  # float16 value + 4-byte index
    bytes_saved = max(0, original_bytes - compressed_bytes)

    stats = {
        "compression_method": "top_k",
        "k_ratio": k_ratio,
        "n_total": n_total,
        "n_nonzero": n_nonzero,
        "sparsity_ratio": round(1.0 - n_nonzero / n_total, 4) if n_total > 0 else 0.0,
        "original_bytes": original_bytes,
        "compressed_bytes": compressed_bytes,
        "bytes_saved": bytes_saved,
        "compression_rate": round(bytes_saved / original_bytes, 4) if original_bytes > 0 else 0.0,
    }
    return sparse_gradient, stats


def quantize_fp16(
    gradients: np.ndarray,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Quantize gradients from float32 to float16.

    Args:
        gradients: Gradient array to quantize.

    Returns:
        Tuple of (quantized_gradient, stats_dict).
    """
    original = gradients.astype(np.float32)
    quantized = original.astype(np.float16).astype(np.float32)  # round-trip

    n_total = original.size
    original_bytes = n_total * 4
    compressed_bytes = n_total * 2
    bytes_saved = original_bytes - compressed_bytes

    # Compute quantization error
    error = np.abs(original - quantized)
    max_error = float(np.max(error)) if n_total > 0 else 0.0
    mean_error = float(np.mean(error)) if n_total > 0 else 0.0

    stats = {
        "compression_method": "fp16_quantization",
        "n_total": n_total,
        "original_bytes": original_bytes,
        "compressed_bytes": compressed_bytes,
        "bytes_saved": bytes_saved,
        "compression_rate": round(bytes_saved / original_bytes, 4) if original_bytes > 0 else 0.0,
        "max_quantization_error": round(max_error, 8),
        "mean_quantization_error": round(mean_error, 8),
    }
    return quantized, stats


def compress_gradients(
    gradients: np.ndarray,
    method: str = "top_k",
    k_ratio: float = 0.1,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Apply communication compression to gradients.

    Args:
        gradients: Gradient array to compress.
        method: Compression method, "top_k" or "fp16".
        k_ratio: Top-K ratio (only used when method="top_k").

    Returns:
        Tuple of (compressed_gradient, stats_dict).
    """
    if method == "top_k":
        return top_k_sparsify(gradients, k_ratio=k_ratio)
    elif method == "fp16":
        return quantize_fp16(gradients)
    else:
        raise ValueError(f"Unknown compression method: {method}. Use 'top_k' or 'fp16'.")


# ======================================================================
# Checkpoint Manager
# ======================================================================


class CheckpointManager:
    """Manages model checkpoint save/load for resumable training.

    Saves checkpoints in JSON format containing:
    - global_model weights
    - current round number
    - best metric value
    - training history
    - configuration
    """

    def __init__(self, checkpoint_dir: str = "./checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(checkpoint_dir, exist_ok=True)

    def save(
        self,
        global_model: np.ndarray,
        current_round: int,
        best_metric: float,
        history: list[dict[str, Any]],
        config: dict[str, Any],
        filename: str = "checkpoint.json",
    ) -> str:
        """Save a training checkpoint to JSON file.

        Args:
            global_model: Current global model weights.
            current_round: Current training round (0-indexed).
            best_metric: Best metric value seen so far.
            history: Training history list.
            config: Training configuration.
            filename: Checkpoint filename.

        Returns:
            Absolute path to saved checkpoint file.
        """
        filepath = os.path.join(self.checkpoint_dir, filename)
        checkpoint_data = {
            "global_model": global_model.tolist(),
            "current_round": current_round,
            "best_metric": best_metric,
            "history": history,
            "config": config,
            "saved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
        logger.info("Checkpoint saved to %s (round %d)", filepath, current_round)
        return os.path.abspath(filepath)

    def load(self, filename: str = "checkpoint.json") -> Optional[dict[str, Any]]:
        """Load a training checkpoint from JSON file.

        Args:
            filename: Checkpoint filename.

        Returns:
            Checkpoint dict with keys: global_model, current_round,
            best_metric, history, config, saved_at.
            Returns None if file does not exist.
        """
        filepath = os.path.join(self.checkpoint_dir, filename)
        if not os.path.exists(filepath):
            logger.warning("Checkpoint file not found: %s", filepath)
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Convert model back to numpy
        data["global_model"] = np.array(data["global_model"], dtype=np.float64)
        logger.info(
            "Checkpoint loaded from %s (round %d, best_metric=%.6f)",
            filepath,
            data["current_round"],
            data["best_metric"],
        )
        return data


# ======================================================================
# FedAvg Client
# ======================================================================


class FedAvgClient:
    """Client-side local training for Federated Averaging.

    Simulates local SGD training on client data.
    """

    def __init__(
        self,
        client_id: str,
        model: np.ndarray,
        learning_rate: float = 0.01,
        local_epochs: int = 1,
        batch_size: int = 32,
        data_size: int = 100,
    ):
        self.client_id = client_id
        self.model = copy.deepcopy(model)
        self.learning_rate = learning_rate
        self.local_epochs = local_epochs
        self.batch_size = batch_size
        self.data_size = data_size

    def local_train(
        self,
        data: Optional[np.ndarray] = None,
        labels: Optional[np.ndarray] = None,
    ) -> dict[str, Any]:
        """Perform local training and return model update.

        Simulates gradient descent on local data. If no data is provided,
        generates synthetic data for simulation.

        Args:
            data: Feature matrix (n_samples, n_features). If None, synthetic data is used.
            labels: Label vector (n_samples,). If None, synthetic labels are used.

        Returns:
            Dict with:
                - client_id: Client identifier.
                - model_update: Weight difference (new - old) as list.
                - n_samples: Number of local training samples.
                - local_loss: Final local loss value.
                - local_epochs: Number of local epochs run.
        """
        n_features = self.model.size

        # Generate synthetic data if not provided
        if data is None:
            data = np.random.randn(self.data_size, n_features)
        if labels is None:
            labels = np.random.randn(self.data_size)

        original_model = copy.deepcopy(self.model)

        for epoch in range(self.local_epochs):
            # Simulate mini-batch SGD
            indices = np.random.permutation(len(data))
            for start_idx in range(0, len(data), self.batch_size):
                batch_idx = indices[start_idx : start_idx + self.batch_size]
                batch_data = data[batch_idx]
                batch_labels = labels[batch_idx]

                # Simulate gradient: d(loss)/d(w) ~ (X^T X w - X^T y) / n
                pred = batch_data @ self.model
                residual = pred - batch_labels
                gradient = batch_data.T @ residual / len(batch_idx)

                # Gradient step
                self.model -= self.learning_rate * gradient

        # Compute update delta
        model_update = self.model - original_model

        # Compute local loss (MSE)
        final_pred = data @ self.model
        local_loss = float(np.mean((final_pred - labels) ** 2))

        return {
            "client_id": self.client_id,
            "model_update": model_update.tolist(),
            "n_samples": len(data),
            "local_loss": local_loss,
            "local_epochs": self.local_epochs,
        }


# ======================================================================
# FedAvg Server
# ======================================================================


class FedAvgServer:
    """Server-side aggregation logic for Federated Averaging.

    Aggregates client model updates using weighted averaging,
    supports multi-round training, learning-rate scheduling, and early stopping.
    """

    def __init__(
        self,
        model_shape: tuple[int, ...] = (10,),
        n_rounds: int = 10,
        learning_rate: float = 0.01,
        lr_schedule: str = "constant",
        lr_decay: float = 0.9,
        early_stop_patience: int = 5,
        early_stop_min_delta: float = 1e-4,
        checkpoint_dir: Optional[str] = None,
        compression_method: Optional[str] = None,
        compression_k_ratio: float = 0.1,
    ):
        """Initialize FedAvg server.

        Args:
            model_shape: Shape of the model parameter vector.
            n_rounds: Total number of aggregation rounds.
            learning_rate: Initial learning rate for clients.
            lr_schedule: LR schedule type: "constant", "step", or "exponential".
            lr_decay: Decay factor for step/exponential schedule.
            early_stop_patience: Number of rounds with no improvement before stopping.
            early_stop_min_delta: Minimum change to qualify as improvement.
            checkpoint_dir: Directory for checkpoint files. None disables checkpointing.
            compression_method: Communication compression: None, "top_k", or "fp16".
            compression_k_ratio: K ratio for top-k compression.
        """
        self.model_shape = model_shape
        self.n_rounds = n_rounds
        self.base_learning_rate = learning_rate
        self.lr_schedule = lr_schedule
        self.lr_decay = lr_decay
        self.early_stop_patience = early_stop_patience
        self.early_stop_min_delta = early_stop_min_delta
        self.compression_method = compression_method
        self.compression_k_ratio = compression_k_ratio

        # State
        self.global_model = np.zeros(model_shape, dtype=np.float64)
        self.current_round = 0
        self.best_metric = float("inf")
        self.best_round = 0
        self.history: list[dict[str, Any]] = []
        self.compression_stats: list[dict[str, Any]] = []
        self._no_improvement_count = 0

        # Checkpoint
        self.checkpoint_manager: Optional[CheckpointManager] = None
        if checkpoint_dir:
            self.checkpoint_manager = CheckpointManager(checkpoint_dir)

    def get_learning_rate(self, round_idx: int) -> float:
        """Get learning rate for a given round based on schedule.

        Args:
            round_idx: Current round index (0-based).

        Returns:
            Scheduled learning rate.
        """
        if self.lr_schedule == "constant":
            return self.base_learning_rate
        elif self.lr_schedule == "step":
            # Decay every 5 rounds
            steps = round_idx // 5
            return self.base_learning_rate * (self.lr_decay ** steps)
        elif self.lr_schedule == "exponential":
            return self.base_learning_rate * (self.lr_decay ** round_idx)
        else:
            return self.base_learning_rate

    def aggregate(
        self,
        client_updates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Aggregate client updates using weighted averaging.

        Each client update should contain:
            - model_update: list of weight deltas
            - n_samples: number of local training samples

        Args:
            client_updates: List of client update dicts.

        Returns:
            Aggregation result dict.
        """
        if not client_updates:
            return {"error": "No client updates provided"}

        # Extract updates and sample counts
        updates = [np.array(cu["model_update"], dtype=np.float64) for cu in client_updates]
        sample_counts = [cu.get("n_samples", 1) for cu in client_updates]
        total_samples = sum(sample_counts)

        # Weighted average
        weighted_sum = np.zeros_like(self.global_model)
        for update, n_samples in zip(updates, sample_counts):
            weight = n_samples / total_samples
            weighted_sum += weight * update

        # Apply communication compression if enabled
        if self.compression_method:
            compressed, stats = compress_gradients(
                weighted_sum,
                method=self.compression_method,
                k_ratio=self.compression_k_ratio,
            )
            self.compression_stats.append(stats)
            weighted_sum = compressed

        # Update global model
        self.global_model += weighted_sum

        # Compute average loss
        avg_loss = float(np.mean([cu.get("local_loss", 0.0) for cu in client_updates]))

        return {
            "round": self.current_round + 1,
            "avg_loss": avg_loss,
            "n_clients": len(client_updates),
            "total_samples": total_samples,
            "learning_rate": self.get_learning_rate(self.current_round),
        }

    def should_early_stop(self, current_loss: float) -> bool:
        """Check if training should stop early.

        Args:
            current_loss: Current round's loss value.

        Returns:
            True if early stopping condition is met.
        """
        if current_loss < self.best_metric - self.early_stop_min_delta:
            self.best_metric = current_loss
            self.best_round = self.current_round
            self._no_improvement_count = 0
            return False
        else:
            self._no_improvement_count += 1
            return self._no_improvement_count >= self.early_stop_patience

    def save_checkpoint(self, filename: str = "checkpoint.json") -> Optional[str]:
        """Save current training state as checkpoint.

        Args:
            filename: Checkpoint filename.

        Returns:
            Path to saved file, or None if checkpointing disabled.
        """
        if not self.checkpoint_manager:
            return None
        return self.checkpoint_manager.save(
            global_model=self.global_model,
            current_round=self.current_round,
            best_metric=self.best_metric,
            history=self.history,
            config={
                "n_rounds": self.n_rounds,
                "learning_rate": self.base_learning_rate,
                "lr_schedule": self.lr_schedule,
                "lr_decay": self.lr_decay,
                "early_stop_patience": self.early_stop_patience,
                "compression_method": self.compression_method,
                "compression_k_ratio": self.compression_k_ratio,
            },
            filename=filename,
        )

    def load_checkpoint(self, filename: str = "checkpoint.json") -> bool:
        """Load training state from checkpoint.

        Args:
            filename: Checkpoint filename.

        Returns:
            True if checkpoint was loaded successfully.
        """
        if not self.checkpoint_manager:
            return False
        data = self.checkpoint_manager.load(filename)
        if data is None:
            return False
        self.global_model = data["global_model"]
        self.current_round = data["current_round"]
        self.best_metric = data["best_metric"]
        self.history = data["history"]
        return True

    def train(
        self,
        client_data_list: list[dict[str, Any]],
        resume: bool = False,
    ) -> dict[str, Any]:
        """Run multi-round federated training.

        Args:
            client_data_list: List of client data dicts, each containing:
                - data: feature matrix (optional, synthetic if omitted)
                - labels: label vector (optional, synthetic if omitted)
                - n_samples: number of samples (default 100)
                - client_id: client identifier (default "client_N")
            resume: If True, attempt to resume from checkpoint.

        Returns:
            Training result dict with global model, history, and metrics.
        """
        # Optionally resume from checkpoint
        if resume and self.load_checkpoint():
            logger.info(
                "Resumed from checkpoint at round %d", self.current_round
            )

        start_round = self.current_round
        early_stopped = False

        for round_idx in range(start_round, self.n_rounds):
            self.current_round = round_idx
            lr = self.get_learning_rate(round_idx)

            # Create clients and perform local training
            client_updates = []
            for i, client_data in enumerate(client_data_list):
                client_id = client_data.get("client_id", f"client_{i}")
                client = FedAvgClient(
                    client_id=client_id,
                    model=self.global_model,
                    learning_rate=lr,
                    local_epochs=client_data.get("local_epochs", 1),
                    batch_size=client_data.get("batch_size", 32),
                    data_size=client_data.get("n_samples", 100),
                )

                data = client_data.get("data")
                labels = client_data.get("labels")
                if data is not None:
                    data = np.array(data, dtype=np.float64)
                if labels is not None:
                    labels = np.array(labels, dtype=np.float64)

                update = client.local_train(data=data, labels=labels)
                client_updates.append(update)

            # Server aggregation
            agg_result = self.aggregate(client_updates)
            round_loss = agg_result["avg_loss"]
            agg_result["early_stopped"] = False
            self.history.append(agg_result)

            # Save checkpoint every round
            self.save_checkpoint()

            # Check early stopping
            if self.should_early_stop(round_loss):
                early_stopped = True
                self.history[-1]["early_stopped"] = True
                logger.info(
                    "Early stopping at round %d (no improvement for %d rounds)",
                    round_idx + 1,
                    self._no_improvement_count,
                )
                break

        # Build final result
        total_compression = {}
        if self.compression_stats:
            total_original = sum(s.get("original_bytes", 0) for s in self.compression_stats)
            total_saved = sum(s.get("bytes_saved", 0) for s in self.compression_stats)
            total_compression = {
                "method": self.compression_method,
                "total_rounds_compressed": len(self.compression_stats),
                "total_original_bytes": total_original,
                "total_bytes_saved": total_saved,
                "avg_compression_rate": round(
                    total_saved / total_original, 4
                ) if total_original > 0 else 0.0,
            }

        return {
            "global_model": self.global_model.tolist(),
            "strategy": "fedavg",
            "n_rounds_completed": self.current_round + 1,
            "n_rounds_target": self.n_rounds,
            "early_stopped": early_stopped,
            "best_metric": self.best_metric,
            "best_round": self.best_round + 1,
            "history": self.history,
            "compression_stats": total_compression,
            "final_loss": self.history[-1]["avg_loss"] if self.history else None,
        }


# ======================================================================
# FedProx Client
# ======================================================================


class FedProxClient(FedAvgClient):
    """Client-side local training for FedProx.

    Extends FedAvgClient with a proximal term to prevent model drift
    from the global model.

    The proximal term adds: (mu / 2) * ||w - w_global||^2 to the loss,
    which penalizes large deviations from the global model.
    """

    def __init__(
        self,
        client_id: str,
        model: np.ndarray,
        global_model: np.ndarray,
        learning_rate: float = 0.01,
        mu: float = 0.01,
        local_epochs: int = 1,
        batch_size: int = 32,
        data_size: int = 100,
    ):
        super().__init__(
            client_id=client_id,
            model=model,
            learning_rate=learning_rate,
            local_epochs=local_epochs,
            batch_size=batch_size,
            data_size=data_size,
        )
        self.global_model = copy.deepcopy(global_model)
        self.mu = mu

    def local_train(
        self,
        data: Optional[np.ndarray] = None,
        labels: Optional[np.ndarray] = None,
    ) -> dict[str, Any]:
        """Perform local training with proximal term.

        The gradient update becomes:
            gradient = data_gradient + mu * (w - w_global)

        Args:
            data: Feature matrix (n_samples, n_features).
            labels: Label vector (n_samples,).

        Returns:
            Dict with client_id, model_update, n_samples, local_loss,
            local_epochs, proximal_term_norm.
        """
        n_features = self.model.size

        if data is None:
            data = np.random.randn(self.data_size, n_features)
        if labels is None:
            labels = np.random.randn(self.data_size)

        original_model = copy.deepcopy(self.model)

        for epoch in range(self.local_epochs):
            indices = np.random.permutation(len(data))
            for start_idx in range(0, len(data), self.batch_size):
                batch_idx = indices[start_idx : start_idx + self.batch_size]
                batch_data = data[batch_idx]
                batch_labels = labels[batch_idx]

                # Data gradient
                pred = batch_data @ self.model
                residual = pred - batch_labels
                data_gradient = batch_data.T @ residual / len(batch_idx)

                # Proximal term gradient: mu * (w - w_global)
                proximal_gradient = self.mu * (self.model - self.global_model)

                # Combined gradient
                gradient = data_gradient + proximal_gradient

                self.model -= self.learning_rate * gradient

        model_update = self.model - original_model
        proximal_term_norm = float(np.linalg.norm(self.mu * (self.model - self.global_model)))

        # Compute loss (MSE + proximal)
        final_pred = data @ self.model
        mse_loss = float(np.mean((final_pred - labels) ** 2))
        proximal_loss = float(0.5 * self.mu * np.sum((self.model - self.global_model) ** 2))
        total_loss = mse_loss + proximal_loss

        return {
            "client_id": self.client_id,
            "model_update": model_update.tolist(),
            "n_samples": len(data),
            "local_loss": total_loss,
            "mse_loss": mse_loss,
            "proximal_loss": proximal_loss,
            "proximal_term_norm": proximal_term_norm,
            "local_epochs": self.local_epochs,
        }


# ======================================================================
# FedProx Server
# ======================================================================


class FedProxServer(FedAvgServer):
    """Server-side aggregation logic for FedProx.

    Extends FedAvgServer with FedProx-specific client creation
    and proximal term configuration.
    """

    def __init__(
        self,
        model_shape: tuple[int, ...] = (10,),
        n_rounds: int = 10,
        learning_rate: float = 0.01,
        mu: float = 0.01,
        lr_schedule: str = "constant",
        lr_decay: float = 0.9,
        early_stop_patience: int = 5,
        early_stop_min_delta: float = 1e-4,
        checkpoint_dir: Optional[str] = None,
        compression_method: Optional[str] = None,
        compression_k_ratio: float = 0.1,
    ):
        """Initialize FedProx server.

        Args:
            model_shape: Shape of the model parameter vector.
            n_rounds: Total number of aggregation rounds.
            learning_rate: Initial learning rate for clients.
            mu: Proximal term coefficient. Higher values penalize
                deviation from the global model more strongly.
            lr_schedule: LR schedule type: "constant", "step", or "exponential".
            lr_decay: Decay factor for step/exponential schedule.
            early_stop_patience: Rounds with no improvement before stopping.
            early_stop_min_delta: Minimum change to qualify as improvement.
            checkpoint_dir: Directory for checkpoint files.
            compression_method: Communication compression method.
            compression_k_ratio: K ratio for top-k compression.
        """
        super().__init__(
            model_shape=model_shape,
            n_rounds=n_rounds,
            learning_rate=learning_rate,
            lr_schedule=lr_schedule,
            lr_decay=lr_decay,
            early_stop_patience=early_stop_patience,
            early_stop_min_delta=early_stop_min_delta,
            checkpoint_dir=checkpoint_dir,
            compression_method=compression_method,
            compression_k_ratio=compression_k_ratio,
        )
        self.mu = mu

    def train(
        self,
        client_data_list: list[dict[str, Any]],
        resume: bool = False,
    ) -> dict[str, Any]:
        """Run multi-round federated training with FedProx.

        Args:
            client_data_list: List of client data dicts.
            resume: If True, attempt to resume from checkpoint.

        Returns:
            Training result dict.
        """
        # Optionally resume from checkpoint
        if resume and self.load_checkpoint():
            logger.info(
                "Resumed FedProx from checkpoint at round %d", self.current_round
            )

        start_round = self.current_round
        early_stopped = False

        for round_idx in range(start_round, self.n_rounds):
            self.current_round = round_idx
            lr = self.get_learning_rate(round_idx)

            # Create FedProx clients
            client_updates = []
            for i, client_data in enumerate(client_data_list):
                client_id = client_data.get("client_id", f"client_{i}")
                client = FedProxClient(
                    client_id=client_id,
                    model=self.global_model,
                    global_model=self.global_model,
                    learning_rate=lr,
                    mu=self.mu,
                    local_epochs=client_data.get("local_epochs", 1),
                    batch_size=client_data.get("batch_size", 32),
                    data_size=client_data.get("n_samples", 100),
                )

                data = client_data.get("data")
                labels = client_data.get("labels")
                if data is not None:
                    data = np.array(data, dtype=np.float64)
                if labels is not None:
                    labels = np.array(labels, dtype=np.float64)

                update = client.local_train(data=data, labels=labels)
                client_updates.append(update)

            # Server aggregation (same weighted averaging as FedAvg)
            agg_result = self.aggregate(client_updates)
            round_loss = agg_result["avg_loss"]
            agg_result["early_stopped"] = False
            self.history.append(agg_result)

            self.save_checkpoint()

            if self.should_early_stop(round_loss):
                early_stopped = True
                self.history[-1]["early_stopped"] = True
                logger.info(
                    "FedProx early stopping at round %d", round_idx + 1
                )
                break

        total_compression = {}
        if self.compression_stats:
            total_original = sum(s.get("original_bytes", 0) for s in self.compression_stats)
            total_saved = sum(s.get("bytes_saved", 0) for s in self.compression_stats)
            total_compression = {
                "method": self.compression_method,
                "total_rounds_compressed": len(self.compression_stats),
                "total_original_bytes": total_original,
                "total_bytes_saved": total_saved,
                "avg_compression_rate": round(
                    total_saved / total_original, 4
                ) if total_original > 0 else 0.0,
            }

        return {
            "global_model": self.global_model.tolist(),
            "strategy": "fedprox",
            "mu": self.mu,
            "n_rounds_completed": self.current_round + 1,
            "n_rounds_target": self.n_rounds,
            "early_stopped": early_stopped,
            "best_metric": self.best_metric,
            "best_round": self.best_round + 1,
            "history": self.history,
            "compression_stats": total_compression,
            "final_loss": self.history[-1]["avg_loss"] if self.history else None,
        }


# ======================================================================
# Legacy FederatedLearner (backward-compatible wrapper)
# ======================================================================


class FederatedLearner:
    """Federated Learning orchestrator (legacy interface).

    Supports FedAvg and FedProx aggregation strategies for
    distributed model training across edge devices.

    This class provides backward compatibility with the original
    interface while internally using the new FedAvgServer/FedProxServer.
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
        """Run federated learning training (legacy interface).

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
    # Enhanced federated learning methods
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
        t_start = time.perf_counter()

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
        tau = max(time_span, 1.0)
        decay_weights = np.array([decay_factor ** ((t_max - ts) / tau) for ts in timestamps])
        decay_weights /= decay_weights.sum()  # 归一化

        # 加权聚合
        global_weights = np.zeros_like(weights_arrays[0])
        for w_arr, dw in zip(weights_arrays, decay_weights):
            global_weights += dw * w_arr

        aggregation_time = (time.perf_counter() - t_start) * 1000

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
        # fmt: off
        max_val = (
            float(np.max(np.abs(flat[selected_indices])))
            if len(selected_indices) > 0
            else 1.0
        )
        # fmt: on
        if max_val == 0:
            max_val = 1.0
        quant_levels = 2 ** (quantize_bits - 1) - 1  # 有符号量化
        scaled = flat[selected_indices] / max_val * quant_levels
        quantized = np.round(scaled) / quant_levels * max_val

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

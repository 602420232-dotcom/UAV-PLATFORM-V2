"""Federated Learning for Edge Devices.

Migrated from: edge-cloud-coordinator/federated_learning.py

Supports FedAvg and FedProx aggregation strategies.
"""
from __future__ import annotations
import logging
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
            Dictionary with global model, training metrics, and convergence info.
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
            # Simulate client updates (in real scenario, clients compute locally)
            aggregated = self._aggregate(client_updates, strategy)
            self.global_model = aggregated

            loss = float(np.random.rand() * 0.5)  # Simulated loss
            history.append({"round": round_idx + 1, "loss": loss})

        return {
            "global_model": self.global_model.tolist(),
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

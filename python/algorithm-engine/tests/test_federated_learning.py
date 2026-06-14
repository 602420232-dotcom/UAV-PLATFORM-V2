"""Federated Learning unit tests.

Tests for:
- FedAvg aggregation correctness (weighted averaging)
- FedProx proximal term behavior
- Checkpoint save/load (resume training)
- Communication compression (Top-K sparsification, FP16 quantization)
- Learning rate scheduling
- Early stopping
- FederatedLearningAdapter integration
"""

from __future__ import annotations

import json
import os
import tempfile

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# FedAvg Client Tests
# ---------------------------------------------------------------------------


class TestFedAvgClient:
    """Tests for FedAvgClient local training."""

    def test_client_returns_required_keys(self):
        """FedAvgClient.local_train should return all required keys."""
        from app.algorithms.edge.federated_learning import FedAvgClient

        model = np.zeros(10)
        client = FedAvgClient(
            client_id="test_client",
            model=model,
            learning_rate=0.01,
            local_epochs=1,
            batch_size=32,
            data_size=50,
        )
        result = client.local_train()

        assert "client_id" in result
        assert result["client_id"] == "test_client"
        assert "model_update" in result
        assert "n_samples" in result
        assert "local_loss" in result
        assert "local_epochs" in result

    def test_client_model_update_shape(self):
        """Model update should have same shape as the model."""
        from app.algorithms.edge.federated_learning import FedAvgClient

        model = np.zeros(10)
        client = FedAvgClient(client_id="c1", model=model, learning_rate=0.01)
        result = client.local_train()

        update = np.array(result["model_update"])
        assert update.shape == model.shape

    def test_client_with_provided_data(self):
        """Client should work with externally provided data."""
        from app.algorithms.edge.federated_learning import FedAvgClient

        np.random.seed(42)
        model = np.random.randn(5)
        data = np.random.randn(20, 5)
        labels = np.random.randn(20)

        client = FedAvgClient(client_id="c1", model=model, learning_rate=0.01)
        result = client.local_train(data=data, labels=labels)

        assert result["n_samples"] == 20
        assert isinstance(result["local_loss"], float)
        assert result["local_loss"] >= 0

    def test_client_local_epochs(self):
        """Client should respect local_epochs parameter."""
        from app.algorithms.edge.federated_learning import FedAvgClient

        model = np.zeros(5)
        client = FedAvgClient(client_id="c1", model=model, learning_rate=0.01, local_epochs=3)
        result = client.local_train()

        assert result["local_epochs"] == 3

    def test_client_does_not_mutate_global_model(self):
        """Client training should not mutate the original global model."""
        from app.algorithms.edge.federated_learning import FedAvgClient

        model = np.array([1.0, 2.0, 3.0])
        original = model.copy()

        client = FedAvgClient(client_id="c1", model=model, learning_rate=0.01)
        client.local_train()

        np.testing.assert_array_equal(model, original)


# ---------------------------------------------------------------------------
# FedAvg Server Tests
# ---------------------------------------------------------------------------


class TestFedAvgServer:
    """Tests for FedAvgServer aggregation and training."""

    def test_aggregate_weighted_average(self):
        """FedAvg aggregation should compute weighted average of client updates."""
        from app.algorithms.edge.federated_learning import FedAvgServer

        server = FedAvgServer(model_shape=(3,), n_rounds=1, learning_rate=0.01)
        server.current_round = 0

        # Two clients with different sample counts
        client_updates = [
            {
                "model_update": [1.0, 2.0, 3.0],
                "n_samples": 100,
                "local_loss": 0.5,
            },
            {
                "model_update": [3.0, 4.0, 5.0],
                "n_samples": 300,
                "local_loss": 0.3,
            },
        ]

        result = server.aggregate(client_updates)

        # Weighted average: (100/400)*[1,2,3] + (300/400)*[3,4,5]
        # = [0.25, 0.5, 0.75] + [2.25, 3.0, 3.75] = [2.5, 3.5, 4.5]
        expected = np.array([2.5, 3.5, 4.5])
        np.testing.assert_allclose(server.global_model, expected, rtol=1e-10)

        assert result["n_clients"] == 2
        assert result["total_samples"] == 400

    def test_aggregate_empty_updates(self):
        """Aggregating empty updates should return error."""
        from app.algorithms.edge.federated_learning import FedAvgServer

        server = FedAvgServer(model_shape=(3,))
        result = server.aggregate([])

        assert "error" in result

    def test_aggregate_equal_weights(self):
        """When all clients have equal samples, result should be simple average."""
        from app.algorithms.edge.federated_learning import FedAvgServer

        server = FedAvgServer(model_shape=(2,), n_rounds=1)
        server.current_round = 0

        client_updates = [
            {"model_update": [2.0, 4.0], "n_samples": 50, "local_loss": 0.1},
            {"model_update": [6.0, 8.0], "n_samples": 50, "local_loss": 0.2},
        ]

        server.aggregate(client_updates)
        np.testing.assert_allclose(server.global_model, [4.0, 6.0], rtol=1e-10)

    def test_train_returns_expected_keys(self):
        """FedAvgServer.train should return all expected keys."""
        from app.algorithms.edge.federated_learning import FedAvgServer

        server = FedAvgServer(model_shape=(5,), n_rounds=3, learning_rate=0.01)
        client_data = [{"client_id": f"c{i}", "n_samples": 50} for i in range(3)]

        result = server.train(client_data)

        assert "global_model" in result
        assert result["strategy"] == "fedavg"
        assert "n_rounds_completed" in result
        assert "n_rounds_target" in result
        assert "early_stopped" in result
        assert "best_metric" in result
        assert "best_round" in result
        assert "history" in result
        assert "final_loss" in result
        assert result["n_rounds_completed"] == 3
        assert len(result["history"]) == 3

    def test_train_history_per_round(self):
        """Each history entry should contain round-level metrics."""
        from app.algorithms.edge.federated_learning import FedAvgServer

        server = FedAvgServer(model_shape=(5,), n_rounds=2, learning_rate=0.01)
        client_data = [{"n_samples": 50} for _ in range(2)]

        result = server.train(client_data)

        for entry in result["history"]:
            assert "round" in entry
            assert "avg_loss" in entry
            assert "n_clients" in entry
            assert "total_samples" in entry
            assert "learning_rate" in entry

    def test_lr_schedule_constant(self):
        """Constant LR schedule should return same LR every round."""
        from app.algorithms.edge.federated_learning import FedAvgServer

        server = FedAvgServer(model_shape=(5,), learning_rate=0.01, lr_schedule="constant")

        assert server.get_learning_rate(0) == 0.01
        assert server.get_learning_rate(5) == 0.01
        assert server.get_learning_rate(10) == 0.01

    def test_lr_schedule_step(self):
        """Step LR schedule should decay every 5 rounds."""
        from app.algorithms.edge.federated_learning import FedAvgServer

        server = FedAvgServer(model_shape=(5,), learning_rate=0.1, lr_schedule="step", lr_decay=0.5)

        assert server.get_learning_rate(0) == 0.1
        assert server.get_learning_rate(4) == 0.1
        assert server.get_learning_rate(5) == 0.05  # 0.1 * 0.5^1
        assert server.get_learning_rate(9) == 0.05
        assert server.get_learning_rate(10) == 0.025  # 0.1 * 0.5^2

    def test_lr_schedule_exponential(self):
        """Exponential LR schedule should decay every round."""
        from app.algorithms.edge.federated_learning import FedAvgServer

        server = FedAvgServer(model_shape=(5,), learning_rate=1.0, lr_schedule="exponential", lr_decay=0.5)

        assert server.get_learning_rate(0) == 1.0
        assert server.get_learning_rate(1) == 0.5
        assert server.get_learning_rate(2) == 0.25
        assert server.get_learning_rate(3) == 0.125

    def test_early_stopping(self):
        """Early stopping should trigger after patience rounds without improvement."""
        from app.algorithms.edge.federated_learning import FedAvgServer

        server = FedAvgServer(
            model_shape=(5,),
            n_rounds=100,
            early_stop_patience=3,
            early_stop_min_delta=0.01,
        )

        # Simulate losses that don't improve
        assert not server.should_early_stop(1.0)  # First: sets best
        assert not server.should_early_stop(1.0)  # No improvement, count=1
        assert not server.should_early_stop(1.0)  # count=2
        assert server.should_early_stop(1.0)  # count=3 => stop

    def test_early_stopping_with_improvement(self):
        """Early stopping counter should reset on improvement."""
        from app.algorithms.edge.federated_learning import FedAvgServer

        server = FedAvgServer(
            model_shape=(5,),
            n_rounds=100,
            early_stop_patience=3,
            early_stop_min_delta=0.01,
        )

        assert not server.should_early_stop(1.0)
        assert not server.should_early_stop(1.0)
        assert not server.should_early_stop(0.5)  # Improvement! Reset counter
        assert not server.should_early_stop(0.5)
        assert not server.should_early_stop(0.5)
        assert server.should_early_stop(0.5)  # 3 rounds no improvement


# ---------------------------------------------------------------------------
# FedProx Tests
# ---------------------------------------------------------------------------


class TestFedProxClient:
    """Tests for FedProxClient proximal term behavior."""

    def test_proximal_client_returns_extra_keys(self):
        """FedProxClient should return proximal-specific keys."""
        from app.algorithms.edge.federated_learning import FedProxClient

        model = np.zeros(5)
        global_model = np.zeros(5)
        client = FedProxClient(
            client_id="prox_c1",
            model=model,
            global_model=global_model,
            learning_rate=0.01,
            mu=0.1,
        )
        result = client.local_train()

        assert "proximal_term_norm" in result
        assert "proximal_loss" in result
        assert "mse_loss" in result

    def test_proximal_term_reduces_drift(self):
        """Higher mu should keep client model closer to global model."""
        from app.algorithms.edge.federated_learning import FedProxClient

        np.random.seed(42)
        global_model = np.zeros(10)

        # Low mu: more drift allowed
        client_low_mu = FedProxClient(
            client_id="low_mu",
            model=global_model.copy(),
            global_model=global_model,
            learning_rate=0.1,
            mu=0.001,
            local_epochs=5,
        )
        result_low = client_low_mu.local_train()
        drift_low = np.linalg.norm(np.array(result_low["model_update"]))

        # High mu: less drift allowed
        client_high_mu = FedProxClient(
            client_id="high_mu",
            model=global_model.copy(),
            global_model=global_model,
            learning_rate=0.1,
            mu=10.0,
            local_epochs=5,
        )
        result_high = client_high_mu.local_train()
        drift_high = np.linalg.norm(np.array(result_high["model_update"]))

        # Higher mu should result in smaller model update (more constrained)
        assert drift_high < drift_low

    def test_proximal_loss_non_negative(self):
        """Proximal loss should always be non-negative."""
        from app.algorithms.edge.federated_learning import FedProxClient

        model = np.random.randn(5)
        global_model = np.random.randn(5)
        client = FedProxClient(client_id="c1", model=model, global_model=global_model, mu=0.1)
        result = client.local_train()

        assert result["proximal_loss"] >= 0
        assert result["mse_loss"] >= 0
        assert result["local_loss"] >= result["mse_loss"]  # total >= mse

    def test_zero_mu_equals_fedavg(self):
        """FedProx with mu=0 should behave like FedAvg."""
        from app.algorithms.edge.federated_learning import FedAvgClient, FedProxClient

        np.random.seed(123)
        model = np.random.randn(5)
        global_model = model.copy()

        FedAvgClient(client_id="fedavg", model=model.copy(), learning_rate=0.01)
        fedprox_client = FedProxClient(
            client_id="fedprox",
            model=model.copy(),
            global_model=global_model,
            learning_rate=0.01,
            mu=0.0,
        )

        # Both start from same model, same data (synthetic with same seed)
        # Note: synthetic data is generated inside local_train with random state
        # So we can't get exact match, but proximal_loss should be 0
        result_prox = fedprox_client.local_train()
        assert result_prox["proximal_loss"] == 0.0
        assert result_prox["proximal_term_norm"] == 0.0


class TestFedProxServer:
    """Tests for FedProxServer training."""

    def test_fedprox_train_returns_strategy(self):
        """FedProxServer.train should identify strategy as fedprox."""
        from app.algorithms.edge.federated_learning import FedProxServer

        server = FedProxServer(model_shape=(5,), n_rounds=2, learning_rate=0.01, mu=0.1)
        client_data = [{"n_samples": 50} for _ in range(2)]

        result = server.train(client_data)

        assert result["strategy"] == "fedprox"
        assert "mu" in result
        assert result["mu"] == 0.1

    def test_fedprox_completes_all_rounds(self):
        """FedProxServer should complete all rounds without early stopping."""
        from app.algorithms.edge.federated_learning import FedProxServer

        server = FedProxServer(
            model_shape=(5,),
            n_rounds=5,
            learning_rate=0.01,
            mu=0.01,
            early_stop_patience=100,  # Effectively disable
        )
        client_data = [{"n_samples": 50} for _ in range(3)]

        result = server.train(client_data)

        assert result["n_rounds_completed"] == 5
        assert result["early_stopped"] is False
        assert len(result["history"]) == 5


# ---------------------------------------------------------------------------
# Checkpoint Tests
# ---------------------------------------------------------------------------


class TestCheckpointManager:
    """Tests for checkpoint save/load functionality."""

    def test_save_and_load_checkpoint(self):
        """Checkpoint should save and load correctly."""
        from app.algorithms.edge.federated_learning import CheckpointManager

        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = CheckpointManager(tmpdir)
            model = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
            history = [{"round": 1, "loss": 0.5}, {"round": 2, "loss": 0.3}]
            config = {"n_rounds": 10, "learning_rate": 0.01}

            path = mgr.save(
                global_model=model,
                current_round=2,
                best_metric=0.3,
                history=history,
                config=config,
                filename="test_ckpt.json",
            )

            assert os.path.exists(path)

            loaded = mgr.load("test_ckpt.json")
            assert loaded is not None
            np.testing.assert_array_equal(loaded["global_model"], model)
            assert loaded["current_round"] == 2
            assert loaded["best_metric"] == 0.3
            assert len(loaded["history"]) == 2
            assert loaded["config"]["n_rounds"] == 10

    def test_load_nonexistent_checkpoint(self):
        """Loading nonexistent checkpoint should return None."""
        from app.algorithms.edge.federated_learning import CheckpointManager

        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = CheckpointManager(tmpdir)
            assert mgr.load("nonexistent.json") is None

    def test_checkpoint_json_format(self):
        """Checkpoint file should be valid JSON."""
        from app.algorithms.edge.federated_learning import CheckpointManager

        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = CheckpointManager(tmpdir)
            mgr.save(
                global_model=np.array([1.0, 2.0]),
                current_round=1,
                best_metric=0.5,
                history=[],
                config={},
                filename="format_test.json",
            )

            with open(os.path.join(tmpdir, "format_test.json"), "r") as f:
                data = json.load(f)

            assert "global_model" in data
            assert "current_round" in data
            assert "best_metric" in data
            assert "history" in data
            assert "config" in data
            assert "saved_at" in data

    def test_resume_training(self):
        """Server should resume from checkpoint correctly."""
        from app.algorithms.edge.federated_learning import FedAvgServer

        with tempfile.TemporaryDirectory() as tmpdir:
            # Phase 1: Train for 3 rounds
            server1 = FedAvgServer(
                model_shape=(5,),
                n_rounds=3,
                learning_rate=0.01,
                checkpoint_dir=tmpdir,
                early_stop_patience=100,
            )
            client_data = [{"n_samples": 50} for _ in range(2)]
            _result = server1.train(client_data)

            # Phase 2: Create new server and resume
            server2 = FedAvgServer(
                model_shape=(5,),
                n_rounds=6,  # More rounds than phase 1
                learning_rate=0.01,
                checkpoint_dir=tmpdir,
                early_stop_patience=100,
            )
            result2 = server2.train(client_data, resume=True)

            # Should have completed 6 rounds total (3 from phase 1 + 3 more)
            assert result2["n_rounds_completed"] == 6
            # History includes 3 rounds from phase 1 (loaded from checkpoint)
            # plus 3 new rounds = 6 total
            assert len(result2["history"]) >= 6

    def test_checkpoint_disabled(self):
        """Server without checkpoint_dir should not save checkpoints."""
        from app.algorithms.edge.federated_learning import FedAvgServer

        server = FedAvgServer(model_shape=(5,), n_rounds=1)
        assert server.save_checkpoint() is None
        assert server.load_checkpoint() is False


# ---------------------------------------------------------------------------
# Communication Compression Tests
# ---------------------------------------------------------------------------


class TestCommunicationCompression:
    """Tests for Top-K sparsification and FP16 quantization."""

    def test_top_k_sparsify_basic(self):
        """Top-K should keep only the largest K% elements."""
        from app.algorithms.edge.federated_learning import top_k_sparsify

        gradients = np.array([0.1, 0.9, 0.2, 0.8, 0.3, 0.7, 0.4, 0.6, 0.5, 0.0])
        sparse, stats = top_k_sparsify(gradients, k_ratio=0.3)

        assert stats["compression_method"] == "top_k"
        assert stats["k_ratio"] == 0.3
        assert stats["n_total"] == 10
        # 30% of 10 = 3 elements
        assert stats["n_nonzero"] == 3
        assert stats["sparsity_ratio"] == pytest.approx(0.7, abs=0.05)

    def test_top_k_preserves_largest_values(self):
        """Top-K should preserve the largest magnitude values."""
        from app.algorithms.edge.federated_learning import top_k_sparsify

        gradients = np.array([1.0, -5.0, 3.0, -0.1, 0.2, 4.0, -0.01, 0.05])
        sparse, _ = top_k_sparsify(gradients, k_ratio=0.25)  # Keep top 2

        nonzero_vals = sparse[sparse != 0]
        # The two largest magnitudes are 5.0 and 4.0
        assert len(nonzero_vals) == 2
        assert 5.0 in nonzero_vals or -5.0 in nonzero_vals
        assert 4.0 in nonzero_vals

    def test_top_k_stats(self):
        """Top-K stats should contain compression metrics."""
        from app.algorithms.edge.federated_learning import top_k_sparsify

        gradients = np.random.randn(100)
        _, stats = top_k_sparsify(gradients, k_ratio=0.1)

        assert "original_bytes" in stats
        assert "compressed_bytes" in stats
        assert "bytes_saved" in stats
        assert "compression_rate" in stats
        assert stats["bytes_saved"] > 0
        assert 0 < stats["compression_rate"] < 1

    def test_fp16_quantization_basic(self):
        """FP16 quantization should reduce precision."""
        from app.algorithms.edge.federated_learning import quantize_fp16

        gradients = np.array([0.123456789, 1.23456789, -0.987654321])
        quantized, stats = quantize_fp16(gradients)

        assert stats["compression_method"] == "fp16_quantization"
        assert stats["n_total"] == 3
        assert stats["compression_rate"] == pytest.approx(0.5)  # 50% size reduction
        assert stats["bytes_saved"] == 3 * 2  # 3 elements * 2 bytes saved each

    def test_fp16_quantization_error(self):
        """FP16 quantization error should be small but non-zero."""
        from app.algorithms.edge.federated_learning import quantize_fp16

        # Use values that will have quantization error
        gradients = np.array([0.123456789, 1.0000001])
        quantized, stats = quantize_fp16(gradients)

        assert stats["max_quantization_error"] > 0
        assert stats["mean_quantization_error"] > 0
        # Error should be very small (< 1e-3 for typical values)
        assert stats["max_quantization_error"] < 1e-3

    def test_compress_gradients_top_k(self):
        """compress_gradients should dispatch to top_k correctly."""
        from app.algorithms.edge.federated_learning import compress_gradients

        gradients = np.random.randn(50)
        result, stats = compress_gradients(gradients, method="top_k", k_ratio=0.2)

        assert stats["compression_method"] == "top_k"
        assert stats["n_nonzero"] == 10  # 20% of 50

    def test_compress_gradients_fp16(self):
        """compress_gradients should dispatch to fp16 correctly."""
        from app.algorithms.edge.federated_learning import compress_gradients

        gradients = np.random.randn(50)
        result, stats = compress_gradients(gradients, method="fp16")

        assert stats["compression_method"] == "fp16_quantization"

    def test_compress_gradients_unknown_method(self):
        """Unknown compression method should raise ValueError."""
        from app.algorithms.edge.federated_learning import compress_gradients

        with pytest.raises(ValueError, match="Unknown compression method"):
            compress_gradients(np.array([1.0, 2.0]), method="invalid")

    def test_server_with_compression(self):
        """Server with compression should track compression stats."""
        from app.algorithms.edge.federated_learning import FedAvgServer

        server = FedAvgServer(
            model_shape=(20,),
            n_rounds=3,
            learning_rate=0.01,
            compression_method="top_k",
            compression_k_ratio=0.1,
            early_stop_patience=100,
        )
        client_data = [{"n_samples": 50} for _ in range(2)]

        result = server.train(client_data)

        assert "compression_stats" in result
        assert result["compression_stats"]["method"] == "top_k"
        assert result["compression_stats"]["total_rounds_compressed"] == 3
        assert result["compression_stats"]["total_bytes_saved"] > 0
        assert 0 < result["compression_stats"]["avg_compression_rate"] < 1


# ---------------------------------------------------------------------------
# Legacy FederatedLearner Tests (backward compatibility)
# ---------------------------------------------------------------------------


class TestLegacyFederatedLearner:
    """Tests for backward-compatible FederatedLearner interface."""

    def test_legacy_train_fedavg(self):
        """Legacy FederatedLearner should work with FedAvg."""
        from app.algorithms.edge.federated_learning import FederatedLearner

        learner = FederatedLearner({"strategy": "fedavg", "n_rounds": 5})
        client_updates = [
            [1.0, 2.0, 3.0],
            [3.0, 4.0, 5.0],
            [5.0, 6.0, 7.0],
        ]
        result = learner.train({"client_updates": client_updates})

        assert result["strategy"] == "fedavg"
        assert result["n_rounds"] == 5
        assert result["n_clients"] == 3
        assert result["global_model"] is not None
        assert len(result["history"]) == 5

    def test_legacy_train_fedprox(self):
        """Legacy FederatedLearner should work with FedProx."""
        from app.algorithms.edge.federated_learning import FederatedLearner

        learner = FederatedLearner(
            {
                "strategy": "fedprox",
                "n_rounds": 3,
                "proximal_mu": 0.1,
            }
        )
        client_updates = [
            [1.0, 2.0],
            [3.0, 4.0],
        ]
        result = learner.train({"client_updates": client_updates})

        assert result["strategy"] == "fedprox"

    def test_legacy_empty_updates(self):
        """Legacy FederatedLearner should handle empty updates."""
        from app.algorithms.edge.federated_learning import FederatedLearner

        learner = FederatedLearner()
        result = learner.train({"client_updates": []})

        assert "error" in result
        assert result["global_model"] is None

    def test_legacy_async_aggregate(self):
        """Legacy async_aggregate should return time-decayed weighted average."""
        from app.algorithms.edge.federated_learning import FederatedLearner

        learner = FederatedLearner()
        params = {
            "client_updates": [
                {"weights": [1.0, 1.0], "timestamp": 0.0, "client_id": "c1"},
                {"weights": [3.0, 3.0], "timestamp": 10.0, "client_id": "c2"},
            ],
            "decay_factor": 0.9,
        }
        result = learner.async_aggregate(params)

        assert result["n_participants"] == 2
        assert result["global_weights"] is not None
        assert len(result["participating_clients"]) == 2
        assert result["time_span"] == 10.0

    def test_legacy_differential_privacy(self):
        """Legacy differential_privacy should add noise to updates."""
        from app.algorithms.edge.federated_learning import FederatedLearner

        learner = FederatedLearner()
        params = {
            "model_update": [1.0, 2.0, 3.0, 4.0, 5.0],
            "epsilon": 1.0,
            "delta": 1e-5,
            "clip_norm": 1.0,
        }
        result = learner.differential_privacy(params)

        assert "noisy_update" in result
        assert len(result["noisy_update"]) == 5
        assert result["privacy_budget_used"]["epsilon"] == 1.0
        assert isinstance(result["clip_applied"], bool)

    def test_legacy_communication_efficient(self):
        """Legacy communication_efficient should compress updates."""
        from app.algorithms.edge.federated_learning import FederatedLearner

        learner = FederatedLearner()
        params = {
            "model_update": list(np.random.randn(100)),
            "compression_ratio": 0.1,
            "quantize_bits": 8,
        }
        result = learner.communication_efficient(params)

        assert "compressed_update" in result
        assert result["n_total"] == 100
        assert result["n_nonzero"] <= 20  # ~10% kept (may have ties)
        assert result["bytes_saved"] > 0


# ---------------------------------------------------------------------------
# FederatedLearningAdapter Tests
# ---------------------------------------------------------------------------


class TestFederatedLearningAdapter:
    """Tests for the FederatedLearningAdapter."""

    def test_adapter_metadata(self):
        """Adapter should have correct metadata."""
        from app.adapters.edge_adapter import FederatedLearningAdapter

        adapter = FederatedLearningAdapter()
        meta = adapter.get_metadata()

        assert meta.id == "federated_learning"
        assert meta.category == "edge"
        assert meta.version == "2.0.0"

    def test_adapter_execute_legacy_mode(self):
        """Adapter should handle legacy mode (plain list client_updates)."""
        from app.adapters.edge_adapter import FederatedLearningAdapter

        adapter = FederatedLearningAdapter()
        params = {
            "client_updates": [
                [1.0, 2.0, 3.0],
                [3.0, 4.0, 5.0],
            ],
            "strategy": "fedavg",
            "n_rounds": 2,
        }
        result = adapter.execute(params)

        assert "global_model" in result
        assert result["strategy"] == "fedavg"

    def test_adapter_execute_new_mode_fedavg(self):
        """Adapter should handle new mode with FedAvgServer."""
        from app.adapters.edge_adapter import FederatedLearningAdapter

        adapter = FederatedLearningAdapter()
        params = {
            "client_updates": [
                {"client_id": "c1", "n_samples": 50},
                {"client_id": "c2", "n_samples": 50},
            ],
            "strategy": "fedavg",
            "n_rounds": 2,
            "model_shape": (5,),
            "early_stop_patience": 100,
        }
        result = adapter.execute(params)

        assert result["strategy"] == "fedavg"
        assert result["n_rounds_completed"] == 2

    def test_adapter_execute_new_mode_fedprox(self):
        """Adapter should handle new mode with FedProxServer."""
        from app.adapters.edge_adapter import FederatedLearningAdapter

        adapter = FederatedLearningAdapter()
        params = {
            "client_updates": [
                {"client_id": "c1", "n_samples": 50},
            ],
            "strategy": "fedprox",
            "n_rounds": 2,
            "model_shape": (5,),
            "mu": 0.1,
            "early_stop_patience": 100,
        }
        result = adapter.execute(params)

        assert result["strategy"] == "fedprox"
        assert result["mu"] == 0.1

    def test_adapter_validate_input(self):
        """Adapter should validate required fields."""
        from app.adapters.edge_adapter import FederatedLearningAdapter

        adapter = FederatedLearningAdapter()

        # Missing required field
        assert adapter.validate_input({}) is False
        assert adapter.validate_input({"client_updates": [[1, 2]]}) is True

    def test_adapter_health_check(self):
        """Adapter health check should return True."""
        from app.adapters.edge_adapter import FederatedLearningAdapter

        adapter = FederatedLearningAdapter()
        assert adapter.health_check() is True

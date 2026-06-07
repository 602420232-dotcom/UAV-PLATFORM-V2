"""
联邦学习框架单元测试
"""
import logging
import os
import sys

import numpy as np
import pytest

logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'edge-cloud-coordinator'))

from federated_learning import FederatedLearning, ClientUpdate, DroneClient  # type: ignore[import-not-found]  # noqa: E402


class TestFederatedLearning:

    def setup_method(self):
        self.fl = FederatedLearning(aggregation_strategy="fedavg", min_clients=2)

    def _make_weights(self, base=1.0):
        return {"layer1": np.array([base, base * 2]), "layer2": np.array([[base, base], [base, base]])}

    def test_init(self):
        assert self.fl.strategy == "fedavg"
        assert self.fl.min_clients == 2
        assert self.fl.round_id == 0
        assert self.fl.client_updates == []
        assert self.fl.global_model is None

    def test_fedavg_aggregate_single_update(self):
        w = self._make_weights(1.0)
        update = ClientUpdate(drone_id="uav-1", weights=w, n_samples=100, metrics={"accuracy": 0.9}, round_id=0)
        aggregated = self.fl.fedavg_aggregate([update])
        for key in w:
            np.testing.assert_array_equal(aggregated[key], w[key])

    def test_fedavg_aggregate_multiple_updates(self):
        w1 = self._make_weights(1.0)
        w2 = self._make_weights(2.0)
        updates = [
            ClientUpdate(drone_id="uav-1", weights=w1, n_samples=100, metrics={"accuracy": 0.8}, round_id=0),
            ClientUpdate(drone_id="uav-2", weights=w2, n_samples=300, metrics={"accuracy": 0.9}, round_id=0)
        ]
        aggregated = self.fl.fedavg_aggregate(updates)
        expected = {k: (w1[k] * 0.25 + w2[k] * 0.75) for k in w1}
        for key in aggregated:
            np.testing.assert_array_almost_equal(aggregated[key], expected[key])

    def test_receive_update_triggers_aggregate(self):
        w = self._make_weights(1.0)
        result1 = self.fl.receive_update("uav-1", w, 100, {"accuracy": 0.85})
        assert result1 is False
        assert self.fl.global_model is None
        result2 = self.fl.receive_update("uav-2", w, 200, {"accuracy": 0.90})
        assert result2 is True
        assert self.fl.global_model is not None
        assert self.fl.global_model.round_id == 1
        assert self.fl.global_model.participating_drones == 2

    def test_aggregate_increments_round(self):
        self.fl.receive_update("uav-1", self._make_weights(1.0), 100, {"accuracy": 0.8})
        self.fl.receive_update("uav-2", self._make_weights(2.0), 200, {"accuracy": 0.9})
        assert self.fl.round_id == 1

    def test_get_global_model_returns_none_before_aggregate(self):
        assert self.fl.get_global_model() is None

    def test_get_global_model_returns_model_after_aggregate(self):
        self.fl.receive_update("uav-1", self._make_weights(1.0), 100, {"accuracy": 0.8})
        self.fl.receive_update("uav-2", self._make_weights(2.0), 200, {"accuracy": 0.9})
        model = self.fl.get_global_model()
        assert model is not None
        assert model.round_id == 1
        assert model.participating_drones == 2

    def test_round_history(self):
        self.fl.receive_update("uav-1", self._make_weights(1.0), 100, {"accuracy": 0.8})
        self.fl.receive_update("uav-2", self._make_weights(2.0), 200, {"accuracy": 0.9})
        assert len(self.fl.round_history) == 1
        assert self.fl.round_history[0]["round"] == 1
        assert self.fl.round_history[0]["clients"] == 2
        assert self.fl.round_history[0]["strategy"] == "fedavg"

    def test_get_round_summary(self):
        self.fl.receive_update("uav-1", self._make_weights(1.0), 100, {"accuracy": 0.8})
        self.fl.receive_update("uav-2", self._make_weights(2.0), 200, {"accuracy": 0.9})
        summary = self.fl.get_round_summary(1)
        assert summary is not None
        assert summary["round"] == 1
        assert self.fl.get_round_summary(99) is None

    def test_fedprox_aggregate(self):
        fl_prox = FederatedLearning(aggregation_strategy="fedprox", min_clients=2)
        w = self._make_weights(1.0)
        fl_prox.receive_update("uav-1", w, 100, {"accuracy": 0.8})
        fl_prox.receive_update("uav-2", w, 200, {"accuracy": 0.9})
        assert fl_prox.global_model is not None

    def test_client_updates_cleared_after_aggregate(self):
        self.fl.receive_update("uav-1", self._make_weights(1.0), 100, {"accuracy": 0.8})
        self.fl.receive_update("uav-2", self._make_weights(2.0), 200, {"accuracy": 0.9})
        assert len(self.fl.client_updates) == 0

    def test_min_clients_not_reached(self):
        fl3 = FederatedLearning(aggregation_strategy="fedavg", min_clients=3)
        fl3.receive_update("uav-1", self._make_weights(1.0), 100, {"accuracy": 0.8})
        fl3.receive_update("uav-2", self._make_weights(1.0), 100, {"accuracy": 0.8})
        assert fl3.global_model is None
        fl3.receive_update("uav-3", self._make_weights(1.0), 100, {"accuracy": 0.8})
        assert fl3.global_model is not None


class TestDroneClient:

    def setup_method(self):
        self.client = DroneClient(drone_id="uav-test-1")

    def test_init(self):
        assert self.client.drone_id == "uav-test-1"
        assert self.client.local_data == []

    def test_set_local_data(self):
        data = [{"feature": [1, 2, 3], "label": 0}, {"feature": [4, 5, 6], "label": 1}]
        self.client.set_local_data(data)
        assert len(self.client.local_data) == 2

    def test_local_train_returns_valid_shape(self):
        global_weights = {"w": np.array([1.0, 2.0, 3.0]), "b": np.array([0.0])}
        self.client.set_local_data([{"x": 1} for _ in range(50)])
        updated, n_samples, metrics = self.client.local_train(global_weights, epochs=3)
        assert n_samples == 50
        assert "accuracy" in metrics
        assert "loss" in metrics
        for key in global_weights:
            assert updated[key].shape == global_weights[key].shape


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

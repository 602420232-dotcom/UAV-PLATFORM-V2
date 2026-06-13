"""Smart algorithm scheduler unit tests.

Tests the SmartAlgorithmScheduler decision tree for correct algorithm selection.
"""

from __future__ import annotations


class TestSmartScheduler:
    """Tests for SmartAlgorithmScheduler."""

    def test_risk_aware_selects_5dvar(self, scheduler):
        """When require_risk_aware=True and params contain risk_field, should select 5dvar."""
        result = scheduler.select_algorithm(
            params={"risk_field": [[0.1, 0.2], [0.3, 0.4]], "risk_cost": 1.0},
            grid_shape=(50, 50),
            observation_count=10,
            time_budget_seconds=5.0,
            require_risk_aware=True,
        )

        assert isinstance(result, dict)
        assert "algorithm_id" in result
        assert result["algorithm_id"] == "5dvar"
        assert "reason" in result
        assert "config_overrides" in result
        assert result["config_overrides"]["enable_risk_cost"] is True

    def test_large_grid_with_gpu_selects_4dvar_gpu(self, scheduler):
        """Large grid + GPU available should select 4dvar-gpu."""
        result = scheduler.select_algorithm(
            params={},
            grid_shape=(120, 120),
            observation_count=10,
            time_budget_seconds=60.0,
            gpu_available=True,
        )

        assert result["algorithm_id"] == "4dvar-gpu"
        assert "config_overrides" in result
        assert result["config_overrides"]["use_gpu"] is True

    def test_large_grid_without_gpu_falls_back_to_4dvar(self, scheduler):
        """Large grid without GPU should fall back to standard 4dvar."""
        result = scheduler.select_algorithm(
            params={},
            grid_shape=(120, 120),
            observation_count=10,
            time_budget_seconds=60.0,
            gpu_available=False,
        )

        assert result["algorithm_id"] == "4dvar"
        assert result["config_overrides"]["use_gpu"] is False

    def test_many_observations_selects_enkf(self, scheduler):
        """Many observations + sufficient time budget should select enkf."""
        result = scheduler.select_algorithm(
            params={},
            grid_shape=(50, 50),
            observation_count=60,
            time_budget_seconds=45.0,
        )

        assert result["algorithm_id"] == "enkf"
        assert "ensemble_size" in result["config_overrides"]

    def test_many_observations_insufficient_time_falls_through(self, scheduler):
        """Many observations but insufficient time should not select enkf."""
        result = scheduler.select_algorithm(
            params={},
            grid_shape=(50, 50),
            observation_count=60,
            time_budget_seconds=5.0,
        )

        assert result["algorithm_id"] != "enkf"

    def test_moderate_observations_selects_hybrid(self, scheduler):
        """Moderate observation count (21-50) should select hybrid_assimilation."""
        result = scheduler.select_algorithm(
            params={},
            grid_shape=(50, 50),
            observation_count=30,
            time_budget_seconds=20.0,
        )

        assert result["algorithm_id"] == "hybrid_assimilation"
        assert "hybrid_weight" in result["config_overrides"]

    def test_few_obs_fast_budget_selects_3dvar(self, scheduler):
        """Few observations + tight time budget should select 3dvar."""
        result = scheduler.select_algorithm(
            params={},
            grid_shape=(50, 50),
            observation_count=10,
            time_budget_seconds=5.0,
        )

        assert result["algorithm_id"] == "3dvar"
        assert result["config_overrides"]["max_iterations"] == 10

    def test_probabilistic_selects_enkf(self, scheduler):
        """When probabilistic output is required, should select enkf."""
        result = scheduler.select_algorithm(
            params={},
            grid_shape=(50, 50),
            observation_count=15,
            time_budget_seconds=20.0,
            require_probabilistic=True,
        )

        assert result["algorithm_id"] == "enkf"
        assert result["config_overrides"]["enable_adaptive_variance"] is True

    def test_default_selects_adaptive_hybrid(self, scheduler):
        """When no specific rules match, should select adaptive_hybrid as default."""
        result = scheduler.select_algorithm(
            params={},
            grid_shape=(50, 50),
            observation_count=15,
            time_budget_seconds=20.0,
        )

        assert result["algorithm_id"] == "adaptive_hybrid"
        assert "hybrid_weight" in result["config_overrides"]

    def test_decision_chain_completeness(self, scheduler):
        """After select_algorithm, the decision chain should have been recorded."""
        scheduler.select_algorithm(
            params={"risk_field": [[1, 2], [3, 4]]},
            grid_shape=(50, 50),
            observation_count=10,
            require_risk_aware=True,
        )

        explanation = scheduler.get_decision_explanation()
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert "5dvar" in explanation

    def test_decision_chain_contains_all_rules(self, scheduler):
        """Decision chain should contain entries for all 7 rules when no early match."""
        scheduler.select_algorithm(
            params={},
            grid_shape=(50, 50),
            observation_count=15,
            time_budget_seconds=20.0,
        )

        explanation = scheduler.get_decision_explanation()
        # All 7 rules should appear in the explanation
        assert "risk_aware" in explanation
        assert "large_grid_gpu" in explanation
        assert "many_obs_enkf" in explanation
        assert "moderate_obs_hybrid" in explanation
        assert "few_obs_fast" in explanation
        assert "probabilistic" in explanation
        assert "default" in explanation

    def test_no_decision_yet_returns_hint(self, scheduler):
        """get_decision_explanation before any selection should return a hint message."""
        explanation = scheduler.get_decision_explanation()
        assert "尚未执行" in explanation

    def test_result_keys_are_present(self, scheduler):
        """Every select_algorithm result must contain algorithm_id, reason, config_overrides."""
        result = scheduler.select_algorithm(
            params={},
            grid_shape=(50, 50),
            observation_count=10,
            time_budget_seconds=5.0,
        )

        assert set(result.keys()) == {"algorithm_id", "reason", "config_overrides"}
        assert isinstance(result["algorithm_id"], str)
        assert isinstance(result["reason"], str)
        assert isinstance(result["config_overrides"], dict)

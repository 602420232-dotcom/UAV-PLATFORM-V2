"""Algorithm registry unit tests.

Tests the AlgorithmRegistry for registration, querying, and capacity.
"""

from __future__ import annotations

import pytest


class DummyAlgorithm:
    """Dummy algorithm class for testing registration."""

    pass


class AnotherAlgorithm:
    """Another dummy algorithm class for testing."""

    pass


class TestAlgorithmRegistry:
    """Tests for AlgorithmRegistry."""

    @pytest.fixture
    def registry(self):
        """Fresh registry instance for each test."""
        from app.core.registry import AlgorithmRegistry

        return AlgorithmRegistry()

    def test_register_single_algorithm(self, registry):
        """Registering a single algorithm should increase registry size to 1."""
        registry.register(
            algorithm_id="dummy_1",
            algorithm_class=DummyAlgorithm,
            category="test",
            version="1.0.0",
            description="A dummy algorithm",
        )
        assert len(registry) == 1
        assert "dummy_1" in registry

    def test_register_102_algorithms(self, registry):
        """Registering 102 algorithms should succeed without error."""
        for i in range(102):
            registry.register(
                algorithm_id=f"algo_{i:04d}",
                algorithm_class=DummyAlgorithm,
                category="test",
                version="1.0.0",
                description=f"Algorithm number {i}",
            )
        assert len(registry) == 102

    def test_register_overwrite(self, registry):
        """Registering with the same algorithm_id should overwrite the existing entry."""
        registry.register(
            algorithm_id="overwrite_test",
            algorithm_class=DummyAlgorithm,
            category="test_v1",
            version="1.0.0",
        )
        registry.register(
            algorithm_id="overwrite_test",
            algorithm_class=AnotherAlgorithm,
            category="test_v2",
            version="2.0.0",
        )
        assert len(registry) == 1
        entry = registry.get_entry("overwrite_test")
        assert entry.algorithm_class is AnotherAlgorithm
        assert entry.version == "2.0.0"
        assert entry.category == "test_v2"

    def test_get_existing_algorithm(self, registry):
        """Getting an existing algorithm should return the correct class."""
        registry.register(
            algorithm_id="get_test",
            algorithm_class=DummyAlgorithm,
            category="test",
        )
        cls = registry.get("get_test")
        assert cls is DummyAlgorithm

    def test_get_nonexistent_algorithm(self, registry):
        """Getting a nonexistent algorithm should return None."""
        assert registry.get("nonexistent") is None

    def test_get_entry_nonexistent(self, registry):
        """Getting entry for a nonexistent algorithm should return None."""
        assert registry.get_entry("nonexistent") is None

    def test_list_by_category(self, registry):
        """Listing by category should return only algorithms in that category."""
        for i in range(5):
            registry.register(
                algorithm_id=f"planning_{i}",
                algorithm_class=DummyAlgorithm,
                category="planning",
            )
        for i in range(3):
            registry.register(
                algorithm_id=f"assimilation_{i}",
                algorithm_class=AnotherAlgorithm,
                category="assimilation",
            )

        planning_list = registry.list_by_category("planning")
        assert len(planning_list) == 5

        assimilation_list = registry.list_by_category("assimilation")
        assert len(assimilation_list) == 3

        empty_list = registry.list_by_category("nonexistent")
        assert len(empty_list) == 0

    def test_list_all(self, registry):
        """Listing all should return every registered algorithm."""
        registry.register(algorithm_id="a1", algorithm_class=DummyAlgorithm, category="cat1")
        registry.register(algorithm_id="a2", algorithm_class=AnotherAlgorithm, category="cat2")

        all_list = registry.list_all()
        assert len(all_list) == 2

    def test_categories(self, registry):
        """Categories should return a sorted list of unique categories."""
        registry.register(algorithm_id="a1", algorithm_class=DummyAlgorithm, category="planning")
        registry.register(algorithm_id="a2", algorithm_class=AnotherAlgorithm, category="assimilation")
        registry.register(algorithm_id="a3", algorithm_class=DummyAlgorithm, category="planning")

        cats = registry.categories()
        assert cats == ["assimilation", "planning"]

    def test_list_by_version_match(self, registry):
        """Listing by version should return metadata when version matches."""
        registry.register(
            algorithm_id="versioned",
            algorithm_class=DummyAlgorithm,
            category="test",
            version="2.5.0",
        )
        meta = registry.list_by_version("versioned", "2.5.0")
        assert meta is not None
        assert meta.version == "2.5.0"

    def test_list_by_version_mismatch(self, registry):
        """Listing by version should return None when version does not match."""
        registry.register(
            algorithm_id="versioned",
            algorithm_class=DummyAlgorithm,
            category="test",
            version="2.5.0",
        )
        meta = registry.list_by_version("versioned", "1.0.0")
        assert meta is None

    def test_contains(self, registry):
        """The 'in' operator should correctly check algorithm existence."""
        registry.register(algorithm_id="exists", algorithm_class=DummyAlgorithm, category="test")
        assert "exists" in registry
        assert "not_exists" not in registry

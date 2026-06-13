"""Algorithm execution unit tests.

Tests the core algorithms return valid results with expected keys.
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# A* algorithm
# ---------------------------------------------------------------------------

class TestAStar:
    """Tests for A* path planning algorithm."""

    def test_a_star_returns_valid_path(self, planning_params):
        """A* should return a result dict containing 'path', 'cost', and 'nodes_explored'."""
        from app.algorithms.planning.a_star import AStarPlanner

        planner = AStarPlanner(params=planning_params)
        result = planner.solve()

        assert isinstance(result, dict)
        assert "path" in result
        assert "cost" in result
        assert "nodes_explored" in result

    def test_a_star_path_not_empty(self, planning_params):
        """A* should find a non-empty path from start to goal on an open grid."""
        from app.algorithms.planning.a_star import AStarPlanner

        planner = AStarPlanner(params=planning_params)
        result = planner.solve()

        assert isinstance(result["path"], list)
        assert len(result["path"]) > 0
        assert result["cost"] < float("inf")
        assert result["cost"] > 0

    def test_a_star_path_starts_and_ends_correctly(self, planning_params, start, goal):
        """A* path should start near 'start' and end near 'goal'."""
        from app.algorithms.planning.a_star import AStarPlanner

        planner = AStarPlanner(params=planning_params)
        result = planner.solve()
        path = result["path"]

        # First point should be close to start
        assert path[0][0] == pytest.approx(start[0], abs=1)
        assert path[0][1] == pytest.approx(start[1], abs=1)
        # Last point should be close to goal
        assert path[-1][0] == pytest.approx(goal[0], abs=1)
        assert path[-1][1] == pytest.approx(goal[1], abs=1)


# ---------------------------------------------------------------------------
# Dijkstra algorithm
# ---------------------------------------------------------------------------

class TestDijkstra:
    """Tests for Dijkstra shortest path algorithm."""

    def test_dijkstra_returns_valid_path(self, planning_params):
        """Dijkstra should return a result dict containing 'path', 'cost', and 'nodes_explored'."""
        from app.algorithms.planning.dijkstra import DijkstraPlanner

        planner = DijkstraPlanner(params=planning_params)
        result = planner.solve()

        assert isinstance(result, dict)
        assert "path" in result
        assert "cost" in result
        assert "nodes_explored" in result

    def test_dijkstra_path_not_empty(self, planning_params):
        """Dijkstra should find a non-empty path from start to goal on an open grid."""
        from app.algorithms.planning.dijkstra import DijkstraPlanner

        planner = DijkstraPlanner(params=planning_params)
        result = planner.solve()

        assert isinstance(result["path"], list)
        assert len(result["path"]) > 0
        assert result["cost"] < float("inf")
        assert result["cost"] > 0

    def test_dijkstra_path_starts_and_ends_correctly(self, planning_params, start, goal):
        """Dijkstra path should start near 'start' and end near 'goal'."""
        from app.algorithms.planning.dijkstra import DijkstraPlanner

        planner = DijkstraPlanner(params=planning_params)
        result = planner.solve()
        path = result["path"]

        assert path[0][0] == pytest.approx(start[0], abs=1)
        assert path[0][1] == pytest.approx(start[1], abs=1)
        assert path[-1][0] == pytest.approx(goal[0], abs=1)
        assert path[-1][1] == pytest.approx(goal[1], abs=1)


# ---------------------------------------------------------------------------
# RRT* algorithm
# ---------------------------------------------------------------------------

class TestRRTStar:
    """Tests for RRT* optimal path planning algorithm."""

    def test_rrt_star_returns_valid_result(self, planning_params):
        """RRT* should return a result dict containing 'path', 'cost', and 'iterations'."""
        from app.algorithms.planning.rrt_star import RRTStarPlanner

        planner = RRTStarPlanner(params=planning_params)
        result = planner.solve()

        assert isinstance(result, dict)
        assert "path" in result
        assert "cost" in result
        assert "iterations" in result

    def test_rrt_star_finds_path(self, planning_params):
        """RRT* should find a path within max_iterations on a simple open grid."""
        from app.algorithms.planning.rrt_star import RRTStarPlanner

        params = {**planning_params, "max_iterations": 2000, "step_size": 2.0, "goal_radius": 2.0}
        planner = RRTStarPlanner(params=params)
        result = planner.solve()

        assert isinstance(result["path"], list)
        assert len(result["path"]) > 0
        assert result["cost"] < float("inf")


# ---------------------------------------------------------------------------
# 3D-VAR assimilation algorithm
# ---------------------------------------------------------------------------

class TestThreeDimensionalVAR:
    """Tests for 3D-VAR data assimilation algorithm."""

    def test_3dvar_returns_analysis_field(self, assimilation_params):
        """3D-VAR should return a dict containing 'analysis_field' key."""
        from app.algorithms.assimilation.three_dimensional_var import ThreeDimensionalVAR

        algorithm = ThreeDimensionalVAR(config={"max_iterations": 20})
        result = algorithm.assimilate(params=assimilation_params)

        assert isinstance(result, dict)
        assert "analysis_field" in result

    def test_3dvar_returns_cost_and_iterations(self, assimilation_params):
        """3D-VAR should return 'cost' and 'iterations' keys."""
        from app.algorithms.assimilation.three_dimensional_var import ThreeDimensionalVAR

        algorithm = ThreeDimensionalVAR(config={"max_iterations": 20})
        result = algorithm.assimilate(params=assimilation_params)

        assert "cost" in result
        assert "iterations" in result
        assert isinstance(result["cost"], float)
        assert isinstance(result["iterations"], int)
        assert result["iterations"] > 0

    def test_3dvar_returns_convergence_info(self, assimilation_params):
        """3D-VAR should return 'converged' and 'grid_shape' keys."""
        from app.algorithms.assimilation.three_dimensional_var import ThreeDimensionalVAR

        algorithm = ThreeDimensionalVAR(config={"max_iterations": 20})
        result = algorithm.assimilate(params=assimilation_params)

        assert "converged" in result
        assert "grid_shape" in result
        assert isinstance(result["converged"], bool)
        assert isinstance(result["grid_shape"], list)

    def test_3dvar_analysis_field_is_list(self, assimilation_params):
        """3D-VAR analysis_field should be a serializable list."""
        from app.algorithms.assimilation.three_dimensional_var import ThreeDimensionalVAR

        algorithm = ThreeDimensionalVAR(config={"max_iterations": 20})
        result = algorithm.assimilate(params=assimilation_params)

        assert isinstance(result["analysis_field"], list)
        assert len(result["analysis_field"]) > 0

"""DE-RRT* (Differential Evolution RRT*).

Enhanced implementation with:
- Differential Evolution (DE/rand/1) for tree node rewiring
- Weather-aware wind resistance cost in path evaluation
- B-spline path smoothing
- Path safety margin checking
- Comprehensive metrics reporting
"""

from __future__ import annotations

import logging
import random
import time
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class DERRTStarPlanner:
    """Differential Evolution enhanced RRT* for complex environments.

    Enhanced with DE-based rewiring, weather awareness, path smoothing,
    and safety margin analysis.

    Params schema:
        start: [x, y] start position
        goal: [x, y] goal position
        obstacles: list of [x, y, radius]
        max_iterations: int (default 1000)
        step_size: float (default 1.0)
        goal_radius: float (default 1.0)
        rewire_radius: float, neighborhood radius for rewiring (default 3.0)
        de_population_size: int, DE population for rewiring (default 20)
        de_generations: int, DE generations per rewiring step (default 5)
        de_F: float, DE scaling factor (default 0.8)
        de_CR: float, DE crossover rate (default 0.9)
        smooth_points: int, number of points for B-spline smoothing (default 50)
        safety_margin: float, extra clearance from obstacles (default 0.5)
        weather_context: dict with wind field data (optional)
            u10, v10: 2D numpy arrays (wind components)
            wind_speed: 2D numpy array
            turbulence: 2D numpy array
    """

    def __init__(self, params: dict[str, Any] | None = None):
        self.params = params or {}
        self.start = tuple(self.params.get("start", [0, 0]))
        self.goal = tuple(self.params.get("goal", [10, 10]))
        self.obstacles = self.params.get("obstacles", [])
        self.max_iterations = self.params.get("max_iterations", 1000)
        self.step_size = self.params.get("step_size", 1.0)
        self.goal_radius = self.params.get("goal_radius", 1.0)
        self.rewire_radius = self.params.get("rewire_radius", 3.0)
        self.de_population_size = self.params.get("de_population_size", 20)
        self.de_generations = self.params.get("de_generations", 5)
        self.de_F = self.params.get("de_F", 0.8)
        self.de_CR = self.params.get("de_CR", 0.9)
        self.smooth_points = self.params.get("smooth_points", 50)
        self.safety_margin = self.params.get("safety_margin", 0.5)
        self.weather_context = self.params.get("weather_context", None)

        # Bounding box for sampling
        self.x_min = min(self.start[0], self.goal[0]) - 5
        self.x_max = max(self.start[0], self.goal[0]) + 5
        self.y_min = min(self.start[1], self.goal[1]) - 5
        self.y_max = max(self.start[1], self.goal[1]) + 5

    def solve(self) -> dict[str, Any]:
        t_start = time.time()

        nodes: list[np.ndarray] = [np.array(self.start, dtype=float)]
        parents: dict[int, int | None] = {0: None}
        costs: dict[int, float] = {0: 0.0}

        for i_iter in range(self.max_iterations):
            # Sample random point (10% bias toward goal)
            if random.random() < 0.1:
                rand_point = np.array(self.goal, dtype=float)
            else:
                rand_point = np.array([
                    random.uniform(self.x_min, self.x_max),
                    random.uniform(self.y_min, self.y_max),
                ])

            # Find nearest node
            nearest_idx = self._find_nearest(nodes, rand_point)
            nearest = nodes[nearest_idx]

            # Steer toward random point
            new_point = self._steer(nearest, rand_point)

            if self._check_collision(new_point):
                continue

            new_idx = len(nodes)
            nodes.append(new_point)

            # Find best parent (with weather-aware cost)
            best_parent, best_cost = self._find_best_parent(
                new_point, nodes, costs, new_idx,
            )

            parents[new_idx] = best_parent
            costs[new_idx] = best_cost

            # Rewire neighbors using DE optimization
            self._de_rewire(new_idx, nodes, parents, costs)

            # Check if we reached the goal
            if float(np.linalg.norm(new_point - np.array(self.goal))) < self.goal_radius:
                raw_path = self._extract_path(new_idx, nodes, parents)
                smooth_path = self._smooth_path(raw_path)
                path_length = self._path_length(smooth_path)
                wind_cost = self._compute_wind_cost(smooth_path)
                smoothness = self._compute_smoothness(smooth_path)
                safety = self._compute_safety_margin(smooth_path)
                compute_time = time.time() - t_start

                return {
                    "path": [p.tolist() for p in smooth_path],
                    "raw_path": [p.tolist() for p in raw_path],
                    "cost": float(best_cost),
                    "iterations": i_iter + 1,
                    "metrics": {
                        "path_length": float(path_length),
                        "wind_cost": float(wind_cost),
                        "smoothness": float(smoothness),
                        "safety_margin": float(safety),
                        "compute_time": float(compute_time),
                    },
                }

        # Failed to find path
        compute_time = time.time() - t_start
        return {
            "path": [],
            "raw_path": [],
            "cost": float("inf"),
            "iterations": self.max_iterations,
            "metrics": {
                "path_length": 0.0,
                "wind_cost": 0.0,
                "smoothness": 0.0,
                "safety_margin": 0.0,
                "compute_time": float(compute_time),
            },
        }

    # ------------------------------------------------------------------
    # Core RRT* operations
    # ------------------------------------------------------------------

    def _find_nearest(self, nodes, point):
        """Find the nearest node to the given point."""
        return int(min(
            range(len(nodes)),
            key=lambda i: float(np.linalg.norm(nodes[i] - point)),
        ))

    def _steer(self, from_point, to_point):
        """Steer from from_point toward to_point by step_size."""
        direction = to_point - from_point
        dist = float(np.linalg.norm(direction))
        if dist < 1e-6:
            return from_point.copy()
        step = min(self.step_size, dist)
        return from_point + (direction / dist * step)

    def _find_best_parent(self, new_point, nodes, costs, new_idx):
        """Find the best parent for a new node considering neighbors and weather."""
        best_parent = 0
        best_cost = float("inf")

        for i, node in enumerate(nodes):
            if i == new_idx:
                continue
            dist = float(np.linalg.norm(node - new_point))
            if dist > self.rewire_radius:
                continue
            if self._check_line_collision(node, new_point):
                continue
            edge_cost = self._edge_cost(node, new_point, dist)
            total_cost = costs[i] + edge_cost
            if total_cost < best_cost:
                best_parent = i
                best_cost = total_cost

        # Fallback: use nearest node if no neighbor found
        if best_cost == float("inf"):
            nearest_idx = self._find_nearest(nodes, new_point)
            dist = float(np.linalg.norm(nodes[nearest_idx] - new_point))
            best_parent = nearest_idx
            best_cost = costs[nearest_idx] + self._edge_cost(
                nodes[nearest_idx], new_point, dist,
            )

        return best_parent, best_cost

    def _edge_cost(self, p1, p2, dist):
        """Compute edge cost including wind resistance."""
        base_cost = dist
        wind_cost = self._wind_edge_cost(p1, p2)
        return base_cost + wind_cost

    # ------------------------------------------------------------------
    # DE Rewiring
    # ------------------------------------------------------------------

    def _de_rewire(self, new_idx, nodes, parents, costs):
        """Rewire nearby nodes using DE/rand/1 mutation strategy.

        For each neighbor of the new node, use differential evolution to
        find an improved parent configuration that minimizes total cost.
        """
        new_point = nodes[new_idx]

        # Find neighbors within rewire radius
        neighbors = []
        for i, node in enumerate(nodes):
            if i == new_idx or i == 0:
                continue
            dist = float(np.linalg.norm(node - new_point))
            if dist <= self.rewire_radius:
                if not self._check_line_collision(new_point, node):
                    neighbors.append(i)

        if not neighbors:
            return

        # For each neighbor, check if connecting through new_idx reduces cost
        for n_idx in neighbors:
            n_point = nodes[n_idx]
            dist = float(np.linalg.norm(new_point - n_point))
            new_cost = costs[new_idx] + self._edge_cost(new_point, n_point, dist)

            if new_cost < costs[n_idx]:
                # Apply DE/rand/1 to refine the connection
                refined_cost = self._de_refine_connection(
                    n_idx, new_idx, nodes, costs,
                )
                if refined_cost < costs[n_idx]:
                    parents[n_idx] = new_idx
                    costs[n_idx] = refined_cost

    def _de_refine_connection(self, target_idx, candidate_parent, nodes, costs):
        """Use DE/rand/1 to find optimal intermediate point for connection.

        The DE optimizes a point along the edge from candidate_parent to target
        that minimizes the combined cost considering wind and obstacles.
        """
        p1 = nodes[candidate_parent]
        p2 = nodes[target_idx]
        edge_len = float(np.linalg.norm(p2 - p1))

        if edge_len < 1e-6:
            return costs[candidate_parent] + 0.0

        # DE population: parameterize as offset ratio along the edge
        # Each individual is a 2D offset from the straight-line midpoint
        pop_size = min(self.de_population_size, 10)
        dim = 2  # (dx, dy) offset from midpoint

        # Initialize population around the midpoint
        mid = (p1 + p2) / 2.0
        pop = np.random.randn(pop_size, dim) * edge_len * 0.2
        pop_costs = np.full(pop_size, float("inf"))

        for g in range(self.de_generations):
            # Evaluate
            for k in range(pop_size):
                point = mid + pop[k]
                if self._check_collision(point):
                    pop_costs[k] = float("inf")
                    continue
                d1 = float(np.linalg.norm(p1 - point))
                d2 = float(np.linalg.norm(point - p2))
                cost = (
                    costs[candidate_parent]
                    + self._edge_cost(p1, point, d1)
                    + self._edge_cost(point, p2, d2)
                )
                pop_costs[k] = cost

            # DE/rand/1 mutation and crossover
            new_pop = np.copy(pop)
            for k in range(pop_size):
                # Select three distinct random individuals
                candidates = list(range(pop_size))
                candidates.remove(k)
                r1, r2, r3 = random.sample(candidates, 3)

                # Mutation: v = x_r1 + F * (x_r2 - x_r3)
                mutant = pop[r1] + self.de_F * (pop[r2] - pop[r3])

                # Crossover: binomial
                trial = np.copy(pop[k])
                for d in range(dim):
                    if random.random() < self.de_CR:
                        trial[d] = mutant[d]

                # Selection: greedy
                trial_point = mid + trial
                if not self._check_collision(trial_point):
                    d1 = float(np.linalg.norm(p1 - trial_point))
                    d2 = float(np.linalg.norm(trial_point - p2))
                    trial_cost = (
                        costs[candidate_parent]
                        + self._edge_cost(p1, trial_point, d1)
                        + self._edge_cost(trial_point, p2, d2)
                    )
                    if trial_cost < pop_costs[k]:
                        new_pop[k] = trial
                        pop_costs[k] = trial_cost

            pop = new_pop

        # Return best cost found
        best_idx = int(np.argmin(pop_costs))
        return pop_costs[best_idx]

    # ------------------------------------------------------------------
    # Path Smoothing (B-spline)
    # ------------------------------------------------------------------

    def _smooth_path(self, path):
        """Smooth the path using cubic B-spline interpolation."""
        if len(path) < 3:
            return path

        path_arr = np.array(path)
        n = len(path_arr)

        # Number of interpolation points
        num_points = max(self.smooth_points, n * 3)

        # Parameterize by cumulative arc length
        diffs = np.diff(path_arr, axis=0)
        seg_lengths = np.sqrt(np.sum(diffs ** 2, axis=1))
        cum_length = np.concatenate([[0], np.cumsum(seg_lengths)])
        total_length = cum_length[-1]

        if total_length < 1e-6:
            return path

        t_uniform = np.linspace(0, total_length, num_points)

        # Interpolate each dimension using cubic spline
        from scipy.interpolate import CubicSpline

        smooth_path = []
        for dim in range(path_arr.shape[1]):
            cs = CubicSpline(cum_length, path_arr[:, dim], bc_type="clamped")
            smooth_path.append(cs(t_uniform))

        smooth_arr = np.column_stack(smooth_path)

        # Verify smoothed path doesn't collide with obstacles
        final_path = [smooth_arr[0]]
        for i in range(1, len(smooth_arr)):
            if not self._check_collision(smooth_arr[i]):
                final_path.append(smooth_arr[i])
            else:
                # If collision, skip this point (keep previous)
                final_path.append(final_path[-1])

        return final_path

    # ------------------------------------------------------------------
    # Collision Detection
    # ------------------------------------------------------------------

    def _check_collision(self, point):
        """Check if a point collides with any obstacle (including safety margin)."""
        effective_radius = self.safety_margin
        for obs in self.obstacles:
            r = obs[2] if len(obs) > 2 else 1.0
            if float(np.linalg.norm(np.array(point) - np.array([obs[0], obs[1]]))) < r + effective_radius:
                return True
        return False

    def _check_line_collision(self, p1, p2):
        """Check if the line segment between p1 and p2 collides with any obstacle."""
        p1 = np.asarray(p1)
        p2 = np.asarray(p2)
        num_checks = max(int(float(np.linalg.norm(p2 - p1)) / 0.5), 10)
        for t in np.linspace(0, 1, num_checks):
            mid = p1 + t * (p2 - p1)
            if self._check_collision(mid):
                return True
        return False

    # ------------------------------------------------------------------
    # Path Extraction
    # ------------------------------------------------------------------

    def _extract_path(self, idx, nodes, parents):
        """Extract path from goal node back to start."""
        path = []
        while idx is not None:
            path.append(nodes[idx])
            idx = parents[idx]
        path.reverse()
        return path

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def _path_length(self, path):
        """Compute total path length."""
        if len(path) < 2:
            return 0.0
        total = 0.0
        for i in range(len(path) - 1):
            total += float(np.linalg.norm(np.array(path[i + 1]) - np.array(path[i])))
        return total

    def _compute_wind_cost(self, path):
        """Compute total wind resistance cost along the path."""
        if self.weather_context is None or len(path) < 2:
            return 0.0
        u10 = self.weather_context.get("u10", None)
        v10 = self.weather_context.get("v10", None)
        if u10 is None or v10 is None:
            return 0.0

        total = 0.0
        for i in range(len(path) - 1):
            total += self._wind_edge_cost(np.array(path[i]), np.array(path[i + 1]))
        return total

    def _wind_edge_cost(self, p1, p2):
        """Compute wind resistance cost for an edge."""
        if self.weather_context is None:
            return 0.0
        u10 = self.weather_context.get("u10", None)
        v10 = self.weather_context.get("v10", None)
        if u10 is None or v10 is None:
            return 0.0

        direction = p2 - p1
        dist = float(np.linalg.norm(direction))
        if dist < 1e-6:
            return 0.0

        d_unit = direction / dist
        mid = (p1 + p2) / 2.0
        wind_u = self._sample_wind(np.asarray(u10), mid)
        wind_v = self._sample_wind(np.asarray(v10), mid)
        wind_vec = np.array([wind_u, wind_v])
        headwind = float(np.dot(wind_vec, d_unit))
        return max(0.0, headwind) * dist * 0.3

    def _sample_wind(self, wind_field, position):
        """Sample wind at a position using bilinear interpolation."""
        field = np.asarray(wind_field)
        rows, cols = field.shape
        gi = position[0]
        gj = position[1]
        gi_norm = max(0.0, min(gi * (rows - 1) / max(rows, 1), rows - 1.0))
        gj_norm = max(0.0, min(gj * (cols - 1) / max(cols, 1), cols - 1.0))
        gi0 = int(gi_norm)
        gj0 = int(gj_norm)
        gi1 = min(gi0 + 1, rows - 1)
        gj1 = min(gj0 + 1, cols - 1)
        di = gi_norm - gi0
        dj = gj_norm - gj0
        return (
            field[gi0, gj0] * (1 - di) * (1 - dj)
            + field[gi1, gj0] * di * (1 - dj)
            + field[gi0, gj1] * (1 - di) * dj
            + field[gi1, gj1] * di * dj
        )

    def _compute_smoothness(self, path):
        """Compute path smoothness as inverse of average curvature.

        Lower values indicate smoother paths.
        """
        if len(path) < 3:
            return 0.0

        total_curvature = 0.0
        count = 0
        for i in range(1, len(path) - 1):
            v1 = np.array(path[i]) - np.array(path[i - 1])
            v2 = np.array(path[i + 1]) - np.array(path[i])
            l1 = float(np.linalg.norm(v1))
            l2 = float(np.linalg.norm(v2))
            if l1 < 1e-6 or l2 < 1e-6:
                continue
            cos_angle = np.clip(np.dot(v1, v2) / (l1 * l2), -1.0, 1.0)
            angle = float(np.arccos(cos_angle))
            total_curvature += angle
            count += 1

        if count == 0:
            return 0.0
        avg_curvature = total_curvature / count
        # Smoothness = inverse of average curvature (higher = smoother)
        return 1.0 / (1.0 + avg_curvature)

    def _compute_safety_margin(self, path):
        """Compute minimum distance from path to any obstacle.

        Returns the minimum clearance along the entire path.
        """
        if not self.obstacles or len(path) < 2:
            return float("inf") if not self.obstacles else 0.0

        min_clearance = float("inf")
        for point in path:
            for obs in self.obstacles:
                r = obs[2] if len(obs) > 2 else 1.0
                dist = float(np.linalg.norm(np.array(point) - np.array([obs[0], obs[1]])))
                clearance = dist - r
                if clearance < min_clearance:
                    min_clearance = clearance

        return max(0.0, min_clearance)

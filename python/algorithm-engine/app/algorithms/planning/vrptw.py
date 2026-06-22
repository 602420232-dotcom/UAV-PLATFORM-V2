"""VRPTW (Vehicle Routing Problem with Time Windows).

Enhanced implementation with:
- Time window constraints (earliest_time, latest_time, service_time)
- Weather-aware wind resistance cost
- Clarke-Wright savings algorithm for initial solution
- 2-opt local search optimization
- Multi-objective evaluation (distance, time window violation, weather cost)
"""

from __future__ import annotations

import logging
import math
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class VRPTWPlanner:
    """Vehicle Routing Problem with Time Windows for multi-UAV mission planning.

    Enhanced with weather awareness, Clarke-Wright savings, and 2-opt optimization.

    Params schema:
        start: [x, y] depot location
        waypoints: list of [x, y, demand, earliest_time, latest_time, service_time]
        capacity: float, vehicle capacity
        num_vehicles: int, max number of vehicles
        speed: float, average travel speed (default 1.0)
        weather_context: dict with wind field data (optional)
            u10, v10: 2D numpy arrays (wind components)
            wind_speed: 2D numpy array
            t2m: 2D numpy array (temperature)
            turbulence: 2D numpy array
    """

    def __init__(self, params: dict[str, Any] | None = None):
        self.params = params or {}
        self.weather_context = self.params.get("weather_context", None)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def solve(self) -> dict[str, Any]:
        start = self.params.get("start", [0, 0])
        waypoints = self.params.get("waypoints", [])
        capacity = self.params.get("capacity", 10.0)
        num_vehicles = self.params.get("num_vehicles", 5)
        speed = self.params.get("speed", 1.0)

        if not waypoints:
            return {
                "routes": [],
                "total_cost": 0.0,
                "vehicles_used": 0,
                "metrics": {
                    "total_distance": 0.0,
                    "tw_violations": 0,
                    "weather_cost": 0.0,
                    "vehicle_utilization": 0.0,
                },
            }

        n = len(waypoints)
        wp_arr = np.array(waypoints, dtype=float)

        # Parse waypoint attributes
        positions = wp_arr[:, :2]
        demands = wp_arr[:, 2] if wp_arr.shape[1] > 2 else np.ones(n)
        earliest = wp_arr[:, 3] if wp_arr.shape[1] > 3 else np.zeros(n)
        latest = wp_arr[:, 4] if wp_arr.shape[1] > 4 else np.full(n, 1e9)
        service_time = wp_arr[:, 5] if wp_arr.shape[1] > 5 else np.zeros(n)

        depot = np.array(start, dtype=float)

        # Distance matrix (Euclidean)
        dist_matrix = np.zeros((n + 1, n + 1))
        for i in range(n):
            dist_matrix[0, i + 1] = float(np.linalg.norm(depot - positions[i]))
            dist_matrix[i + 1, 0] = dist_matrix[0, i + 1]
        for i in range(n):
            for j in range(n):
                if i != j:
                    dist_matrix[i + 1, j + 1] = float(
                        np.linalg.norm(positions[i] - positions[j])
                    )

        # Weather cost matrix (wind resistance)
        weather_cost_matrix = self._build_weather_cost_matrix(positions, depot, n)

        # Combined cost = distance + weather_cost
        combined_matrix = dist_matrix + weather_cost_matrix

        # Travel time matrix (distance / speed)
        time_matrix = dist_matrix / speed

        # --- Clarke-Wright Savings Algorithm ---
        routes = self._clarke_wright_savings(
            n, combined_matrix, time_matrix, demands, capacity,
            earliest, latest, service_time, num_vehicles,
        )

        # --- 2-opt local search ---
        routes = self._two_opt_optimize(
            routes, combined_matrix, time_matrix, demands, capacity,
            earliest, latest, service_time,
        )

        # --- Build result ---
        total_distance = 0.0
        total_weather_cost = 0.0
        tw_violations = 0
        total_load = 0.0
        result_routes = []

        for route in routes:
            route_positions = [depot.tolist()]
            route_dist = 0.0
            route_weather = 0.0
            route_load = 0.0
            prev_node = 0  # depot index
            arrival_time = 0.0

            for customer_idx in route:
                node = customer_idx + 1  # offset for depot
                route_dist += dist_matrix[prev_node, node]
                route_weather += weather_cost_matrix[prev_node, node]
                arrival_time += time_matrix[prev_node, node]

                # Time window check
                if arrival_time < earliest[customer_idx]:
                    arrival_time = earliest[customer_idx]
                elif arrival_time > latest[customer_idx]:
                    tw_violations += 1

                arrival_time += service_time[customer_idx]
                route_positions.append(positions[customer_idx].tolist())
                route_load += demands[customer_idx]
                prev_node = node

            # Return to depot
            route_dist += dist_matrix[prev_node, 0]
            route_weather += weather_cost_matrix[prev_node, 0]
            route_positions.append(depot.tolist())

            total_distance += route_dist
            total_weather_cost += route_weather
            total_load += route_load

            result_routes.append({
                "waypoints": route_positions,
                "cost": float(route_dist),
                "load": float(route_load),
                "weather_cost": float(route_weather),
            })

        vehicles_used = len(routes)
        vehicle_utilization = (
            total_load / (vehicles_used * capacity) if vehicles_used > 0 else 0.0
        )

        return {
            "routes": result_routes,
            "total_cost": float(total_distance),
            "vehicles_used": vehicles_used,
            "metrics": {
                "total_distance": float(total_distance),
                "tw_violations": tw_violations,
                "weather_cost": float(total_weather_cost),
                "vehicle_utilization": float(vehicle_utilization),
            },
        }

    # ------------------------------------------------------------------
    # Clarke-Wright Savings Algorithm
    # ------------------------------------------------------------------

    def _clarke_wright_savings(
        self, n, cost_matrix, time_matrix, demands, capacity,
        earliest, latest, service_time, num_vehicles,
    ):
        """Build initial routes using Clarke-Wright savings heuristic."""
        # Each customer starts in its own route: depot -> i -> depot
        routes: list[list[int]] = [[i] for i in range(n)]

        # Compute savings: s(i,j) = cost(depot,i) + cost(depot,j) - cost(i,j)
        savings = []
        for i in range(n):
            for j in range(i + 1, n):
                s = cost_matrix[0, i + 1] + cost_matrix[0, j + 1] - cost_matrix[i + 1, j + 1]
                savings.append((s, i, j))
        savings.sort(reverse=True, key=lambda x: x[0])

        # Route lookup: customer -> route index
        route_of: dict[int, int] = {i: i for i in range(n)}

        for s, i, j in savings:
            ri = route_of[i]
            rj = route_of[j]
            if ri == rj:
                continue

            route_i = routes[ri]
            route_j = routes[rj]

            # i must be last in its route, j must be first in its route
            if route_i[-1] != i or route_j[0] != j:
                continue

            # Capacity check
            new_load = sum(demands[c] for c in route_i) + sum(demands[c] for c in route_j)
            if new_load > capacity:
                continue

            # Time feasibility check (simplified)
            if not self._check_route_feasibility(
                route_i + route_j, time_matrix, earliest, latest, service_time,
            ):
                continue

            # Merge routes
            merged = route_i + route_j
            routes[ri] = merged
            routes[rj] = []
            for c in route_j:
                route_of[c] = ri

        # Remove empty routes
        routes = [r for r in routes if r]
        return routes

    def _check_route_feasibility(
        self, route, time_matrix, earliest, latest, service_time,
    ):
        """Check if a route satisfies time window constraints."""
        arrival = 0.0
        prev = 0  # depot
        for c in route:
            node = c + 1
            arrival += time_matrix[prev, node]
            if arrival < earliest[c]:
                arrival = earliest[c]
            if arrival > latest[c]:
                return False
            arrival += service_time[c]
            prev = node
        return True

    # ------------------------------------------------------------------
    # 2-opt Local Search
    # ------------------------------------------------------------------

    def _two_opt_optimize(
        self, routes, cost_matrix, time_matrix, demands, capacity,
        earliest, latest, service_time,
    ):
        """Apply 2-opt improvement to each route."""
        improved_routes = []
        for route in routes:
            if len(route) < 2:
                improved_routes.append(route)
                continue
            best_route = list(route)
            best_cost = self._route_cost(
                best_route, cost_matrix
            )
            improved = True
            iterations = 0
            max_iter = min(len(route) * 5, 50)
            while improved and iterations < max_iter:
                improved = False
                iterations += 1
                for i in range(len(best_route) - 1):
                    for j in range(i + 1, len(best_route)):
                        new_route = (
                            best_route[:i]
                            + best_route[i : j + 1][::-1]
                            + best_route[j + 1 :]
                        )
                        # Check capacity
                        new_load = sum(demands[c] for c in new_route)
                        if new_load > capacity:
                            continue
                        # Check time feasibility
                        if not self._check_route_feasibility(
                            new_route, time_matrix, earliest, latest, service_time,
                        ):
                            continue
                        new_cost = self._route_cost(new_route, cost_matrix)
                        if new_cost < best_cost:
                            best_route = new_route
                            best_cost = new_cost
                            improved = True
            improved_routes.append(best_route)
        return improved_routes

    def _route_cost(self, route, cost_matrix):
        """Calculate total cost of a route including depot."""
        if not route:
            return 0.0
        cost = cost_matrix[0, route[0] + 1]  # depot to first
        for i in range(len(route) - 1):
            cost += cost_matrix[route[i] + 1, route[i + 1] + 1]
        cost += cost_matrix[route[-1] + 1, 0]  # last to depot
        return cost

    # ------------------------------------------------------------------
    # Weather Cost
    # ------------------------------------------------------------------

    def _build_weather_cost_matrix(self, positions, depot, n):
        """Build a weather cost matrix based on wind resistance.

        For each edge (i, j), the weather cost is proportional to the
        component of wind opposing the travel direction.
        """
        matrix = np.zeros((n + 1, n + 1))

        if self.weather_context is None:
            return matrix

        u10 = self.weather_context.get("u10", None)
        v10 = self.weather_context.get("v10", None)
        if u10 is None or v10 is None:
            return matrix

        u10 = np.asarray(u10)
        v10 = np.asarray(v10)

        all_positions = [depot] + [positions[i] for i in range(n)]

        for i in range(n + 1):
            for j in range(n + 1):
                if i == j:
                    continue
                p1 = all_positions[i]
                p2 = all_positions[j]
                direction = p2 - p1
                dist = float(np.linalg.norm(direction))
                if dist < 1e-6:
                    continue
                # Unit direction vector of travel
                d_unit = direction / dist
                # Sample wind at midpoint of edge
                mid = (p1 + p2) / 2.0
                wind_u = self._sample_wind(u10, mid)
                wind_v = self._sample_wind(v10, mid)
                wind_vec = np.array([wind_u, wind_v])
                # Headwind component (dot product of wind with travel direction)
                headwind = float(np.dot(wind_vec, d_unit))
                # Weather cost: penalty for headwind, small bonus for tailwind
                # headwind > 0 means wind blows against travel direction
                matrix[i, j] = max(0.0, headwind) * dist * 0.3

        return matrix

    def _sample_wind(self, wind_field, position):
        """Sample wind value at a given position from a 2D wind field.

        Uses bilinear interpolation if the position falls within the field,
        otherwise returns the nearest boundary value.
        """
        field = np.asarray(wind_field)
        rows, cols = field.shape

        # Map position to grid indices (assume grid covers the planning area)
        # Use a simple mapping: position coordinates -> grid indices
        gi = position[0]
        gj = position[1]

        # Normalize to grid coordinates
        gi_norm = gi * (rows - 1) / max(rows, 1)
        gj_norm = gj * (cols - 1) / max(cols, 1)

        # Clamp to grid bounds
        gi_norm = max(0.0, min(gi_norm, rows - 1.0))
        gj_norm = max(0.0, min(gj_norm, cols - 1.0))

        # Bilinear interpolation
        gi0 = int(gi_norm)
        gj0 = int(gj_norm)
        gi1 = min(gi0 + 1, rows - 1)
        gj1 = min(gj0 + 1, cols - 1)

        di = gi_norm - gi0
        dj = gj_norm - gj0

        val = (
            field[gi0, gj0] * (1 - di) * (1 - dj)
            + field[gi1, gj0] * di * (1 - dj)
            + field[gi0, gj1] * (1 - di) * dj
            + field[gi1, gj1] * di * dj
        )
        return val

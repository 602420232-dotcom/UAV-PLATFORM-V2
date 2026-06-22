"""DWA (Dynamic Window Approach) local planning.

Enhanced implementation with:
- True dynamic window based on current velocity and acceleration constraints
- Weather-aware wind disturbance in trajectory evaluation
- Obstacle inflation (safety distance)
- Heading angle scoring function
- Comprehensive metrics reporting
"""

from __future__ import annotations

import logging
import math
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class DWAPlanner:
    """Dynamic Window Approach for local obstacle avoidance.

    Enhanced with true dynamic window, weather awareness, obstacle inflation,
    and heading angle evaluation.

    Params schema:
        start: [x, y] current position
        goal: [x, y] target position
        obstacles: list of [x, y, radius]
        velocity: [vx, vy] current velocity
        max_speed: float, maximum speed (default 2.0)
        max_accel: float, maximum acceleration (default 1.0)
        predict_time: float, prediction horizon in seconds (default 2.0)
        dt: float, time step for trajectory simulation (default 0.1)
        resolution: int, number of velocity samples per axis (default 20)
        safety_distance: float, obstacle inflation distance (default 0.5)
        heading_weight: float, weight for heading score (default 1.0)
        clearance_weight: float, weight for obstacle clearance score (default 0.5)
        speed_weight: float, weight for speed score (default 0.1)
        weather_context: dict with wind field data (optional)
            u10, v10: 2D numpy arrays (wind components)
            wind_speed: 2D numpy array
            turbulence: 2D numpy array
    """

    def __init__(self, params: dict[str, Any] | None = None):
        self.params = params or {}
        self.start = self.params.get("start", [0, 0])
        self.goal = self.params.get("goal", [10, 10])
        self.obstacles = self.params.get("obstacles", [])
        self.velocity = self.params.get("velocity", [0, 0])
        self.max_speed = self.params.get("max_speed", 2.0)
        self.max_accel = self.params.get("max_accel", 1.0)
        self.predict_time = self.params.get("predict_time", 2.0)
        self.dt = self.params.get("dt", 0.1)
        self.resolution = self.params.get("resolution", 20)
        self.safety_distance = self.params.get("safety_distance", 0.5)
        self.heading_weight = self.params.get("heading_weight", 1.0)
        self.clearance_weight = self.params.get("clearance_weight", 0.5)
        self.speed_weight = self.params.get("speed_weight", 0.1)
        self.weather_context = self.params.get("weather_context", None)

    def solve(self) -> dict[str, Any]:
        current = np.array(self.start, dtype=float)
        goal = np.array(self.goal, dtype=float)
        current_vel = np.array(self.velocity, dtype=float)

        # --- Compute Dynamic Window ---
        # Vs: space of achievable velocities (bounded by max speed)
        vs_x = [-self.max_speed, self.max_speed]
        vs_y = [-self.max_speed, self.max_speed]

        # Vd: dynamic window based on current velocity and acceleration
        vd_x = [
            current_vel[0] - self.max_accel * self.predict_time,
            current_vel[0] + self.max_accel * self.predict_time,
        ]
        vd_y = [
            current_vel[1] - self.max_accel * self.predict_time,
            current_vel[1] + self.max_accel * self.predict_time,
        ]

        # Intersection of Vs and Vd
        dw_x = [max(vs_x[0], vd_x[0]), min(vs_x[1], vd_x[1])]
        dw_y = [max(vs_y[0], vd_y[0]), min(vs_y[1], vd_y[1])]

        if dw_x[0] >= dw_x[1] or dw_y[0] >= dw_y[1]:
            # Degenerate dynamic window: return current velocity
            return self._build_result(
                current_vel, current, goal, 0.0, 0.0, float("inf"),
            )

        # Sample velocities within dynamic window
        v_samples_x = np.linspace(dw_x[0], dw_x[1], self.resolution)
        v_samples_y = np.linspace(dw_y[0], dw_y[1], self.resolution)

        best_velocity = current_vel.copy()
        best_score = -float("inf")
        best_heading = 0.0
        best_clearance = float("inf")
        best_wind_comp = 0.0

        for v_x in v_samples_x:
            for v_y in v_samples_y:
                vel = np.array([v_x, v_y])

                # Simulate trajectory
                trajectory = self._simulate_trajectory(current, vel)

                # Evaluate trajectory
                heading_score, heading_angle = self._heading_score(
                    trajectory[-1], goal,
                )
                clearance_score, min_dist = self._clearance_score(trajectory)
                speed_score = self._speed_score(vel)
                wind_score, wind_comp = self._wind_score(current, vel)

                # Total score (higher is better)
                score = (
                    self.heading_weight * heading_score
                    + self.clearance_weight * clearance_score
                    + self.speed_weight * speed_score
                    - 0.3 * wind_score  # penalize wind disturbance
                )

                if score > best_score:
                    best_score = score
                    best_velocity = vel.copy()
                    best_heading = heading_angle
                    best_clearance = min_dist
                    best_wind_comp = wind_comp

        trajectory = self._simulate_trajectory(current, best_velocity)

        return {
            "trajectory": [p.tolist() for p in trajectory],
            "velocity": best_velocity.tolist(),
            "score": float(best_score),
            "metrics": {
                "optimal_speed": float(np.linalg.norm(best_velocity)),
                "heading_angle": float(best_heading),
                "obstacle_distance": float(best_clearance),
                "wind_compensation": float(best_wind_comp),
            },
        }

    # ------------------------------------------------------------------
    # Dynamic Window
    # ------------------------------------------------------------------

    def _simulate_trajectory(self, start, velocity):
        """Simulate a trajectory from start with constant velocity.

        Accounts for wind disturbance if weather_context is available.
        """
        trajectory = [start.copy()]
        pos = start.copy()
        n_steps = int(self.predict_time / self.dt)

        for _ in range(n_steps):
            # Wind disturbance
            wind_disturbance = np.zeros(2)
            if self.weather_context is not None:
                wind_disturbance = self._get_wind_disturbance(pos)

            # Update position: pos += (velocity + wind_disturbance) * dt
            pos = pos + (velocity + wind_disturbance) * self.dt
            trajectory.append(pos.copy())

        return trajectory

    # ------------------------------------------------------------------
    # Scoring Functions
    # ------------------------------------------------------------------

    def _heading_score(self, position, goal):
        """Compute heading score based on angle to goal.

        Returns (score, angle_in_radians).
        Score is higher when pointing toward the goal.
        """
        to_goal = goal - position
        dist = float(np.linalg.norm(to_goal))
        if dist < 1e-6:
            return 1.0, 0.0

        angle = float(math.atan2(to_goal[1], to_goal[0]))
        # Score: 1.0 when heading directly toward goal, 0.0 when heading away
        # Normalize angle to [0, pi]
        score = (math.cos(angle) + 1.0) / 2.0
        return score, angle

    def _clearance_score(self, trajectory):
        """Compute obstacle clearance score.

        Returns (score, min_distance).
        Score is higher when farther from obstacles.
        """
        if not self.obstacles:
            return 1.0, float("inf")

        min_dist = float("inf")
        for point in trajectory:
            for obs in self.obstacles:
                r = obs[2] if len(obs) > 2 else 1.0
                inflated_r = r + self.safety_distance
                dist = float(np.linalg.norm(point - np.array(obs[:2]))) - inflated_r
                if dist < min_dist:
                    min_dist = dist

        # Score: 1.0 if far from obstacles, 0.0 if touching
        if min_dist <= 0:
            return 0.0, 0.0
        score = min(1.0, min_dist / 5.0)
        return score, min_dist

    def _speed_score(self, velocity):
        """Compute speed score.

        Encourages higher speeds (up to max_speed).
        """
        speed = float(np.linalg.norm(velocity))
        return speed / self.max_speed

    def _wind_score(self, position, velocity):
        """Compute wind disturbance score.

        Returns (score, wind_compensation_vector_magnitude).
        Lower score means less wind disturbance.
        """
        if self.weather_context is None:
            return 0.0, 0.0

        wind_dist = self._get_wind_disturbance(position)
        wind_mag = float(np.linalg.norm(wind_dist))

        # Wind compensation: the velocity adjustment needed to counteract wind
        compensation = -wind_dist
        comp_mag = float(np.linalg.norm(compensation))

        return wind_mag, comp_mag

    # ------------------------------------------------------------------
    # Wind Disturbance
    # ------------------------------------------------------------------

    def _get_wind_disturbance(self, position):
        """Get wind disturbance vector at a given position.

        Wind disturbance is proportional to the difference between
        wind velocity and the UAV's velocity, scaled by a drag coefficient.
        """
        u10 = self.weather_context.get("u10", None)
        v10 = self.weather_context.get("v10", None)
        if u10 is None or v10 is None:
            return np.zeros(2)

        u10 = np.asarray(u10)
        v10 = np.asarray(v10)

        wind_u = self._sample_wind(u10, position)
        wind_v = self._sample_wind(v10, position)

        # Wind disturbance = drag_coefficient * wind_velocity
        drag_coeff = 0.1
        return np.array([wind_u * drag_coeff, wind_v * drag_coeff])

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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_result(self, velocity, current, goal, heading, clearance, wind_comp):
        """Build a fallback result when dynamic window is degenerate."""
        trajectory = self._simulate_trajectory(current, velocity)
        return {
            "trajectory": [p.tolist() for p in trajectory],
            "velocity": velocity.tolist(),
            "score": 0.0,
            "metrics": {
                "optimal_speed": float(np.linalg.norm(velocity)),
                "heading_angle": float(heading),
                "obstacle_distance": float(clearance),
                "wind_compensation": float(wind_comp),
            },
        }

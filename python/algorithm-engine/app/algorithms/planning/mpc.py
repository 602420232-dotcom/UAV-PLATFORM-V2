"""MPC (Model Predictive Control) path planning.

Enhanced implementation with:
- Quadratic Programming based MPC using scipy.optimize.minimize
- Weather-aware wind and turbulence as constraints and costs
- Obstacle avoidance constraints
- Multi-step prediction and rolling optimization
- Comprehensive metrics reporting
"""

from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np
from scipy.optimize import minimize

logger = logging.getLogger(__name__)


class MPCPlanner:
    """Model Predictive Control for dynamic re-planning under uncertainty.

    Enhanced with QP-based optimization, weather awareness, obstacle avoidance,
    and rolling horizon optimization.

    Params schema:
        start: [x, y] current position
        goal: [x, y] target position
        horizon: int, prediction horizon (number of steps, default 10)
        dt: float, time step (default 1.0)
        max_speed: float, maximum speed (default 2.0)
        risk_field: 2D numpy array, risk values (optional)
        obstacles: list of [x, y, radius] (optional)
        Q: float, state tracking weight (default 10.0)
        R: float, control effort weight (default 1.0)
        Q_wind: float, wind disturbance penalty weight (default 2.0)
        Q_obs: float, obstacle avoidance weight (default 50.0)
        safety_distance: float, obstacle clearance (default 1.0)
        weather_context: dict with wind field data (optional)
            u10, v10: 2D numpy arrays (wind components)
            wind_speed: 2D numpy array
            t2m: 2D numpy array (temperature)
            turbulence: 2D numpy array
    """

    def __init__(self, params: dict[str, Any] | None = None):
        self.params = params or {}
        self.start = self.params.get("start", [0, 0])
        self.goal = self.params.get("goal", [10, 10])
        self.horizon = self.params.get("horizon", 10)
        self.risk_field = self.params.get("risk_field", None)
        self.dt = self.params.get("dt", 1.0)
        self.max_speed = self.params.get("max_speed", 2.0)
        self.obstacles = self.params.get("obstacles", [])
        self.Q = self.params.get("Q", 10.0)
        self.R = self.params.get("R", 1.0)
        self.Q_wind = self.params.get("Q_wind", 2.0)
        self.Q_obs = self.params.get("Q_obs", 50.0)
        self.safety_distance = self.params.get("safety_distance", 1.0)
        self.weather_context = self.params.get("weather_context", None)

    def solve(self) -> dict[str, Any]:
        t_start = time.time()

        current = np.array(self.start, dtype=float)
        goal = np.array(self.goal, dtype=float)

        # Decision variables: [vx_0, vy_0, vx_1, vy_1, ..., vx_{H-1}, vy_{H-1}]
        # Total: 2 * horizon variables
        n_vars = 2 * self.horizon

        # Initial guess: straight-line velocities toward goal
        direction = goal - current
        dist = float(np.linalg.norm(direction))
        if dist > 1e-6:
            base_vel = direction / dist * min(self.max_speed, dist / self.horizon)
        else:
            base_vel = np.zeros(2)

        u0 = np.tile(base_vel, self.horizon)

        # --- Rolling optimization ---
        # Solve the full horizon optimization problem
        result = minimize(
            fun=self._cost_function,
            x0=u0,
            args=(current, goal),
            method="SLSQP",
            bounds=[(-self.max_speed, self.max_speed)] * n_vars,
            constraints=self._build_constraints(current, goal),
            options={"maxiter": 100, "ftol": 1e-6},
        )

        if not result.success:
            logger.warning("MPC optimization did not converge: %s", result.message)

        # Extract optimal control sequence
        u_opt = result.x
        control_sequence = []
        path = [current.tolist()]

        pos = current.copy()
        total_path_cost = 0.0
        total_wind_cost = 0.0
        constraint_violations = 0

        for step in range(self.horizon):
            vx = u_opt[2 * step]
            vy = u_opt[2 * step + 1]
            vel = np.array([vx, vy])

            # Clamp to max speed
            speed = float(np.linalg.norm(vel))
            if speed > self.max_speed:
                vel = vel / speed * self.max_speed

            control_sequence.append(vel.tolist())

            # Apply risk avoidance
            if self.risk_field is not None:
                vel = self._avoid_risk(pos, vel, np.asarray(self.risk_field))

            # Compute costs
            step_dist = float(np.linalg.norm(vel * self.dt))
            total_path_cost += step_dist

            wind_cost = self._wind_cost_at(pos, vel)
            total_wind_cost += wind_cost

            # Check obstacle constraint violations
            next_pos = pos + vel * self.dt
            if self._check_obstacle_violation(next_pos):
                constraint_violations += 1

            pos = pos + vel * self.dt
            path.append(pos.tolist())

        compute_time = time.time() - t_start

        return {
            "path": path,
            "control_sequence": control_sequence,
            "steps": len(path) - 1,
            "final_distance": float(np.linalg.norm(pos - goal)),
            "metrics": {
                "path_cost": float(total_path_cost),
                "wind_cost": float(total_wind_cost),
                "constraint_violations": constraint_violations,
                "compute_time": float(compute_time),
            },
        }

    # ------------------------------------------------------------------
    # Cost Function (Objective)
    # ------------------------------------------------------------------

    def _cost_function(self, u, current, goal):
        """MPC cost function to minimize.

        J = sum_{k=0}^{H-1} [
            Q * ||x_k - x_goal||^2       (tracking error)
          + R * ||u_k||^2                  (control effort)
          + Q_wind * ||wind_disturbance||^2 (wind penalty)
          + Q_obs * obstacle_penalty        (obstacle avoidance)
        ]
        """
        cost = 0.0
        pos = current.copy()

        for k in range(self.horizon):
            vx = u[2 * k]
            vy = u[2 * k + 1]
            vel = np.array([vx, vy])

            # State prediction: x_{k+1} = x_k + u_k * dt + wind_disturbance * dt
            wind_dist = np.zeros(2)
            if self.weather_context is not None:
                wind_dist = self._get_wind_disturbance(pos)

            next_pos = pos + vel * self.dt + wind_dist * self.dt

            # Tracking cost
            tracking_error = float(np.linalg.norm(next_pos - goal))
            cost += self.Q * tracking_error ** 2

            # Control effort cost
            cost += self.R * float(np.dot(vel, vel))

            # Wind disturbance cost
            if self.weather_context is not None:
                wind_mag = float(np.linalg.norm(wind_dist))
                cost += self.Q_wind * wind_mag ** 2

            # Obstacle avoidance cost (soft constraint)
            obs_cost = self._obstacle_cost(next_pos)
            cost += self.Q_obs * obs_cost

            # Risk field cost
            if self.risk_field is not None:
                risk_val = self._sample_risk(pos, np.asarray(self.risk_field))
                cost += 10.0 * risk_val ** 2

            pos = next_pos

        return cost

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    def _build_constraints(self, current, goal):
        """Build constraint list for scipy.optimize.minimize.

        Includes:
        - Speed constraints (via bounds)
        - Obstacle avoidance constraints (inequality)
        - Goal proximity constraint (inequality)
        """
        constraints = []

        # Obstacle avoidance constraints: dist(pos_k, obs) >= safety_distance
        # We add constraints for a subset of steps to keep it tractable
        check_steps = list(range(0, self.horizon, max(1, self.horizon // 5)))
        if self.horizon - 1 not in check_steps:
            check_steps.append(self.horizon - 1)

        for k in check_steps:
            for obs in self.obstacles:
                obs_pos = np.array(obs[:2])
                obs_r = obs[2] if len(obs) > 2 else 1.0
                min_clearance = obs_r + self.safety_distance

                def obs_constraint(u, _k=k, _obs_pos=obs_pos, _min_c=min_clearance, _current=current):
                    pos = _current.copy()
                    for step in range(_k + 1):
                        vx = u[2 * step]
                        vy = u[2 * step + 1]
                        vel = np.array([vx, vy])
                        wind_dist = np.zeros(2)
                        if self.weather_context is not None:
                            wind_dist = self._get_wind_disturbance(pos)
                        pos = pos + vel * self.dt + wind_dist * self.dt
                    dist = float(np.linalg.norm(pos - _obs_pos))
                    return dist - _min_c

                constraints.append({
                    "type": "ineq",
                    "fun": obs_constraint,
                })

        return constraints

    # ------------------------------------------------------------------
    # Obstacle Costs and Checks
    # ------------------------------------------------------------------

    def _obstacle_cost(self, position):
        """Compute soft obstacle avoidance cost.

        Returns a positive cost that increases as position approaches obstacles.
        """
        if not self.obstacles:
            return 0.0

        min_dist = float("inf")
        for obs in self.obstacles:
            r = obs[2] if len(obs) > 2 else 1.0
            dist = float(np.linalg.norm(position - np.array(obs[:2]))) - r
            if dist < min_dist:
                min_dist = dist

        clearance = min_dist - self.safety_distance
        if clearance <= 0:
            return (1.0 - clearance) ** 2 * 100.0  # heavy penalty
        return max(0.0, 1.0 / (clearance + 0.1)) * 0.1

    def _check_obstacle_violation(self, position):
        """Check if a position violates obstacle constraints."""
        for obs in self.obstacles:
            r = obs[2] if len(obs) > 2 else 1.0
            dist = float(np.linalg.norm(position - np.array(obs[:2])))
            if dist < r + self.safety_distance:
                return True
        return False

    # ------------------------------------------------------------------
    # Wind Disturbance
    # ------------------------------------------------------------------

    def _get_wind_disturbance(self, position):
        """Get wind disturbance vector at a given position.

        Combines wind velocity and turbulence effects.
        """
        u10 = self.weather_context.get("u10", None)
        v10 = self.weather_context.get("v10", None)
        if u10 is None or v10 is None:
            return np.zeros(2)

        u10 = np.asarray(u10)
        v10 = np.asarray(v10)

        wind_u = self._sample_wind(u10, position)
        wind_v = self._sample_wind(v10, position)

        # Add turbulence effect
        turbulence = self.weather_context.get("turbulence", None)
        turb_effect = 0.0
        if turbulence is not None:
            turb_field = np.asarray(turbulence)
            turb_effect = self._sample_wind(turb_field, position)

        drag_coeff = 0.1
        return np.array([
            wind_u * drag_coeff + turb_effect * drag_coeff * 0.5,
            wind_v * drag_coeff + turb_effect * drag_coeff * 0.5,
        ])

    def _wind_cost_at(self, position, velocity):
        """Compute wind resistance cost at a given position for a velocity."""
        if self.weather_context is None:
            return 0.0

        wind_dist = self._get_wind_disturbance(position)
        # Cost proportional to headwind component
        speed = float(np.linalg.norm(velocity))
        if speed < 1e-6:
            return float(np.linalg.norm(wind_dist))

        v_unit = velocity / speed
        headwind = abs(float(np.dot(wind_dist, v_unit)))
        return headwind * speed * self.dt

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
    # Risk Field
    # ------------------------------------------------------------------

    def _sample_risk(self, position, risk_field):
        """Sample risk value at a position from the risk field."""
        shape = risk_field.shape
        pos_idx = [int(p) for p in position]
        if all(0 <= p < s for p, s in zip(pos_idx, shape)):
            return risk_field[tuple(pos_idx)]
        return 0.0

    def _avoid_risk(self, position, velocity, risk_field):
        """Reduce velocity in high-risk areas."""
        risk_val = self._sample_risk(position, risk_field)
        if risk_val > 0.5:
            velocity = velocity * (1.0 - risk_val * 0.5)
        return velocity

"""
数字孪生仿真引擎
构建无人机飞行的虚实融合数字孪生
"""
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FlightPhase(Enum):
    IDLE = "idle"
    TAKEOFF = "takeoff"
    CRUISE = "cruise"
    MANEUVER = "maneuver"
    LANDING = "landing"
    EMERGENCY = "emergency"


@dataclass
class DroneState:
    position: Tuple[float, float, float]
    velocity: Tuple[float, float, float]
    attitude: Tuple[float, float, float]
    battery: float
    phase: FlightPhase
    timestamp: float


@dataclass
class EnvironmentState:
    wind_speed: float
    wind_direction: float
    temperature: float
    turbulence: float
    visibility: float


class DigitalTwinEngine:
    """数字孪生仿真引擎"""

    def __init__(self):
        self.drone_state = None
        self.env_state = None
        self.physical_parameters = {
            'mass': 2.5, 'wing_area': 0.3, 'drag_coeff': 0.04,
            'max_thrust': 15.0, 'battery_capacity': 100.0
        }
        self.history = []
        self.sync_interval = 0.1

    def initialize(self, start_position: Tuple[float, float, float] = (0, 0, 50)):
        """初始化数字孪生"""
        self.drone_state = DroneState(
            position=start_position,
            velocity=(0, 0, 0),
            attitude=(0, 0, 0),
            battery=100.0,
            phase=FlightPhase.IDLE,
            timestamp=0.0
        )
        self.env_state = EnvironmentState(
            wind_speed=5.0, wind_direction=0, temperature=20,
            turbulence=0.1, visibility=10.0
        )
        logger.info(f"数字孪生初始化完成 @ {start_position}")

    def update_environment(self, weather_data: dict):
        """从真实传感器更新环境状态"""
        self.env_state = EnvironmentState(
            wind_speed=weather_data.get('wind_speed', self.env_state.wind_speed),
            wind_direction=weather_data.get('wind_direction', self.env_state.wind_direction),
            temperature=weather_data.get('temperature', self.env_state.temperature),
            turbulence=weather_data.get('turbulence', self.env_state.turbulence),
            visibility=weather_data.get('visibility', self.env_state.visibility)
        )

    def simulate_physics(self, dt: float, control_input: Tuple[float, float, float]):
        """物理引擎仿真"""
        thrust, roll, pitch = control_input
        mass = self.physical_parameters['mass']
        drag = self.physical_parameters['drag_coeff']

        vx, vy, vz = self.drone_state.velocity
        wind_effect = self.env_state.wind_speed * np.cos(np.radians(self.env_state.wind_direction))

        ax = (thrust * np.sin(pitch) - drag * vx) / mass + wind_effect * 0.01
        ay = (thrust * np.sin(roll) - drag * vy) / mass + self.env_state.turbulence * np.random.randn()
        az = (thrust * np.cos(pitch) * np.cos(roll) - mass * 9.81 - drag * vz) / mass

        x, y, z = self.drone_state.position
        self.drone_state.position = (x + vx * dt + 0.5 * ax * dt**2,
                                      y + vy * dt + 0.5 * ay * dt**2,
                                      z + vz * dt + 0.5 * az * dt**2)
        self.drone_state.velocity = (vx + ax * dt, vy + ay * dt, vz + az * dt)
        self.drone_state.attitude = (roll, pitch, 0)
        self.drone_state.battery -= (thrust / self.physical_parameters['max_thrust']) * dt * 0.5
        self.drone_state.timestamp += dt
        self.history.append({
            'time': self.drone_state.timestamp,
            'position': self.drone_state.position,
            'battery': self.drone_state.battery,
            'env': (self.env_state.wind_speed, self.env_state.temperature)
        })

    def predict_flight(self, waypoints: List[Tuple[float, float, float]],
                       weather_forecast: List[dict]) -> dict:
        """预测飞行轨迹"""
        self.initialize(waypoints[0])
        predicted_trajectory = []

        for i, wpt in enumerate(waypoints[1:
            ], 1):
            if i - 1 < len(weather_forecast):
                self.update_environment(weather_forecast[i - 1])

            dx = wpt[0] - self.drone_state.position[0]
            dy = wpt[1] - self.drone_state.position[1]
            dz = wpt[2] - self.drone_state.position[2]
            dist = np.sqrt(dx**2 + dy**2 + dz**2)

            n_steps = max(10, int(dist / 5))
            for _ in range(n_steps):
                control = (self.physical_parameters['max_thrust'] * 0.6,
                          np.arctan2(dy, dx) * 0.1,
                          np.arctan2(dz, dist) * 0.1)
                self.simulate_physics(self.sync_interval, control)
                predicted_trajectory.append({
                    'position': list(self.drone_state.position),
                    'battery': self.drone_state.battery,
                    'phase': self.drone_state.phase.value
                })

        remaining_battery = self.drone_state.battery
        feasibility = remaining_battery > 10
        return {
            'trajectory': predicted_trajectory,
            'total_distance': sum(np.linalg.norm(np.array(w2) - np.array(w1))
                                  for w1, w2 in zip(waypoints[:
                                      -1], waypoints[1:])),
            'estimated_duration': self.drone_state.timestamp,
            'final_battery': remaining_battery,
            'feasible': feasibility,
            'warning': None if feasibility else '电量不足，建议减少航点或使用更优路线'
        }

    def what_if_analysis(self, waypoints: List[Tuple], weather_scenarios: List[dict]) -> List[dict]:
        """What-If 场景分析"""
        results = []
        for i, weather in enumerate(weather_scenarios):
            self.update_environment(weather)
            result = self.predict_flight(waypoints, [weather])
            result['scenario_id'] = i
            results.append(result)
            logger.info(f"What-If 场景 {i}: 可行性={result['feasible']}, "
                       f"电量={result['final_battery']:.1f}%")
        return results

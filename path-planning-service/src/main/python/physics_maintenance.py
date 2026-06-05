"""
数字孪生完善 - 物理引擎增强 + 预测性维护
"""
import numpy as np
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ComponentStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"


@dataclass
class ComponentHealth:
    name: str
    status: ComponentStatus
    health_score: float
    remaining_life_hours: float
    maintenance_due: bool


class PhysicsEngine:
    """增强物理引擎 - 六自由度仿真"""

    def __init__(self):
        self.dt = 0.02
        self.gravity = 9.81
        self.air_density = 1.225

    def simulate_six_dof(self, state: np.ndarray, controls: np.ndarray,
                         wind: Tuple[float, float, float]) -> np.ndarray:
        """六自由度仿真"""
        x, y, z, vx, vy, vz, phi, theta, psi, p, q, r = state
        thrust, roll_cmd, pitch_cmd, yaw_cmd = controls
        mass, Ixx, Iyy, Izz = 2.5, 0.03, 0.03, 0.05

        wx, wy, wz = wind
        vx_w = vx - wx
        vy_w = vy - wy
        vz_w = vz - wz
        speed = np.sqrt(vx_w**2 + vy_w**2 + vz_w**2)
        drag = 0.5 * self.air_density * speed**2 * 0.04
        drag_x = -drag * vx_w / (speed + 1e-10)
        drag_y = -drag * vy_w / (speed + 1e-10)
        drag_z = -drag * vz_w / (speed + 1e-10)

        ax = (thrust * (np.cos(phi) * np.sin(theta) * np.cos(psi) +
                        np.sin(phi) * np.sin(psi))) / mass + drag_x
        ay = (thrust * (np.cos(phi) * np.sin(theta) * np.sin(psi) -
                        np.sin(phi) * np.cos(psi))) / mass + drag_y
        az = (thrust * np.cos(phi) * np.cos(theta)) / mass - self.gravity + drag_z

        p_dot = (Iyy - Izz) * q * r / Ixx + roll_cmd / Ixx
        q_dot = (Izz - Ixx) * p * r / Iyy + pitch_cmd / Iyy
        r_dot = (Ixx - Iyy) * p * q / Izz + yaw_cmd / Izz

        return np.array([
            x + vx * self.dt, y + vy * self.dt, z + vz * self.dt,
            vx + ax * self.dt, vy + ay * self.dt, vz + az * self.dt,
            phi + p * self.dt, theta + q * self.dt, psi + r * self.dt,
            p + p_dot * self.dt, q + q_dot * self.dt, r + r_dot * self.dt
        ])


class PredictiveMaintenance:
    """预测性维护引擎"""

    def __init__(self):
        self.components: Dict[str, ComponentHealth] = {}
        self.failure_history: List[dict] = []
        self._init_components()

    def _init_components(self):
        for name in ["motor", "battery", "gps", "imu", "esc", "propeller"]:
            self.components[name] = ComponentHealth(
                name=name, status=ComponentStatus.HEALTHY,
                health_score=100.0, remaining_life_hours=500.0,
                maintenance_due=False
            )

    def update_from_telemetry(self, telemetry: dict):
        """根据遥测数据更新组件健康状态"""
        for comp_name, comp in self.components.items():
            if comp_name == "battery":
                cycles = telemetry.get("battery_cycles", 0)
                temp = telemetry.get("battery_temp", 25)
                comp.health_score = max(0, 100 - cycles * 0.5 - max(0, temp - 40) * 2)
                comp.remaining_life_hours = comp.health_score * 5
            elif comp_name == "motor":
                rpm = telemetry.get("motor_rpm", 0)
                motor_temp = telemetry.get("motor_temp", 30)
                comp.health_score = max(0, 100 - abs(rpm - 5000) / 200 - max(0, motor_temp - 60) * 1.5)
                comp.remaining_life_hours = comp.health_score * 3

            if comp.health_score < 60:
                comp.status = ComponentStatus.CRITICAL
                comp.maintenance_due = True
            elif comp.health_score < 80:
                comp.status = ComponentStatus.WARNING
            else:
                comp.status = ComponentStatus.HEALTHY

    def predict_failure(self) -> List[dict]:
        """预测未来24小时内的故障"""
        predictions = []
        for comp in self.components.values():
            if comp.remaining_life_hours < 24:
                predictions.append({
                    "component": comp.name,
                    "remaining_hours": round(comp.remaining_life_hours, 1),
                    "risk": "HIGH",
                    "action": "立即维护"
                })
            elif comp.remaining_life_hours < 100:
                predictions.append({
                    "component": comp.name,
                    "remaining_hours": round(comp.remaining_life_hours, 1),
                    "risk": "MEDIUM",
                    "action": "计划维护"
                })
        return predictions

    def get_maintenance_report(self) -> dict:
        return {
            "overall_health": np.mean([c.health_score for c in self.components.values()]),
            "components": {n: {"health": c.health_score, "status": c.status.value,
                               "remaining_hours": round(c.remaining_life_hours, 1)}
                          for n, c in self.components.items()},
            "predictions": self.predict_failure()
        }


class WhatIfAnalyzer:
    """What-If 场景分析器"""

    def __init__(self, physics_engine: PhysicsEngine):
        self.physics = physics_engine

    def analyze(self, base_scenario: dict, what_if_params: dict) -> dict:
        """执行What-If分析"""
        base_wind = base_scenario.get("wind_speed", 5)
        alt_wind = what_if_params.get("wind_speed", base_wind)
        base_temp = base_scenario.get("temperature", 20)
        alt_temp = what_if_params.get("temperature", base_temp)

        results = {
            "scenario": what_if_params,
            "base": {"wind": base_wind, "temp": base_temp},
            "impacts": {}
        }

        wind_delta = alt_wind - base_wind
        if wind_delta > 3:
            results["impacts"]["flight_stability"] = "显著下降(高风险)"
            results["impacts"]["battery_consumption"] = f"增加{wind_delta * 3:.0f}%"
            results["impacts"]["recommendation"] = "建议推迟飞行或选择替代路线"
        elif wind_delta > 1:
            results["impacts"]["flight_stability"] = "轻微下降"
            results["impacts"]["battery_consumption"] = f"增加{wind_delta * 2:.0f}%"
            results["impacts"]["recommendation"] = "可飞行，需注意风速变化"

        temp_delta = alt_temp - base_temp
        if temp_delta > 10:
            results["impacts"]["battery_efficiency"] = f"降低{temp_delta * 1.5:.0f}%"
        elif temp_delta < -15:
            results["impacts"]["battery_efficiency"] = f"降低{abs(temp_delta) * 2:.0f}%"
            results["impacts"]["icing_risk"] = "存在结冰风险"

        return results

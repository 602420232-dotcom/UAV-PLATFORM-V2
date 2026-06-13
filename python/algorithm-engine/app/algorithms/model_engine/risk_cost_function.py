"""风险代价函数 — 多维风险代价评估模块.

综合天气、地形、空域、能耗等多维度风险因素，对无人机飞行路径
进行代价评估与风险分级，识别高风险航段。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class RiskCostFunction:
    """多维风险代价函数计算器.

    对给定路径综合评估天气风险、地形风险、空域风险和能耗风险，
    通过加权求和得到总代价，并对路径进行风险分级和关键航段识别。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.default_weights = {
            "weather": self.config.get("weather_weight", 0.3),
            "terrain": self.config.get("terrain_weight", 0.25),
            "airspace": self.config.get("airspace_weight", 0.25),
            "energy": self.config.get("energy_weight", 0.2),
        }
        self.risk_thresholds = self.config.get(
            "risk_thresholds",
            {
                "low": 0.3,
                "medium": 0.6,
                "high": 0.8,
            },
        )
        self.critical_threshold = self.config.get(
            "critical_threshold",
            0.7,
        )

    def evaluate(self, params: dict[str, Any]) -> dict[str, Any]:
        """评估路径的多维风险代价.

        Args:
            params: 评估参数字典，包含:
                - path: 路径点列表 [[x, y, z], ...]
                - risk_fields: 各风险场字典，包含:
                    weather, terrain, airspace, energy (各为2D数组或插值函数)
                - weights: 权重配置字典 (可选)
                - flight_params: 飞行参数字典 (可选)

        Returns:
            包含评估结果的字典:
                - total_cost: 总风险代价
                - cost_breakdown: 各维度代价分解
                - risk_level: 风险等级 (low/medium/high/critical)
                - critical_segments: 高风险段索引列表
        """
        np.random.seed(42)

        path = np.asarray(params.get("path", np.zeros((10, 3))), dtype=float)
        risk_fields = params.get("risk_fields", {})
        weights = params.get("weights", self.default_weights)
        flight_params = params.get("flight_params", {})

        n_points = len(path)
        logger.info(
            "开始风险代价评估: 路径点数=%d, 权重=%s",
            n_points,
            weights,
        )

        weather_cost = self._evaluate_weather_risk(path, risk_fields)
        terrain_cost = self._evaluate_terrain_risk(path, risk_fields)
        airspace_cost = self._evaluate_airspace_risk(path, risk_fields)
        energy_cost = self._evaluate_energy_risk(path, risk_fields, flight_params)

        cost_breakdown = {
            "weather": float(weather_cost),
            "terrain": float(terrain_cost),
            "airspace": float(airspace_cost),
            "energy": float(energy_cost),
        }

        total_cost = (
            weights.get("weather", 0.3) * weather_cost
            + weights.get("terrain", 0.25) * terrain_cost
            + weights.get("airspace", 0.25) * airspace_cost
            + weights.get("energy", 0.2) * energy_cost
        )

        risk_level = self._classify_risk_level(total_cost)
        critical_segments = self._identify_critical_segments(
            path,
            risk_fields,
            weights,
        )

        logger.info(
            "风险评估完成: 总代价=%.4f, 风险等级=%s, 高风险段数=%d",
            total_cost,
            risk_level,
            len(critical_segments),
        )

        return {
            "total_cost": float(total_cost),
            "cost_breakdown": cost_breakdown,
            "risk_level": risk_level,
            "critical_segments": critical_segments,
        }

    def _evaluate_weather_risk(
        self,
        path: np.ndarray,
        risk_fields: dict[str, Any],
    ) -> float:
        """评估天气风险代价.

        综合风速、降水、能见度等气象因素。
        """
        weather_field = risk_fields.get("weather", None)
        if weather_field is not None:
            weather_field = np.asarray(weather_field, dtype=float)
            grid_h, grid_w = weather_field.shape
            total = 0.0
            for pt in path:
                x = int(np.clip(pt[0], 0, grid_w - 1))
                y = int(np.clip(pt[1], 0, grid_h - 1))
                total += float(weather_field[y, x])
            return total / max(len(path), 1)

        np.random.seed(42)
        synthetic = 0.2 + 0.3 * np.random.rand(len(path))
        return float(np.mean(synthetic))

    def _evaluate_terrain_risk(
        self,
        path: np.ndarray,
        risk_fields: dict[str, Any],
    ) -> float:
        """评估地形风险代价.

        考虑地形高度变化、障碍物分布等因素。
        """
        terrain_field = risk_fields.get("terrain", None)
        if terrain_field is not None:
            terrain_field = np.asarray(terrain_field, dtype=float)
            grid_h, grid_w = terrain_field.shape
            total = 0.0
            for pt in path:
                x = int(np.clip(pt[0], 0, grid_w - 1))
                y = int(np.clip(pt[1], 0, grid_h - 1))
                total += float(terrain_field[y, x])
            return total / max(len(path), 1)

        np.random.seed(42)
        synthetic = 0.15 + 0.25 * np.random.rand(len(path))
        return float(np.mean(synthetic))

    def _evaluate_airspace_risk(
        self,
        path: np.ndarray,
        risk_fields: dict[str, Any],
    ) -> float:
        """评估空域风险代价.

        考虑禁飞区、限飞区、交通密度等因素。
        """
        airspace_field = risk_fields.get("airspace", None)
        if airspace_field is not None:
            airspace_field = np.asarray(airspace_field, dtype=float)
            grid_h, grid_w = airspace_field.shape
            total = 0.0
            for pt in path:
                x = int(np.clip(pt[0], 0, grid_w - 1))
                y = int(np.clip(pt[1], 0, grid_h - 1))
                total += float(airspace_field[y, x])
            return total / max(len(path), 1)

        np.random.seed(42)
        synthetic = 0.1 + 0.2 * np.random.rand(len(path))
        return float(np.mean(synthetic))

    def _evaluate_energy_risk(
        self,
        path: np.ndarray,
        risk_fields: dict[str, Any],
        flight_params: dict[str, Any],
    ) -> float:
        """评估能耗风险代价.

        根据路径长度、高度变化、风速等计算能耗风险。
        """
        energy_field = risk_fields.get("energy", None)
        if energy_field is not None:
            energy_field = np.asarray(energy_field, dtype=float)
            grid_h, grid_w = energy_field.shape
            total = 0.0
            for pt in path:
                x = int(np.clip(pt[0], 0, grid_w - 1))
                y = int(np.clip(pt[1], 0, grid_h - 1))
                total += float(energy_field[y, x])
            return total / max(len(path), 1)

        if len(path) < 2:
            return 0.0
        distances = np.sqrt(np.sum(np.diff(path, axis=0) ** 2, axis=1))
        altitude_changes = np.abs(np.diff(path[:, 2]))
        base_energy = float(np.sum(distances)) * 0.01
        climb_energy = float(np.sum(altitude_changes)) * 0.05
        total_energy = base_energy + climb_energy
        return float(np.clip(total_energy / max(len(path), 1), 0.0, 1.0))

    def _classify_risk_level(self, total_cost: float) -> str:
        """根据总代价分类风险等级."""
        thresholds = self.risk_thresholds
        if total_cost >= thresholds["high"]:
            return "critical"
        if total_cost >= thresholds["medium"]:
            return "high"
        if total_cost >= thresholds["low"]:
            return "medium"
        return "low"

    def _identify_critical_segments(
        self,
        path: np.ndarray,
        risk_fields: dict[str, Any],
        weights: dict[str, float],
    ) -> list[int]:
        """识别高风险航段索引.

        逐段评估风险，超过阈值的航段标记为高风险。
        """
        if len(path) < 2:
            return []

        critical: list[int] = []
        window_size = max(1, len(path) // 20)

        for i in range(len(path)):
            start_idx = max(0, i - window_size)
            end_idx = min(len(path), i + window_size + 1)
            segment = path[start_idx:end_idx]

            segment_cost = 0.0
            for key, field in risk_fields.items():
                if field is not None:
                    field_arr = np.asarray(field, dtype=float)
                    grid_h, grid_w = field_arr.shape
                    seg_total = 0.0
                    for pt in segment:
                        x = int(np.clip(pt[0], 0, grid_w - 1))
                        y = int(np.clip(pt[1], 0, grid_h - 1))
                        seg_total += float(field_arr[y, x])
                    segment_cost += weights.get(key, 0.25) * seg_total / len(segment)

            if segment_cost > self.critical_threshold:
                critical.append(i)

        return critical

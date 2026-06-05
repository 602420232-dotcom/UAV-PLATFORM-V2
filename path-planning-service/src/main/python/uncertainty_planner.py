"""
不确定性感知路径规划器
基于气象集合预报的鲁棒规划，输出置信区间和备选方案
"""
import numpy as np
import logging
from typing import List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EnsemblePath:
    path: List[Tuple[float, float]]
    cost: float
    risk_score: float


class UncertaintyAwarePlanner:
    """不确定性感知规划器 - 气象集合预报驱动的鲁棒规划"""

    def __init__(self, n_scenarios: int = 50, confidence_level: float = 0.95):
        self.n_scenarios = n_scenarios
        self.confidence_level = confidence_level

    def generate_scenarios(self, weather_data: dict) -> List[dict]:
        """基于气象集合预报生成多个场景"""
        base_wind = weather_data.get('wind_speed', 5)
        base_temp = weather_data.get('temperature', 20)
        base_humidity = weather_data.get('humidity', 60)
        wind_std = weather_data.get('wind_std', base_wind * 0.2)
        temp_std = weather_data.get('temp_std', base_temp * 0.1)

        scenarios = []
        for _ in range(self.n_scenarios):
            scenarios.append({
                'wind_speed': np.random.normal(base_wind, wind_std),
                'temperature': np.random.normal(base_temp, temp_std),
                'humidity': np.random.normal(base_humidity, base_humidity * 0.1),
                'wind_gust': np.random.exponential(base_wind * 0.3),
                'turbulence': np.random.gamma(2, 0.5)
            })
        return scenarios

    def simulate_path(self, start: Tuple, goal: Tuple, scenario: dict) -> EnsemblePath:
        """在给定场景下模拟路径"""
        path = [start]
        n_steps = 50
        wind = scenario['wind_speed']
        turbulence = scenario['turbulence']

        for i in range(n_steps):
            t = (i + 1) / n_steps
            base_x = start[0] + (goal[0] - start[0]) * t
            base_y = start[1] + (goal[1] - start[1]) * t
            perturbation = np.random.normal(0, turbulence) * wind * 0.1
            path.append((base_x + perturbation, base_y + perturbation))

        path.append(goal)
        cost = sum(np.linalg.norm(np.array(path[j]) - np.array(path[j + 1]))
                   for j in range(len(path) - 1))
        risk_score = wind * 0.3 + turbulence * 10 + max(0, scenario.get('wind_gust', 0)) * 0.5
        return EnsemblePath(path=path, cost=cost, risk_score=risk_score)

    def select_robust_path(self, paths: List[EnsemblePath]) -> Tuple[int, float]:
        """选择最鲁棒的路径"""
        costs = np.array([p.cost for p in paths])
        risks = np.array([p.risk_score for p in paths])

        normalized_costs = (costs - costs.min()) / (costs.max() - costs.min() + 1e-10)
        normalized_risks = (risks - risks.min()) / (risks.max() - risks.min() + 1e-10)

        scores = normalized_costs * 0.4 + normalized_risks * 0.6
        best_idx = int(np.argmin(scores))
        return best_idx, scores[best_idx]

    def calculate_confidence(self, paths: List[EnsemblePath]) -> dict:
        """计算路径置信区间"""
        costs = np.array([p.cost for p in paths])
        mean_cost = np.mean(costs)
        std_cost = np.std(costs)
        ci = 1.96 * std_cost / np.sqrt(len(paths))
        return {
            'mean_cost': float(mean_cost),
            'std_cost': float(std_cost),
            'ci_lower': float(mean_cost - ci),
            'ci_upper': float(mean_cost + ci),
            'confidence_level': self.confidence_level
        }

    def plan(self, start: Tuple[float, float], goal: Tuple[float, float],
             weather_ensemble: dict = None) -> dict:
        """执行不确定性感知路径规划"""
        scenarios = self.generate_scenarios(weather_ensemble or {})
        ensemble_paths = [self.simulate_path(start, goal, s) for s in scenarios]
        best_idx, best_score = self.select_robust_path(ensemble_paths)

        top_3 = sorted(range(len(ensemble_paths)), key=lambda i: ensemble_paths[i].risk_score)[:3]
        alternatives = [ensemble_paths[i].path for i in top_3[1:]]
        confidence = self.calculate_confidence(ensemble_paths)

        return {
            'success': True,
            'path': ensemble_paths[best_idx].path,
            'confidence': confidence,
            'alternatives': alternatives,
            'n_scenarios_evaluated': self.n_scenarios,
            'robustness_score': float(1.0 - best_score)
        }

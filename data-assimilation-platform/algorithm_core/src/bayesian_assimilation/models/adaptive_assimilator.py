"""
自适应同化算法
根据数据质量和计算资源动态选择最优同化算法
"""
import numpy as np
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AlgorithmPerformance:
    name: str
    accuracy: float
    speed: float
    memory_usage: float
    data_quality_threshold: float


class AdaptiveAssimilator:
    """自适应同化器 - 根据数据质量动态选择最优算法"""

    def __init__(self):
        self.algorithms = {}
        self.performance_history = []
        self.algorithm_scores = {}
        self._register_algorithms()

    def _register_algorithms(self):
        from bayesian_assimilation.models.three_dimensional_var import \
            ThreeDimensionalVAR as ThreeDimensionalVar
        from bayesian_assimilation.models.four_dimensional_var import FourDimensionalVar
        from bayesian_assimilation.models.enkf import EnKF

        self.algorithms = {
            '3dvar': ThreeDimensionalVar,
            '4dvar': FourDimensionalVar,
            'enkf': EnKF
        }

    def evaluate_data_quality(self, observations: np.ndarray) -> Dict[str, float]:
        """评估数据质量"""
        n_valid = np.sum(~np.isnan(observations))
        total = observations.size
        completeness = n_valid / total if total > 0 else 0
        spatial_std = np.nanstd(observations)
        temporal_std = np.nanstd(np.diff(observations, axis=0)) if observations.shape[0] > 1 else 0
        return {
            'completeness': completeness,
            'spatial_variability': spatial_std,
            'temporal_variability': temporal_std
        }

    def estimate_compute_resources(self) -> Dict[str, float]:
        """估算可用计算资源"""
        import psutil
        return {
            'cpu_available': psutil.cpu_percent(interval=0.1),
            'memory_available': psutil.virtual_memory().available / (1024**3),
            'memory_percent': psutil.virtual_memory().percent
        }

    def select_algorithm(self, observations: np.ndarray, method_hint: Optional[str] = None) -> str:
        """根据数据质量和资源动态选择算法"""
        data_quality = self.evaluate_data_quality(observations)
        compute_resources = self.estimate_compute_resources()

        if method_hint and method_hint in self.algorithms:
            logger.info(f"使用指定算法: {method_hint}")
            return method_hint

        scores = {}
        for name, algo_cls in self.algorithms.items():
            score = 0
            if name == '3dvar':
                score = data_quality['completeness'] * 40 + \
                    (100 - compute_resources['memory_percent']) * 30 + 30
            elif name == '4dvar':
                score = data_quality['completeness'] * 30 + \
                    compute_resources['memory_available'] * 40 + 30
            elif name == 'enkf':
                score = data_quality['spatial_variability'] * 30 + \
                    data_quality['temporal_variability'] * 30 + 40
            scores[name] = score

        best_algo = max(scores, key=scores.get)
        logger.info(f"自适应选择算法: {best_algo} (评分: {scores})")
        return best_algo

    def assimilate(
        self,
        background: np.ndarray,
        observations: np.ndarray,
        method: Optional[str] = None
    ) -> tuple:
        """执行自适应同化"""
        algorithm_name = self.select_algorithm(observations, method)
        algo_cls = self.algorithms[algorithm_name]
        assimilator = algo_cls()
        analysis, uncertainty = assimilator.assimilate(background, observations)
        from datetime import datetime
        self.performance_history.append({
            'algorithm': algorithm_name,
            'timestamp': datetime.now().isoformat(),
            'data_shape': observations.shape
        })
        return analysis, uncertainty

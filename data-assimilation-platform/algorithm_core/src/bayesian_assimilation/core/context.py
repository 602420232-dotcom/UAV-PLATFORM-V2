# algorithm_core/src/bayesian_assimilation/core/context.py

import logging
logger = logging.getLogger(__name__)

from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
import numpy as np


@dataclass
class AssimilationContext:
    """
    同化执行上下文
    保存状态、配置、历史结果
    """

    # 网格状态
    grid_shape: Optional[Tuple[int, int, int]] = None
    resolution: Optional[float] = None

    # 当前执行状态
    current_strategy: Optional[str] = None
    iteration_count: int = 0

    # 历史结果（用于增量同化）
    previous_analysis: Optional[np.ndarray] = None
    previous_variance: Optional[np.ndarray] = None
    previous_background: Optional[np.ndarray] = None

    # 性能统计
    stats: Dict[str, Any] = field(default_factory=dict)

    # 缓存
    cache: Dict[str, Any] = field(default_factory=dict)

    def update_state(self, analysis: np.ndarray, variance: np.ndarray, background: np.ndarray):
        """更新状态（用于下一次增量）"""
        self.previous_analysis = analysis.copy()
        self.previous_variance = variance.copy()
        self.previous_background = background.copy()
        self.iteration_count += 1

    def has_incremental_base(self) -> bool:
        """检查是否有增量基础"""
        return (self.previous_analysis is not None and
                self.previous_variance is not None)

    def detect_change_ratio(self, current_background: np.ndarray) -> float:
        """检测背景场变化比例"""
        if self.previous_background is None:
            return 1.0  # 首次运行，100%变化

        change = np.abs(current_background - self.previous_background)
        relative_change = change / (np.abs(self.previous_background) + 1e-6)

        return float(np.mean(relative_change))

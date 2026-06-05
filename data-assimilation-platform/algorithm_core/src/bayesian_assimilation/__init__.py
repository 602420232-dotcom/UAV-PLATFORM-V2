"""
贝叶斯同化系统
提供贝叶斯数据同化算法及其配套工具
"""

import logging

from .utils.config import (
    BaseConfig, OptimizedConfig, AdaptiveConfig, CompatibleConfig,
    ConfigFactory, AssimilationConfig)
from .core.base import AssimilationBase
from .core.assimilator import BayesianAssimilator
from .core.compatible_assimilator import CompatibleAssimilator
from .models.enhanced_bayesian import EnhancedBayesianAssimilation
from .models.enkf import EnKF
from .models.three_dimensional_var import ThreeDimensionalVAR
from .models.four_dimensional_var import FourDimensionalVar
from .quality_control import MeteorologicalQualityControl
from .risk_assessment import MeteorologicalRiskAssessment, RiskThresholds
from .time_series import TimeSeriesAnalyzer
from .adapters.data import (
    WRFDataAdapter, ObservationAdapter, convert_to_assimilation_format)
from .adapters.grid import GridAdapter, interpolate_data, resample_data
from .utils.validation import DataValidator
from .utils.metrics import (
    PerformanceMetrics, DataQualityMetrics, AssimilationMetrics)
from .utils.log_utils import setup_logging

logger = logging.getLogger(__name__)

__version__ = "1.0.0"

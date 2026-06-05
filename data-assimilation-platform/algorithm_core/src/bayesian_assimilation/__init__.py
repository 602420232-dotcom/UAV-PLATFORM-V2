"""
贝叶斯同化系统
提供贝叶斯数据同化算法及其配套工具
"""

# 配置模块
from .utils.config import BaseConfig, OptimizedConfig, AdaptiveConfig, CompatibleConfig, ConfigFactory, AssimilationConfig

# 核心同化模块
from .core.base import AssimilationBase
from .core.assimilator import BayesianAssimilator
from .core.compatible_assimilator import CompatibleAssimilator

# 同化模型
from .models.enhanced_bayesian import EnhancedBayesianAssimilation
from .models.enkf import EnKF
from .models.three_dimensional_var import ThreeDimensionalVAR
from .models.four_dimensional_var import FourDimensionalVar

# 质量控制模块
from .quality_control import MeteorologicalQualityControl

# 风险评估模块
from .risk_assessment import MeteorologicalRiskAssessment, RiskThresholds

# 时间序列分析模块
from .time_series import TimeSeriesAnalyzer

# 数据适配器
from .adapters.data import WRFDataAdapter, ObservationAdapter, convert_to_assimilation_format
from .adapters.grid import GridAdapter, interpolate_data, resample_data

# 工具函数
from .utils.validation import DataValidator
from .utils.metrics import PerformanceMetrics, DataQualityMetrics, AssimilationMetrics
from .utils.log_utils import setup_logging

__version__ = "1.0.0"

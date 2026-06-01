"""
工具模块
提供配置管理、日志、性能指标、性能分析和参数校验等功能
"""

# 配置模块
from .config import (
    BaseConfig,
    OptimizedConfig,
    AdaptiveConfig,
    CompatibleConfig,
    ConfigFactory,
    AssimilationConfig,
    get_config_from_env
)

# 日志模块
from .log_utils import (
    setup_logging,
    get_logger,
    log_function_call
)

# 性能指标模块
from .metrics import (
    PerformanceMetrics,
    DataQualityMetrics,
    AssimilationMetrics,
    generate_performance_report
)

# 性能分析模块
from .profiler import (
    Profiler,
    profile_function,
    get_profiler,
    timing_block,
    Timer
)

# 参数校验模块
from .validation import (
    DataValidator,
    validate_wind_speed,
    validate_temperature,
    validate_humidity,
    validate_assimilation_inputs
)

__all__ = [
    # 配置
    'BaseConfig',
    'OptimizedConfig',
    'AdaptiveConfig',
    'CompatibleConfig',
    'ConfigFactory',
    'AssimilationConfig',
    'get_config_from_env',
    
    # 日志
    'setup_logging',
    'get_logger',
    'log_function_call',
    
    # 性能指标
    'PerformanceMetrics',
    'DataQualityMetrics',
    'AssimilationMetrics',
    'generate_performance_report',
    
    # 性能分析
    'Profiler',
    'profile_function',
    'get_profiler',
    'timing_block',
    'Timer',
    
    # 参数校验
    'DataValidator',
    'validate_wind_speed',
    'validate_temperature',
    'validate_humidity',
    'validate_assimilation_inputs'
]

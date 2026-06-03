"""
原项目桥接层 — 不动原文件，直接引用

meteor-forecast-service/src/main/python/ 下的1919行代码
保持原位置不动，通过 sys.path 引入
"""
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 原项目 Python 模块路径
METEOR_FORECAST_PATH = str(
    Path(__file__).parent.parent.parent.parent
    / "meteor-forecast-service/src/main/python"
)

def _ensure_import():
    """确保原项目模块可导入"""
    if METEOR_FORECAST_PATH not in sys.path:
        sys.path.insert(0, METEOR_FORECAST_PATH)
        logger.info(f"桥接: 添加原项目路径 {METEOR_FORECAST_PATH}")

# 导入原项目模块
_ensure_import()

try:
    from meteor_forecast import MeteorForecast, Cache, prediction_cache, fusion_cache, risk_cache
    from meteor_forecast_enhanced import MeteorForecast as MeteorForecastEnhanced, ModelConfig, DataPreprocessor, HyperparameterTuner, TrainingMonitor
    from mlops_pipeline import MLOpsPipeline, ModelVersion, ModelMetrics
    from model_serving import ModelServingAPI, ModelStatus, RLModelServing
    LEGACY_AVAILABLE = True
    logger.info("✅ 原项目 meteor-forecast 模块成功桥接")
except ImportError as e:
    logger.warning(f"⚠️ 原项目模块导入失败: {e}（不影响新模型运行）")
    MeteorForecast = None
    MeteorForecastEnhanced = None
    MLOpsPipeline = None
    ModelServingAPI = None
    LEGACY_AVAILABLE = False

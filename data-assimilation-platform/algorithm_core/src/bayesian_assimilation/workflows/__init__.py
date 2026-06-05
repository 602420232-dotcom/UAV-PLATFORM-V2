"""
工作流模块
提供批处理、流水线和流式处理等工作流功能
"""

import logging

# 批处理
from .batch import (
    BatchAssimilator,
    batch_assimilate
)

# 流水线工作流
from .pipeline import (
    PipelineStage,
    PipelineResult,
    StageConfig,
    PipelineStep,
    DataLoadingStep,
    PreprocessingStep,
    AssimilationStep,
    PostprocessingStep,
    AssimilationPipeline,
    create_standard_pipeline
)

# 流式处理工作流
from .streaming import (
    StreamData,
    AssimilationResult,
    StreamBuffer,
    StreamingAssimilator,
    ContinuousAssimilator,
    create_stream_processor,
    process_data_stream
)

logger = logging.getLogger(__name__)

__all__ = [
    # 批处理
    'BatchAssimilator',
    'batch_assimilate',

    # 流水线
    'PipelineStage',
    'PipelineResult',
    'StageConfig',
    'PipelineStep',
    'DataLoadingStep',
    'PreprocessingStep',
    'AssimilationStep',
    'PostprocessingStep',
    'AssimilationPipeline',
    'create_standard_pipeline',

    # 流式处理
    'StreamData',
    'AssimilationResult',
    'StreamBuffer',
    'StreamingAssimilator',
    'ContinuousAssimilator',
    'create_stream_processor',
    'process_data_stream'
]

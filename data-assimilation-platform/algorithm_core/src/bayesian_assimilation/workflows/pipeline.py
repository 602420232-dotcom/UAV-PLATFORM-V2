"""
流水线工作流模块
提供数据处理流水线功能，支持多阶段处理
"""

import logging
from typing import List, Dict, Any, Optional, Callable, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

# 尝试导入必要的类
try:
    from bayesian_assimilation.core.assimilator import BayesianAssimilator
except ImportError:
    class BayesianAssimilator:
        def __init__(self, config=None):
            self.config = config
            self.logger = logging.getLogger(__name__)
        
        def initialize_grid(self: Any, domain_size: int, resolution: Any = None):
            self.domain_size = domain_size
            self.resolution = resolution
        
        def assimilate_3dvar(self, background, observations, obs_locations, obs_errors=None):
            return background.copy(), np.zeros_like(background)

try:
    from bayesian_assimilation.adapters.data import WRFDataAdapter, ObservationAdapter
except ImportError:
    class WRFDataAdapter:
        def __init__(self, config=None):
            self.config = config

    class ObservationAdapter:
        def __init__(self, config=None):
            self.config = config

try:
    from bayesian_assimilation.adapters.grid import interpolate_data, resample_data
except ImportError:
    def interpolate_data(data: Dict[str, Any], grid: str):
        return data
    
    def resample_data(data: Dict[str, Any], factor: Any):
        return data

try:
    from bayesian_assimilation.utils.config import AssimilationConfig
except ImportError:
    class AssimilationConfig:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

try:
    from bayesian_assimilation.utils.logging import setup_logging
except ImportError:
    def setup_logging(level=None, format_str=None, log_file=None):
        pass

logger = logging.getLogger(__name__)

# 真实数据检测标记
# 如果所有数据源均返回模拟数据，应标记整个管线的输出为模拟
REAL_DATA_DETECTED = False


def detect_real_data(sources: dict) -> bool:
    """
    检测是否有真实数据源接入
    
    检查所有配置的数据源是否返回了非模拟的真实观测数据。
    如果没有任何真实数据源，应降低输出结果的置信度标记。
    """
    has_real_data = False
    real_sources = []
    simulated_sources = []
    
    for name, source in sources.items():
        if hasattr(source, 'is_real_data') and source.is_real_data():
            has_real_data = True
            real_sources.append(name)
        else:
            simulated_sources.append(name)
    
    if not has_real_data:
        logger.warning(
            "\n" + "="*60 + "\n"
            "⚠️  警告: 当前无真实数据源接入！\n"
            f"    模拟数据源: {', '.join(simulated_sources)}\n"
            "    同化结果无实际气象参考价值。\n"
            "    请配置真实数据源后重新运行。\n"
            "="*60
        )
    
    return has_real_data


class PipelineStage(Enum):
    """流水线阶段枚举"""
    DATA_LOADING = "data_loading"
    DATA_PREPROCESSING = "data_preprocessing"
    QUALITY_CONTROL = "quality_control"
    ASSIMILATION = "assimilation"
    POSTPROCESSING = "postprocessing"
    OUTPUT = "output"


@dataclass
class PipelineResult:
    """流水线执行结果"""
    stage: PipelineStage
    success: bool
    data: Any = None
    error: Optional[str] = None
    elapsed_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StageConfig:
    """阶段配置"""
    enabled: bool = True
    timeout: Optional[float] = None
    retry_count: int = 0
    custom_params: Dict[str, Any] = field(default_factory=dict)


class PipelineStep:
    """
    流水线步骤基类
    """
    
    def __init__(self, 
                 name: str, 
                 stage: PipelineStage,
                 config: Optional[StageConfig] = None):
        """
        Args:
            name: 步骤名称
            stage: 所属阶段
            config: 阶段配置
        """
        self.name = name
        self.stage = stage
        self.config = config or StageConfig()
        self._result = None
    
    def execute(self, input_data: Any) -> PipelineResult:
        """
        执行步骤
        
        Args:
            input_data: 输入数据
        
        Returns:
            PipelineResult对象
        """
        raise NotImplementedError("子类必须实现 execute 方法")
    
    @property
    def result(self) -> Optional[PipelineResult]:
        """获取执行结果"""
        return self._result
    
    def reset(self):
        """重置步骤状态"""
        self._result = None


class DataLoadingStep(PipelineStep):
    """数据加载步骤"""
    
    def __init__(self, 
                 background_path: str,
                 observation_path: str,
                 config: Optional[StageConfig] = None):
        super().__init__("data_loading", PipelineStage.DATA_LOADING, config)
        self.background_path = background_path
        self.observation_path = observation_path
    
    def execute(self, input_data: Any) -> PipelineResult:
        """加载数据"""
        start_time = datetime.now()
        
        try:
            bg_adapter = WRFDataAdapter(self.background_path)
            background = bg_adapter.load()
            
            obs_adapter = ObservationAdapter(self.observation_path)
            observations, obs_locations, obs_errors = obs_adapter.load()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            result = PipelineResult(
                stage=self.stage,
                success=True,
                data={
                    'background': background,
                    'observations': observations,
                    'obs_locations': obs_locations,
                    'obs_errors': obs_errors
                },
                elapsed_time=elapsed
            )
            
            logger.info(f"数据加载成功: 背景场 {background.shape}, 观测 {len(observations)} 个")
            
        except Exception as e:
            result = PipelineResult(
                stage=self.stage,
                success=False,
                error=str(e),
                elapsed_time=(datetime.now() - start_time).total_seconds()
            )
            logger.error(f"数据加载失败: {e}")
        
        self._result = result
        return result


class PreprocessingStep(PipelineStep):
    """数据预处理步骤"""
    
    def __init__(self, 
                 target_resolution: Optional[float] = None,
                 interpolation_method: str = 'linear',
                 config: Optional[StageConfig] = None):
        super().__init__("preprocessing", PipelineStage.DATA_PREPROCESSING, config)
        self.target_resolution = target_resolution
        self.interpolation_method = interpolation_method
    
    def execute(self, input_data: Dict[str, Any]) -> PipelineResult:
        """预处理数据"""
        start_time = datetime.now()
        
        try:
            background = input_data['background']
            
            # 重采样到目标分辨率
            if self.target_resolution is not None:
                background = resample_data(
                    background, 
                    target_resolution=self.target_resolution,
                    method=self.interpolation_method
                )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            result = PipelineResult(
                stage=self.stage,
                success=True,
                data={
                    'background': background,
                    'observations': input_data['observations'],
                    'obs_locations': input_data['obs_locations'],
                    'obs_errors': input_data['obs_errors']
                },
                elapsed_time=elapsed,
                metadata={'resolution': self.target_resolution}
            )
            
            logger.info(f"数据预处理成功: 分辨率 {self.target_resolution}")
            
        except Exception as e:
            result = PipelineResult(
                stage=self.stage,
                success=False,
                error=str(e),
                elapsed_time=(datetime.now() - start_time).total_seconds()
            )
            logger.error(f"数据预处理失败: {e}")
        
        self._result = result
        return result


class AssimilationStep(PipelineStep):
    """同化步骤"""
    
class AssimilationStep(PipelineStep):
    """同化步骤"""
    
    def __init__(self, 
                 assimilation_config: Optional[AssimilationConfig] = None,
                 config: Optional[StageConfig] = None):
        super().__init__("assimilation", PipelineStage.ASSIMILATION, config)
        self.assimilation_config = assimilation_config
    
    def execute(self, input_data: Dict[str, Any]) -> PipelineResult:
        """执行同化"""
        start_time = datetime.now()
        
        try:
            assimilator = BayesianAssimilator(self.assimilation_config)
            
            analysis, variance = assimilator.assimilate(
                input_data['background'],
                input_data['observations'],
                input_data['obs_locations'],
                input_data['obs_errors']
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            result = PipelineResult(
                stage=self.stage,
                success=True,
                data={
                    'analysis': analysis,
                    'variance': variance,
                    'background': input_data['background']
                },
                elapsed_time=elapsed,
                metadata={
                    'grid_shape': analysis.shape,
                    'mean_variance': float(np.mean(variance))
                }
            )
            
            logger.info(f"同化成功: 分析场 {analysis.shape}, 耗时 {elapsed:.2f}s")
            
        except Exception as e:
            result = PipelineResult(
                stage=self.stage,
                success=False,
                error=str(e),
                elapsed_time=(datetime.now() - start_time).total_seconds()
            )
            logger.error(f"同化失败: {e}")
        
        self._result = result
        return result


class PostprocessingStep(PipelineStep):
    """后处理步骤"""
    
    def __init__(self,
                 compute_statistics: bool = True,
                 compute_gradients: bool = False,
                 config: Optional[StageConfig] = None):
        super().__init__("postprocessing", PipelineStage.POSTPROCESSING, config)
        self.compute_statistics = compute_statistics
        self.compute_gradients = compute_gradients
    
    def execute(self, input_data: Dict[str, Any]) -> PipelineResult:
        """后处理"""
        start_time = datetime.now()
        
        try:
            analysis = input_data['analysis']
            variance = input_data['variance']
            
            output_data = {
                'analysis': analysis,
                'variance': variance,
                'background': input_data['background']
            }
            
            # 计算统计信息
            if self.compute_statistics:
                output_data['statistics'] = {
                    'analysis_mean': float(np.mean(analysis)),
                    'analysis_std': float(np.std(analysis)),
                    'variance_mean': float(np.mean(variance)),
                    'variance_min': float(np.min(variance)),
                    'variance_max': float(np.max(variance))
                }
            
            # 计算梯度
            if self.compute_gradients:
                output_data['analysis_gradient'] = np.gradient(analysis)
                output_data['variance_gradient'] = np.gradient(variance)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            result = PipelineResult(
                stage=self.stage,
                success=True,
                data=output_data,
                elapsed_time=elapsed
            )
            
            logger.info(f"后处理成功")
            
        except Exception as e:
            result = PipelineResult(
                stage=self.stage,
                success=False,
                error=str(e),
                elapsed_time=(datetime.now() - start_time).total_seconds()
            )
            logger.error(f"后处理失败: {e}")
        
        self._result = result
        return result


class AssimilationPipeline:
    """
    同化流水线
    组合多个处理步骤执行完整的数据同化流程
    """
    
    def __init__(self, name: str = "assimilation_pipeline"):
        """
        Args:
            name: 流水线名称
        """
        self.name = name
        self.steps: List[PipelineStep] = []
        self.results: List[PipelineResult] = []
        self._current_data = None
    
    def add_step(self, step: PipelineStep) -> 'AssimilationPipeline':
        """
        添加处理步骤
        
        Args:
            step: PipelineStep对象
        
        Returns:
            self
        """
        self.steps.append(step)
        return self
    
    def remove_step(self, index: int) -> 'AssimilationPipeline':
        """
        移除步骤
        
        Args:
            index: 步骤索引
        
        Returns:
            self
        """
        if 0 <= index < len(self.steps):
            self.steps.pop(index)
        return self
    
    def execute(self, input_data: Any = None) -> Dict[str, Any]:
        """
        执行流水线
        
        Args:
            input_data: 输入数据
        
        Returns:
            最终结果字典
        """
        logger.info(f"开始执行流水线: {self.name}")
        start_time = datetime.now()
        
        self.results = []
        self._current_data = input_data
        
        for i, step in enumerate(self.steps):
            if not step.config.enabled:
                logger.info(f"跳过步骤 {i}: {step.name} (已禁用)")
                continue
            
            logger.info(f"执行步骤 {i+1}/{len(self.steps)}: {step.name}")
            
            result = step.execute(self._current_data)
            self.results.append(result)
            
            if not result.success:
                logger.error(f"流水线执行失败于步骤: {step.name}")
                return {
                    'success': False,
                    'failed_stage': result.stage.value,
                    'error': result.error,
                    'results': self.results
                }
            
            # 将结果数据传递给下一步
            if result.data is not None:
                self._current_data = result.data
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"流水线执行完成: {self.name}, 总耗时 {total_time:.2f}s")
        
        return {
            'success': True,
            'data': self._current_data,
            'results': self.results,
            'total_time': total_time
        }
    
    def reset(self):
        """重置流水线状态"""
        self.results = []
        self._current_data = None
        for step in self.steps:
            step.reset()
    
    def get_timing_report(self) -> str:
        """获取时间报告"""
        lines = [
            "=" * 60,
            f"流水线时间报告: {self.name}",
            "=" * 60
        ]
        
        total = 0.0
        for result in self.results:
            lines.append(f"{result.stage.value}: {result.elapsed_time:.3f}s")
            total += result.elapsed_time
        
        lines.append("-" * 60)
        lines.append(f"总耗时: {total:.3f}s")
        lines.append("=" * 60)
        
        return "\n".join(lines)


def create_standard_pipeline(background_path: str,
                             observation_path: str,
                             output_path: str,
                             config: Optional[AssimilationConfig] = None,
                             target_resolution: Optional[float] = None) -> AssimilationPipeline:
    """
    创建标准同化流水线
    
    Args:
        background_path: 背景场文件路径
        observation_path: 观测数据文件路径
        output_path: 输出文件路径
        config: 同化配置
        target_resolution: 目标分辨率
    
    Returns:
        AssimilationPipeline对象
    """
    pipeline = AssimilationPipeline("standard_assimilation")
    
    # 添加步骤
    pipeline.add_step(DataLoadingStep(background_path, observation_path))
    
    if target_resolution is not None:
        pipeline.add_step(PreprocessingStep(target_resolution=target_resolution))
    
    pipeline.add_step(AssimilationStep(config=config))
    pipeline.add_step(PostprocessingStep(compute_statistics=True))
    
    return pipeline

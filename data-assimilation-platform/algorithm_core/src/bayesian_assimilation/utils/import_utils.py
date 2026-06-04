"""
统一的导入工具模块
提供安全导入功能，支持可选依赖的回退机制
"""

import logging
from typing import Optional, Type, Any, Dict, Callable

logger = logging.getLogger(__name__)


class MockClass:
    """模拟类基类，当真实类无法导入时使用"""
    def __init__(self, *args, **kwargs):
        pass


def safe_import(module_name: str, class_name: Optional[str] = None, mock_methods: Optional[Dict[str, Callable]] = None) -> Any:
    """
    安全导入模块或类，失败时返回模拟类

    Args:
        module_name: 模块名称
        class_name: 类名称（可选）
        mock_methods: 模拟类的方法字典（可选）

    Returns:
        导入的类或模块，或模拟类
    """
    try:
        if class_name:
            module = __import__(module_name, fromlist=[class_name])
            return getattr(module, class_name)
        else:
            return __import__(module_name)
    except ImportError as e:
        logger.debug(f"无法导入 {module_name}.{class_name}: {e}")

        if class_name:
            if mock_methods:
                # 创建带有指定方法的模拟类
                MockClassWithMethods = type(class_name, (MockClass,), mock_methods)
                return MockClassWithMethods
            else:
                # 返回基本的模拟类
                return MockClass
        return None


def create_assimilation_base_mock() -> Type:
    """创建 AssimilationBase 模拟类"""
    from abc import ABC, abstractmethod

    class AssimilationBaseMock(ABC):
        def __init__(self, config=None):
            self.config = config
            self.logger = logging.getLogger(__name__)

        @abstractmethod
        def initialize_grid(self: Any, domain_size: int, resolution: Any = None):
            pass

        @abstractmethod
        def assimilate(self, *args, **kwargs):
            pass

    return AssimilationBaseMock


def create_bayesian_assimilator_mock() -> Type:
    """创建 BayesianAssimilator 模拟类"""
    import numpy as np

    class BayesianAssimilatorMock:
        def __init__(self, config=None):
            self.config = config
            self.logger = logging.getLogger(__name__)

        def initialize_grid(self: Any, domain_size: int, resolution: Any = None):
            self.domain_size = domain_size
            self.resolution = resolution

        def assimilate_3dvar(self, background, observations, obs_locations, obs_errors=None):
            return background.copy(), np.zeros_like(background)

        def assimilate_4dvar(self, background, observations, obs_locations, times, obs_errors=None):
            return background.copy(), np.zeros_like(background)

        def assimilate_enkf(self, background_ensemble, observations, obs_locations, obs_errors=None):
            n_members = background_ensemble.shape[0] if len(background_ensemble.shape) > 1 else 1
            analysis = background_ensemble.copy() if n_members > 1 else background_ensemble
            variance = np.zeros_like(background_ensemble) if n_members == 1 else np.zeros_like(background_ensemble[0])
            return analysis, variance

    return BayesianAssimilatorMock


def create_assimilation_config_mock() -> Type:
    """创建 AssimilationConfig 模拟类"""

    class AssimilationConfigMock:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    return AssimilationConfigMock


def create_performance_metrics_mock() -> Type:
    """创建 PerformanceMetrics 模拟类"""

    class PerformanceMetricsMock:
        def __init__(self):
            self.metrics = {}

        def record(self, name: str, value: float):
            self.metrics[name] = value

        def get_metrics(self) -> Dict[str, float]:
            return self.metrics

    return PerformanceMetricsMock


def create_data_adapter_mocks() -> Dict[str, Type]:
    """创建数据适配器模拟类"""

    class WRFDataAdapterMock:
        def __init__(self, config=None):
            self.config = config

    class ObservationAdapterMock:
        def __init__(self, config=None):
            self.config = config

    class GridAdapterMock:
        def __init__(self, config=None):
            self.config = config

    return {
        'WRFDataAdapter': WRFDataAdapterMock,
        'ObservationAdapter': ObservationAdapterMock,
        'GridAdapter': GridAdapterMock
    }


def create_io_adapter_mocks() -> Dict[str, Any]:
    """创建IO适配器模拟类和函数"""

    class NetCDFReaderMock:
        def __init__(self, path):
            self.path = path

    def write_netcdf_mock(data: Dict[str, Any], path: str):
        pass

    return {
        'NetCDFReader': NetCDFReaderMock,
        'write_netcdf': write_netcdf_mock
    }


def create_parallel_manager_mock() -> Type:
    """创建并行管理器模拟类"""

    class ParallelManagerMock:
        def __init__(self, config=None):
            self.config = config
            self.logger = logging.getLogger(__name__)

        def start(self):
            pass

        def stop(self):
            pass

        def execute(self, func, *args, **kwargs):
            return func(*args, **kwargs)

    return ParallelManagerMock


def get_mock_classes() -> Dict[str, Type]:
    """获取所有模拟类字典"""
    return {
        'AssimilationBase': create_assimilation_base_mock(),
        'BayesianAssimilator': create_bayesian_assimilator_mock(),
        'AssimilationConfig': create_assimilation_config_mock(),
        'PerformanceMetrics': create_performance_metrics_mock(),
        **create_data_adapter_mocks(),
        **create_io_adapter_mocks(),
        'ParallelManager': create_parallel_manager_mock()
    }

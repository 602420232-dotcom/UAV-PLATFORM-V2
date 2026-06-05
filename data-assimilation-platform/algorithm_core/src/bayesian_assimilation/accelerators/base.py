"""
加速器抽象基类
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Any, Dict, Type


class AcceleratorType(Enum):
    """加速器类型"""
    CPU = "cpu"
    OPENMP = "openmp"
    BLAS = "blas"
    CUPY = "cupy"
    PYCUDA = "pycuda"
    JAX = "jax"
    TPU = "tpu"


class BaseAccelerator(ABC):
    """
    加速器抽象基类
    定义所有加速器必须实现的接口
    """

    def __init__(self, config: Optional[Any] = None):
        """
        初始化加速器

        Args:
            config: 加速器配置
        """
        self.config = config
        self.accelerator_type = AcceleratorType.CPU
        self.initialized = False

    @abstractmethod
    def initialize(self) -> bool:
        """
        初始化加速器

        Returns:
            bool: 初始化是否成功
        """
        pass

    @abstractmethod
    def finalize(self):
        """
        释放加速器资源
        """
        pass

    @abstractmethod
    def to_device(self, data: Any) -> Any:
        """
        将数据转移到加速设备

        Args:
            data: 输入数据

        Returns:
            设备上的数据
        """
        pass

    @abstractmethod
    def to_host(self, data: Any) -> Any:
        """
        将数据从设备移回主机

        Args:
            data: 设备上的数据

        Returns:
            主机上的数据
        """
        pass

    @abstractmethod
    def matmul(self, A: Any, B: Any) -> Any:
        """
        矩阵乘法

        Args:
            A: 左矩阵
            B: 右矩阵

        Returns:
            结果矩阵
        """
        pass

    @abstractmethod
    def solve(self, A: Any, b: Any) -> Any:
        """
        求解线性系统 Ax = b

        Args:
            A: 系数矩阵
            b: 右端向量

        Returns:
            解向量
        """
        pass


class AcceleratorFactory:
    """
    加速器工厂类
    用于创建不同类型的加速器实例
    """

    def __init__(self):
        """初始化加速器工厂"""
        self._accelerators: Dict[AcceleratorType, Type[BaseAccelerator]] = {}

    def register(self, accelerator_type: AcceleratorType, accelerator_class: Type[BaseAccelerator]):
        """
        注册加速器类型

        Args:
            accelerator_type: 加速器类型
            accelerator_class: 加速器类
        """
        self._accelerators[accelerator_type] = accelerator_class

    def create(self, accelerator_type: AcceleratorType, config: Optional[Any] = None) -> BaseAccelerator:
        """
        创建加速器实例

        Args:
            accelerator_type: 加速器类型
            config: 加速器配置

        Returns:
            加速器实例

        Raises:
            ValueError: 未知的加速器类型
        """
        if accelerator_type not in self._accelerators:
            raise ValueError(f"Unknown accelerator type: {accelerator_type}")

        return self._accelerators[accelerator_type](config)


# 全局加速器工厂实例
accelerator_factory = AcceleratorFactory()

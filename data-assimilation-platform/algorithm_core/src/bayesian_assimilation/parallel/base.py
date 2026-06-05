"""
并行计算抽象基类
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Any, Dict, Callable, Type, List
import logging


class ParallelType(Enum):
    """并行类型"""
    SEQUENTIAL = "sequential"
    THREAD = "thread"
    PROCESS = "process"
    BLOCK = "block"
    DASK = "dask"
    MPI = "mpi"
    RAY = "ray"


class ParallelManager(ABC):
    """
    并行管理器抽象基类
    定义所有并行管理器必须实现的接口
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化并行管理器

        Args:
            config: 并行管理器配置
        """
        self.config = config or {}
        self.parallel_type = ParallelType.SEQUENTIAL
        self.initialized = False
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def start(self) -> bool:
        """
        启动并行计算环境

        Returns:
            bool: 启动是否成功
        """
        pass

    @abstractmethod
    def stop(self) -> bool:
        """
        停止并行计算环境

        Returns:
            bool: 停止是否成功
        """
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """
        检查并行环境是否运行

        Returns:
            bool: 是否在运行
        """
        pass

    @abstractmethod
    def parallelize(self, func: Callable, data: List[Any], **kwargs) -> List[Any]:
        """
        并行执行函数

        Args:
            func: 要执行的函数
            data: 数据列表
            **kwargs: 其他参数

        Returns:
            List[Any]: 执行结果列表
        """
        pass

    def get_resource_info(self) -> Dict:
        """
        获取资源信息

        Returns:
            Dict: 资源信息
        """
        return {"status": "not_implemented"}

    def initialize(self):
        """初始化（兼容方法）"""
        return self.start()

    def finalize(self):
        """释放资源（兼容方法）"""
        return self.stop()


class ParallelFactory:
    """
    并行管理器工厂类
    用于创建不同类型的并行管理器实例
    """

    def __init__(self):
        """初始化并行管理器工厂"""
        self._managers: Dict[ParallelType, Type[ParallelManager]] = {}

    def register(self, parallel_type: ParallelType, manager_class: Type[ParallelManager]):
        """
        注册并行管理器类型

        Args:
            parallel_type: 并行类型
            manager_class: 管理器类
        """
        self._managers[parallel_type] = manager_class

    def create(self, parallel_type: ParallelType, config: Optional[Dict] = None) -> ParallelManager:
        """
        创建并行管理器实例

        Args:
            parallel_type: 并行类型
            config: 管理器配置

        Returns:
            ParallelManager: 并行管理器实例

        Raises:
            ValueError: 未知的并行类型
        """
        if parallel_type not in self._managers:
            raise ValueError(f"Unknown parallel type: {parallel_type}")

        return self._managers[parallel_type](config)


# 全局并行管理器工厂实例
parallel_factory = ParallelFactory()


class SequentialParallelManager(ParallelManager):
    """
    串行并行管理器（基准实现）
    用于在没有并行环境时的降级处理
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.parallel_type = ParallelType.SEQUENTIAL

    def start(self) -> bool:
        self.initialized = True
        self.logger.info("串行模式启动成功")
        return True

    def stop(self) -> bool:
        self.initialized = False
        self.logger.info("串行模式已停止")
        return True

    def is_running(self) -> bool:
        return self.initialized

    def parallelize(self, func: Callable, data: List[Any], **kwargs) -> List[Any]:
        self.logger.debug(f"串行执行 {len(data)} 个任务")
        return [func(item, **kwargs) for item in data]

    def get_resource_info(self) -> Dict:
        return {
            "status": "running",
            "parallel_type": "sequential",
            "workers": 1
        }


# 注册串行管理器
parallel_factory.register(ParallelType.SEQUENTIAL, SequentialParallelManager)

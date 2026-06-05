# data_sources/base.py
# 数据源处理基类

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class DataSourceBase(ABC):
    """
    数据源基类
    为所有数据源提供统一的接口
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.data = None
        self.metadata = {}

    @abstractmethod
    def load_data(self, *args, **kwargs) -> bool:
        """
        加载数据

        Returns:
            bool: 加载是否成功
        """
        pass

    @abstractmethod
    def process_data(self) -> Any:
        """
        处理数据

        Returns:
            Any: 处理后的数据
        """
        pass

    @abstractmethod
    def get_observations(self) -> Tuple[List[float], List[Tuple[float, float, float]], List[float]]:
        """
        获取观测数据

        Returns:
            Tuple[观测值列表, 观测位置列表, 观测误差列表]
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """
        获取元数据

        Returns:
            Dict[str, Any]: 元数据
        """
        return self.metadata

    def validate_data(self) -> bool:
        """
        验证数据有效性

        Returns:
            bool: 数据是否有效
        """
        if self.data is None:
            logger.error("数据未加载")
            return False
        return True

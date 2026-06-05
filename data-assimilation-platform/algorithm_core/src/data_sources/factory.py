# data_sources/factory.py
# 数据源工厂类

from typing import Optional, Dict, Any
import logging


try:
    from .base import DataSourceBase


except ImportError:
    from abc import ABC, abstractmethod
    class DataSourceBase(ABC):
        def __init__(self, config=None):
            self.config = config or {}
            self.data = None
            self.metadata = {}

        @abstractmethod
        def load_data(self, *args, **kwargs):
            pass

try:
    from .satellite import SatelliteDataSource


except ImportError:
    class SatelliteDataSource(DataSourceBase):
        def __init__(self, config=None):
            super().__init__(config)

        def load_data(self, *args, **kwargs):
            return False

try:
    from .radar import RadarDataSource


except ImportError:
    class RadarDataSource(DataSourceBase):
        def __init__(self, config=None):
            super().__init__(config)

        def load_data(self, *args, **kwargs):
            return False

logger = logging.getLogger(__name__)


class DataSourceFactory:
    """
    数据源工厂类
    用于创建和管理不同类型的数据源
    """

    # 支持的数据源类型
    _data_source_types = {
        'satellite': SatelliteDataSource,
        'radar': RadarDataSource
    }

    @classmethod
    def create_data_source(cls, source_type: str, config: Optional[Dict[str, Any]] = None) -> Optional[DataSourceBase]:
        """
        创建数据源实例

        Args:
            source_type: 数据源类型
            config: 配置参数

        Returns:
            Optional[DataSourceBase]: 数据源实例
        """
        try:
            if source_type not in cls._data_source_types:
                logger.error(f"不支持的数据源类型: {source_type}")
                return None

            data_source_class = cls._data_source_types[source_type]
            data_source = data_source_class(config)
            logger.info(f"成功创建{source_type}数据源实例")
            return data_source
        except Exception as e:
            logger.error(f"创建数据源失败: {e}")
            return None

    @classmethod
    def get_supported_types(cls) -> list:
        """
        获取支持的数据源类型

        Returns:
            list: 支持的数据源类型列表
        """
        return list(cls._data_source_types.keys())

    @classmethod
    def register_data_source(cls, source_type: str, data_source_class: type):
        """
        注册新的数据源类型

        Args:
            source_type: 数据源类型
            data_source_class: 数据源类
        """
        if not issubclass(data_source_class, DataSourceBase):
            logger.error(f"数据源类必须继承自DataSourceBase: {data_source_class}")
            return

        cls._data_source_types[source_type] = data_source_class
        logger.info(f"成功注册新的数据源类型: {source_type}")

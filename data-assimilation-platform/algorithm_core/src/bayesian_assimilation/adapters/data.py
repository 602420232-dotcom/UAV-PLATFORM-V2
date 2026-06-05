"""
数据格式转换模块
提供数据格式转换、验证等功能
"""

import logging
import numpy as np
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)


class DataAdapter:
    """
    数据适配器基类
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def adapt(self, data: Any) -> Any:
        """
        适配数据格式

        Args:
            data: 原始数据

        Returns:
            适配后的数据
        """
        raise NotImplementedError

    def validate(self, data: Any) -> bool:
        """
        验证数据格式

        Args:
            data: 数据

        Returns:
            是否有效
        """
        raise NotImplementedError


class WRFDataAdapter(DataAdapter):
    """
    WRF数据适配器
    """

    def adapt(self, wrf_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        适配WRF数据格式

        Args:
            wrf_data: WRF原始数据

        Returns:
            适配后的数据
        """
        try:
            # 提取必要的变量
            wind_speed = wrf_data.get('wind_speed', np.zeros((10, 10, 10)))
            temperature = wrf_data.get('temperature', np.zeros((10, 10, 10)))
            humidity = wrf_data.get('humidity', np.zeros((10, 10, 10)))
            precipitation = wrf_data.get('precipitation', np.zeros((10, 10, 10)))

            # 转换为同化需要的格式
            adapted_data = {
                'wind_speed': wind_speed,
                'temperature': temperature,
                'humidity': humidity,
                'precipitation': precipitation,
                'domain_size': wrf_data.get('domain_size', (1000, 1000, 100))
            }

            if self.validate(adapted_data):
                logger.info("WRF数据适配成功")
                return adapted_data
            else:
                logger.error("WRF数据验证失败")
                return {}

        except Exception as e:
            logger.error(f"WRF数据适配失败: {e}")
            return {}

    def validate(self, data: Dict[str, Any]) -> bool:
        """
        验证WRF数据
        """
        required_keys = ['wind_speed', 'temperature', 'domain_size']
        for key in required_keys:
            if key not in data:
                logger.error(f"缺少必要键: {key}")
                return False

        # 检查数据维度
        wind_shape = data['wind_speed'].shape
        temp_shape = data['temperature'].shape

        if wind_shape != temp_shape:
            logger.error("风速和温度数据维度不匹配")
            return False

        return True


class ObservationAdapter(DataAdapter):
    """
    观测数据适配器
    """

    def adapt(self, obs_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        适配观测数据格式

        Args:
            obs_data: 观测原始数据

        Returns:
            适配后的数据
        """
        try:
            # 提取必要的变量
            observations = obs_data.get('observations', np.array([]))
            locations = obs_data.get('locations', np.array([]))

            # 转换为同化需要的格式
            adapted_data = {
                'observations': observations,
                'locations': locations,
                'obs_count': len(observations)
            }

            if self.validate(adapted_data):
                logger.info("观测数据适配成功")
                return adapted_data
            else:
                logger.error("观测数据验证失败")
                return {}

        except Exception as e:
            logger.error(f"观测数据适配失败: {e}")
            return {}

    def validate(self, data: Dict[str, Any]) -> bool:
        """
        验证观测数据
        """
        required_keys = ['observations', 'locations']
        for key in required_keys:
            if key not in data:
                logger.error(f"缺少必要键: {key}")
                return False

        # 检查观测值和位置数量是否匹配
        obs_len = len(data['observations'])
        loc_len = len(data['locations'])

        if obs_len != loc_len:
            logger.error("观测值和位置数量不匹配")
            return False

        return True


def convert_to_assimilation_format(data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
    """
    转换为同化格式

    Args:
        data: 原始数据
        data_type: 数据类型 ('wrf' 或 'observation')

    Returns:
        同化格式数据
    """
    if data_type == 'wrf':
        adapter = WRFDataAdapter()
        return adapter.adapt(data)
    elif data_type == 'observation':
        adapter = ObservationAdapter()
        return adapter.adapt(data)
    else:
        logger.error(f"未知数据类型: {data_type}")
        return {}


def validate_data_format(data: Dict[str, Any], data_type: str) -> bool:
    """
    验证数据格式

    Args:
        data: 数据
        data_type: 数据类型

    Returns:
        是否有效
    """
    if data_type == 'wrf':
        adapter = WRFDataAdapter()
        return adapter.validate(data)
    elif data_type == 'observation':
        adapter = ObservationAdapter()
        return adapter.validate(data)
    else:
        logger.error(f"未知数据类型: {data_type}")
        return False

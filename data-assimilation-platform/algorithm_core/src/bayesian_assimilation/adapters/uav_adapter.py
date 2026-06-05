"""
UAV数据适配器模块
提供UAV数据处理和格式转换功能
"""

import logging
import numpy as np
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class UAVDataAdapter:
    """
    UAV数据适配器
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.min_altitude = self.config.get('min_altitude', 0)
        self.max_altitude = self.config.get('max_altitude', 1000)
        self.min_speed = self.config.get('min_speed', 0)
        self.max_speed = self.config.get('max_speed', 100)

    def adapt(self, uav_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        适配UAV数据格式

        Args:
            uav_data: UAV原始数据

        Returns:
            适配后的数据
        """
        try:
            # 处理UAV数据
            processed_data = process_uav_data(uav_data, self.config)

            # 转换为标准格式
            standard_data = uav_to_standard_format(processed_data)

            if self.validate(standard_data):
                logger.info("UAV数据适配成功")
                return standard_data
            else:
                logger.error("UAV数据验证失败")
                return {}

        except Exception as e:
            logger.error(f"UAV数据适配失败: {e}")
            return {}

    def validate(self, data: Dict[str, Any]) -> bool:
        """
        验证UAV数据
        """
        required_keys = ['observations', 'locations']
        for key in required_keys:
            if key not in data:
                logger.error(f"缺少必要键: {key}")
                return False

        # 检查数据范围
        observations = data['observations']
        locations = data['locations']

        if len(observations) != len(locations):
            logger.error("观测值和位置数量不匹配")
            return False

        # 检查风速范围
        if np.any(observations < self.min_speed) or np.any(observations > self.max_speed):
            logger.warning("风速超出合理范围")

        # 检查高度范围
        altitudes = locations[:, 2]
        if np.any(altitudes < self.min_altitude) or np.any(altitudes > self.max_altitude):
            logger.warning("高度超出合理范围")

        return True


def process_uav_data(uav_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    处理UAV数据

    Args:
        uav_data: UAV原始数据
        config: 配置参数

    Returns:
        处理后的数据
    """
    config = config or {}

    try:
        # 提取数据
        flight_data = uav_data.get('flight_data', [])
        sensor_data = uav_data.get('sensor_data', [])

        if not flight_data or not sensor_data:
            logger.error("UAV数据为空")
            return {}

        # 处理飞行数据
        locations = []
        observations = []

        for i, flight in enumerate(flight_data):
            if i < len(sensor_data):
                # 提取位置信息
                lat = flight.get('latitude', 0)
                lon = flight.get('longitude', 0)
                alt = flight.get('altitude', 0)

                # 提取传感器数据
                wind_speed = sensor_data[i].get('wind_speed', 0)
                temperature = sensor_data[i].get('temperature', 25)  # noqa: F841
                humidity = sensor_data[i].get('humidity', 50)  # noqa: F841

                # 转换为笛卡尔坐标（简化处理）
                x = lat * 111319.9  # 纬度转米
                y = lon * 111319.9 * np.cos(np.radians(lat))  # 经度转米
                z = alt

                locations.append([x, y, z])
                observations.append(wind_speed)

        processed_data = {
            'locations': np.array(locations),
            'observations': np.array(observations),
            'sensor_count': len(sensor_data),
            'flight_count': len(flight_data)
        }

        logger.info(f"成功处理UAV数据: {len(observations)} 个观测点")
        return processed_data

    except Exception as e:
        logger.error(f"处理UAV数据失败: {e}")
        return {}


def uav_to_standard_format(uav_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    将UAV数据转换为标准格式

    Args:
        uav_data: 处理后的UAV数据

    Returns:
        标准格式数据
    """
    try:
        # 提取数据
        locations = uav_data.get('locations', np.array([]))
        observations = uav_data.get('observations', np.array([]))

        # 转换为标准格式
        standard_data = {
            'observations': observations,
            'locations': locations,
            'obs_count': len(observations),
            'data_type': 'uav',
            'metadata': {
                'sensor_count': uav_data.get('sensor_count', 0),
                'flight_count': uav_data.get('flight_count', 0)
            }
        }

        logger.info("UAV数据转换为标准格式成功")
        return standard_data

    except Exception as e:
        logger.error(f"UAV数据转换失败: {e}")
        return {}

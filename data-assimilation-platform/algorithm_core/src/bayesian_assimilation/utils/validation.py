"""
参数校验模块
提供数据验证、参数校验等功能
"""

import logging
import numpy as np
from typing import Dict, Any, List, Tuple, Union

logger = logging.getLogger(__name__)


class DataValidator:
    """
    数据验证器
    """

    @staticmethod
    def validate_array(data: np.ndarray, name: str = 'data') -> bool:
        """
        验证数组数据

        Args:
            data: 数组数据
            name: 数据名称

        Returns:
            是否有效
        """
        if data is None:
            logger.error(f"{name} 为 None")
            return False

        if not isinstance(data, np.ndarray):
            logger.error(f"{name} 不是 numpy 数组")
            return False

        if data.size == 0:
            logger.error(f"{name} 为空数组")
            return False

        if np.any(np.isnan(data)):
            nan_count = np.sum(np.isnan(data))
            logger.warning(f"{name} 包含 {nan_count} 个 NaN 值")

        if np.any(np.isinf(data)):
            inf_count = np.sum(np.isinf(data))
            logger.warning(f"{name} 包含 {inf_count} 个 Inf 值")

        return True

    @staticmethod
    def validate_shape(data: np.ndarray, expected_shape: Tuple[int, ...],
                       name: str = 'data') -> bool:
        """
        验证数组形状

        Args:
            data: 数组数据
            expected_shape: 期望形状
            name: 数据名称

        Returns:
            是否有效

        Raises:
            ValueError: 形状不匹配时抛出
        """
        if not DataValidator.validate_array(data, name):
            return False

        if data.shape != expected_shape:
            msg = f"{name} 形状不匹配: 期望 {expected_shape}, 实际 {data.shape}"
            logger.error(msg)
            raise ValueError(msg)

        return True

    @staticmethod
    def validate_range(data: np.ndarray, min_val: float, max_val: float,
                       name: str = 'data') -> bool:
        """
        验证数组值范围

        Args:
            data: 数组数据
            min_val: 最小值
            max_val: 最大值
            name: 数据名称

        Returns:
            是否有效
        """
        if not DataValidator.validate_array(data, name):
            return False

        data_min = np.min(data)
        data_max = np.max(data)

        if data_min < min_val or data_max > max_val:
            logger.warning(
                f"{name} 值范围超出限制: [{data_min:.2f}, {data_max:.2f}], "
                f"期望 [{min_val}, {max_val}]"
            )
            return False

        return True

    @staticmethod
    def validate_dict(data: Dict[str, Any], required_keys: List[str],
                      name: str = 'data') -> bool:
        """
        验证字典数据

        Args:
            data: 字典数据
            required_keys: 必需的键列表
            name: 数据名称

        Returns:
            是否有效
        """
        if data is None:
            logger.error(f"{name} 为 None")
            return False

        if not isinstance(data, dict):
            logger.error(f"{name} 不是字典")
            return False

        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            logger.error(f"{name} 缺少必需键: {missing_keys}")
            return False

        return True

    @staticmethod
    def validate_config(config: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """
        验证配置字典

        Args:
            config: 配置字典
            schema: 配置模式定义

        Returns:
            是否有效
        """
        if not DataValidator.validate_dict(config, list(schema.keys()), 'config'):
            return False

        valid = True
        for key, expected_type in schema.items():
            if key in config:
                if not isinstance(config[key], expected_type):
                    logger.error(f"配置项 {key} 类型错误: 期望 {expected_type}, 实际 {type(config[key])}")
                    valid = False

        return valid

    @staticmethod
    def validate_positive(value: Union[int, float], name: str = 'value') -> bool:
        """
        验证正数

        Args:
            value: 数值
            name: 名称

        Returns:
            是否有效
        """
        if value <= 0:
            logger.error(f"{name} 必须为正数: {value}")
            return False
        return True

    @staticmethod
    def validate_probability(value: float, name: str = 'probability') -> bool:
        """
        验证概率值（0-1之间）

        Args:
            value: 概率值
            name: 名称

        Returns:
            是否有效
        """
        if value < 0 or value > 1:
            logger.error(f"{name} 必须在 0-1 之间: {value}")
            return False
        return True


def validate_wind_speed(wind_speed: np.ndarray) -> bool:
    """
    验证风速数据

    Args:
        wind_speed: 风速数组 (m/s)

    Returns:
        是否有效
    """
    return DataValidator.validate_range(wind_speed, 0.0, 83.3, 'wind_speed')


def validate_temperature(temperature: np.ndarray) -> bool:
    """
    验证温度数据

    Args:
        temperature: 温度数组 (K)

    Returns:
        是否有效
    """
    return DataValidator.validate_range(temperature, 200.0, 330.0, 'temperature')


def validate_humidity(humidity: np.ndarray) -> bool:
    """
    验证湿度数据

    Args:
        humidity: 湿度数组 (%)

    Returns:
        是否有效
    """
    return DataValidator.validate_range(humidity, 0.0, 100.0, 'humidity')


def validate_assimilation_inputs(background: np.ndarray, observations: np.ndarray,
                                 obs_locations: np.ndarray) -> bool:
    """
    验证同化输入数据

    Args:
        background: 背景场数据
        observations: 观测数据
        obs_locations: 观测位置

    Returns:
        是否有效
    """
    valid = True

    if not DataValidator.validate_array(background, 'background'):
        valid = False

    if not DataValidator.validate_array(observations, 'observations'):
        valid = False

    if not DataValidator.validate_array(obs_locations, 'obs_locations'):
        valid = False

    if len(observations) != len(obs_locations):
        logger.error("观测值和位置数量不匹配")
        valid = False

    return valid

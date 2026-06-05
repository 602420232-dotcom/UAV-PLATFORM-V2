"""
气象数据质量控制验证器
提供风速、温度、湿度等气象数据的质量控制功能
"""

import logging
import numpy as np
from typing import Tuple, Optional
from scipy.ndimage import gaussian_filter

logger = logging.getLogger(__name__)


class MeteorologicalQualityControl:
    """
    气象数据质量控制类
    """

    # 风速范围常量 (m/s)
    WIND_SPEED_MIN = 0.0
    WIND_SPEED_MAX = 83.3  # 300 km/h，台风级风速上限

    # 温度范围常量 (K)
    TEMPERATURE_MIN = 200.0  # 约 -73°C
    TEMPERATURE_MAX = 330.0  # 约 57°C

    # 湿度范围常量 (%)
    HUMIDITY_MIN = 0.0
    HUMIDITY_MAX = 100.0

    # 默认梯度阈值 (m/s)
    DEFAULT_GRADIENT_THRESHOLD = 5.0

    @classmethod
    def validate_wind_speed(cls, wind_speed: np.ndarray) -> np.ndarray:
        """
        验证风速数据

        Args:
            wind_speed: 风速数组 (m/s)

        Returns:
            验证后的风速数组
        """
        mask = (wind_speed < cls.WIND_SPEED_MIN) | (wind_speed > cls.WIND_SPEED_MAX)
        if np.any(mask):
            count = np.sum(mask)
            logger.warning(f"发现 {count} 个无效风速值，裁剪到有效范围")
            wind_speed = np.clip(wind_speed, cls.WIND_SPEED_MIN, cls.WIND_SPEED_MAX)

        return wind_speed

    @classmethod
    def validate_temperature(cls, temperature: np.ndarray) -> np.ndarray:
        """
        验证温度数据

        Args:
            temperature: 温度数组 (K)

        Returns:
            验证后的温度数组
        """
        mask = (temperature < cls.TEMPERATURE_MIN) | (temperature > cls.TEMPERATURE_MAX)
        if np.any(mask):
            count = np.sum(mask)
            logger.warning(f"发现 {count} 个无效温度值，裁剪到有效范围")
            temperature = np.clip(temperature, cls.TEMPERATURE_MIN, cls.TEMPERATURE_MAX)

        return temperature

    @classmethod
    def validate_humidity(cls, humidity: np.ndarray) -> np.ndarray:
        """
        验证湿度数据

        Args:
            humidity: 湿度数组 (%)

        Returns:
            验证后的湿度数组
        """
        mask = (humidity < cls.HUMIDITY_MIN) | (humidity > cls.HUMIDITY_MAX)
        if np.any(mask):
            count = np.sum(mask)
            logger.warning(f"发现 {count} 个无效湿度值，裁剪到有效范围")
            humidity = np.clip(humidity, cls.HUMIDITY_MIN, cls.HUMIDITY_MAX)

        return humidity

    @staticmethod
    def detect_outliers(data: np.ndarray, threshold: float = 3.0) -> np.ndarray:
        """
        检测异常值

        Args:
            data: 输入数据
            threshold: 标准差阈值

        Returns:
            异常值掩码
        """
        mean = np.mean(data)
        std = np.std(data)
        outliers = np.abs(data - mean) > threshold * std
        return outliers

    @classmethod
    def check_wind_gradient(cls, wind_speed: np.ndarray,
                           max_gradient: Optional[float] = None) -> np.ndarray:
        """
        检查风速梯度，检测不合理的风速突变

        Args:
            wind_speed: 风速数组
            max_gradient: 最大梯度阈值（可选）

        Returns:
            处理后的风速数组
        """
        if wind_speed.ndim != 3:
            return wind_speed

        max_gradient = max_gradient or cls.DEFAULT_GRADIENT_THRESHOLD

        # 计算水平梯度
        gradient_x = np.abs(np.diff(wind_speed, axis=0))
        gradient_y = np.abs(np.diff(wind_speed, axis=1))

        # 计算垂直梯度
        gradient_z = np.abs(np.diff(wind_speed, axis=2))

        # 检查梯度是否超过阈值
        max_gradient_x = gradient_x.max()
        max_gradient_y = gradient_y.max()
        max_gradient_z = gradient_z.max()

        if max_gradient_x > max_gradient or max_gradient_y > max_gradient or max_gradient_z > max_gradient:
            logger.warning(f"风速梯度超过阈值: x={max_gradient_x:.2f}, y={max_gradient_y:.2f}, z={max_gradient_z:.2f} m/s")

            # 平滑处理
            wind_speed = gaussian_filter(wind_speed, sigma=1.0)
            wind_speed = MeteorologicalQualityControl.validate_wind_speed(wind_speed)

        return wind_speed

    @staticmethod
    def check_time_consistency(time_series_data: list, max_change: float = 10.0) -> list:
        """
        检查时间一致性，确保气象数据随时间合理变化

        Args:
            time_series_data: 时间序列数据列表
            max_change: 最大允许变化量

        Returns:
            处理后的时间序列数据
        """
        if len(time_series_data) < 2:
            return time_series_data

        for i in range(1, len(time_series_data)):
            current_data = time_series_data[i]['wind_speed']
            previous_data = time_series_data[i-1]['wind_speed']

            # 计算时间变化
            time_change = np.abs(current_data - previous_data)
            max_time_change = time_change.max()

            if max_time_change > max_change:
                logger.warning(f"检测到时间不一致: 最大变化 {max_time_change:.2f} m/s 超过阈值 {max_change:.2f} m/s")

                # 平滑处理
                time_series_data[i]['wind_speed'] = 0.7 * current_data + 0.3 * previous_data
                time_series_data[i]['wind_speed'] = MeteorologicalQualityControl.validate_wind_speed(
                    time_series_data[i]['wind_speed']
                )

        return time_series_data

    @staticmethod
    def quality_control_observations(observations: np.ndarray, obs_types: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        质量控制观测数据

        Args:
            observations: 观测值数组
            obs_types: 观测类型数组

        Returns:
            验证后的观测值和有效掩码
        """
        validated_obs = []
        valid_mask = []

        for obs, obs_type in zip(observations, obs_types):
            if obs_type == 'wind_speed':
                # 风速质量控制
                if 0 <= obs <= 83.3:
                    validated_obs.append(obs)
                    valid_mask.append(True)
                else:
                    logger.warning(f"无效风速观测: {obs} m/s，已丢弃")
                    valid_mask.append(False)
            elif obs_type == 'temperature':
                # 温度质量控制（转换为K）
                if 200 <= obs <= 330:
                    validated_obs.append(obs)
                    valid_mask.append(True)
                else:
                    logger.warning(f"无效温度观测: {obs} K，已丢弃")
                    valid_mask.append(False)
            elif obs_type == 'humidity':
                # 湿度质量控制
                if 0 <= obs <= 100:
                    validated_obs.append(obs)
                    valid_mask.append(True)
                else:
                    logger.warning(f"无效湿度观测: {obs} %，已丢弃")
                    valid_mask.append(False)
            else:
                validated_obs.append(obs)
                valid_mask.append(True)

        return np.array(validated_obs), np.array(valid_mask)

    @classmethod
    def adaptive_gradient_threshold(cls, grid_resolution: float,
                                   wind_speed_range: Tuple[float, float]) -> float:
        """
        动态计算梯度阈值

        Args:
            grid_resolution: 网格分辨率
            wind_speed_range: 风速范围 (min, max)

        Returns:
            动态计算的梯度阈值
        """
        base_threshold = cls.DEFAULT_GRADIENT_THRESHOLD

        # 根据网格分辨率调整
        resolution_factor = 100.0 / grid_resolution

        # 根据风速范围调整
        speed_factor = 1.0 + (wind_speed_range[1] - wind_speed_range[0]) / 20.0

        return base_threshold * resolution_factor * speed_factor

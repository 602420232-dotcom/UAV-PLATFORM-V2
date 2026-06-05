"""
气象风险评估器
提供风速风险、湍流风险、风切变风险等评估功能
"""

import logging
import numpy as np
from scipy.special import erf
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class RiskThresholds:
    """
    风险阈值配置类
    """

    # 风速风险阈值 (m/s)
    WIND_SPEED = {
        'low': 10.8,  # 6级风
        'moderate': 17.2,  # 8级风
        'high': 24.5,  # 10级风
        'extreme': 32.7   # 12级风
    }

    # 湍流风险阈值
    TURBULENCE = {
        'low': 5,
        'moderate': 15,
        'high': 25,
        'extreme': 35
    }

    # 垂直风切变风险阈值 (m/s per 100m)
    SHEAR = {
        'low': 2.0,
        'moderate': 4.0,
        'high': 6.0,
        'extreme': 8.0
    }

    # 降水风险阈值 (mm/h)
    PRECIPITATION = {
        'low': 2.5,  # 小雨
        'moderate': 10.0,  # 中雨
        'high': 25.0,  # 大雨
        'extreme': 50.0    # 暴雨
    }

    # 综合风险权重
    COMPOSITE_WEIGHTS = {
        'wind': 0.4,
        'turbulence': 0.3,
        'shear': 0.2,
        'precipitation': 0.1
    }


class MeteorologicalRiskAssessment:
    """
    气象风险评估类
    """

    @staticmethod
    def assess_wind_risk(wind_speed: np.ndarray) -> np.ndarray:
        """
        评估风速风险

        Args:
            wind_speed: 风速数组 (m/s)

        Returns:
            风险等级数组 (0-4)
        """
        thresholds = RiskThresholds.WIND_SPEED

        risk_levels = np.zeros_like(wind_speed, dtype=int)
        risk_levels[wind_speed > thresholds['extreme']] = 4
        risk_levels[(wind_speed > thresholds['high']) & (wind_speed <= thresholds['extreme'])] = 3
        risk_levels[(wind_speed > thresholds['moderate']) & (wind_speed <= thresholds['high'])] = 2
        risk_levels[(wind_speed > thresholds['low']) & (wind_speed <= thresholds['moderate'])] = 1

        return risk_levels

    @staticmethod
    def assess_turbulence_risk(wind_speed: np.ndarray, variance: np.ndarray) -> np.ndarray:
        """
        评估湍流风险

        Args:
            wind_speed: 风速数组
            variance: 方差数组

        Returns:
            风险等级数组 (0-4)
        """
        thresholds = RiskThresholds.TURBULENCE

        # 基于风速和方差的湍流风险评估
        turbulence_index = wind_speed * np.sqrt(variance)

        risk_levels = np.zeros_like(turbulence_index, dtype=int)
        risk_levels[turbulence_index > thresholds['extreme']] = 4
        risk_levels[(turbulence_index > thresholds['high']) & (turbulence_index <= thresholds['extreme'])] = 3
        risk_levels[(turbulence_index > thresholds['moderate']) & (turbulence_index <= thresholds['high'])] = 2
        risk_levels[(turbulence_index > thresholds['low']) & (turbulence_index <= thresholds['moderate'])] = 1

        return risk_levels

    @staticmethod
    def assess_shear_risk(vertical_shear: np.ndarray) -> np.ndarray:
        """
        评估垂直风切变风险

        Args:
            vertical_shear: 垂直风切变数组

        Returns:
            风险等级数组 (0-4)
        """
        thresholds = RiskThresholds.SHEAR

        risk_levels = np.zeros_like(vertical_shear, dtype=int)
        risk_levels[vertical_shear > thresholds['extreme']] = 4
        risk_levels[(vertical_shear > thresholds['high']) & (vertical_shear <= thresholds['extreme'])] = 3
        risk_levels[(vertical_shear > thresholds['moderate']) & (vertical_shear <= thresholds['high'])] = 2
        risk_levels[(vertical_shear > thresholds['low']) & (vertical_shear <= thresholds['moderate'])] = 1

        return risk_levels

    @staticmethod
    def assess_precipitation_risk(precipitation_data: np.ndarray,
                                  duration_hours: float = 1.0) -> np.ndarray:
        """
        评估降水风险

        Args:
            precipitation_data: 降水数据
            duration_hours: 降水持续时间（小时）

        Returns:
            风险等级数组 (0-4)
        """
        thresholds = RiskThresholds.PRECIPITATION

        # 持续性降水的风险调整因子
        if duration_hours >= 6:
            duration_factor = 1.5  # 持续6小时以上，风险增加50%
        elif duration_hours >= 3:
            duration_factor = 1.2  # 持续3-6小时，风险增加20%
        elif duration_hours >= 1:
            duration_factor = 1.0  # 持续1-3小时，风险不变
        else:
            duration_factor = 0.8  # 短时强降水（<1小时），风险降低20%

        risk_levels = np.zeros_like(precipitation_data, dtype=int)

        # 计算风险等级
        extreme_mask = precipitation_data > thresholds['extreme']
        high_mask = (precipitation_data > thresholds['high']) & (precipitation_data <= thresholds['extreme'])
        moderate_mask = (precipitation_data > thresholds['moderate']) & (precipitation_data <= thresholds['high'])
        low_mask = (precipitation_data > thresholds['low']) & (precipitation_data <= thresholds['moderate'])

        risk_levels[extreme_mask] = 4
        risk_levels[high_mask] = 3
        risk_levels[moderate_mask] = 2
        risk_levels[low_mask] = 1

        # 应用持续时间调整因子
        risk_levels = np.clip(np.round(risk_levels * duration_factor), 0, 4).astype(int)

        return risk_levels

    @staticmethod
    def enhanced_precipitation_risk(precipitation: np.ndarray, duration: float,
                                   trend: float) -> np.ndarray:
        """
        增强降水风险评估

        Args:
            precipitation: 降水数据
            duration: 持续时间
            trend: 趋势因子

        Returns:
            风险等级数组
        """
        base_risk = MeteorologicalRiskAssessment.assess_precipitation_risk(precipitation, duration)

        # 持续时间因子
        duration_factor = min(1.0, duration / 60.0)  # 超过1小时风险增加

        # 强度变化率因子
        trend_factor = 1.0 + abs(trend) * 0.5

        return (base_risk * duration_factor * trend_factor).astype(int)

    @classmethod
    def composite_risk_assessment(cls, analysis: np.ndarray, variance: np.ndarray,
                                 precipitation_data: Optional[np.ndarray] = None,
                                 precipitation_duration: float = 1.0,
                                 precipitation_trend: float = 0.0,
                                 wind_speed: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        综合风险评估

        Args:
            analysis: 分析场
            variance: 方差场
            precipitation_data: 降水数据（可选）
            precipitation_duration: 降水持续时间
            precipitation_trend: 降水趋势
            wind_speed: 风速场（可选）

        Returns:
            综合风险评估结果
        """
        if wind_speed is None:
            wind_speed = analysis

        # 评估风速风险
        wind_risk = cls.assess_wind_risk(wind_speed)

        # 评估湍流风险
        turbulence_risk = cls.assess_turbulence_risk(wind_speed, variance)

        # 计算垂直风切变
        vertical_shear = cls.calculate_vertical_shear(wind_speed)

        # 评估垂直风切变风险
        shear_risk = cls.assess_shear_risk(vertical_shear)

        # 降水风险评估（如果数据可用）
        if precipitation_data is not None:
            precipitation_risk = cls.enhanced_precipitation_risk(
                precipitation_data, precipitation_duration, precipitation_trend
            )
        else:
            precipitation_risk = np.zeros_like(wind_speed, dtype=int)

        # 获取权重配置
        weights = RiskThresholds.COMPOSITE_WEIGHTS

        # 综合风险（加权平均）
        composite_risk = (
            weights['wind'] * wind_risk +
            weights['turbulence'] * turbulence_risk +
            weights['shear'] * shear_risk +
            weights['precipitation'] * precipitation_risk
        ).astype(int)

        return {
            'wind_risk': wind_risk,
            'turbulence_risk': turbulence_risk,
            'shear_risk': shear_risk,
            'precipitation_risk': precipitation_risk,
            'composite_risk': composite_risk,
            'vertical_shear': vertical_shear
        }

    @staticmethod
    def calculate_vertical_shear(wind_field: np.ndarray, dz: float = 100.0) -> np.ndarray:
        """
        计算垂直风切变

        Args:
            wind_field: 风场数据 (x, y, z)
            dz: 垂直分辨率

        Returns:
            垂直风切变数组
        """
        if wind_field.ndim != 3:
            raise ValueError("Wind field must be 3D (x, y, z)")

        # 使用中心差分法计算梯度（更精确）
        vertical_shear = np.zeros_like(wind_field)

        # 内部层使用中心差分
        for z in range(1, wind_field.shape[2] - 1):
            shear = np.abs(wind_field[:, :, z+1] - wind_field[:, :, z-1]) / (2 * dz)
            vertical_shear[:, :, z] = shear

        # 边界层使用前向/后向差分
        vertical_shear[:, :, 0] = np.abs(wind_field[:, :, 1] - wind_field[:, :, 0]) / dz
        vertical_shear[:, :, -1] = np.abs(wind_field[:, :, -1] - wind_field[:, :, -2]) / dz

        # 单位转换：m/s per 100m
        vertical_shear = vertical_shear * 100.0

        return vertical_shear

    @staticmethod
    def probabilistic_risk_assessment(analysis: np.ndarray, variance: np.ndarray,
                                     confidence_level: float = 0.95) -> Dict[str, Any]:
        """
        概率风险评估

        Args:
            analysis: 分析场
            variance: 方差场
            confidence_level: 置信水平

        Returns:
            概率风险评估结果
        """
        # 计算置信区间
        z_score = 1.96  # 95%置信水平
        std_dev = np.sqrt(variance)

        # 上下限
        upper_bound = analysis + z_score * std_dev
        lower_bound = analysis - z_score * std_dev

        # 基于上限的风险评估（保守估计）
        upper_risk = MeteorologicalRiskAssessment.assess_wind_risk(upper_bound)

        # 风险概率
        risk_probability = np.zeros_like(analysis)

        for risk_level in [1, 2, 3, 4]:
            threshold = {1: 10.8, 2: 17.2, 3: 24.5, 4: 32.7}[risk_level]
            # 计算超过阈值的概率
            z = (threshold - analysis) / (std_dev + 1e-10)
            prob = 0.5 * (1 + erf(z / np.sqrt(2)))
            risk_probability[upper_risk >= risk_level] = np.maximum(
                risk_probability[upper_risk >= risk_level],
                1 - prob[upper_risk >= risk_level]
            )

        return {
            'upper_bound': upper_bound,
            'lower_bound': lower_bound,
            'risk_probability': risk_probability,
            'confidence_level': confidence_level
        }

    @staticmethod
    def generate_risk_alerts(risk_result: Dict[str, Any], threshold: float = 0.5) -> list:
        """
        生成风险预警

        Args:
            risk_result: 风险评估结果
            threshold: 高风险区域百分比阈值

        Returns:
            预警列表
        """
        alerts = []

        # 高风险区域百分比超过阈值
        if risk_result.get('composite_risk_percentage', 0) > threshold * 100:
            alerts.append({
                'level': 'high',
                'message': f"高风险区域比例达 {risk_result['composite_risk_percentage']:.2f}%, 建议重新规划路线",
                'recommendations': ["避开中心区域", "调整飞行高度", "延迟起飞"]
            })

        # 风险等级超过阈值
        if risk_result.get('max_composite_risk', 0) >= 3:
            alerts.append({
                'level': 'high',
                'message': f"最大风险等级达 {risk_result['max_composite_risk']}，存在高风险区域",
                'recommendations': ["立即避让高风险区域", "准备应急方案"]
            })

        # 检测到中等风险
        if '中等风险' in risk_result.get('risk_zones', []):
            alerts.append({
                'level': 'medium',
                'message': "检测到中等风险区域，需密切关注",
                'recommendations': ["加强监测", "准备备用方案"]
            })

        # 垂直风切变风险
        if 'shear_risk' in risk_result:
            max_shear_risk = np.max(risk_result['shear_risk'])
            if max_shear_risk >= 3:
                alerts.append({
                    'level': 'medium',
                    'message': f"垂直风切变风险较高（等级 {max_shear_risk}），可能影响飞行稳定",
                    'recommendations': ["避免在强风切变区域飞行", "调整飞行速度"]
                })

        # 降水风险
        if 'precipitation_risk' in risk_result:
            max_precip_risk = np.max(risk_result['precipitation_risk'])
            if max_precip_risk >= 3:
                alerts.append({
                    'level': 'medium',
                    'message': f"降水风险较高（等级 {max_precip_risk}），能见度可能受影响",
                    'recommendations': ["关注天气变化", "准备备降机场"]
                })

        return alerts

    @staticmethod
    def generate_risk_region_report(risk_result: Dict[str, Any]) -> list:
        """
        生成风险区域详细报告

        Args:
            risk_result: 风险评估结果

        Returns:
            风险区域列表
        """
        regions = []

        # 降水风险区
        if 'precipitation_risk' in risk_result:
            precip_mask = risk_result['precipitation_risk'] > 0
            if np.any(precip_mask):
                regions.append({
                    'type': 'precipitation',
                    'location': 'center_area',
                    'intensity': 'moderate',
                    'impact': 'visibility_reduction',
                    'recommendation': 'monitor_visibility'
                })

        # 高方差区
        if 'variance' in risk_result and 'risk_threshold' in risk_result:
            high_var_mask = risk_result['variance'] > risk_result['risk_threshold']
            if np.any(high_var_mask):
                regions.append({
                    'type': 'uncertainty',
                    'location': 'scattered',
                    'intensity': 'low',
                    'impact': 'prediction_confidence',
                    'recommendation': 'increase_observations'
                })

        # 风切变风险区
        if 'shear_risk' in risk_result:
            shear_mask = risk_result['shear_risk'] > 0
            if np.any(shear_mask):
                regions.append({
                    'type': 'wind_shear',
                    'location': 'upper_levels',
                    'intensity': 'low',
                    'impact': 'flight_stability',
                    'recommendation': 'avoid_strong_shear'
                })

        return regions

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UAV Edge SDK - 纯 Python 风险评估器（回退模块）

当 C++ 模块不可用时使用此模块
"""

from typing import Dict, List, Any


class RiskLevel:
    """风险等级枚举"""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    SEVERE = 3


class RiskAssessment:
    """风险评估结果"""
    
    def __init__(self):
        self.level = RiskLevel.LOW
        self.score = 0.0
        self.warnings = []


class RiskAssessorFallback:
    """
    纯 Python 实现的气象风险评估器
    """
    
    def __init__(self):
        self.wind_speed_threshold = 10.0
        self.visibility_threshold = 3.0
        self.min_temperature = -20.0
        self.max_temperature = 50.0
    
    def _calculate_wind_risk(self, wind_speed: float) -> float:
        """计算风速风险"""
        if wind_speed < 5.0:
            return 0.0
        elif wind_speed < 10.0:
            return (wind_speed - 5.0) * 10.0
        elif wind_speed < 15.0:
            return 50.0 + (wind_speed - 10.0) * 10.0
        else:
            return 100.0
    
    def _calculate_visibility_risk(self, visibility: float) -> float:
        """计算能见度风险"""
        if visibility > 10.0:
            return 0.0
        elif visibility > 5.0:
            return (10.0 - visibility) * 10.0
        elif visibility > 3.0:
            return 50.0 + (5.0 - visibility) * 25.0
        else:
            return 100.0
    
    def _calculate_temperature_risk(self, temperature: float) -> float:
        """计算温度风险"""
        if 15.0 <= temperature <= 25.0:
            return 0.0
        elif temperature < 15.0:
            diff = 15.0 - temperature
            return min(100.0, diff * 5.0)
        else:
            diff = temperature - 25.0
            return min(100.0, diff * 5.0)
    
    def _calculate_humidity_risk(self, humidity: float) -> float:
        """计算湿度风险"""
        if humidity < 80.0:
            return 0.0
        elif humidity < 95.0:
            return (humidity - 80.0) * 5.0
        else:
            return 75.0 + (humidity - 95.0) * 5.0
    
    def _calculate_precipitation_risk(self, precipitation: float) -> float:
        """计算降水风险"""
        if precipitation < 0.1:
            return 0.0
        elif precipitation < 2.5:
            return precipitation * 20.0
        elif precipitation < 7.5:
            return 50.0 + (precipitation - 2.5) * 10.0
        else:
            return 100.0
    
    def _calculate_thunderstorm_risk(self, has_thunderstorm: bool) -> float:
        """计算雷暴风险"""
        return 100.0 if has_thunderstorm else 0.0
    
    def _score_to_level(self, score: float) -> int:
        """将分数转换为等级"""
        if score < 25.0:
            return RiskLevel.LOW
        elif score < 50.0:
            return RiskLevel.MEDIUM
        elif score < 75.0:
            return RiskLevel.HIGH
        else:
            return RiskLevel.SEVERE
    
    def assess(self, weather: Dict[str, Any]) -> RiskAssessment:
        """评估气象风险"""
        result = RiskAssessment()
        
        # 计算各因素风险
        wind_risk = self._calculate_wind_risk(weather.get('wind_speed', 0.0))
        vis_risk = self._calculate_visibility_risk(weather.get('visibility', 10.0))
        temp_risk = self._calculate_temperature_risk(weather.get('temperature', 20.0))
        hum_risk = self._calculate_humidity_risk(weather.get('humidity', 50.0))
        precip_risk = self._calculate_precipitation_risk(weather.get('precipitation', 0.0))
        thunder_risk = self._calculate_thunderstorm_risk(weather.get('has_thunderstorm', False))
        
        # 加权平均
        total_score = (
            wind_risk * 0.30 +
            vis_risk * 0.25 +
            temp_risk * 0.15 +
            hum_risk * 0.10 +
            precip_risk * 0.15 +
            thunder_risk * 0.05
        )
        
        result.score = min(100.0, max(0.0, total_score))
        result.level = self._score_to_level(result.score)
        
        # 生成警告
        if wind_risk > 50.0:
            if wind_risk >= 75.0:
                result.warnings.append("严重警告: 风速过高，建议推迟飞行")
            else:
                result.warnings.append("警告: 风速较高，谨慎飞行")
        
        if vis_risk > 50.0:
            if vis_risk >= 75.0:
                result.warnings.append("严重警告: 能见度极差，禁止飞行")
            else:
                result.warnings.append("警告: 能见度较低")
        
        if thunder_risk > 0.0:
            result.warnings.append("严重警告: 检测到雷暴天气，禁止飞行")
        
        if precip_risk > 50.0:
            result.warnings.append("警告: 有降水，建议推迟飞行")
        
        if temp_risk > 50.0:
            result.warnings.append("警告: 温度超出适宜范围")
        
        return result
    
    def assess_batch(self, weather_list: List[Dict[str, Any]]) -> List[RiskAssessment]:
        """批量评估"""
        return [self.assess(w) for w in weather_list]
    
    def get_flight_window_advice(self, weather: Dict[str, Any]) -> str:
        """获取飞行窗口建议"""
        assessment = self.assess(weather)
        
        level_names = {
            RiskLevel.LOW: "适宜飞行",
            RiskLevel.MEDIUM: "可以飞行，但需谨慎",
            RiskLevel.HIGH: "不建议飞行",
            RiskLevel.SEVERE: "禁止飞行"
        }
        
        advice = level_names.get(assessment.level, "未知")
        advice += f" (风险分数: {assessment.score:.1f}/100)"
        
        return advice
    
    def set_wind_speed_threshold(self, threshold: float):
        self.wind_speed_threshold = threshold
    
    def set_visibility_threshold(self, threshold: float):
        self.visibility_threshold = threshold
    
    def set_temperature_range(self, min_temp: float, max_temp: float):
        self.min_temperature = min_temp
        self.max_temperature = max_temp

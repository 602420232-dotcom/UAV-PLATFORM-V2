#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UAV Edge SDK - Python 封装层

提供 Python 接口调用 C++ 核心模块，支持离线路径规划和气象风险评估。

Author: Dithiothreitol
License: Apache 2.0
"""

import sys
import os
from typing import List, Tuple, Dict, Any, Optional

# 尝试导入 C++ 模块，如果失败则使用纯 Python 回退
try:
    from . import edge_sdk_cpp
    HAS_CPP_MODULE = True
except ImportError:
    HAS_CPP_MODULE = False
    logger.info("[EdgeSDK] Warning: C++ module not found, using pure Python fallback")

from .config import SDKConfig
from .logger import get_logger

__version__ = "1.0.0"


class EdgeSDK:
    """
    UAV Edge SDK 主类
    
    提供统一的接口访问 C++ 核心功能（路径规划、气象风险评估、飞控通信）
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 Edge SDK
        
        Args:
            config: 配置字典，包含：
                - grid_width: 网格宽度（米）
                - grid_height: 网格高度（米）
                - resolution: 分辨率（米/格）
                - serial_device: 串口设备路径
                - baudrate: 串口波特率
        """
        self.logger = get_logger(__name__)
        self.config = config or {}
        
        # 初始化 C++ 模块
        self._init_cpp_modules()
        
        self.logger.info(f"EdgeSDK initialized (C++: {HAS_CPP_MODULE})")
    
    def _init_cpp_modules(self):
        """初始化 C++ 模块"""
        if HAS_CPP_MODULE:
            try:
                # 初始化路径规划器
                grid_width = self.config.get('grid_width', 100)
                grid_height = self.config.get('grid_height', 100)
                resolution = self.config.get('resolution', 1.0)
                
                self.planner = edge_sdk_cpp.PathPlanner(
                    grid_width, grid_height, resolution
                )
                
                # 初始化风险评估器
                self.risk_assessor = edge_sdk_cpp.RiskAssessor()
                
                # 初始化飞控接口
                serial_device = self.config.get('serial_device', 'COM3')
                baudrate = self.config.get('baudrate', 57600)
                
                self.flight_controller = edge_sdk_cpp.FlightController(
                    serial_device, baudrate
                )
                
                self.logger.info("C++ modules initialized successfully")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize C++ modules: {e}")
                self._use_fallback = True
        else:
            self._use_fallback = True
            self._init_python_fallback()
    
    def _init_python_fallback(self):
        """初始化纯 Python 回退模块"""
        from .path_planner_python import PathPlannerFallback
        from .risk_assessor_python import RiskAssessorFallback
        
        self.logger.warning("Using pure Python fallback (slower performance)")
        
        grid_width = self.config.get('grid_width', 100)
        grid_height = self.config.get('grid_height', 100)
        resolution = self.config.get('resolution', 1.0)
        
        self.planner = PathPlannerFallback(grid_width, grid_height, resolution)
        self.risk_assessor = RiskAssessorFallback()
    
    def plan_path(
        self,
        start: Tuple[int, int],
        goal: Tuple[int, int],
        obstacles: Optional[List[Tuple[int, int]]] = None
    ) -> List[Tuple[int, int]]:
        """
        规划路径
        
        Args:
            start: 起点坐标 (x, y)
            goal: 终点坐标 (x, y)
            obstacles: 障碍物列表 [(x1, y1), (x2, y2), ...]
        
        Returns:
            路径点列表 [(x1, y1), (x2, y2), ...]
        """
        if obstacles is None:
            obstacles = []
        
        self.logger.info(f"Planning path from {start} to {goal}")
        
        try:
            path = self.planner.plan(start, goal, obstacles)
            self.logger.info(f"Path found with {len(path)} waypoints")
            return path
            
        except Exception as e:
            self.logger.error(f"Path planning failed: {e}")
            return []
    
    def assess_weather_risk(self, weather: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估气象风险
        
        Args:
            weather: 气象数据字典，包含：
                - wind_speed (float): 风速 m/s
                - wind_direction (float): 风向 度
                - temperature (float): 温度 °C
                - humidity (float): 湿度 %
                - visibility (float): 能见度 km
                - precipitation (float): 降水量 mm/h
                - has_thunderstorm (bool): 是否有雷暴
        
        Returns:
            风险评估结果字典
        """
        self.logger.info("Assessing weather risk")
        
        try:
            assessment = self.risk_assessor.assess(weather)
            
            # 转换结果为 Python 字典
            level_map = {
                0: "LOW",
                1: "MEDIUM",
                2: "HIGH",
                3: "SEVERE"
            }
            
            return {
                "level": level_map.get(int(assessment.level), "UNKNOWN"),
                "score": assessment.score,
                "warnings": list(assessment.warnings)
            }
            
        except Exception as e:
            self.logger.error(f"Weather risk assessment failed: {e}")
            return {
                "level": "UNKNOWN",
                "score": -1,
                "warnings": [f"Assessment failed: {str(e)}"]
            }
    
    def connect_flight_controller(self) -> bool:
        """连接飞控"""
        try:
            return self.flight_controller.connect()
        except Exception as e:
            self.logger.error(f"Failed to connect flight controller: {e}")
            return False
    
    def disconnect_flight_controller(self):
        """断开飞控连接"""
        try:
            self.flight_controller.disconnect()
        except Exception as e:
            self.logger.error(f"Failed to disconnect flight controller: {e}")
    
    def arm(self) -> bool:
        """解锁电机"""
        try:
            return self.flight_controller.arm()
        except Exception as e:
            self.logger.error(f"Failed to arm: {e}")
            return False
    
    def disarm(self) -> bool:
        """上锁电机"""
        try:
            return self.flight_controller.disarm()
        except Exception as e:
            self.logger.error(f"Failed to disarm: {e}")
            return False
    
    def takeoff(self, altitude: float) -> bool:
        """起飞"""
        try:
            return self.flight_controller.takeoff(altitude)
        except Exception as e:
            self.logger.error(f"Failed to takeoff: {e}")
            return False
    
    def land(self) -> bool:
        """降落"""
        try:
            return self.flight_controller.land()
        except Exception as e:
            self.logger.error(f"Failed to land: {e}")
            return False
    
    def get_uav_state(self) -> Dict[str, Any]:
        """获取无人机状态"""
        try:
            state = self.flight_controller.get_state()
            return {
                "latitude": state.latitude,
                "longitude": state.longitude,
                "altitude": state.altitude,
                "abs_altitude": state.abs_altitude,
                "heading": state.heading,
                "speed": state.speed,
                "battery": state.battery,
                "mode": str(state.mode),
                "armed": state.armed,
                "flying": state.flying
            }
        except Exception as e:
            self.logger.error(f"Failed to get UAV state: {e}")
            return {}
    
    def upload_mission(self, waypoints: List[Dict[str, Any]]) -> bool:
        """上传任务"""
        try:
            return self.flight_controller.upload_mission(waypoints)
        except Exception as e:
            self.logger.error(f"Failed to upload mission: {e}")
            return False
    
    def execute_mission(self) -> bool:
        """执行任务"""
        try:
            return self.flight_controller.execute_mission()
        except Exception as e:
            self.logger.error(f"Failed to execute mission: {e}")
            return False


# 便捷函数
def create_sdk(config: Optional[Dict[str, Any]] = None) -> EdgeSDK:
    """
    创建 Edge SDK 实例
    
    Args:
        config: 配置字典
    
    Returns:
        EdgeSDK 实例
    """
    return EdgeSDK(config)


def plan_path(
    start: Tuple[int, int],
    goal: Tuple[int, int],
    obstacles: Optional[List[Tuple[int, int]]] = None
) -> List[Tuple[int, int]]:
    """
    快速路径规划（使用默认配置）
    """
    sdk = create_sdk()
    return sdk.plan_path(start, goal, obstacles)


def assess_weather(weather: Dict[str, Any]) -> Dict[str, Any]:
    """
    快速气象风险评估
    """
    sdk = create_sdk()
    return sdk.assess_weather_risk(weather)


if __name__ == "__main__":
    # 示例用法
    logger.info("UAV Edge SDK - Python Wrapper")
    logger.info(f"Version: {__version__}")
    logger.info(f"C++ Module Available: {HAS_CPP_MODULE}")
    print()
    
    # 创建 SDK 实例
    sdk = EdgeSDK({
        'grid_width': 100,
        'grid_height': 100,
        'resolution': 1.0
    })
    
    # 示例：路径规划
    logger.info("Example: Path Planning")
    path = sdk.plan_path(
        start=(0, 0),
        goal=(50, 50),
        obstacles=[(10, 10), (10, 11), (11, 10)]
    )
    logger.info(f"  Path length: {len(path)} waypoints")
    
    # 示例：气象风险评估
    logger.info("\nExample: Weather Risk Assessment")
    weather = {
        'wind_speed': 8.0,      # 8 m/s
        'wind_direction': 180,   # 南风
        'temperature': 20.0,      # 20°C
        'humidity': 65.0,        # 65%
        'visibility': 10.0,      # 10 km
        'precipitation': 0.0,    # 无降水
        'has_thunderstorm': False
    }
    
    assessment = sdk.assess_weather_risk(weather)
    logger.info(f"  Risk Level: {assessment['level']}")
    logger.info(f"  Risk Score: {assessment['score']}")
    logger.info(f"  Warnings: {assessment['warnings']}")


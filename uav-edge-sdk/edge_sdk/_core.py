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
import threading
import concurrent.futures
from typing import List, Tuple, Dict, Any, Optional
import logging

# 配置日志
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 尝试导入 C++ 模块，如果失败则使用纯 Python 回退
HAS_CPP_MODULE = False
edge_sdk_cpp = None

try:
    from . import edge_sdk_cpp
    HAS_CPP_MODULE = True
except ImportError:
    logger.info("[EdgeSDK] C++ module not found, using pure Python fallback")

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
        self._lock = threading.Lock()
        self._use_fallback = False
        
        # 初始化 C++ 模块
        self._init_cpp_modules()
        
        self.logger.info(f"EdgeSDK initialized (C++: {HAS_CPP_MODULE})")
    
    def _init_cpp_modules(self):
        """初始化 C++ 模块"""
        with self._lock:
            if HAS_CPP_MODULE:
                try:
                    grid_width = self.config.get('grid_width', 100)
                    grid_height = self.config.get('grid_height', 100)
                    resolution = self.config.get('resolution', 1.0)

                    self.planner = edge_sdk_cpp.PathPlanner(
                        grid_width, grid_height, resolution
                    )

                    self.risk_assessor = edge_sdk_cpp.RiskAssessor()

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
        with self._lock:
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
        obstacles: Optional[List[Tuple[int, int]]] = None,
        timeout_seconds: float = 5.0,
        max_retries: int = 2,
    ) -> List[Tuple[int, int]]:
        """
        Plan a path from start to goal with timeout and retry.

        Args:
            start: Starting (x, y) coordinate.
            goal: Target (x, y) coordinate.
            obstacles: List of obstacle (x, y) coordinates.
            timeout_seconds: Max seconds per planning attempt.
            max_retries: Number of retries on timeout or failure.

        Returns:
            List of (x, y) waypoints, or empty list on failure.
        """
        if obstacles is None:
            obstacles = []

        self.logger.info(f"Planning path from {start} to {goal}")

        for attempt in range(1 + max_retries):
            try:
                with self._lock:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                        future = pool.submit(self.planner.plan, start, goal, obstacles)
                        path = future.result(timeout=timeout_seconds)

                if path:
                    self.logger.info(f"Path found with {len(path)} waypoints (attempt {attempt + 1})")
                    return path

                self.logger.warning(f"Path not found (attempt {attempt + 1})")

            except concurrent.futures.TimeoutError:
                self.logger.warning(
                    f"Path planning timed out after {timeout_seconds}s "
                    f"(attempt {attempt + 1}/{1 + max_retries})"
                )
            except Exception as e:
                self.logger.error(
                    f"Path planning failed (attempt {attempt + 1}): {e}"
                )
                if attempt == max_retries:
                    return []

            if attempt < max_retries:
                self.logger.info(f"Retrying path planning...")

        return []

    def assess_weather_risk(self, weather: Dict[str, Any]) -> Dict[str, Any]:
        """..."""
        self.logger.info("Assessing weather risk")

        try:
            with self._lock:
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
        """Connect to flight controller."""
        try:
            with self._lock:
                return self.flight_controller.connect()
        except Exception as e:
            self.logger.error(f"Failed to connect flight controller: {e}")
            return False

    def disconnect_flight_controller(self):
        """Disconnect from flight controller."""
        try:
            self.flight_controller.disconnect()
        except Exception as e:
            self.logger.error(f"Failed to disconnect flight controller: {e}")

    def arm(self) -> bool:
        """Arm motors."""
        try:
            return self.flight_controller.arm()
        except Exception as e:
            self.logger.error(f"Failed to arm: {e}")
            return False

    def disarm(self) -> bool:
        """Disarm motors."""
        try:
            return self.flight_controller.disarm()
        except Exception as e:
            self.logger.error(f"Failed to disarm: {e}")
            return False

    def takeoff(self, altitude: float) -> bool:
        """Takeoff to target altitude."""
        try:
            return self.flight_controller.takeoff(altitude)
        except Exception as e:
            self.logger.error(f"Failed to takeoff: {e}")
            return False

    def land(self) -> bool:
        """Land the drone."""
        try:
            return self.flight_controller.land()
        except Exception as e:
            self.logger.error(f"Failed to land: {e}")
            return False

    def get_uav_state(self) -> Dict[str, Any]:
        """Get current UAV state."""
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


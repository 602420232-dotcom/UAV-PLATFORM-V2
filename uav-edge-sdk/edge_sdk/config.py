#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UAV Edge SDK - 配置管理模块
"""

from typing import Dict, Any, Optional
import json
import os


class SDKConfig:
    """SDK 配置类"""

    DEFAULT_CONFIG = {
        # 路径规划参数
        'grid_width': 100,
        'grid_height': 100,
        'resolution': 1.0,  # 米/格

        # 串口配置
        'serial_device': 'COM3',
        'baudrate': 57600,

        # 风险评估阈值
        'wind_speed_threshold': 10.0,  # m/s
        'visibility_threshold': 3.0,  # km
        'min_temperature': -20.0,  # °C
        'max_temperature': 50.0,  # °C

        # 日志配置
        'log_level': 'INFO',
        'log_file': None,

        # 其他
        'offline_mode': True,
        'enable_cpp': True
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化配置

        Args:
            config: 配置字典，如果为 None 则使用默认配置
        """
        self._config = self.DEFAULT_CONFIG.copy()

        if config:
            self._config.update(config)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """设置配置项"""
        self._config[key] = value

    def update(self, config: Dict[str, Any]):
        """批量更新配置"""
        self._config.update(config)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self._config.copy()

    def save(self, filepath: str):
        """保存配置到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, filepath: str) -> 'SDKConfig':
        """从文件加载配置"""
        if not os.path.exists(filepath):
            return cls()

        with open(filepath, 'r', encoding='utf-8') as f:
            config = json.load(f)

        return cls(config)

    def __repr__(self) -> str:
        return f"SDKConfig({self._config})"


# 全局配置实例
_global_config = SDKConfig()


def get_config() -> SDKConfig:
    """获取全局配置实例"""
    return _global_config


def set_config(config: Dict[str, Any]):
    """设置全局配置"""
    _global_config.update(config)

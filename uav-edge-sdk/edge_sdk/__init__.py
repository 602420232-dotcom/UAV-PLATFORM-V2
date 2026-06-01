#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UAV Edge SDK - Python Package

提供 C++/Python 混合实现的无人机边缘计算 SDK

使用方法:
    from edge_sdk import EdgeSDK
    sdk = EdgeSDK()
"""

from ._core import EdgeSDK, create_sdk, plan_path, assess_weather
from .config import SDKConfig, get_config, set_config
from .logger import get_logger

__version__ = "1.0.0"

__all__ = [
    'EdgeSDK',
    'create_sdk',
    'plan_path',
    'assess_weather',
    'SDKConfig',
    'get_config',
    'set_config',
    'get_logger',
]

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UAV Edge SDK - 日志模块
"""

import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Logger 实例
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        # 设置日志格式
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # 设置默认级别
        if level:
            logger.setLevel(getattr(logging, level.upper()))
        else:
            logger.setLevel(logging.INFO)

    return logger

# algorithm_core/src/bayesian_assimilation/core/base.py
# 同化算法基类

import os
import sys

SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any
import logging

from bayesian_assimilation.utils.config import BaseConfig

logger = logging.getLogger(__name__)


class AssimilationBase:
    """
    同化算法基类
    为所有同化算法提供基础功能
    """

    def __init__(self, config: Optional[BaseConfig] = None):
        self.config = config or BaseConfig()
        self.grid_shape = None
        self.resolution = None
        self.background = None
        self.analysis = None
        self.variance = None

    def initialize_grid(self, domain_size: Tuple[float, float, float],
                       resolution: Optional[float] = None):
        """
        初始化网格

        Args:
            domain_size: 域大小 (x, y, z)
            resolution: 分辨率
        """
        # 优先使用传入的分辨率，然后是 target_resolution，最后是 grid_resolution
        if resolution is not None:
            res = resolution
        elif hasattr(self.config, 'target_resolution') and self.config.target_resolution is not None:  # type: ignore
            res = self.config.target_resolution  # type: ignore
        else:
            res = self.config.grid_resolution

        self.nx = int(domain_size[0] / res) + 1
        self.ny = int(domain_size[1] / res) + 1
        self.nz = int(domain_size[2] / res) + 1
        self.grid_shape = (self.nx, self.ny, self.nz)
        self.resolution = res

        logger.info(f"初始化网格: {self.nx}×{self.ny}×{self.nz}, 分辨率: {res}m")

    def assimilate(self, background, observations, obs_locations, obs_errors=None):
        """
        执行同化

        Args:
            background: 背景场
            observations: 观测数据
            obs_locations: 观测位置
            obs_errors: 观测误差

        Returns:
            analysis: 分析场
            variance: 方差场
        """
        raise NotImplementedError("子类必须实现assimilate方法")

    def get_analysis(self):
        """
        获取分析场
        """
        return self.analysis

    def get_variance(self):
        """
        获取方差场
        """
        return self.variance

    def get_grid_shape(self):
        """
        获取网格形状
        """
        return self.grid_shape

    def get_resolution(self):
        """
        获取分辨率
        """
        return self.resolution

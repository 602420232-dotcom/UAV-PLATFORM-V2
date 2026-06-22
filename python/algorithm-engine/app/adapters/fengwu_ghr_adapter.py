"""
FengWu-GHR 高分辨率气象模型适配器
支持 0.25° 和 0.09° 两种分辨率
基于 PyTorch 推理
"""
import os
import sys
import torch
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

# 添加 FengWu-GHR 路径
FENGWU_GHR_PATH = os.environ.get('FENGWU_GHR_PATH', 'D:/Developer/FengWu_All/FengWu-GHR')
if FENGWU_GHR_PATH not in sys.path:
    sys.path.insert(0, FENGWU_GHR_PATH)


@dataclass
class FengWuGHRConfig:
    """FengWu-GHR 配置"""
    config_path: str             # 配置文件路径
    checkpoint_dir: str          # 模型检查点目录
    save_path: str               # 输出保存路径
    resolution: str = "0.25"     # 0.25 或 0.09
    version: str = "v2"          # v1 或 v2
    inference_steps: int = 40    # 预报步数
    device: str = "cuda"         # cuda 或 cpu


class FengWuGHRAdapter:
    """FengWu-GHR 高分辨率气象模型适配器"""
    
    def __init__(self, config: FengWuGHRConfig):
        self.config = config
        self.inference = None
        self._init_model()
        
    def _init_model(self):
        """初始化 FengWu-GHR 推理引擎"""
        try:
            from mmengine.config import Config
            from fengwu_ghr_inference_torch import FengWu_GHR_Inference
            
            cfg = Config.fromfile(self.config.config_path)
            cfg.checkpoint_dir = self.config.checkpoint_dir
            cfg.save_cfg.save_path = self.config.save_path
            cfg.inference_steps = self.config.inference_steps
            cfg.fp16 = True
            
            self.inference = FengWu_GHR_Inference(cfg)
            logger.info(f"FengWu-GHR {self.config.resolution}° 模型加载完成")
        except ImportError as e:
            logger.error(f"FengWu-GHR 依赖未安装: {e}")
            raise
        except Exception as e:
            logger.error(f"FengWu-GHR 模型加载失败: {e}")
            raise
        
    def predict(self, timestamp: str) -> Dict:
        """
        执行高分辨率气象预报
        
        Args:
            timestamp: 初始场时间戳 (ISO格式)
            
        Returns:
            预报结果路径和元数据
        """
        try:
            self.inference.inference(timestamp)
            
            return {
                'status': 'success',
                'timestamp': timestamp,
                'resolution': self.config.resolution,
                'output_path': self.config.save_path,
                'variables': getattr(self.inference.cfg.save_cfg, 'variables_list', [])
            }
        except Exception as e:
            logger.error(f"FengWu-GHR 推理失败: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': timestamp
            }
            
    def get_sichuan_basin_forecast(self, timestamp: str) -> Dict:
        """
        获取四川盆地区域的高分辨率预报
        """
        result = self.predict(timestamp)
        
        if result['status'] != 'success':
            return result
            
        # 四川盆地范围：27-35°N, 102-110°E
        # 0.25°分辨率：约32x32格点
        # 0.09°分辨率：约89x89格点
        
        return {
            **result,
            'region': 'sichuan_basin',
            'lat_range': [27, 35],
            'lon_range': [102, 110],
            'resolution': self.config.resolution
        }

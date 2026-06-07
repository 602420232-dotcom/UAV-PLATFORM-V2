#!/usr/bin/env python3
"""
模型训练配置
"""
from dataclasses import dataclass
from pathlib import Path


PROJECT_DIR = Path(__file__).parent.parent
CHECKPOINT_DIR = PROJECT_DIR / "checkpoints"
WEIGHT_DIR = PROJECT_DIR / "weights"


@dataclass
class TrainConfig:
    """训练超参数配置"""
    # 通用
    seed: int = 42
    device: str = "cuda"  # 自动降级为 cpu
    num_workers: int = 4

    # CNN 订正器
    cnn_epochs: int = 100
    cnn_batch_size: int = 16
    cnn_lr: float = 1e-3
    cnn_weight_decay: float = 1e-4

    # U-Net 降尺度
    unet_epochs: int = 100
    unet_batch_size: int = 16
    unet_lr: float = 1e-3

    # XGBoost
    xgboost_n_estimators: int = 200
    xgboost_max_depth: int = 6
    xgboost_lr: float = 0.1

    # 数据
    n_train: int = 3000
    n_val: int = 500
    n_test: int = 500
    auto_generate_data: bool = True  # 无真实数据时自动生成合成数据


CONFIG = TrainConfig()

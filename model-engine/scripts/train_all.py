#!/usr/bin/env python3
"""
一键训练所有模型的统一入口

集成数据生成 → CNN → U-Net → XGBoost
"""
import sys
import logging
from pathlib import Path
import subprocess
import time


logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_script(script_name: str, args: list = None):
    """运行 Python 脚本"""
    script_path = Path(__file__).parent / script_name
    cmd = [sys.executable, str(script_path)] + (args or [])

    logger.info(f"运行: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, cwd=Path(__file__).parent.parent)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"运行 {script_name} 失败: {e}")
        return False


def main():
    logger.info("=" * 60)
    logger.info("无人机气象驱动智能路径规划模型训练流水线")
    logger.info("=" * 60)

    start_time = time.time()

    # 1. 生成训练数据
    logger.info("\n[1/4] 生成训练数据")
    from data_pipeline.training_data import generate_all_training_data
    generate_all_training_data(n_train=3000, n_val=500, n_test=500)

    # 2. 训练 CNN 订正器
    logger.info("\n[2/4] 训练 CNN 订正器")
    if not run_script("train_cnn.py", ["--epochs", "50", "--batch-size", "16"]):
        logger.warning("CNN 训练失败，继续")

    # 3. 训练 U-Net 降尺度
    logger.info("\n[3/4] 训练 U-Net 降尺度器")
    if not run_script("train_unet.py", ["--epochs", "100", "--batch-size", "8"]):
        logger.warning("U-Net 训练失败，继续")

    # 4. 训练 XGBoost 残差订正
    logger.info("\n[4/4] 训练 XGBoost 残差订正器")
    if not run_script("train_xgboost.py"):
        logger.warning("XGBoost 训练失败，继续")

    elapsed = time.time() - start_time
    logger.info("\n" + "=" * 60)
    logger.info(f"流水线完成！耗时 {elapsed:.1f}s")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

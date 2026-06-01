# Type annotations added: 2026-05-08 13:22:43
from typing import Dict, List, Any, Optional, Callable, Tuple

"""
集成所有演示
运行所有四个版本的同化系统
"""

import numpy as np
import logging
from datetime import datetime
import sys
import os

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# 安装说明：在终端执行以下命令
# cd d:\Developer\workplace\py\iteam\trae\data-assimilation-platform\algorithm_core
# pip install -e .
# 导入同化器

from bayesian_assimilation.core.assimilator import BayesianAssimilator # type: ignore
from bayesian_assimilation.core.compatible_assimilator import CompatibleAssimilator # type: ignore
from bayesian_assimilation.utils.config import AssimilationConfig # type: ignore
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '3'  # 启用oneDNN的所有优化
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # 不显示任何信息
import tensorflow as tf  # 进一步设置TensorFlow日志级别
tf.get_logger().setLevel('ERROR')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_synthetic_data(domain_size: int, resolution: Any, n_obs=20: Any):
    """创建合成数据"""
    nx = int(domain_size[0] / resolution) + 1
    ny = int(domain_size[1] / resolution) + 1
    nz = int(domain_size[2] / resolution) + 1

    # 创建网格
    x, y, z = np.meshgrid(
        np.linspace(0, domain_size[0], nx),
        np.linspace(0, domain_size[1], ny),
        np.linspace(0, domain_size[2], nz),
        indexing='ij'
    )

    # 背景场：基本风速 + 涡旋
    background = 5.0 + 2.0 * np.sin(2*np.pi*x/500) * np.cos(2*np.pi*y/500)

    # 观测数据
    np.random.seed(42)
    observations = []
    obs_locations = []

    for i in range(n_obs):
        obs_x = np.random.uniform(0, domain_size[0])
        obs_y = np.random.uniform(0, domain_size[1])
        obs_z = np.random.uniform(0, domain_size[2])

        true_value = 5.0 + 2.0 * np.sin(2*np.pi*obs_x/500) * np.cos(2*np.pi*obs_y/500)
        obs_value = true_value + np.random.normal(0, 0.5)

        observations.append(obs_value)
        obs_locations.append([obs_x, obs_y, obs_z])

    observations = np.array(observations)
    obs_locations = np.array(obs_locations)

    return background, observations, obs_locations


def demo_bayesian():
    """演示贝叶斯同化器"""
    logger.info("="*60)
    logger.info("演示贝叶斯同化器")
    logger.info("="*60)

    config = AssimilationConfig(
        domain_size=(1000, 1000, 100),  # 1km x 1km x 100m
        target_resolution=50.0,          # 50米分辨率
        background_error_scale=1.5,
        observation_error_scale=0.8
    )

    assimilator = BayesianAssimilator(config)
    assimilator.initialize_grid((1000, 1000, 100))

    background, observations, obs_locations = create_synthetic_data(
        (1000, 1000, 100), 50, n_obs=10
    )

    try:
        analysis, variance = assimilator.assimilate_3dvar(
            background, observations, obs_locations
        )

        logger.info(f"贝叶斯同化器完成，分析形状: {analysis.shape}")
        logger.info(f"平均方差: {np.mean(variance):.4f}")

        # 降尺度
        variance_high_res = assimilator.interpolate_to_path_grid(target_resolution=10.0)
        logger.info(f"降尺度形状: {variance_high_res.shape}")

        return True
    except Exception as e:
        logger.error(f"贝叶斯同化器失败: {e}")
        return False


def demo_compatible():
    """演示兼容性同化器"""
    logger.info("\n" + "="*60)
    logger.info("演示兼容性同化器")
    logger.info("="*60)

    config = AssimilationConfig(
        domain_size=(1000, 1000, 100),
        target_resolution=50.0,
        background_error_scale=1.5,
        observation_error_scale=0.8
    )

    assimilator = CompatibleAssimilator(config)
    assimilator.initialize_grid((1000, 1000, 100))

    background, observations, obs_locations = create_synthetic_data(
        (1000, 1000, 100), 50, n_obs=10
    )

    try:
        analysis, variance = assimilator.assimilate_3dvar(
            background, observations, obs_locations
        )

        logger.info(f"兼容性同化器完成，分析形状: {analysis.shape}")
        logger.info(f"平均方差: {np.mean(variance):.4f}")

        return True
    except Exception as e:
        logger.error(f"兼容性同化器失败: {e}")
        return False


def main():
    """主函数：运行所有演示"""
    logger.info("开始运行贝叶斯同化系统演示")
    logger.info("="*60)

    results = {}

    # 1. 贝叶斯同化器
    results['bayesian'] = demo_bayesian()

    # 2. 兼容性同化器
    results['compatible'] = demo_compatible()

    # 汇总结果
    logger.info("\n" + "="*60)
    logger.info("演示结果汇总")
    logger.info("="*60)

    for name, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        logger.info(f"{name}: {status}")

    success_count = sum(results.values())
    total_count = len(results)

    logger.info(f"\n总共运行: {total_count} 个演示")
    logger.info(f"成功: {success_count}")
    logger.info(f"失败: {total_count - success_count}")

    if success_count == total_count:
        logger.info("🎉 所有演示运行成功！")
    else:
        logger.warning("⚠️ 部分演示运行失败，请检查错误信息")

    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

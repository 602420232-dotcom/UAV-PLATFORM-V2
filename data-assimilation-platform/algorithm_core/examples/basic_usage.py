# Type annotations added: 2026-05-08 13:22:43
from typing import Dict, List, Any, Optional, Callable, Tuple

﻿"""
贝叶斯同化基础使用示例
源自: bayesian_assimilation(small).py 和 compatibility.py
"""

import numpy as np
import sys
import os
import logging
import json
from concurrent.futures import ThreadPoolExecutor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def setup_path():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src_path = os.path.join(project_root, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

setup_path()

# 安装说明：在终端执行以下命令
# cd d:\Developer\workplace\py\iteam\trae\data-assimilation-platform\algorithm_core
# pip install -e .

try:
    from bayesian_assimilation.core.assimilator import BayesianAssimilator # type: ignore
    from bayesian_assimilation.utils.config import AssimilationConfig # type: ignore
    from bayesian_assimilation.core.ensemble import EnsembleKalmanFilter # type: ignore
    from bayesian_assimilation.models.four_dimensional_var import FourDimensionalVar # type: ignore
    HAS_ADVANCED_ALGORITHMS = True
except ImportError as e:
    logger.warning(f"高级同化算法模块不可用: {e}")
    from bayesian_assimilation.core.assimilator import BayesianAssimilator  # type: ignore
    from bayesian_assimilation.utils.config import AssimilationConfig  # type: ignore
    HAS_ADVANCED_ALGORITHMS = False

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class EnhancedAssimilationConfig(AssimilationConfig):
    def __post_init__(self):
        """验证配置参数的合理性"""
        super().__post_init__()
        if self.target_resolution <= 0:
            raise ValueError("目标分辨率必须为正数")
        if self.background_error_scale < 0.1 or self.background_error_scale > 10:
            logger.warning("背景误差尺度可能不合理，建议范围[0.1, 10]")
        if self.observation_error_scale < 0.01 or self.observation_error_scale > 5:
            logger.warning("观测误差尺度可能不合理，建议范围[0.01, 5]")


def generate_background_field_chunked(grid_shape: str, domain_size: int):
    """分块生成背景风场，避免大数组一次性加载"""
    nx, ny, nz = grid_shape
    chunk_size = 100  # 每块100x100x100
    
    # 初始化结果数组
    field = np.zeros((nx, ny, nz))
    
    # 分块计算
    for i in range(0, nx, chunk_size):
        for j in range(0, ny, chunk_size):
            for k in range(0, nz, chunk_size):
                # 计算块的边界
                i_end = min(i + chunk_size, nx)
                j_end = min(j + chunk_size, ny)
                k_end = min(k + chunk_size, nz)
                
                # 生成块内的网格
                x_chunk, y_chunk, z_chunk = np.meshgrid(
                    np.linspace(0, domain_size[0], nx)[i:i_end],
                    np.linspace(0, domain_size[1], ny)[j:j_end],
                    np.linspace(0, domain_size[2], nz)[k:k_end],
                    indexing='ij'
                )
                
                # 计算块内的风场
                field_chunk = 5.0 + 2.0 * np.sin(2*np.pi*x_chunk/500) * np.cos(2*np.pi*y_chunk/500)
                field[i:i_end, j:j_end, k:k_end] = np.maximum(field_chunk, 0.1)
    
    return field

def generate_background_field(grid_shape: str, domain_size: int):
    """生成物理合理的背景风场 - 内存优化版本"""
    nx, ny, nz = grid_shape
    
    # 使用内存映射或分块处理，避免大数组一次性加载
    if nx * ny * nz > 10_000_000:  # 1000万点阈值
        logger.warning("网格点数较大，使用分块计算")
        return generate_background_field_chunked(grid_shape, domain_size)
    
    # 原有逻辑
    x, y, z = np.meshgrid(
        np.linspace(0, domain_size[0], nx),
        np.linspace(0, domain_size[1], ny),
        np.linspace(0, domain_size[2], nz),
        indexing='ij'
    )
    field = 5.0 + 2.0 * np.sin(2*np.pi*x/500) * np.cos(2*np.pi*y/500)
    return np.maximum(field, 0.1)  # 最小风速0.1m/s

def validate_observations(observations, locations):
    """验证观测数据的合理性"""
    if np.any(observations < 0):
        raise ValueError("观测风速不能为负值")
    if len(observations) != len(locations):
        raise ValueError("观测值数量与位置数量不匹配")
    return True

def assimilate_with_parallel(assimilator, background, observations, locations):
    """并行化同化计算 - 性能优化版本"""
    # 根据数据大小动态选择线程数
    data_size = background.size
    max_workers = min(4, os.cpu_count() or 1) if data_size > 1_000_000 else 1
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future = executor.submit(
            assimilator.assimilate_3dvar,
            background, observations, locations
        )
        try:
            # 添加超时机制
            return future.result(timeout=300)  # 5分钟超时
        except TimeoutError:
            logger.warning("同化计算超时，使用单线程回退")
            return assimilator.assimilate_3dvar(background, observations, locations)


def adaptive_resolution_assimilation(assimilator: Any, config: Dict[str, Any], min_resolution=5.0: Any):
    """动态分辨率同化，根据计算资源自动调整"""
    original_resolution = config.target_resolution
    
    try:
        # 尝试原始分辨率
        assimilator.initialize_grid(config.domain_size)
        return assimilator.grid_shape
    except MemoryError:
        # 内存不足时自动降低分辨率
        new_resolution = max(original_resolution * 2, min_resolution)
        logger.warning(f"内存不足，自动调整分辨率: {original_resolution}m → {new_resolution}m")
        
        # 创建新的配置
        new_config = EnhancedAssimilationConfig(
            domain_size=config.domain_size,
            target_resolution=new_resolution,
            background_error_scale=config.background_error_scale,
            observation_error_scale=config.observation_error_scale
        )
        assimilator.config = new_config
        assimilator.initialize_grid(config.domain_size)
        return assimilator.grid_shape


def generate_multi_variable_background(grid_shape: str, domain_size: int):
    """生成多变量背景场（风速、温度、湿度）"""
    nx, ny, nz = grid_shape
    x, y, z = np.meshgrid(
        np.linspace(0, domain_size[0], nx),
        np.linspace(0, domain_size[1], ny),
        np.linspace(0, domain_size[2], nz),
        indexing='ij'
    )
    
    # 风速场
    wind_speed = 5.0 + 2.0 * np.sin(2*np.pi*x/500) * np.cos(2*np.pi*y/500)
    wind_speed = np.maximum(wind_speed, 0.1)
    
    # 温度场（随高度降低）
    temperature = 25.0 - 0.0065 * z  # 标准大气温度递减率
    
    # 湿度场（随高度降低）
    humidity = 80.0 * np.exp(-z/500)
    
    return {
        'wind_speed': wind_speed,
        'temperature': temperature,
        'humidity': humidity
    }


def assimilate_with_progress(assimilator, background, observations, locations):
    """带进度显示的同化计算"""
    try:
        from tqdm import tqdm
        has_tqdm = True
    except ImportError:
        has_tqdm = False
    
    if has_tqdm:
        with tqdm(total=100, desc="3DVAR同化进度", unit="%") as pbar:
            # 模拟进度更新
            def progress_callback(progress):
                pbar.update(progress - pbar.n)
            
            # 假设assimilator支持进度回调
            try:
                return assimilator.assimilate_3dvar(
                    background, observations, locations,
                    progress_callback=progress_callback
                )
            except TypeError:
                # 如果assimilator不支持进度回调，回退到普通调用
                pbar.update(100)
                return assimilator.assimilate_3dvar(background, observations, locations)
    else:
        logger.info("安装tqdm可获得进度显示: pip install tqdm")
        return assimilator.assimilate_3dvar(background, observations, locations)


def load_config_from_file(config_path=None):
    """从配置文件加载参数"""
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), 'default_config.json')
    
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        return EnhancedAssimilationConfig(
            domain_size=tuple(config_data.get('domain_size', [1000, 1000, 100])),
            target_resolution=config_data.get('target_resolution', 50.0),
            background_error_scale=config_data.get('background_error_scale', 1.5),
            observation_error_scale=config_data.get('observation_error_scale', 0.8)
        )
    except Exception as e:
        logger.warning(f"配置文件加载失败，使用默认配置: {e}")
        return EnhancedAssimilationConfig(
            domain_size=(1000, 1000, 100),
            target_resolution=50.0,
            background_error_scale=1.5,
            observation_error_scale=0.8
        )


def visualize_results(background, analysis, variance):
    """可视化同化结果"""
    if not HAS_MATPLOTLIB:
        logger.warning("matplotlib 未安装，无法可视化")
        return
    
    # 配置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # 背景场
    im1 = axes[0].imshow(background[:, :, background.shape[2]//2], cmap='viridis', origin='lower')
    axes[0].set_title('背景场')
    plt.colorbar(im1, ax=axes[0], label='风速 (m/s)')
    
    # 分析场
    im2 = axes[1].imshow(analysis[:, :, analysis.shape[2]//2], cmap='viridis', origin='lower')
    axes[1].set_title('分析场')
    plt.colorbar(im2, ax=axes[1], label='风速 (m/s)')
    
    # 方差场
    im3 = axes[2].imshow(variance[:, :, variance.shape[2]//2], cmap='hot', origin='lower')
    axes[2].set_title('方差场')
    plt.colorbar(im3, ax=axes[2], label='方差')
    
    plt.tight_layout()
    plt.savefig('assimilation_results.png')
    logger.info("可视化结果已保存为 assimilation_results.png")

def main():
    logger.info("=" * 60)
    logger.info("贝叶斯同化基础示例")
    logger.info("=" * 6 0)
    
    try:
        # 从配置文件加载配置
        config = load_config_from_file()
        
        # 初始化同化器
        assimilator = BayesianAssimilator(config)
        
        # 动态分辨率适配
        grid_shape = adaptive_resolution_assimilation(assimilator, config)
        nx, ny, nz = grid_shape
        logger.info(f"\n网格: {nx}×{ny}×{nz} = {nx*ny*nz:,} 点")
        
        # 内存使用预估
        estimated_memory_gb = (nx * ny * nz * 8) / (1024 ** 3)  # 8字节/float64
        logger.info(f"预估内存使用: {estimated_memory_gb:.2f} GB")
        
        if estimated_memory_gb > 4.0:  # 4GB阈值
            logger.warning("内存使用较高，考虑分块处理或降低分辨率")
        
        # 生成模拟背景场（风场）
        background = generate_background_field((nx, ny, nz), config.domain_size)
        logger.info(f"背景场范围: [{background.min():.2f}, {background.max():.2f}] m/s")
        
        # 生成多变量背景场（可选）
        multi_var_background = generate_multi_variable_background((nx, ny, nz), config.domain_size)
        logger.info(f"温度场范围: [{multi_var_background['temperature'].min():.2f}, {multi_var_background['temperature'].max():.2f}] °C")
        logger.info(f"湿度场范围: [{multi_var_background['humidity'].min():.2f}, {multi_var_background['humidity'].max():.2f}] %")
        
        # 生成观测（3个气象站）
        observations = np.array([4.5, 5.8, 3.2])
        obs_locations = np.array([
            [250, 250, 50],   # 站点1
            [500, 500, 50],   # 站点2
            [750, 750, 50]    # 站点3
        ])
        
        # 验证观测数据
        validate_observations(observations, obs_locations)
        logger.info(f"\n观测点: {len(observations)} 个")
        logger.info(f"观测值: {observations}")
        
        # 执行同化
        logger.info("\n执行3DVAR同化...")
        try:
            # 尝试带进度显示的并行计算
            analysis, variance = assimilate_with_progress(
                assimilator, background, observations, obs_locations
            )
            
            # 应用物理约束
            if np.any(analysis < 0):
                logger.warning("检测到负风速，应用物理约束修正")
                analysis = np.maximum(analysis, 0.0)
            
            logger.info(f"\n分析场范围: [{analysis.min():.2f}, {analysis.max():.2f}] m/s")
            logger.info(f"方差场范围: [{variance.min():.4f}, {variance.max():.4f}]")
            
            # 降尺度到10米
            logger.info("\n降尺度到10米分辨率...")
            variance_fine = assimilator.interpolate_to_path_grid(target_resolution=10.0)
            logger.info(f"降尺度后形状: {variance_fine.shape}")
            
            # 可视化结果
            visualize_results(background, analysis, variance)
            
        except Exception as e:
            logger.error(f"同化过程失败: {str(e)}")
            # 提供回退方案
            analysis = background.copy()
            variance = np.ones_like(background) * config.background_error_scale
            logger.info("使用背景场作为回退方案")
        
        # 展示高级算法支持
        if HAS_ADVANCED_ALGORITHMS:
            logger.info("\n" + "=" * 60)
        logger.info("高级同化算法支持")
        logger.info("=" * 60)
            logger.info("支持的算法: EnKF, 4DVAR")
        
    except Exception as e:
        logger.error(f"程序运行失败: {str(e)}")
        raise
    
    logger.info("\n" + "=" * 60)
    logger.info("示例完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()


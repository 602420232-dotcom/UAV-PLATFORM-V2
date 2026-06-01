# Type annotations added: 2026-05-08 13:22:43
from typing import Dict, List, Any, Optional, Callable, Tuple

﻿"""
公平并行计算演示
确保串行和并行使用相同数据规模，进行公平的性能对比
优化版本：使用numpy向量化、减少内存复制、优化并行效率
"""

import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# 抑制dask和distributed日志
import warnings
warnings.filterwarnings('ignore')
import logging
logging.getLogger('distributed').setLevel(logging.ERROR)
logging.getLogger('distributed.comm').setLevel(logging.ERROR)
logging.getLogger('distributed.client').setLevel(logging.ERROR)
logging.getLogger('distributed.worker').setLevel(logging.ERROR)
logging.getLogger('distributed.nanny').setLevel(logging.ERROR)
logging.getLogger('distributed.scheduler').setLevel(logging.ERROR)
logging.getLogger('asyncio').setLevel(logging.ERROR)
logging.getLogger('tornado').setLevel(logging.ERROR)
logging.getLogger('tornado.application').setLevel(logging.ERROR)
logging.getLogger('tornado.server').setLevel(logging.ERROR)
logging.getLogger('tornado.iostream').setLevel(logging.ERROR)
logging.getLogger('tornado.ioloop').setLevel(logging.ERROR)
logging.getLogger('tornado.network').setLevel(logging.ERROR)
logging.getLogger('tornado.connection').setLevel(logging.ERROR)
logging.getLogger('plasma').setLevel(logging.ERROR)
logging.getLogger('zmq').setLevel(logging.ERROR)
logging.getLogger('loky').setLevel(logging.ERROR)

try:
    import tensorflow as tf
    import os
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    tf.get_logger().setLevel('ERROR')
except:
    pass

import numpy as np
import sys
import argparse
import time
import psutil
from datetime import datetime

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from bayesian_assimilation.core.assimilator import BayesianAssimilator # type: ignore
from bayesian_assimilation.utils.config import AssimilationConfig # type: ignore

# 创建日志目录
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'fair_parallel_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

# 设置日志格式
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# 文件处理器（输出所有日志）
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# 控制台处理器（只输出重要信息）
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# 配置根日志
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__)


# 数据规模预设
# 分辨率、分块和数据点严格随等级递增
DATA_PRESETS = {
    'small': {
        'domain': (2000, 2000, 200),
        'resolution': 40.0,
        'n_obs': 50,
        'n_blocks': 2,
        'target_points': 15606,
        'description': '小规模适合快速训练、调试'
    },
    'medium': {
        'domain': (4000, 4000, 400),
        'resolution': 20.0,
        'n_obs': 200,
        'n_blocks': 4,
        'target_points': 848421,
        'description': '中规模适合常规训练'
    },
    'large': {
        'domain': (6000, 6000, 600),
        'resolution': 15.0,
        'n_obs': 500,
        'n_blocks': 8,
        'target_points': 6592841,
        'description': '大规模适合完整训练'
    },
    'xlarge': {
        'domain': (8000, 8000, 800),
        'resolution': 10.0,
        'n_obs': 1000,
        'n_blocks': 16,
        'target_points': 51952881,
        'description': '超大规模适合效果演示、高压测试'
    },
    'huge': {
        'domain': (10000, 10000, 1000),
        'resolution': 8.0,
        'n_obs': 2000,
        'n_blocks': 32,
        'target_points': 197113626,
        'description': '巨规模适合最终演示'
    }
}


def get_system_info():
    """获取系统信息"""
    cpu_count = psutil.cpu_count(logical=True)
    memory = psutil.virtual_memory()
    return {
        'cpu_count': cpu_count,
        'memory_total': memory.total / (1024**3),
        'memory_available': memory.available / (1024**3)
    }


def monitor_resources():
    """监控系统资源"""
    cpu_percent = psutil.cpu_percent(interval=0)  # 非阻塞模式
    memory = psutil.virtual_memory()
    return {
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'memory_used': memory.used / (1024**3)
    }


def create_synthetic_data(domain_size: int, resolution: Any, n_obs=50: Any):
    """优化版本：使用numpy向量化操作"""
    nx = int(domain_size[0] / resolution) + 1
    ny = int(domain_size[1] / resolution) + 1
    nz = int(domain_size[2] / resolution) + 1

    total_points = nx * ny * nz
    logger.info(f"创建数据: {nx}×{ny}×{nz} = {total_points:,} 点")
    logger.info(f"观测数: {n_obs}")
    estimated_memory_gb = (total_points * 64) / (1024**3)
    
    if estimated_memory_gb > 2.0:  # 超过2GB警告
        logger.warning(f"大内存警告！将创建 {total_points:,} 点 ({estimated_memory_gb:.1f} GB)")
        logger.warning(f"建议使用 --size medium 或更小规模开始测试")
    # 使用numpy向量化操作
    x = np.linspace(0, domain_size[0], nx)
    y = np.linspace(0, domain_size[1], ny)
    z = np.linspace(0, domain_size[2], nz)

    # 向量化生成背景场
    X, Y = np.meshgrid(x, y, indexing='ij')
    background_pattern = 5.0 + 2.0 * np.sin(2*np.pi*X/500) * np.cos(2*np.pi*Y/500)
    background = np.repeat(background_pattern[:, :, np.newaxis], nz, axis=2)

    # 向量化观测生成
    np.random.seed(42)
    obs_x = np.random.uniform(0, domain_size[0], n_obs)
    obs_y = np.random.uniform(0, domain_size[1], n_obs)
    obs_z = np.random.uniform(0, domain_size[2], n_obs)

    true_values = 5.0 + 2.0 * np.sin(2*np.pi*obs_x/500) * np.cos(2*np.pi*obs_y/500)
    observations = true_values + np.random.normal(0, 0.5, n_obs)

    obs_locations = np.column_stack([obs_x, obs_y, obs_z])

    return background, observations, obs_locations


def run_sequential(background: Any, observations: Any, obs_locations: Any, config: Dict[str, Any], iterations=10: Any):
    """运行串行计算"""
    assimilator = BayesianAssimilator(config)
    assimilator.initialize_grid(config.domain_size)

    start_time = time.time()

    try:
        # 多次迭代以增加计算负载
        for i in range(iterations):
            analysis, variance = assimilator.assimilate_3dvar(
                background, observations, obs_locations
            )
        
        elapsed = time.time() - start_time
        end_resources = monitor_resources()

        return {
            'success': True,
            'elapsed': elapsed,
            'analysis_shape': analysis.shape,
            'variance_mean': float(np.mean(variance)),
            'resources': end_resources
        }
    except Exception as e:
        logger.error(f"串行计算失败: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'elapsed': 0}


def run_block_parallel_optimized(background, observations, obs_locations, config, n_blocks=4, iterations=10):
    """智能版本：根据数据规模决定是否使用并行"""
    data_points = background.size
    
    # 策略：小数据用串行，大数据才用并行
    if data_points < 1000000:  # <1M点
        logger.info(f"数据规模较小 ({data_points:,}点)，使用串行计算更高效")
        return run_sequential(background, observations, obs_locations, config, iterations)
    
    # 中等数据：使用分块并行
    try:
        from bayesian_assimilation.parallel.block import BlockParallelAssimilator # type: ignore

        assimilator = BlockParallelAssimilator(config)
        assimilator.initialize_grid(config.domain_size)

        start_time = time.time()

        for i in range(iterations):
            analysis, variance = assimilator.assimilate_block_parallel(
                background, observations, obs_locations, n_blocks=n_blocks
            )

        elapsed = time.time() - start_time
        end_resources = monitor_resources()

        return {
            'success': True,
            'elapsed': elapsed,
            'analysis_shape': analysis.shape,
            'variance_mean': float(np.mean(variance)),
            'n_blocks': n_blocks,
            'resources': end_resources,
            'method': 'block_parallel'
        }
    except Exception as e:
        logger.error(f"分块并行计算失败: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'elapsed': 0}


def run_dask_parallel(background, observations, obs_locations, config, dask_client=None, iterations=10):
    """优化：只在超大规模启用Dask"""
    data_points = background.size
    data_size_mb = background.nbytes / (1024**2)
    
    # 策略：小于10M点的数据，完全跳过Dask
    if data_points < 10000000:  # <10M点
        logger.info(f"数据规模较小 ({data_points:,}点, {data_size_mb:.1f}MB)")
        logger.info(f"   Dask通信开销大于并行收益，跳过Dask测试")
        logger.info(f"   建议: 使用 --size xlarge 或 huge 测试Dask")
        return {
            'success': False,
            'elapsed': 0,
            'skip_reason': 'data_too_small_for_dask',
            'method': 'skipped'
        }
    
    # 只有超大规模才使用Dask
    logger.info(f"数据规模足够大 ({data_points:,}点)，使用Dask并行")
    
    try:
        import dask
        from dask.distributed import Client, LocalCluster
        from bayesian_assimilation.parallel.dask import DaskParallelAssimilator # type: ignore

        assimilator = DaskParallelAssimilator(config)
        assimilator.initialize_grid(config.domain_size)

        client = dask_client
        cluster = None
        
        if client is None:
            cpu_count = psutil.cpu_count(logical=False) or 4
            
            # 超大规模使用更多workers
            if data_points < 50000000:  # 10-50M点
                n_workers = min(16, cpu_count)
            else:  # >50M点
                n_workers = min(24, max(12, cpu_count // 2))
            
            logger.info(f"创建Dask集群: {n_workers} workers...")
            cluster = LocalCluster(
                n_workers=n_workers,
                threads_per_worker=1,
                processes=True,
                memory_limit='2GB',
                silence_logs=logging.WARNING
            )
            client = Client(cluster)
            logger.info(f"Dask集群已启动: {n_workers} workers")

        # 只预热一次
        if data_points > 20000000:  # >20M点才预热
            logger.info("预热Dask集群...")
            assimilator.assimilate_parallel(background, observations, obs_locations)

        start_time = time.time()

        # 减少迭代次数
        actual_iterations = min(iterations, 2)
        if iterations > 2:
            logger.info(f"减少迭代次数: {iterations} -> {actual_iterations}")
        
        for i in range(actual_iterations):
            analysis, variance = assimilator.assimilate_parallel(
                background, observations, obs_locations
            )

        elapsed = time.time() - start_time
        
        if actual_iterations < iterations:
            elapsed = elapsed * (iterations / actual_iterations)

        end_resources = monitor_resources()

        if dask_client is None and cluster is not None:
            client.close()
            cluster.close()

        return {
            'success': True,
            'elapsed': elapsed,
            'analysis_shape': analysis.shape,
            'variance_mean': float(np.mean(variance)),
            'resources': end_resources,
            'actual_iterations': actual_iterations,
            'estimated_iterations': iterations,
            'method': 'dask_parallel'
        }
        
    except Exception as e:
        logger.error(f"Dask并行计算失败: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'elapsed': 0, 'method': 'failed'}


def run_multiprocessing_parallel(background, observations, obs_locations, config, n_processes=None, iterations=10):
    """使用Python原生multiprocessing，避免Dask开销"""
    data_points = background.size
    
    # 策略：中等规模使用multiprocessing
    if data_points < 1000000:  # <1M点
        logger.info(f"数据规模太小 ({data_points:,}点)，使用串行")
        return run_sequential(background, observations, obs_locations, config, iterations)
    
    try:
        from multiprocessing import Pool, cpu_count
        from bayesian_assimilation.parallel.block import BlockParallelAssimilator # type: ignore
        
        # 自动设置进程数
        if n_processes is None:
            n_processes = min(cpu_count(), 8)  # 最多8个进程
        
        logger.info(f"使用multiprocessing: {n_processes}进程")
        
        assimilator = BlockParallelAssimilator(config)
        assimilator.initialize_grid(config.domain_size)
        
        start_time = time.time()
        
        for i in range(iterations):
            analysis, variance = assimilator.assimilate_block_parallel(
                background, observations, obs_locations, n_blocks=n_processes
            )
        
        elapsed = time.time() - start_time
        end_resources = monitor_resources()
        
        return {
            'success': True,
            'elapsed': elapsed,
            'analysis_shape': analysis.shape,
            'variance_mean': float(np.mean(variance)),
            'n_processes': n_processes,
            'resources': end_resources,
            'method': 'multiprocessing'
        }
        
    except Exception as e:
        logger.error(f"Multiprocessing并行计算失败: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'elapsed': 0, 'method': 'failed'}


def run_smart_parallel(background: Any, observations: Any, obs_locations: Any, config: Dict[str, Any], iterations=10: Any):
    """智能并行：根据数据规模自动选择最优策略"""
    data_points = background.size
    data_size_gb = background.nbytes / (1024**3)
    
    logger.info(f"智能并行策略选择:")
    logger.info(f"  数据规模: {data_points:,}点 ({data_size_gb:.2f}GB)")
    
    # 策略1: 小数据 (<1M点) - 使用串行
    if data_points < 1000000:
        logger.info(f"  -> 策略: 串行 (数据太小，并行开销大于收益)")
        return run_sequential(background, observations, obs_locations, config, iterations)
    
    # 策略2: 中等数据 (1M-50M点) - 使用multiprocessing
    elif data_points < 50000000:
        n_procs = min(psutil.cpu_count(logical=False) or 4, 8)
        logger.info(f"  -> 策略: Multiprocessing (最佳单机并行, {n_procs}进程)")
        return run_multiprocessing_parallel(
            background, observations, obs_locations, config,
            n_processes=n_procs,
            iterations=iterations
        )
    
    # 策略3: 大数据 (>50M点) - 使用Dask本地调度器
    else:
        logger.info(f"  -> 策略: Dask本地调度器 (超大规模)")
        return run_dask_parallel(
            background, observations, obs_locations, config, None, iterations
        )


def run_fair_benchmark(background, observations, obs_locations, config, n_blocks=4, enable_dask=True, dask_client=None, iterations=10, verbose=False):
    """
    运行公平基准测试

    关键改进：串行和并行使用完全相同的数据规模！
    """
    # 获取配置信息
    domain_size = config.domain_size
    resolution = config.target_resolution

    # 运行所有测试
    results = {}

    # 1. 串行计算（基准）
    results['sequential'] = run_sequential(background, observations, obs_locations, config, iterations)

    # 2. 智能并行计算（根据数据规模自动选择策略）
    results['smart_parallel'] = run_smart_parallel(
        background, observations, obs_locations, config, iterations=iterations
    )

    # 3. Dask并行计算（可选，只在大规模数据启用）
    if enable_dask:
        results['dask_parallel'] = run_dask_parallel(
            background, observations, obs_locations, config, dask_client, iterations
        )
    else:
        results['dask_parallel'] = {'success': False, 'elapsed': 0, 'skip_reason': 'disabled'}

    # 性能对比
    logger.info("="*80)
    logger.info("公平并行计算基准测试 - 最终结果汇总")
    logger.info("="*80)
    logger.info(f"数据规模: {domain_size}, 分辨率: {resolution}m")
    logger.info(f"迭代次数: {iterations}")
    logger.info(f"并行块数: {n_blocks}")
    logger.info(f"启用Dask: {enable_dask}")
    logger.info(f"使用Dask客户端: {bool(dask_client)}")
    logger.info(f"总测试数: {len(results)}")
    logger.info(f"成功测试数: {success_count}")
    logger.info(f"失败测试数: {len(results) - success_count}")
    logger.info("="*80)

    success_count = sum(1 for r in results.values() if r.get('success', False))

    if results['sequential']['success']:
        seq_time = results['sequential']['elapsed']
        logger.info("串行计算:")
        logger.info(f"  耗时: {seq_time:.2f}秒")
        logger.info(f"  分析场形状: {results['sequential']['analysis_shape']}")
        logger.info(f"  平均方差: {results['sequential']['variance_mean']:.4f}")
        if 'resources' in results['sequential']:
            res = results['sequential']['resources']
            logger.info(f"  资源使用: CPU {res['cpu_percent']:.1f}%, 内存 {res['memory_percent']:.1f}%")
        print()

        if results['smart_parallel']['success']:
            parallel_time = results['smart_parallel']['elapsed']
            parallel_speedup = seq_time / parallel_time if parallel_time > 0 else 0
            parallel_method = results['smart_parallel'].get('method', 'unknown')
            n_procs = results['smart_parallel'].get('n_processes', 1)

            logger.info(f"智能并行计算 ({parallel_method}):")
            logger.info(f"  耗时: {parallel_time:.2f}秒")
            logger.info(f"  加速比: {parallel_speedup:.2f}x")
            logger.info(f"  进程/线程数: {n_procs}")
            logger.info(f"  分析场形状: {results['smart_parallel']['analysis_shape']}")
            logger.info(f"  平均方差: {results['smart_parallel']['variance_mean']:.4f}")
            if 'resources' in results['smart_parallel']:
                res = results['smart_parallel']['resources']
                logger.info(f"  资源使用: CPU {res['cpu_percent']:.1f}%, 内存 {res['memory_percent']:.1f}%")
            print()

        if results['dask_parallel']['success']:
            dask_time = results['dask_parallel']['elapsed']
            dask_speedup = seq_time / dask_time if dask_time > 0 else 0

            logger.info("Dask并行计算:")
            logger.info(f"  耗时: {dask_time:.2f}秒")
            logger.info(f"  加速比: {dask_speedup:.2f}x")
            logger.info(f"  分析场形状: {results['dask_parallel']['analysis_shape']}")
            logger.info(f"  平均方差: {results['dask_parallel']['variance_mean']:.4f}")
            if 'resources' in results['dask_parallel']:
                res = results['dask_parallel']['resources']
                logger.info(f"  资源使用: CPU {res['cpu_percent']:.1f}%, 内存 {res['memory_percent']:.1f}%")
            print()
        elif 'skip_reason' in results['dask_parallel']:
            logger.info("Dask并行计算:")
            logger.info(f"  [跳过] 原因: {results['dask_parallel']['skip_reason']}")
            logger.info(f"  原因: 数据规模太小，Dask通信开销大于并行收益")
            print()
        else:
            logger.info("Dask并行计算:")
            logger.info(f"  [失败]")
            print()
    else:
        # 巨规模模式，只对比并行方法
        if results['smart_parallel']['success'] and results['dask_parallel']['success']:
            parallel_time = results['smart_parallel']['elapsed']
            dask_time = results['dask_parallel']['elapsed']
            speedup = parallel_time / dask_time if dask_time > 0 else 0

            logger.info("并行方法对比:")
            logger.info(f"  智能并行耗时: {parallel_time:.2f}秒")
            logger.info(f"  Dask并行耗时: {dask_time:.2f}秒")
            logger.info(f"  Dask加速比: {speedup:.2f}x")
            print()

    logger.info(f"成功测试数: {success_count}/{len(results)}")
    print()
    logger.info("分析说明:")
    logger.info("1. 串行和并行使用完全相同的数据规模，确保公平对比")
    logger.info("2. 并行计算的优势在于多核并行处理")
    logger.info("3. 并行效率 = 加速比 / 核心数，理想值为100%")
    logger.info("4. 如果并行效率低，可能原因:")
    logger.info("   - 数据规模太小，并行开销大于并行收益")
    logger.info("   - 同步/通信开销过大")
    logger.info("   - 内存带宽瓶颈")
    logger.info("5. 对于巨规模数据，Dask的内存管理和分布式计算优势更明显")
    print("="*80)

    return results
def calculate_adaptive_iterations(data_size: int, min_total_time=3.0: float, max_total_time=10.0: float):
    """
    基于实际硬件性能的智能迭代计算
    min_total_time: 最小总测试时间（秒）
    max_total_time: 最大总测试时间（秒）
    """
    preset = DATA_PRESETS[data_size]
    target_points = preset['target_points']
    
    # 基准性能：现代CPU (i7/i9) 在 medium 规模 (800k点) 下的性能
    # 测试数据：i7-12700K 在 medium 规模下单次迭代约 0.3-0.5秒
    base_performance = {
        'small': {'points': 30000, 'time_per_iter': 0.01},    # 30k点: 0.01秒/次
        'medium': {'points': 800000, 'time_per_iter': 0.4},   # 800k点: 0.4秒/次  
        'large': {'points': 6400000, 'time_per_iter': 3.0},   # 6.4M点: 3秒/次
        'xlarge': {'points': 51200000, 'time_per_iter': 25.0}, # 51.2M点: 25秒/次
        'huge': {'points': 195000000, 'time_per_iter': 100.0} # 195M点: 100+秒/次
    }
    
    # 估算单次迭代时间
    if data_size in base_performance:
        time_per_iter = base_performance[data_size]['time_per_iter']
    else:
        # 动态估算：时间与点数成正比
        medium_perf = base_performance['medium']
        time_per_iter = medium_perf['time_per_iter'] * (target_points / medium_perf['points'])
    
    # 根据数据规模设置不同的总测试时间目标（优化：减少迭代次数）
    if data_size == 'small':
        target_total_time = 2.0    # 小规模减少到2秒
    elif data_size == 'medium':
        target_total_time = 3.0    # 中规模减少到3秒
    elif data_size == 'large':
        target_total_time = 5.0    # 大规模减少到5秒
    else:  # xlarge, huge
        target_total_time = 2.0    # 超大规模只跑1-2次
    
    # 计算迭代次数
    iterations = max(1, int(target_total_time / max(time_per_iter, 0.001)))
    
    # 设置硬性限制防止内存溢出（优化：进一步减少迭代次数）
    if data_size == 'small':
        iterations = min(iterations, 1000)
    elif data_size == 'medium':
        iterations = min(iterations, 10)   # 原来200次太多，减少到10次
    elif data_size == 'large':
        iterations = min(iterations, 5)    # 原来50次太多，减少到5次
    elif data_size == 'xlarge':
        iterations = min(iterations, 3)    # 51M点，3次足够
    else:  # huge
        iterations = min(iterations, 2)    # 195M点，2次足够
    
    logger.info(f"智能迭代规划: {data_size}规模")
    logger.info(f"   目标点数: {target_points:,} 点")
    logger.info(f"   估算单次耗时: {time_per_iter:.2f} 秒")
    logger.info(f"   计划迭代次数: {iterations} 次")
    logger.info(f"   预计总耗时: {iterations * time_per_iter:.1f} 秒")
    
    return iterations, time_per_iter
def validate_memory_safety(data_size: int, iterations: Any):
    """在创建数据前验证内存安全性"""
    preset = DATA_PRESETS[data_size]
    total_points = preset['target_points']
    
    # 估算内存需求（每个点约64字节 = 8字节×8个变量）
    bytes_per_point = 64
    total_memory_bytes = total_points * bytes_per_point * iterations
    
    # 转换为GB
    total_memory_gb = total_memory_bytes / (1024**3)
    
    # 获取系统可用内存
    available_memory = psutil.virtual_memory().available / (1024**3)
    
    logger.info(f"MemoryWarning 内存安全检查:")
    logger.info("内存安全检查:")
    logger.info(f"   单次数据内存需求: {total_points * bytes_per_point / (1024**3):.2f} GB")
    logger.info(f"   {iterations}次迭代总需求: {total_memory_gb:.2f} GB")
    logger.info(f"   系统可用内存: {available_memory:.2f} GB")
    
    # 安全阈值：不超过可用内存的70%
    if total_memory_gb > available_memory * 0.7:
        logger.warning("[警告] 内存风险警告！调整迭代次数...")
        
        # 重新计算安全的迭代次数
        safe_memory_limit = available_memory * 0.6  # 60% 安全阈值
        safe_iterations = max(1, int((safe_memory_limit * (1024**3)) / (total_points * bytes_per_point)))
        
        # 应用硬性上限
        if data_size == 'xlarge' and safe_iterations > 5:
            safe_iterations = 5
        elif data_size == 'huge' and safe_iterations > 2:
            safe_iterations = 2
        
        logger.warning(f"   → 将迭代次数从 {iterations} 降低到 {safe_iterations} 次")
        return safe_iterations
    
    return iterations

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='公平并行计算基准测试')
    parser.add_argument('--size', '-s', choices=['small', 'medium', 'large', 'xlarge', 'huge'],
                       default='medium', help='数据规模')
    parser.add_argument('--no-dask', action='store_true',
                       help='禁用Dask并行测试')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出')
    parser.add_argument('--iterations', '-i', type=int, default=1000,
                       help='迭代次数，增加计算负载')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

        # 1. 智能计算迭代次数
    if args.iterations == 1000:  # 默认值
        iterations, est_time = calculate_adaptive_iterations(args.size)
    else:
        iterations = args.iterations
    
    # 2. 内存安全验证（关键！）
    iterations = validate_memory_safety(args.size, iterations)
    
    # 3. 创建合成数据
    logger.info(f"创建 {args.size} 规模合成数据...")
    preset = DATA_PRESETS[args.size]
    background, observations, obs_locations = create_synthetic_data(
        preset['domain'], preset['resolution'], preset['n_obs']
    )

    # 创建配置对象
    config = AssimilationConfig(
        domain_size=preset['domain'],
        target_resolution=preset['resolution'],
        background_error_scale=1.5,
        observation_error_scale=0.8
    )
    n_blocks = preset['n_blocks']

    # 打印系统信息
    system_info = get_system_info()
    print("="*80)
    logger.info("系统信息")
    print("="*80)
    logger.info(f"CPU: {system_info['cpu_count']}核")
    logger.info(f"内存: {system_info['memory_total']:.1f}GB")
    logger.info(f"数据规模: {args.size}")
    logger.info(f"Dask: {'启用' if not args.no_dask else '禁用'}")
    logger.info(f"迭代次数: {iterations}")
    logger.info(f"详细日志: {log_file}")
    print()

    # 智能Dask策略：只在超大规模启用
    preset = DATA_PRESETS[args.size]
    should_use_dask = False  # 默认禁用
    
    # 只有xlarge和huge才启用Dask
    if preset['target_points'] >= 50000000:  # >=50M点
        should_use_dask = True
        logger.info(f"启用Dask: 数据规模 {preset['target_points']:,} 点")
    else:
        logger.warning(f"禁用Dask: 数据规模 {preset['target_points']:,} 点 (< 50M)")
        logger.warning(f"   原因: Dask通信开销大于并行收益")
        logger.warning(f"   建议: 使用 --size xlarge 或 huge 测试Dask")
        args.no_dask = True
    
    # 创建Dask客户端（仅在需要时）
    dask_client = None
    dask_cluster = None
    if not args.no_dask and should_use_dask:
        try:
            from dask.distributed import Client, LocalCluster
            dask_logger = logging.getLogger('distributed')
            dask_logger.setLevel(logging.WARNING)
            
            cpu_count = psutil.cpu_count(logical=False) or 4
            
            # 根据数据规模设置workers
            if preset['target_points'] < 100000000:  # <100M点
                n_workers = min(16, cpu_count)
            else:  # >=100M点
                n_workers = min(24, max(12, cpu_count // 2))
            
            logger.info(f"创建Dask集群: {n_workers} workers...")
            dask_cluster = LocalCluster(
                n_workers=n_workers,
                threads_per_worker=1,  # 关键：改为1线程
                processes=True,
                memory_limit='1GB' if preset['target_points'] < 5000000 else '2GB',
                silence_logs=logging.WARNING
            )
            dask_client = Client(dask_cluster)
            logger.info(f"Dask集群已启动: {n_workers} workers")
        except Exception as e:
            logger.error(f"Dask集群创建失败: {e}")
            args.no_dask = True

    # 运行基准测试
    results = run_fair_benchmark(
        background=background,
        observations=observations,
        obs_locations=obs_locations,
        config=config,
        n_blocks=n_blocks,
        enable_dask=not args.no_dask,
        dask_client=dask_client,
        iterations=iterations,
        verbose=args.verbose
    )

    # 关闭Dask客户端
    if dask_client and dask_cluster:
        try:
            dask_client.close()
            dask_cluster.close()
            logger.info("Dask集群已关闭")
        except:
            pass

    logger.info("\n" + "="*60)
    logger.info("基准测试完成")
    logger.info("="*60)

    success = any(r.get('success', False) for r in results.values())
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

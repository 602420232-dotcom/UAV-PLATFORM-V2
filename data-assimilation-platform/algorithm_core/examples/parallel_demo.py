"""
适宜lunix系统计算演示
并行计算演示

演示如何使用分块进行并行贝叶斯同化计算
关键改进：
1. 基于数据规模智能选择并行策略
2. 使用线程并行减少开销
3. 使用共享内存减少数据传输
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import numpy as np
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp
from typing import Dict, Tuple, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from bayesian_assimilation.core.assimilator import BayesianAssimilator # type: ignore
from bayesian_assimilation.utils.config import AssimilationConfig # type: ignore

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_CONFIG = {
    'domain': (5000, 5000, 500),
    'resolution': 5.0,
    'n_obs': 500,
    'n_blocks': 2
}

PARALLEL_THRESHOLDS = {
    'small_to_medium': 100_000_000,
    'medium_to_large': 1_000_000_000,
}


def calculate_data_points(domain_size: int, resolution: Any):
    """计算总数据点数"""
    nx = int(domain_size[0] / resolution) + 1
    ny = int(domain_size[1] / resolution) + 1
    nz = int(domain_size[2] / resolution) + 1
    return nx * ny * nz


def get_parallel_strategy(total_points):
    """根据数据规模选择并行策略"""
    if total_points < PARALLEL_THRESHOLDS['small_to_medium']:
        return 'none', 0
    elif total_points < PARALLEL_THRESHOLDS['medium_to_large']:
        return 'thread', min(mp.cpu_count(), 8)
    else:
        return 'process', min(mp.cpu_count(), 16)


def create_data(domain_size: int, resolution: Any, n_obs=30: Any):
    """创建合成数据"""
    nx = int(domain_size[0] / resolution) + 1
    ny = int(domain_size[1] / resolution) + 1
    nz = int(domain_size[2] / resolution) + 1

    total_points = nx * ny * nz
    logger.info(f"创建数据: {nx}x{ny}x{nz} = {total_points:,} 点")
    logger.info(f"观测数: {n_obs}")

    x, y, _ = np.meshgrid(
        np.linspace(0, domain_size[0], nx),
        np.linspace(0, domain_size[1], ny),
        np.linspace(0, domain_size[2], nz),
        indexing='ij'
    )

    background = 5.0 + 2.0 * np.sin(2*np.pi*x/500) * np.cos(2*np.pi*y/500)

    np.random.seed(42)
    observations = []
    obs_locations = []

    for _ in range(n_obs):
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


def assimilate_block_thread(background, observations, obs_locations, block_info, scale_factors):
    """线程并行：处理单个数据块"""
    block_id, nx_start, nx_end, ny_start, ny_end, nz_start, nz_end = block_info
    scale_x, scale_y, scale_z = scale_factors

    nx = nx_end - nx_start
    ny = ny_end - ny_start
    nz = nz_end - nz_start

    block_bg = background[nx_start:nx_end, ny_start:ny_end, nz_start:nz_end]

    block_obs_mask = (
        (obs_locations[:, 0] >= nx_start * scale_x) &
        (obs_locations[:, 0] < nx_end * scale_x) &
        (obs_locations[:, 1] >= ny_start * scale_y) &
        (obs_locations[:, 1] < ny_end * scale_y) &
        (obs_locations[:, 2] >= nz_start * scale_z) &
        (obs_locations[:, 2] < nz_end * scale_z)
    )

    block_obs = observations[block_obs_mask]
    block_obs_loc = obs_locations[block_obs_mask]

    if len(block_obs) == 0:
        return block_id, block_bg.copy(), np.ones_like(block_bg) * 1.5

    block_obs_loc_scaled = block_obs_loc.copy()
    block_obs_loc_scaled[:, 0] = (block_obs_loc[:, 0] / scale_x) - nx_start
    block_obs_loc_scaled[:, 1] = (block_obs_loc[:, 1] / scale_y) - ny_start
    block_obs_loc_scaled[:, 2] = (block_obs_loc[:, 2] / scale_z) - nz_start

    xb = block_bg.flatten()
    n_obs = len(block_obs)
    n_total = nx * ny * nz

    ix = np.clip((block_obs_loc_scaled[:, 0]).astype(np.int32), 0, nx - 1)
    iy = np.clip((block_obs_loc_scaled[:, 1]).astype(np.int32), 0, ny - 1)
    iz = np.clip((block_obs_loc_scaled[:, 2]).astype(np.int32), 0, nz - 1)

    idx = ix * ny * nz + iy * nz + iz

    obs_err = np.ones(n_obs) * 0.8
    R_diag = obs_err ** 2 + 1e-6
    R_inv = 1.0 / R_diag

    B_diag = np.ones(n_total) * (1.5 ** 2)
    B_inv_diag = 1.0 / (B_diag + 1e-6)

    y = block_obs

    H_T_R_inv_y = np.zeros(n_total)
    H_T_R_inv_y[idx] += R_inv * y

    H_T_R_inv_H_diag = np.zeros(n_total)
    H_T_R_inv_H_diag[idx] += R_inv

    rhs = B_inv_diag * xb + H_T_R_inv_y
    A_diag = B_inv_diag + H_T_R_inv_H_diag

    xa = rhs / A_diag
    variance = 1.0 / (A_diag + 1e-6)

    return block_id, xa.reshape((nx, ny, nz)), variance.reshape((nx, ny, nz))


def run_thread_parallel(background, observations, obs_locations, n_blocks=2):
    """使用共享内存的线程并行计算"""
    nx, ny, nz = background.shape

    resolution_x = DATA_CONFIG['domain'][0] / (nx - 1)
    resolution_y = DATA_CONFIG['domain'][1] / (ny - 1)
    resolution_z = DATA_CONFIG['domain'][2] / (nz - 1)
    scale_factors = (resolution_x, resolution_y, resolution_z)

    block_configs = []
    nx_per_block = nx // n_blocks

    for i in range(n_blocks):
        nx_start = i * nx_per_block
        nx_end = nx if i == n_blocks - 1 else (i + 1) * nx_per_block
        block_configs.append((i, nx_start, nx_end, 0, ny, 0, nz))

    results: Dict[int, Tuple[np.ndarray, np.ndarray]] = {}

    with ThreadPoolExecutor(max_workers=n_blocks) as executor:
        futures = {
            executor.submit(assimilate_block_thread, background, observations, obs_locations, cfg, scale_factors): cfg[0]
            for cfg in block_configs
        }

        for future in futures:
            block_id, block_analysis, block_variance = future.result()
            results[block_id] = (block_analysis, block_variance)

    analysis = np.zeros_like(background)
    variance = np.zeros_like(background)

    for i, cfg in enumerate(block_configs):
        _, nx_start, nx_end, ny_start, ny_end, nz_start, nz_end = cfg
        block_result = results[i]
        analysis[nx_start:nx_end, ny_start:ny_end, nz_start:nz_end] = block_result[0]
        variance[nx_start:nx_end, ny_start:ny_end, nz_start:nz_end] = block_result[1]

    return analysis, variance


def demo_sequential():
    """串行计算基准测试"""
    logger.info("="*60)
    logger.info("串行计算基准测试 ( Sequential Baseline )")
    logger.info("="*60)
    logger.info(f"数据规模: {DATA_CONFIG['domain']}, 分辨率: {DATA_CONFIG['resolution']}m")

    total_points = calculate_data_points(DATA_CONFIG['domain'], DATA_CONFIG['resolution'])
    strategy, _ = get_parallel_strategy(total_points)

    logger.info(f"总数据点: {total_points:,}")
    logger.info(f"推荐并行策略: {strategy}")

    config = AssimilationConfig(
        domain_size=DATA_CONFIG['domain'],
        target_resolution=DATA_CONFIG['resolution'],
        background_error_scale=1.5,
        observation_error_scale=0.8
    )

    assimilator = BayesianAssimilator(config)
    assimilator.initialize_grid(DATA_CONFIG['domain'])

    background, observations, obs_locations = create_data(
        DATA_CONFIG['domain'],
        DATA_CONFIG['resolution'],
        n_obs=DATA_CONFIG['n_obs']
    )

    start_time = time.time()

    try:
        analysis, variance = assimilator.assimilate_3dvar(
            background, observations, obs_locations
        )
        elapsed = time.time() - start_time

        logger.info(f"串行计算完成")
        logger.info(f"   耗时: {elapsed:.2f}秒")
        logger.info(f"   分析场形状: {analysis.shape}")
        logger.info(f"   平均方差: {np.mean(variance):.4f}")

        return {
            'success': True,
            'elapsed': elapsed,
            'analysis_shape': analysis.shape,
            'variance_mean': float(np.mean(variance)),
            'total_points': total_points
        }
    except Exception as e:
        logger.error(f"串行计算失败: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'elapsed': 0}


def demo_thread_parallel():
    """线程并行计算测试"""
    logger.info("\n" + "="*60)
    logger.info(f"线程并行计算测试 ( Thread Parallel )")
    logger.info("="*60)
    logger.info(f"数据规模: {DATA_CONFIG['domain']}, 分辨率: {DATA_CONFIG['resolution']}m")

    total_points = calculate_data_points(DATA_CONFIG['domain'], DATA_CONFIG['resolution'])
    strategy, _ = get_parallel_strategy(total_points)

    if strategy == 'none':
        logger.info(f"数据规模 ({total_points:,}点) 较小，不使用并行")
        return {'success': False, 'elapsed': 0, 'reason': 'data_too_small'}

    logger.info(f"总数据点: {total_points:,}")
    logger.info(f"并行策略: {strategy}")

    config = AssimilationConfig(
        domain_size=DATA_CONFIG['domain'],
        target_resolution=DATA_CONFIG['resolution'],
        background_error_scale=1.5,
        observation_error_scale=0.8
    )

    assimilator = BayesianAssimilator(config)
    assimilator.initialize_grid(DATA_CONFIG['domain'])

    background, observations, obs_locations = create_data(
        DATA_CONFIG['domain'],
        DATA_CONFIG['resolution'],
        n_obs=DATA_CONFIG['n_obs']
    )

    start_time = time.time()

    try:
        analysis, variance = run_thread_parallel(
            background, observations, obs_locations,
            n_blocks=DATA_CONFIG['n_blocks']
        )
        elapsed = time.time() - start_time

        logger.info(f"线程并行计算完成")
        logger.info(f"   耗时: {elapsed:.2f}秒")
        logger.info(f"   分析场形状: {analysis.shape}")
        logger.info(f"   平均方差: {np.mean(variance):.4f}")

        return {
            'success': True,
            'elapsed': elapsed,
            'analysis_shape': analysis.shape,
            'variance_mean': float(np.mean(variance)),
            'n_blocks': DATA_CONFIG['n_blocks'],
            'total_points': total_points
        }
    except Exception as e:
        logger.error(f"线程并行计算失败: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'elapsed': 0}


def main():
    """主函数"""
    logger.info("="*60)
    logger.info("并行计算贝叶斯同化演示")
    logger.info("="*60)
    logger.info(f"数据规模: {DATA_CONFIG['domain']}")
    logger.info(f"分辨率: {DATA_CONFIG['resolution']}m")
    logger.info(f"观测数: {DATA_CONFIG['n_obs']}")
    logger.info(f"分块数: {DATA_CONFIG['n_blocks']}")

    total_points = calculate_data_points(DATA_CONFIG['domain'], DATA_CONFIG['resolution'])
    strategy, n_workers = get_parallel_strategy(total_points)

    logger.info(f"\n总数据点: {total_points:,} ({total_points/1e6:.1f}M)")
    logger.info(f"推荐并行策略: {strategy} ({n_workers} workers)")
    logger.info("\n并行策略说明:")
    logger.info("  - 小数据 (<100M点): 不使用并行 (开销大于收益)")
    logger.info("  - 中数据 (100M-1B点): 使用线程并行 (减少开销)")
    logger.info("  - 大数据 (>1B点): 使用进程并行 (充分利用多核)")

    results = {}

    results['sequential'] = demo_sequential()

    if strategy != 'none':
        results['thread_parallel'] = demo_thread_parallel()

    logger.info("\n" + "="*60)
    logger.info("性能对比")
    logger.info("="*60)

    success_count = sum(1 for r in results.values() if r.get('success', False))

    if results['sequential']['success']:
        seq_time = results['sequential']['elapsed']
        logger.info(f"\n串行计算:")
        logger.info(f"   耗时: {seq_time:.2f}秒")
        logger.info(f"   基准时间")

        if results.get('thread_parallel', {}).get('success'):
            thread_time = results['thread_parallel']['elapsed']
            thread_speedup = seq_time / thread_time if thread_time > 0 else 0
            thread_efficiency = thread_speedup / results['thread_parallel'].get('n_blocks', 1) * 100

            logger.info(f"\n线程并行计算:")
            logger.info(f"   耗时: {thread_time:.2f}秒")
            logger.info(f"   加速比: {thread_speedup:.2f}x")
            logger.info(f"   并行效率: {thread_efficiency:.1f}%")
            logger.info(f"   (使用 {results['thread_parallel'].get('n_blocks', 1)} 个块)")

            if thread_speedup > 1:
                logger.info(f"   并行加速成功!")
            else:
                logger.info(f"   并行未达到加速效果")

    logger.info(f"\n成功测试数: {success_count}/{len(results)}")

    logger.info("\n" + "="*60)
    if success_count == len(results):
        logger.info("所有测试通过!")
    elif success_count > 0:
        logger.info("部分测试通过")
    else:
        logger.info("所有测试失败")

    logger.info("="*60)
    logger.info("演示完成")
    logger.info("="*60)

    return success_count > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

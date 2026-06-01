# Type annotations added: 2026-05-08 13:22:43
from typing import Dict, List, Any, Optional, Callable, Tuple

"""
CUDA加速示例
演示如何使用NVIDIA CUDA进行GPU加速计算
"""

import numpy as np
import logging
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
# 安装CUDA依赖：
# pip install cupy-cuda11x  # 或：
# pip install pycuda
# pip install numba cuda-python

from bayesian_assimilation.core.assimilator import BayesianAssimilator # type: ignore
from bayesian_assimilation.utils.config import AssimilationConfig # type: ignore
from bayesian_assimilation.accelerators import CUDAAccelerator, CuPyAccelerator, PyCUDAccelerator # type: ignore

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_cuda_available():
    """检查CUDA是否可用"""
    try:
        cuda_acc = CUDAAccelerator()
        if cuda_acc.initialize():
            logger.info("✅ CUDA可用")
            return True
        else:
            logger.info("⚠️ CUDA不可用")
            return False
    except ImportError:
        logger.info("⚠️ CUDA相关库未安装")
        return False


def create_synthetic_data(domain_size: int, resolution: Any, n_obs=20: Any):
    """创建合成数据"""
    nx = int(domain_size[0] / resolution) + 1
    ny = int(domain_size[1] / resolution) + 1
    nz = int(domain_size[2] / resolution) + 1

    logger.info(f"创建数据: {nx}×{ny}×{nz} = {nx*ny*nz:,} 点")
    logger.info(f"观测数: {n_obs}")

    x, y, z = np.meshgrid(
        np.linspace(0, domain_size[0], nx),
        np.linspace(0, domain_size[1], ny),
        np.linspace(0, domain_size[2], nz),
        indexing='ij'
    )

    background = 5.0 + 2.0 * np.sin(2*np.pi*x/500) * np.cos(2*np.pi*y/500)

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


def demo_cpu_baseline():
    """CPU基准测试"""
    logger.info("="*60)
    logger.info("CPU基准测试")
    logger.info("="*60)

    # 进一步增加数据规模：提高分辨率到5.0，网格点约501x501x51 = 12,825,751点
    config = AssimilationConfig(
        domain_size=(2500, 2500, 250),
        target_resolution=5.0,  # 从10.0改为5.0
        background_error_scale=1.5,
        observation_error_scale=0.8
    )

    assimilator = BayesianAssimilator(config)
    assimilator.initialize_grid((2500, 2500, 250))

    # 增加观测数量
    background, observations, obs_locations = create_synthetic_data(
        (2500, 2500, 250), 5.0, n_obs=500  # 从200增加到500
    )

    import time
    start_time = time.time()

    try:
        analysis, variance = assimilator.assimilate_3dvar(
            background, observations, obs_locations
        )
        elapsed = time.time() - start_time

        logger.info(f"✅ CPU计算完成，耗时: {elapsed:.2f}秒")
        logger.info(f"分析场形状: {analysis.shape}")
        logger.info(f"平均方差: {np.mean(variance):.4f}")

        return {
            'success': True,
            'elapsed': elapsed,
            'analysis_shape': analysis.shape
        }
    except Exception as e:
        logger.error(f"❌ CPU计算失败: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'elapsed': 0}


def demo_cuda_accelerated():
    """CUDA加速测试"""
    logger.info("\n" + "="*60)
    logger.info("CUDA加速测试")
    logger.info("="*60)

    if not check_cuda_available():
        logger.info("⚠️ 跳过CUDA测试")
        return {'success': False, 'elapsed': 0}

    try:
        cuda_acc = CUDAAccelerator()
        if not cuda_acc.initialize():
            logger.error("❌ CUDA加速器初始化失败")
            return {'success': False, 'elapsed': 0}

        # JIT编译预热
        cuda_acc.warmup()

        device_info = cuda_acc.get_device_info()
        logger.info(f"CUDA后端: {device_info.get('backend', 'unknown')}")
        logger.info(f"CUDA设备: {device_info.get('device_name', 'unknown')}")

        # 进一步增加数据规模：提高分辨率到5.0，网格点约501x501x51 = 12,825,751点
        config = AssimilationConfig(
            domain_size=(2500, 2500, 250),
            target_resolution=5.0,  # 从10.0改为5.0
            background_error_scale=1.5,
            observation_error_scale=0.8
        )

        assimilator = BayesianAssimilator(config)
        assimilator.initialize_grid((2500, 2500, 250))

        # 增加观测数量
        background, observations, obs_locations = create_synthetic_data(
            (2500, 2500, 250), 5.0, n_obs=500  # 从200增加到500
        )

        # 转移数据到GPU
        background_gpu = cuda_acc.to_device(background)
        observations_gpu = cuda_acc.to_device(observations)
        obs_locations_gpu = cuda_acc.to_device(obs_locations)

        # 测试矩阵乘法性能
        test_matrix = np.random.rand(1000, 1000)
        test_matrix_gpu = cuda_acc.to_device(test_matrix)

        import time
        start_time = time.time()
        result_gpu = cuda_acc.matmul(test_matrix_gpu, test_matrix_gpu)
        cuda_time = time.time() - start_time
        logger.info(f"CUDA矩阵乘法: {cuda_time:.4f}秒")

        start_time = time.time()
        result_cpu = np.dot(test_matrix, test_matrix)
        cpu_time = time.time() - start_time
        logger.info(f"CPU矩阵乘法: {cpu_time:.4f}秒")
        logger.info(f"矩阵乘法加速比: {cpu_time/cuda_time:.2f}x")

        # 测试3DVAR同化
        start_time = time.time()

        # 使用GPU版本的3DVAR同化
        if device_info.get('backend') == 'cupy':
            import cupy as cp
            
            def cuda_assimilate_3dvar(bg, obs, obs_loc):
                """CuPy版本的3DVAR同化"""
                nx, ny, nz = bg.shape
                n_total = nx * ny * nz

                xb = bg.flatten()
                n_obs = len(obs)

                # 计算每个观测点的网格索引
                ix = cp.clip((obs_loc[:, 0] / 5.0).astype(cp.int32), 0, nx - 1)
                iy = cp.clip((obs_loc[:, 1] / 5.0).astype(cp.int32), 0, ny - 1)
                iz = cp.clip((obs_loc[:, 2] / 5.0).astype(cp.int32), 0, nz - 1)
                
                # 计算扁平化索引
                idx = ix * ny * nz + iy * nz + iz
                
                # 观测误差和背景误差
                obs_err = cp.ones(n_obs) * 0.8
                R_diag = obs_err ** 2 + 1e-6
                R_inv = 1.0 / R_diag

                B_diag = cp.ones(n_total) * (1.5 ** 2)
                B_inv_diag = 1.0 / (B_diag + 1e-6)

                y = obs
                
                # 计算H^T @ (R_inv * y) - 使用向量化操作
                H_T_R_inv_y = cp.zeros(n_total)
                H_T_R_inv_y[idx] += R_inv * y
                
                # 计算H^T @ R_inv @ H的对角线 - 使用向量化操作
                H_T_R_inv_H_diag = cp.zeros(n_total)
                H_T_R_inv_H_diag[idx] += R_inv
                
                # 计算右侧和矩阵A的对角线
                rhs = B_inv_diag * xb + H_T_R_inv_y
                A_diag = B_inv_diag + H_T_R_inv_H_diag

                xa = rhs / A_diag
                variance = 1.0 / (A_diag + 1e-6)

                return xa.reshape((nx, ny, nz)), variance.reshape((nx, ny, nz))
            
            # 执行GPU计算
            analysis_gpu, variance_gpu = cuda_assimilate_3dvar(
                background_gpu, observations_gpu, obs_locations_gpu
            )
            
            # 转移结果回CPU
            analysis = cuda_acc.to_host(analysis_gpu)
            variance = cuda_acc.to_host(variance_gpu)
        else:
            # 回退到CPU计算
            analysis, variance = assimilator.assimilate_3dvar(
                background, observations, obs_locations
            )

        elapsed = time.time() - start_time

        logger.info(f"✅ CUDA计算完成，耗时: {elapsed:.2f}秒")
        logger.info(f"分析场形状: {analysis.shape}")
        logger.info(f"平均方差: {np.mean(variance):.4f}")

        cuda_acc.finalize()

        return {
            'success': True,
            'elapsed': elapsed,
            'analysis_shape': analysis.shape,
            'backend': device_info.get('backend', 'unknown')
        }

    except ImportError as e:
        logger.error(f"❌ 导入失败: {e}")
        logger.info("请安装必要的CUDA依赖: pip install cupy-cuda11x")
        return {'success': False, 'elapsed': 0}
    except Exception as e:
        logger.error(f"❌ CUDA计算失败: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'elapsed': 0}


def main():
    """主函数"""
    logger.info("="*60)
    logger.info("CUDA加速贝叶斯同化演示")
    logger.info("="*60)

    results = {}

    results['cpu_baseline'] = demo_cpu_baseline()
    results['cuda_accelerated'] = demo_cuda_accelerated()

    logger.info("\n" + "="*60)
    logger.info("性能对比")
    logger.info("="*60)

    if results['cpu_baseline']['success']:
        cpu_time = results['cpu_baseline']['elapsed']
        logger.info(f"CPU耗时: {cpu_time:.2f}秒")

        if results['cuda_accelerated']['success']:
            cuda_time = results['cuda_accelerated']['elapsed']
            backend = results['cuda_accelerated'].get('backend', 'unknown')
            speedup = cpu_time / cuda_time if cuda_time > 0 else 0

            logger.info(f"CUDA耗时: {cuda_time:.2f}秒 (后端: {backend})")
            logger.info(f"加速比: {speedup:.2f}x")

            if speedup > 1:
                logger.info("🎉 CUDA加速成功！")
            elif speedup < 1:
                logger.info("⚠️ CUDA未达到加速效果（可能数据规模不够大）")
        else:
            logger.info("⚠️ CUDA测试失败，无法进行性能对比")
    else:
        logger.info("⚠️ CPU基准测试失败")

    logger.info("\n" + "="*60)
    logger.info("演示完成")
    logger.info("="*60)

    return results['cpu_baseline'].get('success', False)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

# Type annotations added: 2026-05-08 13:22:43
from typing import Dict, List, Any, Optional, Callable, Tuple

"""
GPU/JAX/CUDA加速示例
演示如何使用GPU/JAX/CUDA加速贝叶斯同化计算
优先使用JAX（支持CPU/GPU/TPU），如果JAX不可用则回退到CUDA+GPU
"""

import numpy as np
import logging
import sys
import os

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


def check_jax_available():
    """检查JAX是否可用"""
    try:
        import jax
        import jax.numpy as jnp
        return True
    except ImportError:
        logger.info("⚠️ JAX未安装")
        return False


def check_cuda_available():
    """检查CUDA是否可用"""
    try:
        from bayesian_assimilation.accelerators.cuda import CUDAAccelerator # type: ignore
        cuda_accel = CUDAAccelerator()
        if cuda_accel.initialize():
            info = cuda_accel.get_device_info()
            if info.get('cuda_available'):
                logger.info(f"✅ CUDA可用: {info.get('backend', 'unknown')}")
                return cuda_accel
        cuda_accel.finalize()
        return None
    except ImportError:
        logger.info("⚠️ CUDA加速器模块未安装")
        return None
    except Exception as e:
        logger.info(f"⚠️ CUDA不可用: {e}")
        return None


def create_synthetic_data(domain_size: int, resolution: Any, n_obs=50: Any):
    """创建合成数据（规模适中，在5000-20000点之间）"""
    nx = int(domain_size[0] / resolution) + 1
    ny = int(domain_size[1] / resolution) + 1
    nz = int(domain_size[2] / resolution) + 1

    total_points = nx * ny * nz
    logger.info(f"创建数据: {nx}×{ny}×{nz} = {total_points:,} 点")
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

    # 增加数据规模：提高分辨率到10.0，网格点约251x251x26 = 1,638,806点
    config = AssimilationConfig(
        domain_size=(2500, 2500, 250),
        target_resolution=10.0,  # 改回10.0m分辨率
        background_error_scale=1.5,
        observation_error_scale=0.8
    )

    assimilator = BayesianAssimilator(config)
    assimilator.initialize_grid((2500, 2500, 250))

    # 增加观测数量
    background, observations, obs_locations = create_synthetic_data(
        (2500, 2500, 250), 10.0, n_obs=500  # 从200增加到500
    )

    import time
    # 执行多次迭代来分摊开销
    n_iterations = 5
    logger.info(f"执行 {n_iterations} 次迭代来分摊开销")
    
    # 预热
    logger.info("预热中...")
    assimilator.assimilate_3dvar(background, observations, obs_locations)
    
    # 正式计时
    start_time = time.perf_counter()  # 使用更精确的计时器

    try:
        for i in range(n_iterations):
            analysis, variance = assimilator.assimilate_3dvar(
                background, observations, obs_locations
            )
        elapsed = time.perf_counter() - start_time  # 使用更精确的计时器
        avg_elapsed = elapsed / n_iterations

        logger.info(f"✅ CPU计算完成，总耗时: {elapsed:.2f}秒")
        logger.info(f"平均每次耗时: {avg_elapsed:.2f}秒")
        logger.info(f"分析场形状: {analysis.shape}")
        logger.info(f"网格点数量: {analysis.size:,}点")
        logger.info(f"平均方差: {np.mean(variance):.4f}")

        return {
            'success': True,
            'elapsed': avg_elapsed,  # 返回平均时间
            'analysis_shape': analysis.shape
        }
    except Exception as e:
        logger.error(f"❌ CPU计算失败: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'elapsed': 0}


def demo_jax_accelerated():
    """JAX加速测试（支持CPU/GPU/TPU）"""
    logger.info("\n" + "="*60)
    logger.info("JAX加速测试")
    logger.info("="*60)

    if not check_jax_available():
        logger.info("⚠️ 跳过JAX测试")
        return {'success': False, 'elapsed': 0, 'platform': 'none'}

    try:
        import jax
        import jax.numpy as jnp
        from jax import jit
        from bayesian_assimilation.accelerators.jax import JAXAccelerator # type: ignore

        accelerator = JAXAccelerator()
        if not accelerator.initialize():
            logger.error("❌ JAX加速器初始化失败")
            return {'success': False, 'elapsed': 0, 'platform': 'none'}

        platform = accelerator._backend
        logger.info(f"JAX平台: {platform}")
        logger.info(f"JAX设备数: {accelerator._device_count}")

        # 增加数据规模：提高分辨率到10.0
        config = AssimilationConfig(
            domain_size=(2500, 2500, 250),
            target_resolution=10.0,  # 改回10.0m分辨率
            background_error_scale=1.5,
            observation_error_scale=0.8
        )

        assimilator = BayesianAssimilator(config)
        assimilator.initialize_grid((2500, 2500, 250))

        # 增加观测数量
        background, observations, obs_locations = create_synthetic_data(
            (2500, 2500, 250), 10.0, n_obs=500  # 从200增加到500
        )

        background_jax = accelerator.to_device(background)
        observations_jax = accelerator.to_device(observations)
        obs_locations_jax = accelerator.to_device(obs_locations)

        @jit
        def jax_assimilate_3dvar(bg, obs, obs_loc):
            """JAX版本的3DVAR同化（使用向量化操作，支持JIT）"""
            nx, ny, nz = bg.shape
            n_total = nx * ny * nz

            xb = bg.flatten()

            n_obs = len(obs)

            # 使用向量化操作代替Python循环
            # 计算每个观测点的网格索引
            ix = jnp.clip(jnp.int32(obs_loc[:, 0] / 10.0), 0, nx - 1)
            iy = jnp.clip(jnp.int32(obs_loc[:, 1] / 10.0), 0, ny - 1)
            iz = jnp.clip(jnp.int32(obs_loc[:, 2] / 10.0), 0, nz - 1)
            
            # 计算扁平化索引
            idx = ix * ny * nz + iy * nz + iz
            
            # 观测误差和背景误差
            obs_err = jnp.ones(n_obs) * 0.8
            R_diag = obs_err ** 2 + 1e-6
            R_inv = 1.0 / R_diag

            B_diag = jnp.ones(n_total) * (1.5 ** 2)
            B_inv_diag = 1.0 / (B_diag + 1e-6)

            y = obs
            
            # 计算H^T @ (R_inv * y) - 使用向量化操作
            H_T_R_inv_y = jnp.zeros(n_total)
            H_T_R_inv_y = H_T_R_inv_y.at[idx].add(R_inv * y)
            
            # 计算H^T @ R_inv @ H的对角线 - 使用向量化操作
            H_T_R_inv_H_diag = jnp.zeros(n_total)
            H_T_R_inv_H_diag = H_T_R_inv_H_diag.at[idx].add(R_inv)
            
            # 计算右侧和矩阵A的对角线
            rhs = B_inv_diag * xb + H_T_R_inv_y
            A_diag = B_inv_diag + H_T_R_inv_H_diag

            xa = rhs / A_diag

            variance = 1.0 / (A_diag + 1e-6)

            return xa.reshape((nx, ny, nz)), variance.reshape((nx, ny, nz))

        import time
        # 执行多次迭代来分摊开销
        n_iterations = 5
        logger.info(f"执行 {n_iterations} 次迭代来分摊开销")
        
        # JIT 预热
        logger.info("JIT 编译预热中...")
        for _ in range(2):
            jax_assimilate_3dvar(background_jax, observations_jax, obs_locations_jax)
        
        # 正式计时
        start_time = time.perf_counter()  # 使用更精确的计时器

        for i in range(n_iterations):
            analysis, variance = jax_assimilate_3dvar(
                background_jax, observations_jax, obs_locations_jax
            )
            # 确保计算完成（JAX是异步的）
            analysis.block_until_ready()
            variance.block_until_ready()

        elapsed = time.perf_counter() - start_time  # 使用更精确的计时器
        avg_elapsed = elapsed / n_iterations

        analysis = np.array(analysis)
        variance = np.array(variance)

        logger.info(f"✅ JAX计算完成，总耗时: {elapsed:.2f}秒")
        logger.info(f"平均每次耗时: {avg_elapsed:.2f}秒")
        logger.info(f"分析场形状: {analysis.shape}")
        logger.info(f"网格点数量: {analysis.size:,}点")
        logger.info(f"平均方差: {np.mean(variance):.4f}")

        return {
            'success': True,
            'elapsed': avg_elapsed,  # 返回平均时间
            'analysis_shape': analysis.shape,
            'platform': platform
        }

    except ImportError as e:
        logger.error(f"❌ 导入失败: {e}")
        logger.info("请安装必要的JAX依赖: pip install jax jaxlib")
        return {'success': False, 'elapsed': 0, 'platform': 'none'}
    except Exception as e:
        logger.error(f"❌ JAX计算失败: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'elapsed': 0, 'platform': 'none'}


def demo_cuda_accelerated(cuda_accel=None):
    """CUDA加速测试（使用CuPy/PyCUDA/Numba CUDA）"""
    logger.info("\n" + "="*60)
    logger.info("CUDA加速测试")
    logger.info("="*60)

    if cuda_accel is None:
        cuda_accel = check_cuda_available()

    if cuda_accel is None or not cuda_accel.check_cuda_available():
        logger.info("⚠️ CUDA不可用，跳过CUDA测试")
        if cuda_accel:
            cuda_accel.finalize()
        return {'success': False, 'elapsed': 0, 'backend': 'none'}

    try:
        logger.info("开始CUDA加速测试...")
        backend = cuda_accel.get_device_info().get('backend', 'unknown')
        logger.info(f"CUDA后端: {backend}")

        cuda_accel.warmup()

        # 增加数据规模：提高分辨率到10.0
        config = AssimilationConfig(
            domain_size=(2500, 2500, 250),
            target_resolution=10.0,  # 改回10.0m分辨率
            background_error_scale=1.5,
            observation_error_scale=0.8
        )

        assimilator = BayesianAssimilator(config)
        assimilator.initialize_grid((2500, 2500, 250))

        # 增加观测数量
        background, observations, obs_locations = create_synthetic_data(
            (2500, 2500, 250), 10.0, n_obs=500  # 从200增加到500
        )

        background_dev = cuda_accel.to_device(background)
        observations_dev = cuda_accel.to_device(observations)
        obs_locations_dev = cuda_accel.to_device(obs_locations)

        if backend == 'cupy':
            import cupy as cp

            def cuda_assimilate_3dvar(bg, obs, obs_loc):
                """CuPy版本的3DVAR同化（使用向量化操作）"""
                nx, ny, nz = bg.shape
                n_total = nx * ny * nz

                xb = bg.flatten()

                n_obs = len(obs)

                # 使用向量化操作代替Python循环
                # 计算每个观测点的网格索引
                # 确保所有操作都使用CuPy函数
                ix = cp.clip((obs_loc[:, 0] / 10.0).astype(cp.int32), 0, nx - 1)
                iy = cp.clip((obs_loc[:, 1] / 10.0).astype(cp.int32), 0, ny - 1)
                iz = cp.clip((obs_loc[:, 2] / 10.0).astype(cp.int32), 0, nz - 1)
                
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

            import time
            # 执行多次迭代来分摊开销
            n_iterations = 5
            logger.info(f"执行 {n_iterations} 次迭代来分摊开销")
            
            # 预热
            logger.info("CUDA 预热中...")
            for _ in range(2):
                cuda_assimilate_3dvar(background_dev, observations_dev, obs_locations_dev)
            
            # 正式计时
            start_time = time.perf_counter()  # 使用更精确的计时器

            for i in range(n_iterations):
                analysis, variance = cuda_assimilate_3dvar(
                    background_dev, observations_dev, obs_locations_dev
                )

            analysis = cuda_accel.to_host(analysis)
            variance = cuda_accel.to_host(variance)

            elapsed = time.perf_counter() - start_time  # 使用更精确的计时器
            avg_elapsed = elapsed / n_iterations

            logger.info(f"✅ CUDA计算完成，总耗时: {elapsed:.2f}秒")
            logger.info(f"平均每次耗时: {avg_elapsed:.2f}秒")
            logger.info(f"分析场形状: {analysis.shape}")
            logger.info(f"网格点数量: {analysis.size:,}点")
            logger.info(f"平均方差: {np.mean(variance):.4f}")

            cuda_accel.finalize()

            return {
                'success': True,
                'elapsed': avg_elapsed,  # 返回平均时间
                'analysis_shape': analysis.shape,
                'backend': backend
            }
        else:
            logger.info(f"⚠️ {backend}后端暂不支持自动计算，使用CPU计算进行对比")
            cuda_accel.finalize()
            return {'success': False, 'elapsed': 0, 'backend': backend}

    except Exception as e:
        logger.error(f"❌ CUDA计算失败: {e}")
        import traceback
        traceback.print_exc()
        if cuda_accel:
            cuda_accel.finalize()
        return {'success': False, 'elapsed': 0, 'backend': 'none'}


def main():
    """主函数"""
    logger.info("="*60)
    logger.info("GPU/JAX/CUDA加速贝叶斯同化演示")
    logger.info("="*60)

    results = {}

    results['cpu_baseline'] = demo_cpu_baseline()

    results['jax_accelerated'] = demo_jax_accelerated()

    cuda_accel = check_cuda_available()
    if cuda_accel:
        results['cuda_accelerated'] = demo_cuda_accelerated(cuda_accel)
        cuda_accel.finalize()
    else:
        results['cuda_accelerated'] = {'success': False, 'elapsed': 0, 'backend': 'none'}

    logger.info("\n" + "="*60)
    logger.info("性能对比")
    logger.info("="*60)

    if results['cpu_baseline']['success']:
        cpu_time = results['cpu_baseline']['elapsed']
        logger.info(f"CPU耗时: {cpu_time:.2f}秒")

        if results['jax_accelerated']['success']:
            jax_time = results['jax_accelerated']['elapsed']
            platform = results['jax_accelerated'].get('platform', 'unknown')
            speedup = cpu_time / jax_time if jax_time > 0 else 0

            logger.info(f"JAX耗时: {jax_time:.2f}秒 (平台: {platform})")
            logger.info(f"加速比: {speedup:.2f}x")

            if speedup > 1:
                logger.info("🎉 JAX加速成功！")
            elif speedup < 1:
                logger.info("⚠️ JAX未达到加速效果（JIT编译需要预热）")

        if results['cuda_accelerated']['success']:
            cuda_time = results['cuda_accelerated']['elapsed']
            backend = results['cuda_accelerated'].get('backend', 'unknown')
            speedup = cpu_time / cuda_time if cuda_time > 0 else 0

            logger.info(f"CUDA耗时: {cuda_time:.2f}秒 (后端: {backend})")
            logger.info(f"加速比: {speedup:.2f}x")

            if speedup > 1:
                logger.info("🎉 CUDA加速成功！")
        else:
            backend = results['cuda_accelerated'].get('backend', 'none')
            if backend != 'none':
                logger.info(f"⚠️ CUDA后端{backend}暂不支持自动计算")
            else:
                logger.info("⚠️ CUDA测试失败或不可用")
    else:
        logger.info("⚠️ CPU基准测试失败")

    logger.info("\n" + "="*60)
    logger.info("加速方案总结")
    logger.info("="*60)
    logger.info("1. JAX: 支持CPU/GPU/TPU，跨平台性能优秀")
    logger.info("2. CUDA: 支持CuPy/PyCUDA/Numba，需要NVIDIA GPU")
    logger.info("3. CPU: 通用，但速度较慢")

    logger.info("\n" + "="*60)
    logger.info("演示完成")
    logger.info("="*60)

    return results['cpu_baseline'].get('success', False)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
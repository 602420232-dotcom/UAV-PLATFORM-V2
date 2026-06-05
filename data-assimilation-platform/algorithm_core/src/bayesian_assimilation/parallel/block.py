'''
直接运行 block.py 文件时，Python 找不到 bayesian_assimilation 模块。这是正常的，因为：
1. 模块结构 ： bayesian_assimilation 是一个包，需要从正确的路径导入
2. 执行方式 ：应该通过运行 demo 脚本（如 parallel_demo.py ）来测试，而不是直接运行模块文件。
'''

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import logging
import concurrent.futures
import multiprocessing
from multiprocessing import shared_memory

# 尝试导入必要的类


try:
    from bayesian_assimilation.core.assimilator import BayesianAssimilator


except ImportError:
    # 如果无法导入，创建一个基类
    class BayesianAssimilator:
        def __init__(self, config=None):
            self.config = config
            self.logger = logging.getLogger(__name__)

        def initialize_grid(self: Any, domain_size: int, resolution: Any = None):
            self.domain_size = domain_size
            self.resolution = resolution

        def assimilate_3dvar(self, background, observations, obs_locations, obs_errors=None):
            return background.copy(), np.zeros_like(background)


# 模块级别的process_block函数，用于多进程执行


def _process_block(task_data):
    """处理单个数据块的函数"""
    block_idx, start_x, end_x, bg_block, block_obs, adjusted_obs_loc, obs_errors, config_dict = task_data
    try:
        # 保护逻辑：如果没有观测点，直接返回背景场
        if block_obs is None or len(block_obs) == 0:
            logging.debug(f"块 {block_idx} 没有观测点，使用背景场")
            return (block_idx, start_x, end_x, bg_block.copy(), np.zeros_like(bg_block))

        # 保护逻辑：检查配置参数
        if config_dict.get('target_resolution') is None:
            logging.warning(f"块 {block_idx} target_resolution 为 None，使用默认值 50.0")
            config_dict['target_resolution'] = 50.0

        # 在子进程中创建新的同化器实例
        from bayesian_assimilation.core.assimilator import BayesianAssimilator
        from bayesian_assimilation.utils.config import AssimilationConfig

        # 重建配置对象
        config = AssimilationConfig(
            domain_size=config_dict['domain_size'],
            target_resolution=config_dict['target_resolution'],
            background_error_scale=config_dict.get('background_error_scale', 1.5),
            observation_error_scale=config_dict.get('observation_error_scale', 0.8)
        )
        assimilator = BayesianAssimilator(config)

        # 关键：必须调用 initialize_grid 来设置 self.resolution
        assimilator.initialize_grid(config_dict['domain_size'])

        # 确保观测数据有效
        if obs_errors is not None and len(obs_errors) > 0:
            obs_errors_block = obs_errors
        else:
            obs_errors_block = None

        # 执行同化
        analysis_block, variance_block = assimilator.assimilate_3dvar(
            bg_block, block_obs, adjusted_obs_loc, obs_errors_block
        )
        return (block_idx, start_x, end_x, analysis_block, variance_block)
    except Exception as e:
        logging.error(f"块 {block_idx} 计算失败: {e}")
        import traceback
        traceback.print_exc()
        return (block_idx, start_x, end_x, bg_block.copy(), np.zeros_like(bg_block))


class BlockParallelAssimilator(BayesianAssimilator):
    """
    分块并行同化器
    """

    def __init__(self, config=None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)

    def initialize_grid(self: Any, domain_size: int, resolution: Any = None):
        """
        初始化网格
        """
        super().initialize_grid(domain_size, resolution)

    def assimilate_block_parallel(self, background, observations, obs_locations, n_blocks=4, obs_errors=None):
        """
        分块并行执行3DVAR同化

        Args:
            background: 背景场
            observations: 观测值
            obs_locations: 观测位置
            n_blocks: 分块数量
            obs_errors: 观测误差

        Returns:
            analysis, variance
        """
        import time
        start_time = time.time()

        # 计算分块大小
        nx, ny, nz = background.shape
        block_size_x = (nx + n_blocks - 1) // n_blocks

        # 准备分块
        blocks = []
        for i in range(n_blocks):
            start_x = i * block_size_x
            end_x = min((i + 1) * block_size_x, nx)
            if start_x < end_x:
                blocks.append((i, start_x, end_x))

        # 并行处理每个块
        results = []

        # 准备任务数据
        block_tasks = []

        # 为背景场创建共享内存
        bg_shm = None
        try:
            # 创建共享内存
            bg_nbytes = background.nbytes
            bg_shm = shared_memory.SharedMemory(create=True, size=bg_nbytes)
            bg_shared = np.ndarray(background.shape, dtype=background.dtype, buffer=bg_shm.buf)
            bg_shared[:] = background[:]

            for block_idx, start_x, end_x in blocks:
                # 提取块数据（使用共享内存）
                bg_block = bg_shared[start_x:end_x, :, :]

                # 筛选该块内的观测
                block_obs, block_obs_loc = self._filter_observations_in_block(
                    observations, obs_locations, start_x, end_x, nx
                )

                if len(block_obs) > 0:
                    # 调整观测位置
                    adjusted_obs_loc = block_obs_loc.copy()
                    adjusted_obs_loc[:, 0] -= start_x * self.resolution

                    # 准备配置信息
                    config_dict = {
                        'domain_size': (end_x - start_x, ny, nz),
                        'target_resolution': self.resolution,
                        'background_error_scale': getattr(self.config, 'background_error_scale', 1.5),
                        'observation_error_scale': getattr(self.config, 'observation_error_scale', 0.8)
                    }

                    block_tasks.append((block_idx, start_x, end_x, bg_block, block_obs, adjusted_obs_loc, obs_errors, config_dict))
                else:
                    # 无观测的块，直接使用背景场
                    results.append((block_idx, start_x, end_x, bg_block, np.zeros_like(bg_block)))

            # 使用Joblib执行（推荐）
            if block_tasks:
                try:
                    from joblib import Parallel, delayed

                    # 自动设置进程数
                    max_workers = min(n_blocks, multiprocessing.cpu_count())
                    self.logger.info(f"使用Joblib并行处理: {max_workers}进程")

                    # 使用Joblib的Parallel执行
                    results.extend(Parallel(n_jobs=max_workers, backend='multiprocessing')(
                        delayed(_process_block)(task)
                        for task in block_tasks
                    ))
                except ImportError:
                    # 回退到ProcessPoolExecutor
                    self.logger.warning("Joblib未安装，回退到ProcessPoolExecutor")
                    max_workers = min(n_blocks, multiprocessing.cpu_count())
                    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                        future_to_block = {}
                        for task in block_tasks:
                            future = executor.submit(_process_block, task)
                            future_to_block[future] = task[0]

                        for future in concurrent.futures.as_completed(future_to_block):
                            try:
                                result = future.result()
                                results.append(result)
                            except Exception as e:
                                self.logger.error(f"获取结果失败: {e}")
        finally:
            # 清理共享内存
            if bg_shm is not None:
                bg_shm.close()
                bg_shm.unlink()

        # 合并结果
        analysis = np.copy(background)
        variance = np.zeros_like(background)

        for block_idx, start_x, end_x, analysis_block, variance_block in sorted(results, key=lambda x:
            x[0]):
            analysis[start_x:end_x, :, :] = analysis_block
            variance[start_x:end_x, :, :] = variance_block

        elapsed = time.time() - start_time

        return analysis, variance

    def _filter_observations_in_block(self, observations, obs_locations, start_x, end_x, total_nx):
        """
        筛选块内的观测
        """
        # 保护逻辑：确保所有输入有效
        if observations is None or obs_locations is None:
            logging.warning("观测数据为 None，返回空数组")
            return np.array([]), np.array([]).reshape(0, 3)

        if len(observations) == 0 or len(obs_locations) == 0:
            return np.array([]), np.array([]).reshape(0, 3)

        # 保护逻辑：确保 resolution 有效
        if self.resolution is None:
            logging.warning("self.resolution 为 None，使用默认值 50.0")
            resolution = 50.0
        else:
            resolution = self.resolution

        # 计算物理坐标范围
        x_min = start_x * resolution
        x_max = end_x * resolution

        # 筛选观测
        try:
            mask = (obs_locations[:, 0] >= x_min) & (obs_locations[:, 0] < x_max)
            filtered_obs = observations[mask]
            filtered_locs = obs_locations[mask]
            return filtered_obs, filtered_locs
        except Exception as e:
            logging.error(f"筛选观测失败: {e}")
            return np.array([]), np.array([]).reshape(0, 3)

    def assimilate_parallel(self, background, observations, obs_locations, obs_errors=None):
        """
        并行执行3DVAR同化（别名）
        """
        return self.assimilate_block_parallel(background, observations, obs_locations, 4, obs_errors)

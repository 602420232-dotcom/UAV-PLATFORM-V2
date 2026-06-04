'''
直接运行 mpi.py 文件时，Python 找不到 bayesian_assimilation 模块。这是正常的，因为：
1. 模块结构 ： bayesian_assimilation 是一个包，需要从正确的路径导入
2. 执行方式 ：应该通过运行 demo 脚本（如 parallel_demo.py ）来测试，而不是直接运行模块文件。
'''

import numpy as np
from typing import Dict, List, Optional, Any, Callable
import logging

# 尝试导入mpi4py
try:
    from mpi4py import MPI
    MPI4PY_AVAILABLE = True
except ImportError:
    MPI4PY_AVAILABLE = False
    # 创建一个模拟的MPI类，用于在没有安装mpi4py时的运行
    class DummyMPI:
        COMM_WORLD = None
    MPI = DummyMPI()

# 尝试导入ParallelManager
try:
    from .base import ParallelManager, ParallelType
except ImportError:
    # 如果无法导入，创建一个基类
    class ParallelManager:
        def __init__(self, config=None):
            self.config = config or {}
            self.initialized = False
            self.logger = logging.getLogger(__name__)
        
        def start(self):
            return True
        
        def stop(self):
            return True
        
        def is_running(self):
            return False
        
        def parallelize(self: Any, func: Any, data: Dict[str, Any], **kwargs: Any):
            return [func(item, **kwargs) for item in data]
    
    class ParallelType:
        MPI = 'mpi'
        SEQUENTIAL = 'sequential'


class MPIParallelManager(ParallelManager):
    """
    MPI多机并行管理器
    用于大规模集群环境的分布式计算
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.parallel_type = ParallelType.MPI
        self.config.setdefault("root_rank", 0)
        self.comm = None
        self.rank = 0
        self.size = 1
        self.is_root = True
        self.logger = logging.getLogger(__name__)

        # 检查MPI可用性
        if not MPI4PY_AVAILABLE:
            self.logger.warning("mpi4py未安装，MPI功能不可用")
            self._use_dummy_mode()
        else:
            self._initialize_mpi()

    def _use_dummy_mode(self):
        """使用模拟模式（单进程）"""
        self.rank = 0
        self.size = 1
        self.is_root = True
        self.comm = None

    def _initialize_mpi(self):
        """初始化MPI环境"""
        try:
            if not MPI.Is_initialized():
                MPI.Init()
            
            self.comm = MPI.COMM_WORLD
            self.rank = self.comm.Get_rank()
            self.size = self.comm.Get_size()
            self.is_root = (self.rank == self.config["root_rank"])
            
            if self.is_root:
                self.logger.info(f"MPI环境初始化成功，总进程数: {self.size}")
            
        except Exception as e:
            self.logger.error(f"MPI初始化失败: {e}")
            self._use_dummy_mode()

    def start(self) -> bool:
        """
        启动MPI并行环境
        """
        if not MPI4PY_AVAILABLE:
            self.logger.warning("mpi4py未安装，无法启动MPI环境")
            return False

        try:
            if self.comm is None:
                self._initialize_mpi()
            
            self.initialized = True
            
            if self.is_root:
                self.logger.info(f"MPI并行环境启动，进程数: {self.size}")
            
            return True
        except Exception as e:
            self.logger.error(f"MPI启动失败: {e}")
            return False

    def stop(self) -> bool:
        """
        停止MPI并行环境
        """
        try:
            if self.initialized and MPI4PY_AVAILABLE:
                # 只在最后一个进程或根进程调用Finalize
                if self.is_root and MPI.Is_initialized():
                    MPI.Finalize()
            
            self.initialized = False
            
            if self.is_root:
                self.logger.info("MPI并行环境已停止")
            
            return True
        except Exception as e:
            self.logger.error(f"MPI停止失败: {e}")
            return False

    def is_running(self) -> bool:
        """
        检查MPI环境是否运行
        """
        return self.initialized and (self.comm is not None or self.size == 1)

    def parallelize(self, func: Callable, data: List[Any], **kwargs) -> List[Any]:
        """
        并行执行函数

        Args:
            func: 要执行的函数
            data: 数据列表
            **kwargs: 其他参数

        Returns:
            List[Any]: 执行结果列表
        """
        if not self.is_running() or self.size == 1:
            self.logger.debug("MPI环境未运行或只有一个进程，使用串行执行")
            return [func(item, **kwargs) for item in data]

        try:
            # 根进程分发任务
            if self.is_root:
                tasks = self._split_tasks(data)
            else:
                tasks = None

            # 广播任务分配信息
            tasks = self.comm.bcast(tasks, root=self.config["root_rank"])

            # 获取当前进程的任务
            my_tasks = tasks[self.rank] if self.rank < len(tasks) else []

            # 执行任务
            my_results = []
            for task in my_tasks:
                try:
                    result = func(task, **kwargs)
                    my_results.append(result)
                except Exception as e:
                    self.logger.error(f"进程 {self.rank} 执行任务失败: {e}")
                    my_results.append(None)

            # 收集所有结果
            all_results = self.comm.gather(my_results, root=self.config["root_rank"])

            # 根进程合并结果
            if self.is_root:
                return self._merge_results(all_results, len(data))
            else:
                return []

        except Exception as e:
            self.logger.error(f"MPI并行执行失败: {e}")
            # 降级到串行执行
            if self.is_root:
                return [func(item, **kwargs) for item in data]
            return []

    def _split_tasks(self, data: List[Any]) -> List[List[Any]]:
        """
        将任务分配给各个进程
        """
        n_tasks = len(data)
        tasks_per_process = (n_tasks + self.size - 1) // self.size

        tasks = []
        for i in range(self.size):
            start = i * tasks_per_process
            end = min((i + 1) * tasks_per_process, n_tasks)
            tasks.append(data[start:end])

        return tasks

    def _merge_results(self, all_results: List[List[Any]], n_total: int) -> List[Any]:
        """
        合并所有进程的结果
        """
        results = []
        for proc_results in all_results:
            results.extend(proc_results)
        
        # 确保结果数量正确
        while len(results) < n_total:
            results.append(None)
        
        return results[:n_total]

    def broadcast(self, data: Any) -> Any:
        """
        广播数据到所有进程
        """
        if not self.is_running() or self.size == 1:
            return data

        return self.comm.bcast(data, root=self.config["root_rank"])

    def gather(self, data: Any) -> Optional[List[Any]]:
        """
        收集所有进程的数据到根进程
        """
        if not self.is_running() or self.size == 1:
            return [data]

        return self.comm.gather(data, root=self.config["root_rank"])

    def scatter(self, data: List[Any]) -> Any:
        """
        将数据分发到各个进程
        """
        if not self.is_running() or self.size == 1:
            return data[0] if data else None

        return self.comm.scatter(data, root=self.config["root_rank"])

    def get_resource_info(self) -> Dict:
        """
        获取MPI资源信息
        """
        return {
            "status": "running" if self.is_running() else "stopped",
            "parallel_type": "mpi",
            "rank": self.rank,
            "size": self.size,
            "is_root": self.is_root,
            "mpi4py_available": MPI4PY_AVAILABLE
        }


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


class MPIParallelAssimilator(BayesianAssimilator):
    """
    MPI并行同化器
    """

    def __init__(self, config=None):
        super().__init__(config)
        self.mpi_manager = MPIParallelManager()
        self.logger = logging.getLogger(__name__)

    def initialize_grid(self: Any, domain_size: int, resolution: Any = None):
        """
        初始化网格
        """
        super().initialize_grid(domain_size, resolution)

    def assimilate_parallel(self, background, observations, obs_locations, n_blocks=None, obs_errors=None):
        """
        MPI并行执行3DVAR同化
        """
        if not MPI4PY_AVAILABLE or self.mpi_manager.size == 1:
            self.logger.warning("MPI不可用，使用串行执行")
            return self.assimilate_3dvar(background, observations, obs_locations, obs_errors)

        try:
            import time
            start_time = time.time()

            # 获取背景场形状
            nx, ny, nz = background.shape

            if n_blocks is None:
                n_blocks = self.mpi_manager.size

            # 根进程准备数据
            if self.mpi_manager.is_root:
                # 计算分块大小
                block_size_x = (nx + n_blocks - 1) // n_blocks

                # 准备分块任务
                tasks = []
                for i in range(n_blocks):
                    start_x = i * block_size_x
                    end_x = min((i + 1) * block_size_x, nx)
                    if start_x < end_x:
                        tasks.append((start_x, end_x, background, observations, obs_locations, obs_errors))
            else:
                tasks = None

            # 广播任务
            tasks = self.mpi_manager.broadcast(tasks)

            # 获取当前进程的任务
            if self.mpi_manager.rank < len(tasks):
                task = tasks[self.mpi_manager.rank]
                start_x, end_x, bg, obs, obs_loc, obs_err = task

                # 提取块数据
                bg_block = bg[start_x:end_x, :, :]

                # 筛选该块内的观测
                x_min = start_x * self.resolution
                x_max = end_x * self.resolution
                mask = (obs_loc[:, 0] >= x_min) & (obs_loc[:, 0] < x_max)

                if np.any(mask):
                    block_obs = obs[mask]
                    block_obs_loc = obs_loc[mask].copy()
                    block_obs_loc[:, 0] -= start_x * self.resolution

                    # 执行同化
                    analysis_block, variance_block = self.assimilate_3dvar(
                        bg_block, block_obs, block_obs_loc, obs_err
                    )
                else:
                    # 无观测的块，直接使用背景场
                    analysis_block = bg_block.copy()
                    variance_block = np.zeros_like(bg_block)

                my_result = (start_x, end_x, analysis_block, variance_block)
            else:
                my_result = None

            # 收集所有结果
            all_results = self.mpi_manager.gather(my_result)

            # 根进程合并结果
            if self.mpi_manager.is_root:
                analysis = np.copy(background)
                variance = np.zeros_like(background)

                for result in all_results:
                    if result is not None:
                        start_x, end_x, analysis_block, variance_block = result
                        analysis[start_x:end_x, :, :] = analysis_block
                        variance[start_x:end_x, :, :] = variance_block

                elapsed = time.time() - start_time
                self.logger.info(f"MPI并行同化完成，耗时: {elapsed:.2f}秒")

                return analysis, variance
            else:
                return None, None

        except Exception as e:
            self.logger.error(f"MPI并行同化失败: {e}")
            if self.mpi_manager.is_root:
                return self.assimilate_3dvar(background, observations, obs_locations, obs_errors)
            return None, None


# 便捷函数
def create_mpi_manager(config: Optional[Dict] = None) -> MPIParallelManager:
    """
    创建MPI管理器
    """
    manager = MPIParallelManager(config)
    manager.start()
    return manager

"""
Bayesian Assimilation Parallel Computing Framework
贝叶斯同化并行计算框架
"""


from .base import (
    ParallelManager,
    ParallelType,
    parallel_factory,
    SequentialParallelManager
)
from .block import BlockParallelAssimilator
from .dask import DaskParallelManager, DaskParallelAssimilator, create_dask_client

# 尝试导入MPI模块（可选依赖）
MPI_AVAILABLE = False


try:
    from .mpi import MPIParallelManager, MPIParallelAssimilator, create_mpi_manager
    MPI_AVAILABLE = True


except Exception:
    MPI_AVAILABLE = False

# 尝试导入Ray模块（可选依赖）
RAY_AVAILABLE = False


try:
    from .ray import RayParallelManager, RayParallelAssimilator, create_ray_client
    RAY_AVAILABLE = True


except Exception:
    RAY_AVAILABLE = False


__all__ = [
    # 基类和工厂
    'ParallelManager',
    'ParallelType',
    'parallel_factory',
    'SequentialParallelManager',

    # 分块并行
    'BlockParallelAssimilator',

    # Dask分布式
    'DaskParallelManager',
    'DaskParallelAssimilator',
    'create_dask_client',

    # 可用性标志
    'MPI_AVAILABLE',
    'RAY_AVAILABLE',
]

# 条件导出


if MPI_AVAILABLE:
    __all__.extend(['MPIParallelManager', 'MPIParallelAssimilator', 'create_mpi_manager'])


if RAY_AVAILABLE:
    __all__.extend(['RayParallelManager', 'RayParallelAssimilator', 'create_ray_client'])

# 注册所有并行管理器
parallel_factory.register(ParallelType.BLOCK, BlockParallelAssimilator)
parallel_factory.register(ParallelType.DASK, DaskParallelManager)


if MPI_AVAILABLE:
    parallel_factory.register(ParallelType.MPI, MPIParallelManager)


if RAY_AVAILABLE:
    parallel_factory.register(ParallelType.RAY, RayParallelManager)

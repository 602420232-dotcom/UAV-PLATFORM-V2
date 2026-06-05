"""
Bayesian Assimilation Accelerators
"""

from .base import BaseAccelerator, AcceleratorType, accelerator_factory
from .cpu import CPUAccelerator, OpenMPAccelerator, BLASAccelerator
from .jax import JAXAccelerator, TPUAccelerator, GPUAccelerator, CUDAAccelerator as JAXCUDAAccelerator
from .cuda import CUDAAccelerator, CuPyAccelerator, PyCUDAccelerator


__all__ = [
    'BaseAccelerator',
    'AcceleratorType',
    'accelerator_factory',
    'CPUAccelerator',
    'OpenMPAccelerator',
    'BLASAccelerator',
    'JAXAccelerator',
    'TPUAccelerator',
    'GPUAccelerator',
    'CUDAAccelerator',
    'CuPyAccelerator',
    'PyCUDAccelerator'
]

# 注册所有加速器
accelerator_factory.register(AcceleratorType.CPU, CPUAccelerator)
accelerator_factory.register(AcceleratorType.OPENMP, OpenMPAccelerator)
accelerator_factory.register(AcceleratorType.BLAS, BLASAccelerator)
accelerator_factory.register(AcceleratorType.JAX, JAXAccelerator)
accelerator_factory.register(AcceleratorType.TPU, TPUAccelerator)
accelerator_factory.register(AcceleratorType.CUPY, CuPyAccelerator)
accelerator_factory.register(AcceleratorType.PYCUDA, PyCUDAccelerator)

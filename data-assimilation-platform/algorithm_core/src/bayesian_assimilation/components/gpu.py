"""
GPU 加速器组件

此模块已整合到 accelerators.gpu，请使用：
    from bayesian_assimilation.accelerators import GPUAccelerator

保留此文件仅用于向后兼容。
"""

from bayesian_assimilation.accelerators.gpu import GPUAccelerator

__all__ = ['GPUAccelerator']

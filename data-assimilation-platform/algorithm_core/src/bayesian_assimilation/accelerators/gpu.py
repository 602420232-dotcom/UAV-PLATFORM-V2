"""
GPU加速器
提供GPU计算支持和容量估算功能
"""

import numpy as np
import logging
from typing import Optional, Tuple, Dict, Any


try:
    import cupy as cp
    GPU_AVAILABLE = True


except ImportError:
    GPU_AVAILABLE = False
    cp = None

logger = logging.getLogger(__name__)


class GPUAccelerator:
    """
    GPU加速器

    提供GPU计算支持和容量估算功能。
    支持CuPy库进行GPU加速计算。
    """

    def __init__(self, use_gpu: bool = True, gpu_memory_limit_gb: float = 8.0):
        """
        初始化GPU加速器

        Args:
            use_gpu: 是否使用GPU
            gpu_memory_limit_gb: GPU内存限制（GB）
        """
        self.use_gpu = use_gpu and GPU_AVAILABLE
        self.gpu_memory_limit_gb = gpu_memory_limit_gb
        self.gpu_memory = 0

        if self.use_gpu and cp is not None:
            try:
                mem_info = cp.cuda.Device(0).mem_info
                self.gpu_memory = mem_info[1] / 1e9
                logger.info(f"GPU加速可用: 显存: {self.gpu_memory:.2f}GB")
            except Exception as e:
                logger.warning(f"无法获取GPU内存信息: {e}")
                self.use_gpu = False
        else:
            logger.info("GPU不可用，将使用CPU计算")

    def to_gpu(self, array: np.ndarray) -> np.ndarray:
        """传输数据到GPU"""
        if self.use_gpu and cp is not None:
            return cp.asarray(array)
        return array

    def to_cpu(self, array) -> np.ndarray:
        """从GPU传回数据"""
        if self.use_gpu and cp is not None and hasattr(array, 'device'):
            return cp.asnumpy(array)
        return array

    def estimate_capacity(self, grid_shape: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """
        根据GPU内存限制估算可支持的最大网格形状

        Args:
            grid_shape: 原始网格形状 (nx, ny, nz)

        Returns:
            调整后的网格形状
        """
        if not self.use_gpu or cp is None:
            return grid_shape

        nx, ny, nz = grid_shape
        bytes_per_point = 4
        total_points = nx * ny * nz
        estimated_memory_gb = total_points * bytes_per_point * 8 / 1e9

        if estimated_memory_gb > self.gpu_memory_limit_gb:
            scale_factor = (self.gpu_memory_limit_gb / estimated_memory_gb) ** (1/3)
            new_nx = max(1, int(nx * scale_factor))
            new_ny = max(1, int(ny * scale_factor))
            new_nz = max(1, int(nz * scale_factor))

            logger.warning(f"GPU内存不足，从{grid_shape}降采样到({new_nx}, {new_ny}, {new_nz})")
            return (new_nx, new_ny, new_nz)

        return grid_shape

    def estimate_gpu_capacity(self, grid_shape: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """估计GPU可处理的最大网格（兼容性别名）"""
        return self.estimate_capacity(grid_shape)

    def get_memory_info(self) -> Optional[Dict[str, Any]]:
        """
        获取GPU内存信息

        Returns:
            包含free和total内存信息的字典，如果不可用则返回None
        """
        if not self.use_gpu or cp is None:
            return None

        try:
            mem = cp.cuda.runtime.memGetInfo()
            return {
                'free': mem[0],
                'total': mem[1]
            }
        except Exception as e:
            logger.warning(f"无法获取GPU内存信息: {e}")
            return None

    def gpu_matmul(self, A, B):
        """GPU矩阵乘法"""
        if self.use_gpu and cp is not None:
            if hasattr(A, 'dot'):
                return A.dot(B)
            else:
                return cp.dot(A, B)
        else:
            if hasattr(A, 'dot'):
                return A.dot(B)
            else:
                return np.dot(A, B)

    def is_available(self) -> bool:
        """检查GPU是否可用"""
        return self.use_gpu

    def get_device_info(self) -> Dict[str, Any]:
        """获取设备信息"""
        info = {
            'available': self.use_gpu,
            'memory_limit_gb': self.gpu_memory_limit_gb,
            'memory_gb': self.gpu_memory
        }

        if self.use_gpu and cp is not None:
            try:
                device = cp.cuda.Device(0)
                info['device_name'] = device.name if hasattr(device, 'name') else 'Unknown'
                info['compute_capability'] = device.compute_capability()
            except Exception:
                pass

        return info

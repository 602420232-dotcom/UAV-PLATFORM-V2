"""
CUDA专用加速器
使用NVIDIA CUDA进行GPU加速计算
"""

import os
import sys
import logging
import numpy as np
from typing import Optional, Any, Callable

# 处理相对导入和绝对导入
if __name__ == '__main__':
    # 直接运行时使用绝对导入
    from bayesian_assimilation.accelerators.base import BaseAccelerator, AcceleratorType
else:
    # 作为模块导入时使用相对导入
    from .base import BaseAccelerator, AcceleratorType

logger = logging.getLogger(__name__)


class CUDAAccelerator(BaseAccelerator):
    """
    CUDA专用加速器
    使用NVIDIA CUDA进行GPU加速计算
    支持CuPy、PyCUDA和Numba CUDA
    """

    def __init__(self, config: Optional[Any] = None):
        super().__init__(config)
        self.accelerator_type = AcceleratorType.CUPY
        self._cupy = None
        self._pycuda = None
        self._numba = None
        self._cuda_available = False
        self._device_count = 0
        self._current_device = 0
        self._warmup_completed = False

    def initialize(self) -> bool:
        """
        初始化CUDA加速器

        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("="*60)
            logger.info("初始化CUDA加速器")
            logger.info("="*60)

            # 检查CUDA环境变量
            cuda_visible_devices = os.environ.get('CUDA_VISIBLE_DEVICES', '')
            if cuda_visible_devices:
                logger.info(f"CUDA可见设备: {cuda_visible_devices}")

            # 尝试导入CuPy
            try:
                import cupy as cp
                self._cupy = cp
                logger.info("✅ CuPy已导入")
                self._device_count = cp.cuda.runtime.getDeviceCount()
                logger.info(f"CUDA设备数量: {self._device_count}")
                for i in range(self._device_count):
                    device = cp.cuda.Device(i)
                    with device:
                        logger.info(f"  设备 {i}: {cp.cuda.runtime.getDeviceProperties(i)['name']}")
                self._cuda_available = True
            except ImportError:
                logger.warning("⚠️ CuPy未安装，尝试PyCUDA")
                try:
                    import pycuda.driver as cuda  # type: ignore
                    import pycuda.autoinit  # type: ignore
                    self._pycuda = cuda
                    logger.info("✅ PyCUDA已导入")
                    self._device_count = cuda.Device.count()  # type: ignore
                    for i in range(self._device_count):
                        device = cuda.Device(i)  # type: ignore
                        logger.info(f"  设备 {i}: {device.name()}")  # type: ignore
                    self._cuda_available = True
                except ImportError:
                    logger.warning("⚠️ PyCUDA未安装，尝试Numba CUDA")
                    try:
                        from numba import cuda
                        self._numba = cuda
                        logger.info("✅ Numba CUDA已导入")
                        self._device_count = len(cuda.gpus)
                        for i, gpu in enumerate(cuda.gpus):
                            logger.info(f"  设备 {i}: {gpu.name}")
                        self._cuda_available = True
                    except ImportError:
                        logger.error("❌ CUDA相关库未安装")
                        logger.info("安装CuPy: pip install cupy-cuda11x")
                        logger.info("或安装PyCUDA: pip install pycuda")
                        logger.info("或安装Numba: pip install numba cuda-python")
                        self._cuda_available = False

            if not self._cuda_available:
                logger.warning("⚠️ CUDA不可用，将使用CPU")
                return False

            self.initialized = True
            logger.info("✅ CUDA加速器初始化成功")
            return True

        except Exception as e:
            logger.error(f"❌ CUDA加速器初始化失败: {e}")
            import traceback
            traceback.print_exc()
            self.initialized = False
            return False

    def warmup(self):
        """
        JIT编译预热
        执行一些简单的计算来预热JIT编译器
        """
        if not self.initialized or not self._cuda_available:
            logger.warning("⚠️ 跳过JIT预热，CUDA未初始化")
            return

        logger.info("\n" + "="*60)
        logger.info("JIT编译预热")
        logger.info("="*60)

        try:
            if self._cupy:
                # CuPy预热
                import cupy as cp
                x = cp.ones((100, 100))
                y = cp.ones((100, 100))
                z = cp.dot(x, y)
                cp.cuda.Stream.null.synchronize()
                logger.info("✅ CuPy JIT预热完成")

            elif self._pycuda:
                # PyCUDA预热
                import pycuda.driver as cuda
                import pycuda.compiler as compiler
                
                mod = compiler.SourceModule("""
                __global__ void add(float *a, float *b, float *c) {
                    int i = threadIdx.x + blockIdx.x * blockDim.x;
                    c[i] = a[i] + b[i];
                }
                """)
                add = mod.get_function("add")
                a = np.ones(100, dtype=np.float32)
                b = np.ones(100, dtype=np.float32)
                c = np.zeros(100, dtype=np.float32)
                add(cuda.In(a), cuda.In(b), cuda.Out(c), block=(100, 1, 1), grid=(1, 1))
                logger.info("✅ PyCUDA JIT预热完成")

            elif self._numba:
                # Numba CUDA预热
                from numba import cuda  # type: ignore
                
                @cuda.jit  # type: ignore
                def add_kernel(a, b, c):  # type: ignore
                    i = cuda.grid(1)  # type: ignore
                    if i < len(a):  # type: ignore
                        c[i] = a[i] + b[i]  # type: ignore
                
                a = np.ones(100, dtype=np.float32)
                b = np.ones(100, dtype=np.float32)
                c = np.zeros(100, dtype=np.float32)
                threads_per_block = 32
                blocks_per_grid = (len(a) + threads_per_block - 1) // threads_per_block
                add_kernel[blocks_per_grid, threads_per_block](a, b, c)  # type: ignore
                logger.info("✅ Numba CUDA JIT预热完成")

            self._warmup_completed = True
            logger.info("✅ JIT预热完成")

        except Exception as e:
            logger.error(f"❌ JIT预热失败: {e}")

    def finalize(self):
        """释放CUDA加速器资源"""
        if self._pycuda:
            try:
                import pycuda.autoinit
                # PyCUDA会自动清理
                pass
            except:
                pass
        logger.info("CUDA加速器已释放")

    def to_device(self, data: "np.ndarray") -> Any:
        """
        将数据转移到CUDA设备

        Args:
            data: numpy数组

        Returns:
            设备上的数组
        """
        if not self.initialized or not self._cuda_available:
            return data

        if self._cupy:
            return self._cupy.asarray(data)
        elif self._numba:
            return self._numba.to_device(data)
        else:
            return data

    def to_host(self, data: Any) -> "np.ndarray":
        """
        将数据从设备移回主机

        Args:
            data: 设备上的数组

        Returns:
            numpy数组
        """
        if not self.initialized or not self._cuda_available:
            return np.array(data)

        if self._cupy:
            return self._cupy.asnumpy(data)
        elif self._numba:
            return data.copy_to_host()
        else:
            return np.array(data)

    def matmul(self, A: Any, B: Any) -> Any:
        """
        矩阵乘法

        Args:
            A: 左矩阵
            B: 右矩阵

        Returns:
            结果矩阵
        """
        if not self.initialized or not self._cuda_available:
            return np.dot(A, B)

        if self._cupy:
            return self._cupy.dot(A, B)
        elif self._numba:
            # 使用简化的 numba CUDA 实现
            from numba import cuda  # type: ignore
            
            @cuda.jit  # type: ignore
            def matmul_kernel(A, B, C):  # type: ignore
                i, j = cuda.grid(2)  # type: ignore
                if i < C.shape[0] and j < C.shape[1]:  # type: ignore
                    tmp = 0.0
                    for k in range(A.shape[1]):  # type: ignore
                        tmp += A[i, k] * B[k, j]  # type: ignore
                    C[i, j] = tmp  # type: ignore
            
            C = np.zeros((A.shape[0], B.shape[1]), dtype=A.dtype)
            threads_per_block = (16, 16)
            blocks_per_grid_x = (A.shape[0] + threads_per_block[0] - 1) // threads_per_block[0]
            blocks_per_grid_y = (B.shape[1] + threads_per_block[1] - 1) // threads_per_block[1]
            blocks_per_grid = (blocks_per_grid_x, blocks_per_grid_y)
            
            d_A = cuda.to_device(A)
            d_B = cuda.to_device(B)
            d_C = cuda.to_device(C)
            
            matmul_kernel[blocks_per_grid, threads_per_block](d_A, d_B, d_C)  # type: ignore
            
            return d_C.copy_to_host()
        else:
            return np.dot(A, B)

    def solve(self, A: Any, b: Any) -> Any:
        """
        求解线性系统 Ax = b

        Args:
            A: 系数矩阵
            b: 右端向量

        Returns:
            解向量
        """
        if not self.initialized or not self._cuda_available:
            return np.linalg.solve(A, b)

        if self._cupy:
            return self._cupy.linalg.solve(A, b)
        else:
            return np.linalg.solve(A, b)

    def get_device_info(self) -> dict:
        """
        获取CUDA设备信息

        Returns:
            dict: 设备信息
        """
        info = {
            'cuda_available': self._cuda_available,
            'device_count': self._device_count,
            'warmup_completed': self._warmup_completed
        }

        if self._cupy:
            info['backend'] = 'cupy'
            if self._device_count > 0:
                import cupy as cp
                props = cp.cuda.runtime.getDeviceProperties(0)
                info['device_name'] = props['name']
                info['total_memory'] = f"{props['totalGlobalMem'] / 1e9:.2f} GB"
        elif self._pycuda:
            info['backend'] = 'pycuda'
            if self._device_count > 0:
                import pycuda.driver as cuda  # type: ignore
                device = cuda.Device(0)  # type: ignore
                info['device_name'] = device.name()  # type: ignore
        elif self._numba:
            info['backend'] = 'numba'
            if self._device_count > 0:
                from numba import cuda
                info['device_name'] = cuda.gpus[0].name

        return info

    def check_cuda_available(self) -> bool:
        """
        检查CUDA是否可用

        Returns:
            bool: CUDA是否可用
        """
        return self._cuda_available


class CuPyAccelerator(CUDAAccelerator):
    """
    CuPy专用加速器
    使用CuPy库进行GPU加速
    """

    def __init__(self, config: Optional[Any] = None):
        super().__init__(config)
        self.accelerator_type = AcceleratorType.CUPY

    def initialize(self) -> bool:
        """初始化CuPy加速器"""
        try:
            import cupy as cp
            self._cupy = cp
            self._cuda_available = True
            self._device_count = cp.cuda.runtime.getDeviceCount()
            self.initialized = True
            logger.info("✅ CuPy加速器初始化成功")
            return True
        except ImportError:
            logger.error("❌ CuPy未安装")
            logger.info("安装CuPy: pip install cupy-cuda11x")
            self.initialized = False
            return False


class PyCUDAccelerator(CUDAAccelerator):
    """
    PyCUDA专用加速器
    使用PyCUDA库进行GPU加速
    """

    def __init__(self, config: Optional[Any] = None):
        super().__init__(config)
        self.accelerator_type = AcceleratorType.PYCUDA

    def initialize(self) -> bool:
        """初始化PyCUDA加速器"""
        try:
            import pycuda.driver as cuda
            import pycuda.autoinit
            self._pycuda = cuda
            self._cuda_available = True
            self._device_count = cuda.Device.count() # type: ignore
            self.initialized = True
            logger.info("✅ PyCUDA加速器初始化成功")
            return True
        except ImportError:
            logger.error("❌ PyCUDA未安装")
            logger.info("安装PyCUDA: pip install pycuda")
            self.initialized = False
            return False

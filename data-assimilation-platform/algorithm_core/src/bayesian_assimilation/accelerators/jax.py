"""
JAX加速器
使用Google JAX进行GPU/TPU/CUDA加速计算
"""

import logging
import numpy as np
from typing import Optional, Any, List, Callable

# 处理相对导入问题
if __name__ == '__main__':
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
    from bayesian_assimilation.accelerators.base import BaseAccelerator, AcceleratorType
else:
    from .base import BaseAccelerator, AcceleratorType

logger = logging.getLogger(__name__)


class JAXAccelerator(BaseAccelerator):
    """
    JAX加速器
    支持GPU、TPU和CUDA加速计算
    """

    def __init__(self, config: Optional[Any] = None):
        super().__init__(config)
        self.accelerator_type = AcceleratorType.JAX
        self._jax = None
        self._jnp = None
        self._jitt = None
        self._device_count = 0
        self._default_device = None
        self._platform = None
        self._backend = None

    def initialize(self) -> bool:
        """
        初始化JAX加速器

        Returns:
            bool: 初始化是否成功
        """
        try:
            import jax
            import jax.numpy as jnp
            from jax import jit

            self._jax = jax
            self._jnp = jnp
            self._jitt = jit

            # 使用正确的API检测平台
            try:
                self._backend = jax.default_backend()  # type: ignore
            except AttributeError:
                # 旧版本兼容
                try:
                    self._backend = jax.lib.xla_bridge.get_backend().platform  # type: ignore
                except:
                    self._backend = 'cpu'

            self._platform = self._backend

            # 检测GPU
            gpu_available = self._check_cuda_available()
            if gpu_available:
                logger.info("✅ JAX CUDA/GPU加速已启用")
            else:
                # 检测TPU
                tpu_available = self.check_tpu_available()
                if tpu_available:
                    logger.info("✅ JAX TPU加速已启用")
                else:
                    logger.info("⚠️ JAX未检测到GPU/TPU，将使用CPU")

            self._device_count = jax.device_count()  # type: ignore
            self._default_device = jax.devices()[0]  # type: ignore

            logger.info(f"   后端: {self._backend}")
            logger.info(f"   设备数量: {self._device_count}")
            logger.info(f"   默认设备: {self._default_device}")

            self.initialized = True
            return True

        except ImportError:
            logger.error("❌ JAX未安装，无法使用JAX加速")
            logger.info("安装JAX CPU版本: pip install jax jaxlib")
            logger.info("安装JAX GPU版本: pip install jax[cuda11_pip] -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html")
            self.initialized = False
            return False
        except Exception as e:
            logger.error(f"❌ JAX加速器初始化失败: {e}")
            self.initialized = False
            return False

    def _check_cuda_available(self) -> bool:
        """
        检查CUDA是否可用

        Returns:
            bool: CUDA是否可用
        """
        if self._jax is None:
            return False

        try:
            # 检查JAX是否配置了CUDA后端
            backend = self._backend
            if backend == 'cuda' or backend == 'gpu':
                return True

            # 尝试检查是否有GPU设备
            devices = self._jax.devices()  # type: ignore
            for device in devices:
                if 'cuda' in str(device).lower() or 'gpu' in str(device).lower():
                    return True

            return False
        except Exception:
            return False

    def finalize(self):
        """释放JAX加速器资源"""
        if self._jax:
            try:
                self._jax.clear_cache()  # type: ignore
            except AttributeError:
                pass  # JAX版本可能不支持clear_cache
        logger.info("JAX加速器已释放")

    def to_device(self, data: np.ndarray) -> Any:
        """
        将数据转移到加速设备

        Args:
            data: numpy数组

        Returns:
            JAX数组
        """
        if self._jnp is None:
            raise RuntimeError("JAX未初始化")

        return self._jnp.array(data)

    def to_host(self, data: Any) -> np.ndarray:
        """
        将数据从设备移回主机

        Args:
            data: JAX数组

        Returns:
            numpy数组
        """
        if self._jax is None:
            raise RuntimeError("JAX未初始化")

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
        if self._jnp is None:
            raise RuntimeError("JAX未初始化")

        return self._jnp.dot(A, B)

    def solve(self, A: Any, b: Any) -> Any:
        """
        求解线性系统 Ax = b

        Args:
            A: 系数矩阵
            b: 右端向量

        Returns:
            解向量
        """
        if self._jax is None:
            raise RuntimeError("JAX未初始化")

        try:
            from jax.lax import solve  # type: ignore
            return solve(A, b)  # type: ignore
        except ImportError:
            # 回退到numpy实现
            return np.linalg.solve(A, b)

    def jit(self, func: Callable) -> Callable:
        """
        JIT编译函数

        Args:
            func: 要编译的函数

        Returns:
            编译后的函数
        """
        if self._jitt is None:
            raise RuntimeError("JAX未初始化")

        return self._jitt(func)

    def grad(self, func: Callable) -> Callable:
        """
        计算梯度

        Args:
            func: 要计算梯度的函数

        Returns:
            梯度函数
        """
        if self._jax is None:
            raise RuntimeError("JAX未初始化")

        return self._jax.grad(func)

    def jacfwd(self, func: Callable) -> Callable:
        """
        前向模式雅可比矩阵计算

        Args:
            func: 要计算的函数

        Returns:
            雅可比矩阵函数
        """
        if self._jax is None:
            raise RuntimeError("JAX未初始化")

        return self._jax.jacfwd(func)

    def device_put(self, data: Any, device: Optional[Any] = None) -> Any:
        """
        将数据放到指定设备

        Args:
            data: 数据
            device: 设备

        Returns:
            设备上的数据
        """
        if self._jax is None:
            raise RuntimeError("JAX未初始化")

        if device is None:
            device = self._default_device

        return self._jax.device_put(data, device)

    def pmap(self, func: Callable, devices: Optional[List[Any]] = None) -> Callable:
        """
        并行映射函数到多个设备

        Args:
            func: 要并行化的函数
            devices: 设备列表

        Returns:
            并行化后的函数
        """
        if self._jax is None:
            raise RuntimeError("JAX未初始化")

        if devices is None:
            return self._jax.pmap(func)
        else:
            return self._jax.pmap(func, devices=devices)

    def check_tpu_available(self) -> bool:
        """
        检查TPU是否可用

        Returns:
            bool: TPU是否可用
        """
        if self._jax is None:
            return False

        try:
            backend = self._backend
            if backend == 'tpu':
                return True

            devices = self._jax.devices()
            for device in devices:
                if 'tpu' in str(device).lower():
                    return True

            return False
        except:
            return False

    def check_gpu_available(self) -> bool:
        """
        检查GPU是否可用

        Returns:
            bool: GPU是否可用
        """
        return self._check_cuda_available()

    def check_cuda_available(self) -> bool:
        """
        检查CUDA是否可用

        Returns:
            bool: CUDA是否可用
        """
        return self._check_cuda_available()


class TPUAccelerator(JAXAccelerator):
    """
    TPU专用加速器
    使用Google TPU进行加速计算
    """

    def __init__(self, config: Optional[Any] = None):
        super().__init__(config)
        self.accelerator_type = AcceleratorType.TPU

    def initialize(self) -> bool:
        """初始化TPU加速器"""
        try:
            result = super().initialize()

            if result and not self.check_tpu_available():
                logger.warning("⚠️ 未检测到TPU，JAX将使用其他加速器")
                return False

            logger.info("✅ TPU加速器初始化成功")
            return result

        except Exception as e:
            logger.error(f"❌ TPU加速器初始化失败: {e}")
            return False

    def distributed_init(self, coordinator_address: Optional[str] = None) -> bool:
        """
        初始化分布式TPU

        Args:
            coordinator_address: 协调器地址

        Returns:
            bool: 初始化是否成功
        """
        try:
            try:
                from jax.config import config  # type: ignore
                config.update("jax_xla_profile", True)  # type: ignore
            except ImportError:
                pass  # 某些JAX版本可能没有config模块

            if coordinator_address:
                import os
                os.environ['TPU_COORDINATOR_ADDRESS'] = coordinator_address

            if self._jax is not None:
                self._device_count = len(self._jax.devices('tpu'))  # type: ignore
                logger.info(f"✅ 分布式TPU初始化成功: {self._device_count} 设备")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"❌ 分布式TPU初始化失败: {e}")
            return False


class GPUAccelerator(JAXAccelerator):
    """
    GPU/CUDA专用加速器
    使用NVIDIA GPU进行加速计算
    """

    def __init__(self, config: Optional[Any] = None):
        super().__init__(config)
        self.accelerator_type = AcceleratorType.CUPY

    def initialize(self) -> bool:
        """初始化GPU/CUDA加速器"""
        try:
            result = super().initialize()

            if result and not self.check_cuda_available():
                logger.warning("⚠️ 未检测到NVIDIA GPU/CUDA，JAX将使用其他加速器")
                return False

            logger.info("✅ GPU/CUDA加速器初始化成功")
            return result

        except Exception as e:
            logger.error(f"❌ GPU/CUDA加速器初始化失败: {e}")
            return False

    def get_gpu_info(self) -> dict:
        """
        获取GPU/CUDA信息

        Returns:
            dict: GPU信息
        """
        if self._jax is None:
            return {}

        try:
            backend = self._backend
            devices = self._jax.devices()

            return {
                'backend': backend,
                'cuda_available': self.check_cuda_available(),
                'device_count': self._device_count,
                'default_device': str(self._default_device),
                'devices': [str(d) for d in devices]
            }
        except Exception as e:
            logger.error(f"获取GPU信息失败: {e}")
            return {}


class CUDAAccelerator(GPUAccelerator):
    """
    CUDA专用加速器
    使用NVIDIA CUDA进行GPU加速计算
    """

    def __init__(self, config: Optional[Any] = None):
        super().__init__(config)
        self.accelerator_type = AcceleratorType.PYCUDA

    def initialize(self) -> bool:
        """初始化CUDA加速器"""
        logger.info("="*60)
        logger.info("初始化CUDA加速器")
        logger.info("="*60)

        try:
            # 检查CUDA是否可用
            import os
            cuda_visible_devices = os.environ.get('CUDA_VISIBLE_DEVICES', '')
            if cuda_visible_devices:
                logger.info(f"CUDA可见设备: {cuda_visible_devices}")

            result = super().initialize()

            if result and self.check_cuda_available():
                logger.info("✅ CUDA加速器初始化成功")
                gpu_info = self.get_gpu_info()
                if gpu_info:
                    logger.info(f"   GPU数量: {gpu_info.get('device_count', 'N/A')}")
                    logger.info(f"   默认设备: {gpu_info.get('default_device', 'N/A')}")
            else:
                logger.warning("⚠️ CUDA不可用，将使用CPU")

            return result

        except Exception as e:
            logger.error(f"❌ CUDA加速器初始化失败: {e}")
            return False

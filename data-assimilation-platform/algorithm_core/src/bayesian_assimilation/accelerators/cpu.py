"""
CPU加速器
使用OpenMP和BLAS进行CPU优化
"""

import os
import sys
import logging
import numpy as np
from typing import Optional, Any

# 处理相对导入和绝对导入
if __name__ == '__main__':
    # 直接运行时使用绝对导入
    from bayesian_assimilation.accelerators.base import BaseAccelerator, AcceleratorType
else:
    # 作为模块导入时使用相对导入
    from .base import BaseAccelerator, AcceleratorType

logger = logging.getLogger(__name__)


class CPUAccelerator(BaseAccelerator):
    """
    CPU加速器
    支持OpenMP多线程和BLAS矩阵运算优化
    """

    def __init__(self, config: Optional[Any] = None):
        super().__init__(config)
        self.accelerator_type = AcceleratorType.CPU
        self.n_threads = config.get('n_threads', os.cpu_count()) if config else os.cpu_count()
        self.use_openmp = False
        self.use_blas = False
        self._blas_module = None

    def initialize(self) -> bool:
        """
        初始化CPU加速器

        Returns:
            bool: 初始化是否成功
        """
        try:
            self._setup_openmp()
            self._setup_blas()
            self.initialized = True
            logger.info(f"✅ CPU加速器初始化成功: {self.n_threads} 线程")
            logger.info(f"   OpenMP: {'启用' if self.use_openmp else '未启用'}")
            logger.info(f"   BLAS: {'启用' if self.use_blas else '未启用'}")
            return True
        except Exception as e:
            logger.error(f"❌ CPU加速器初始化失败: {e}")
            self.initialized = False
            return False

    def _setup_openmp(self):
        """设置OpenMP多线程支持"""
        try:
            import threadpoolctl
            os.environ['OMP_NUM_THREADS'] = str(self.n_threads)
            os.environ['MKL_NUM_THREADS'] = str(self.n_threads)
            os.environ['OPENBLAS_NUM_THREADS'] = str(self.n_threads)

            with threadpoolctl.threadpool_limits(limits=self.n_threads, user_api='openmp'):
                test_array = np.random.randn(1000, 1000)
                _ = np.dot(test_array, test_array.T)

            self.use_openmp = True
            logger.info(f"   OpenMP已启用，线程数: {self.n_threads}")
        except ImportError:
            logger.warning("⚠️ threadpoolctl未安装，OpenMP可能未完全启用")
        except Exception as e:
            logger.warning(f"⚠️ OpenMP设置失败: {e}")

    def _setup_blas(self):
        """设置BLAS矩阵运算支持"""
        try:
            if hasattr(np, '__cpu_features__'):
                logger.info(f"   NumPy版本: {np.__version__}")

            try:
                import scipy.linalg
                logger.info("   SciPy可用，BLAS加速已启用")
                self.use_blas = True
                self._blas_module = scipy.linalg
            except ImportError:
                logger.warning("⚠️ SciPy未安装，BLAS加速未启用")
                self._blas_module = None

            # 尝试检测OpenBLAS（可选）
            try:
                # 使用__import__动态导入避免Pylance报错
                openblas = __import__('openblas')
                logger.info("   OpenBLAS可用")
                self.use_blas = True
            except (ImportError, AttributeError):
                pass

            # 尝试检测Intel MKL（可选）
            try:
                # 使用__import__动态导入避免Pylance报错
                mkl = __import__('mkl')
                logger.info("   Intel MKL可用")
                self.use_blas = True
            except (ImportError, AttributeError):
                pass

        except Exception as e:
            logger.warning(f"⚠️ BLAS设置失败: {e}")

    def finalize(self):
        """释放CPU加速器资源"""
        if self.use_openmp:
            try:
                import threadpoolctl
                with threadpoolctl.threadpool_limits(limits=1):
                    pass
            except:
                pass
        logger.info("CPU加速器已释放")

    def to_device(self, data: np.ndarray) -> "np.ndarray":
        """
        将数据转移到加速设备（CPU使用numpy数组，无需转移）

        Args:
            data: numpy数组

        Returns:
            numpy数组
        """
        return np.ascontiguousarray(data)

    def to_host(self, data: np.ndarray) -> "np.ndarray":
        """
        将数据从设备移回主机（CPU使用numpy数组，无需转移）

        Args:
            data: numpy数组

        Returns:
            numpy数组
        """
        return np.array(data)

    def matmul(self, A: np.ndarray, B: np.ndarray) -> "np.ndarray":
        """
        矩阵乘法（使用优化的BLAS或OpenMP）

        Args:
            A: 左矩阵
            B: 右矩阵

        Returns:
            结果矩阵
        """
        if self.use_blas and self._blas_module is not None:
            try:
                # 使用NumPy的dot函数，它会自动使用优化的BLAS
                return np.dot(A, B)
            except Exception:
                return np.dot(A, B)
        else:
            return np.dot(A, B)

    def solve(self, A: np.ndarray, b: np.ndarray) -> "np.ndarray":
        """
        求解线性系统 Ax = b

        Args:
            A: 系数矩阵
            b: 右端向量

        Returns:
            解向量
        """
        if self.use_blas and self._blas_module is not None:
            from scipy.linalg import solve
            return solve(A, b, overwrite_a=True, overwrite_b=True, check_finite=False)
        else:
            return np.linalg.solve(A, b)

    def cholesky(self, A: np.ndarray) -> "np.ndarray":
        """
        Cholesky分解

        Args:
            A: 对称正定矩阵

        Returns:
            下三角矩阵
        """
        if self.use_blas and self._blas_module is not None:
            try:
                from scipy.linalg import cho_factor
                self._chol_cache = cho_factor(A, overwrite_a=True, check_finite=False)
                return self._chol_cache # type: ignore
            except Exception:
                return np.linalg.cholesky(A)
        else:
            return np.linalg.cholesky(A)

    def convolve(self, a: np.ndarray, v: np.ndarray, mode: str = 'valid') -> "np.ndarray":
        """
        卷积运算

        Args:
            a: 输入数组
            v: 卷积核
            mode: 卷积模式

        Returns:
            卷积结果
        """
        from scipy.ndimage import convolve1d
        if a.ndim == 3:
            result = np.zeros_like(a)
            for i in range(a.shape[0]):
                result[i] = convolve1d(a[i], v, mode=mode)
            return result
        else:
            return convolve1d(a, v, mode=mode)

    def interpolate(self, data: np.ndarray, factor: int) -> "np.ndarray":
        """
        数据插值放大

        Args:
            data: 输入数据
            factor: 放大因子

        Returns:
            插值后的数据
        """
        from scipy.ndimage import zoom
        zoom_factor = (factor,) * data.ndim
        return zoom(data, zoom_factor, order=1) # type: ignore


class OpenMPAccelerator(CPUAccelerator):
    """
    OpenMP专用加速器
    使用OpenMP进行多线程并行计算
    """

    def __init__(self, config: Optional[Any] = None):
        super().__init__(config)
        self.accelerator_type = AcceleratorType.OPENMP

    def initialize(self) -> bool:
        """初始化OpenMP加速器"""
        try:
            os.environ['OMP_NUM_THREADS'] = str(self.n_threads)
            os.environ['MKL_NUM_THREADS'] = str(self.n_threads)

            self.initialized = True
            logger.info(f"✅ OpenMP加速器初始化成功: {self.n_threads} 线程")
            return True
        except Exception as e:
            logger.error(f"❌ OpenMP加速器初始化失败: {e}")
            return False


class BLASAccelerator(CPUAccelerator):
    """
    BLAS专用加速器
    使用BLAS进行矩阵运算优化
    """

    def __init__(self, config: Optional[Any] = None):
        super().__init__(config)
        self.accelerator_type = AcceleratorType.BLAS
        self._blas_module = None

    def initialize(self) -> bool:
        """初始化BLAS加速器"""
        try:
            import scipy.linalg as blas
            self._blas_module = blas

            self.initialized = True
            logger.info("✅ BLAS加速器初始化成功")
            logger.info(f"   BLAS后端: scipy.linalg")
            return True
        except ImportError:
            logger.error("❌ SciPy未安装，无法使用BLAS加速")
            return False
        except Exception as e:
            logger.error(f"❌ BLAS加速器初始化失败: {e}")
            return False

    def matmul(self, A: np.ndarray, B: np.ndarray) -> "np.ndarray":
        """使用BLAS进行矩阵乘法"""
        if self._blas_module is not None:
            try:
                # 使用NumPy的dot函数，它会自动使用优化的BLAS
                return np.dot(A, B)
            except Exception:
                return np.dot(A, B)
        else:
            return np.dot(A, B)

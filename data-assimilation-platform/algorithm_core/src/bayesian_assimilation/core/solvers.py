"""
线性求解器模块
实现各种线性方程组求解算法
"""

import os
import sys

SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import numpy as np
from scipy.sparse.linalg import LinearOperator, cg, gmres, bicgstab
from typing import Optional, Tuple, Callable, Dict, Any, Union
import logging

logger = logging.getLogger(__name__)


class LinearSolver:
    """
    线性求解器基类
    """

    def __init__(self, max_iter: int = 200, tol: float = 1e-6):
        self.max_iter = max_iter
        self.tol = tol
        self.stats: Dict[str, Any] = {}

    def solve(self, A, b, x0=None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        求解线性方程组 Ax = b

        Args:
            A: 系数矩阵或线性算子
            b: 右端向量
            x0: 初始猜测

        Returns:
            x: 解向量
            stats: 求解统计信息
        """
        raise NotImplementedError("子类必须实现 solve 方法")


class CGSolver(LinearSolver):
    """
    共轭梯度求解器
    适用于对称正定矩阵
    """

    def solve(self, A, b, x0=None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """使用共轭梯度法求解"""
        self.stats = {}

        if x0 is None:
            x0 = np.zeros_like(b)

        try:
            x, info = cg(A, b, x0=x0, maxiter=self.max_iter, rtol=self.tol)

            self.stats['iterations'] = info if info >= 0 else self.max_iter
            self.stats['converged'] = info == 0
            self.stats['method'] = 'cg'

            if info > 0:
                logger.warning(f"CG 求解器在 {info} 次迭代后未收敛")
            elif info < 0:
                logger.error(f"CG 求解器出现错误: {info}")

            return x, self.stats

        except Exception as e:
            logger.error(f"CG 求解器失败: {e}")
            return x0, {'converged': False, 'error': str(e), 'method': 'cg'}


class GMRESSolver(LinearSolver):
    """
    GMRES求解器
    适用于非对称矩阵
    """

    def __init__(self, max_iter: int = 200, tol: float = 1e-6, restart: int = 200):
        super().__init__(max_iter, tol)
        self.restart = restart

    def solve(self, A, b, x0=None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """使用GMRES法求解"""
        self.stats = {}

        if x0 is None:
            x0 = np.zeros_like(b)

        try:
            x, info = gmres(A, b, x0=x0, maxiter=self.max_iter, rtol=self.tol, restart=self.restart)

            self.stats['iterations'] = info if info >= 0 else self.max_iter
            self.stats['converged'] = info == 0
            self.stats['method'] = 'gmres'
            self.stats['restart'] = self.restart

            if info > 0:
                logger.warning(f"GMRES 求解器在 {info} 次迭代后未收敛")
            elif info < 0:
                logger.error(f"GMRES 求解器出现错误: {info}")

            return x, self.stats

        except Exception as e:
            logger.error(f"GMRES 求解器失败: {e}")
            return x0, {'converged': False, 'error': str(e), 'method': 'gmres'}


class BicgstabSolver(LinearSolver):
    """
    BiCGSTAB求解器
    适用于非对称矩阵，内存效率更高
    """

    def solve(self, A, b, x0=None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """使用BiCGSTAB法求解"""
        self.stats = {}

        if x0 is None:
            x0 = np.zeros_like(b)

        try:
            x, info = bicgstab(A, b, x0=x0, maxiter=self.max_iter, rtol=self.tol)

            self.stats['iterations'] = info if info >= 0 else self.max_iter
            self.stats['converged'] = info == 0
            self.stats['method'] = 'bicgstab'

            if info > 0:
                logger.warning(f"BiCGSTAB 求解器在 {info} 次迭代后未收敛")
            elif info < 0:
                logger.error(f"BiCGSTAB 求解器出现错误: {info}")

            return x, self.stats

        except Exception as e:
            logger.error(f"BiCGSTAB 求解器失败: {e}")
            return x0, {'converged': False, 'error': str(e), 'method': 'bicgstab'}


class DirectSolver(LinearSolver):
    """
    直接求解器
    使用numpy的直接求解方法
    """

    def solve(self, A, b, x0=None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """使用直接方法求解"""
        self.stats = {}

        try:
            if hasattr(A, 'toarray'):
                A_dense = A.toarray()
            else:
                A_dense = np.asarray(A)

            x = np.linalg.solve(A_dense, b)

            self.stats['converged'] = True
            self.stats['method'] = 'direct'
            self.stats['iterations'] = 1

            return x, self.stats

        except np.linalg.LinAlgError as e:
            logger.error(f"直接求解器失败: {e}")
            return np.zeros_like(b), {'converged': False, 'error': str(e), 'method': 'direct'}
        except Exception as e:
            logger.error(f"直接求解器失败: {e}")
            return np.zeros_like(b), {'converged': False, 'error': str(e), 'method': 'direct'}


class SolverFactory:
    """
    求解器工厂类
    根据名称创建不同类型的求解器
    """

    @staticmethod
    def create(
        solver_type: str,
        max_iter: int = 200,
        tol: float = 1e-6,
        **kwargs
    ) -> LinearSolver:
        """
        创建求解器

        Args:
            solver_type: 求解器类型 ('cg', 'gmres', 'bicgstab', 'direct')
            max_iter: 最大迭代次数
            tol: 收敛容差
            **kwargs: 额外参数

        Returns:
            求解器实例
        """
        solver_type = solver_type.lower()

        if solver_type == 'cg':
            return CGSolver(max_iter, tol)
        elif solver_type == 'gmres':
            restart = kwargs.get('restart', 200)
            return GMRESSolver(max_iter, tol, restart)
        elif solver_type == 'bicgstab':
            return BicgstabSolver(max_iter, tol)
        elif solver_type == 'direct':
            return DirectSolver(max_iter, tol)
        else:
            raise ValueError(f"未知的求解器类型: {solver_type}")


def solve_linear_system(
    A,
    b: np.ndarray,
    method: str = 'cg',
    x0: Optional[np.ndarray] = None,
    max_iter: int = 200,
    tol: float = 1e-6,
    **kwargs


) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    求解线性方程组的便捷函数

    Args:
        A: 系数矩阵或线性算子
        b: 右端向量
        method: 求解方法 ('cg', 'gmres', 'bicgstab', 'direct')
        x0: 初始猜测
        max_iter: 最大迭代次数
        tol: 收敛容差
        **kwargs: 额外参数

    Returns:
        x: 解向量
        stats: 求解统计信息
    """
    solver = SolverFactory.create(method, max_iter, tol, **kwargs)
    return solver.solve(A, b, x0)


def build_linear_operator(
    apply_func: Callable[[np.ndarray], np.ndarray],
    shape: Tuple[int, int]


) -> LinearOperator:
    """
    构建线性算子

    Args:
        apply_func: 应用函数，输入向量返回向量
        shape: 算子形状 (n, n)

    Returns:
        LinearOperator 实例
    """
    return LinearOperator(shape=shape, matvec=apply_func)  # type: ignore


class Preconditioner:
    """
    预条件算子基类
    """

    def __init__(self, A):
        self.A = A

    def apply(self, x: np.ndarray) -> np.ndarray:
        """应用预条件"""
        raise NotImplementedError("子类必须实现 apply 方法")


class JacobiPreconditioner(Preconditioner):
    """
    Jacobi预条件算子
    """

    def apply(self, x: np.ndarray) -> np.ndarray:
        """应用Jacobi预条件"""
        if hasattr(self.A, 'diagonal'):
            diag = self.A.diagonal()
        elif hasattr(self.A, 'diag'):
            diag = self.A.diag()
        else:
            diag = np.diag(self.A)

        diag[diag == 0] = 1e-10
        return x / diag


class IdentityPreconditioner(Preconditioner):
    """
    单位预条件算子（无预条件）
    """

    def apply(self, x: np.ndarray) -> np.ndarray:
        """返回原始向量"""
        return x

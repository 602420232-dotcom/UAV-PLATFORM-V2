"""FastAPI 全局异常处理器模块.

提供统一的全局异常拦截和响应格式化，确保所有未处理异常
都返回一致的 JSON 错误响应，同时记录详细的日志信息。

使用方式::

    from app.core.error_handler import register_error_handlers

    app = FastAPI()
    register_error_handlers(app)
"""

from __future__ import annotations

import traceback
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from loguru import logger


class ErrorResponse:
    """统一错误响应格式.

    Attributes:
        code: 业务错误码，与 HTTP 状态码对齐.
        message: 用户可读的错误摘要.
        detail: 错误的详细描述（开发调试用）.
        timestamp: 错误发生的 UTC ISO 时间戳.
    """

    def __init__(
        self,
        code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        message: str = "服务器内部错误",
        detail: str = "",
    ) -> None:
        self.code = code
        self.message = message
        self.detail = detail
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """转换为可序列化的字典."""
        return {
            "code": self.code,
            "message": self.message,
            "detail": self.detail,
            "timestamp": self.timestamp,
        }


def _build_response(
    code: int,
    message: str,
    detail: str,
    log_level: str = "error",
) -> JSONResponse:
    """构建统一的 JSON 错误响应并记录日志.

    Args:
        code: HTTP 状态码.
        message: 用户可读的错误消息.
        detail: 错误详情.
        log_level: 日志级别 (info / warning / error / critical).

    Returns:
        JSONResponse: 格式化的错误响应.
    """
    response = ErrorResponse(code=code, message=message, detail=detail)
    log_msg = f"[{code}] {message}"
    if detail:
        log_msg += f" | detail: {detail}"

    getattr(logger, log_level)(log_msg)
    return JSONResponse(
        status_code=code,
        content=response.to_dict(),
    )


def _value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """处理 ValueError: 参数值不合法."""
    return _build_response(
        code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="参数值不合法",
        detail=str(exc),
        log_level="warning",
    )


def _type_error_handler(request: Request, exc: TypeError) -> JSONResponse:
    """处理 TypeError: 类型错误."""
    return _build_response(
        code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="数据类型错误",
        detail=str(exc),
        log_level="warning",
    )


def _key_error_handler(request: Request, exc: KeyError) -> JSONResponse:
    """处理 KeyError: 缺少必要的字段或键."""
    return _build_response(
        code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="缺少必要的字段",
        detail=f"缺少键: {exc}",
        log_level="warning",
    )


def _index_error_handler(request: Request, exc: IndexError) -> JSONResponse:
    """处理 IndexError: 索引越界."""
    return _build_response(
        code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="索引越界",
        detail=str(exc),
        log_level="warning",
    )


def _file_not_found_handler(request: Request, exc: FileNotFoundError) -> JSONResponse:
    """处理 FileNotFoundError: 文件或资源未找到."""
    return _build_response(
        code=status.HTTP_404_NOT_FOUND,
        message="请求的资源未找到",
        detail=str(exc),
        log_level="warning",
    )


def _numpy_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理 NumPy 相关错误（通过异常类型名称匹配）."""
    exc_name = type(exc).__name__
    return _build_response(
        code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message=f"数值计算错误 ({exc_name})",
        detail=str(exc),
        log_level="error",
    )


def _catch_all_handler(request: Request, exc: Exception) -> JSONResponse:
    """兜底异常处理器: 捕获所有未被特定处理器匹配的异常."""
    stack_trace = traceback.format_exc()
    logger.error(
        "未处理的异常 | path={} | method={} | type={} | message={}\n{}",
        request.url.path,
        request.method,
        type(exc).__name__,
        str(exc),
        stack_trace,
    )
    return _build_response(
        code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="服务器内部错误",
        detail=f"{type(exc).__name__}: {str(exc)}",
        log_level="critical",
    )


def register_error_handlers(app: FastAPI) -> None:
    """向 FastAPI 应用注册所有全局异常处理器.

    Args:
        app: FastAPI 应用实例.
    """
    # 标准异常
    app.add_exception_handler(ValueError, _value_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(TypeError, _type_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(KeyError, _key_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(IndexError, _index_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(FileNotFoundError, _file_not_found_handler)  # type: ignore[arg-type]

    # NumPy 相关异常（运行时检测是否安装了 numpy）
    try:
        import numpy as np

        numpy_errors: list[type] = [
            np.linalg.LinAlgError,
        ]
        # np.AxisError may not exist in all numpy versions
        if hasattr(np, "AxisError"):
            numpy_errors.append(np.AxisError)
        # NumPy 2.0+ 的异常类型
        if hasattr(np, "exceptions"):
            numpy_exceptions = getattr(np.exceptions, "__dict__", {})
            for _name, _obj in numpy_exceptions.items():
                if isinstance(_obj, type) and issubclass(_obj, Exception):
                    numpy_errors.append(_obj)

        for err_cls in numpy_errors:
            app.add_exception_handler(err_cls, _numpy_error_handler)  # type: ignore[arg-type]

        logger.info("已注册 NumPy 异常处理器: {}", [e.__name__ for e in numpy_errors])
    except ImportError:
        logger.warning("numpy 未安装，跳过 NumPy 异常处理器注册")

    # 兜底处理器
    app.add_exception_handler(Exception, _catch_all_handler)  # type: ignore[arg-type]

    logger.info("全局异常处理器注册完成")

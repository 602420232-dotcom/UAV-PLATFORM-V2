"""
统一错误处理框架

提供标准化的错误码、异常类和结果封装，供各服务模块统一使用。


使用示例:
    from common_utils.errors import AppError, ErrorCode, Result

    # 抛出业务异常
    raise AppError(ErrorCode.TASK_NOT_FOUND, task_id="task_001")

    # 返回结果
    return Result.ok(data={"path": [...]})
    return Result.fail(ErrorCode.PLANNING_FAILED, "无法找到路径")
"""

from enum import Enum
from typing import Any, Dict, Optional


class ErrorCode(Enum):
    """统一错误码枚举"""

    SUCCESS = (0, "成功")

    # 通用错误 (1000-1999)
    UNKNOWN_ERROR = (1000, "未知错误")
    VALIDATION_ERROR = (1001, "参数校验失败")
    UNAUTHORIZED = (1002, "未授权")
    FORBIDDEN = (1003, "禁止访问")
    NOT_FOUND = (1004, "资源不存在")
    INTERNAL_ERROR = (1005, "内部服务器错误")
    SERVICE_UNAVAILABLE = (1006, "服务不可用")

    # 任务相关 (2000-2999)
    TASK_NOT_FOUND = (2000, "任务不存在")
    TASK_SUBMIT_FAILED = (2001, "任务提交失败")
    TASK_INVALID_TYPE = (2002, "无效的任务类型")

    # 路径规划 (3000-3999)
    PLANNING_FAILED = (3000, "路径规划失败")
    START_OUT_OF_BOUNDS = (3001, "起点超出范围")
    GOAL_OUT_OF_BOUNDS = (3002, "终点超出范围")
    START_COLLISION = (3003, "起点与障碍物碰撞")
    GOAL_COLLISION = (3004, "终点与障碍物碰撞")

    # 联邦学习 (4000-4999)
    FL_CLIENT_NOT_FOUND = (4000, "联邦学习客户端不存在")
    FL_AGGREGATION_FAILED = (4001, "联邦学习聚合失败")

    # 数据同化 (5000-5999)
    ASSIMILATION_FAILED = (5000, "数据同化失败")
    DATA_SOURCE_ERROR = (5001, "数据源错误")

    # Docker/部署 (6000-6999)
    DOCKER_UNAVAILABLE = (6000, "Docker 不可用")
    CONTAINER_ACTION_FAILED = (6001, "容器操作失败")

    @property
    def code(self) -> int:
        return self.value[0]

    @property
    def message(self) -> str:
        return self.value[1]

    @classmethod
    def from_code(cls, code: int) -> "ErrorCode":
        """根据错误码查找 ErrorCode"""
        for ec in cls:
            if ec.code == code:
                return ec
        return cls.UNKNOWN_ERROR


class AppError(Exception):
    """应用异常基类"""

    def __init__(self, error_code: ErrorCode, detail: Optional[str] = None, **kwargs):
        self.error_code = error_code
        self.detail = detail or error_code.message
        self.extra = kwargs
        super().__init__(self.detail)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "code": self.error_code.code,
            "message": self.error_code.message,
            "detail": self.detail,
        }
        if self.extra:
            result["extra"] = self.extra
        return result


class Result:
    """统一返回结果封装"""

    def __init__(self, success: bool, error_code: ErrorCode = ErrorCode.SUCCESS,
                 data: Any = None, message: Optional[str] = None):
        self.success = success
        self.error_code = error_code
        self.data = data
        self.message = message or error_code.message

    @classmethod
    def ok(cls, data: Any = None, message: str = "success") -> "Result":
        return cls(success=True, error_code=ErrorCode.SUCCESS,
                   data=data, message=message)

    @classmethod
    def fail(cls, error_code: ErrorCode, detail: Optional[str] = None,
             data: Any = None) -> "Result":
        return cls(success=False, error_code=error_code,
                   data=data, message=detail or error_code.message)

    @classmethod
    def from_exception(cls, e: Exception) -> "Result":
        if isinstance(e, AppError):
            return cls.fail(e.error_code, e.detail)
        return cls.fail(ErrorCode.INTERNAL_ERROR, str(e))

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "success": self.success,
            "code": self.error_code.code,
            "message": self.message,
        }
        if self.data is not None:
            result["data"] = self.data
        return result


def handle_errors(func):
    """装饰器：统一处理函数中的异常"""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AppError as e:
            return Result.fail(e.error_code, e.detail).to_dict()
        except Exception as e:
            return Result.fail(ErrorCode.INTERNAL_ERROR, str(e)).to_dict()
    return wrapper

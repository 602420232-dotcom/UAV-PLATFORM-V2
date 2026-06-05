"""
Demo 模式模块

提供 Demo 用户认证、API 调用频率限制和会话管理功能。


使用示例:
    from common_utils.demo_mode import DemoModeService

    # 初始化
    demo_service = DemoModeService(redis_client=redis)

    # 检查 API 调用频率
    if demo_service.check_rate_limit(user_id, "read"):
        # 允许访问
    else:
        # 拒绝访问
"""

from typing import Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import time


class DemoError(Exception):
    """Demo 模式基础异常"""

    def __init__(self, message: str, error_code: str = "DEMO_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class DemoRateLimitError(DemoError):
    """API 调用超限异常"""

    def __init__(self, message: str = "API 调用超限"):
        super().__init__(message, "AUTH_008")


class DemoSessionLimitError(DemoError):
    """Demo 并发会话超限异常"""

    def __init__(self, message: str = "Demo 并发会话超限"):
        super().__init__(message, "AUTH_009")


class DemoSessionExpiredError(DemoError):
    """Demo 会话已过期异常"""

    def __init__(self, message: str = "Demo 会话已过期"):
        super().__init__(message, "AUTH_010")


@dataclass
class DemoSessionInfo:
    """Demo 会话信息"""

    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    purpose: Optional[str] = None
    api_calls_read: int = 0
    api_calls_write: int = 0


@dataclass
class RateLimitConfig:
    """频率限制配置"""

    read_limit: int = 1000
    write_limit: int = 100
    time_window: int = 3600
    max_concurrent_sessions: int = 1
    session_duration: int = 86400


class DemoModeService:
    """Demo 模式服务类"""

    def __init__(
        self,
        redis_client: Any,
        config: Optional[RateLimitConfig] = None,
    ):
        """
        初始化 Demo 模式服务

        Args:
            redis_client: Redis 客户端
            config: 频率限制配置
        """
        self.redis_client = redis_client
        self.config = config or RateLimitConfig()

    def _get_rate_limit_key(
        self,
        user_id: str,
        action_type: str,
        timestamp: Optional[int] = None,
    ) -> str:
        """获取频率限制 Redis 键"""
        if timestamp is None:
            timestamp = int(time.time())
        hour_bucket = timestamp // self.config.time_window
        return f"ratelimit:demo:{user_id}:{hour_bucket}:{action_type}"

    def _get_session_key(self, user_id: str) -> str:
        """获取会话 Redis 键"""
        return f"demo:session:{user_id}"

    def _get_active_sessions_key(self) -> str:
        """获取活跃会话 Redis 键"""
        return "demo:sessions:active"

    def check_rate_limit(
        self,
        user_id: str,
        action_type: str = "read",
        increment: bool = True,
    ) -> bool:
        """
        检查 API 调用频率限制

        Args:
            user_id: 用户 ID
            action_type: 操作类型 ('read' 或 'write')
            increment: 是否增加计数

        Returns:
            bool: 是否在限制范围内
        """
        if not self.redis_client:
            return True

        try:
            limit = (
                self.config.write_limit
                if action_type == "write"
                else self.config.read_limit
            )
            key = self._get_rate_limit_key(user_id, action_type)

            if increment:
                current = self.redis_client.incr(key)
                if current == 1:
                    self.redis_client.expire(key, self.config.time_window)
                return current <= limit
            else:
                current = self.redis_client.get(key)
                return (int(current) if current else 0) <= limit
        except Exception as e:  # noqa: F841
            return True

    def get_rate_limit_remaining(
        self,
        user_id: str,
        action_type: str = "read",
    ) -> int:
        """
        获取剩余 API 调用次数

        Args:
            user_id: 用户 ID
            action_type: 操作类型

        Returns:
            int: 剩余调用次数
        """
        if not self.redis_client:
            return 999999

        try:
            limit = (
                self.config.write_limit
                if action_type == "write"
                else self.config.read_limit
            )
            key = self._get_rate_limit_key(user_id, action_type)
            current = self.redis_client.get(key)
            current = int(current) if current else 0
            return max(0, limit - current)
        except Exception as e:  # noqa: F841
            return 999999

    def create_demo_session(
        self,
        user_id: str,
        session_id: str,
        ip_address: Optional[str] = None,
        purpose: Optional[str] = None,
    ) -> DemoSessionInfo:
        """
        创建 Demo 会话

        Args:
            user_id: 用户 ID
            session_id: 会话 ID
            ip_address: IP 地址
            purpose: 演示目的

        Returns:
            DemoSessionInfo: 会话信息

        Raises:
            DemoSessionLimitError: 并发会话超限
        """
        if not self.redis_client:
            raise DemoError("Redis 客户端未配置")

        now = datetime.now()
        expires_at = now + timedelta(seconds=self.config.session_duration)

        try:
            session_key = self._get_session_key(user_id)
            existing_session = self.redis_client.get(session_key)

            if existing_session:
                self.redis_client.delete(session_key)

            active_count = self.redis_client.scard(self._get_active_sessions_key())
            if active_count >= self.config.max_concurrent_sessions:
                raise DemoSessionLimitError()

            session_info = DemoSessionInfo(
                session_id=session_id,
                user_id=user_id,
                created_at=now,
                expires_at=expires_at,
                ip_address=ip_address,
                purpose=purpose,
                api_calls_read=0,
                api_calls_write=0,
            )

            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "created_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
                "ip_address": ip_address or "",
                "purpose": purpose or "",
            }

            self.redis_client.setex(
                session_key,
                self.config.session_duration,
                str(session_data),
            )
            self.redis_client.sadd(self._get_active_sessions_key(), user_id)
            self.redis_client.expire(
                self._get_active_sessions_key(),
                self.config.session_duration,
            )

            return session_info
        except DemoSessionLimitError:
            raise
        except Exception as e:
            raise DemoError(f"创建 Demo 会话失败: {str(e)}")

    def validate_demo_session(
        self,
        user_id: str,
        session_id: Optional[str] = None,
    ) -> DemoSessionInfo:
        """
        验证 Demo 会话

        Args:
            user_id: 用户 ID
            session_id: 会话 ID（可选）

        Returns:
            DemoSessionInfo: 会话信息

        Raises:
            DemoSessionExpiredError: 会话已过期
        """
        if not self.redis_client:
            raise DemoError("Redis 客户端未配置")

        try:
            session_key = self._get_session_key(user_id)
            session_data = self.redis_client.get(session_key)

            if not session_data:
                raise DemoSessionExpiredError()

            import ast
            data = ast.literal_eval(session_data.decode() if isinstance(session_data, bytes) else session_data)

            expires_at = datetime.fromisoformat(data.get("expires_at", ""))
            if datetime.now() > expires_at:
                self.redis_client.delete(session_key)
                self.redis_client.srem(self._get_active_sessions_key(), user_id)
                raise DemoSessionExpiredError()

            return DemoSessionInfo(
                session_id=data.get("session_id", ""),
                user_id=data.get("user_id", ""),
                created_at=datetime.fromisoformat(data.get("created_at", "")),
                expires_at=expires_at,
                ip_address=data.get("ip_address"),
                purpose=data.get("purpose"),
                api_calls_read=0,
                api_calls_write=0,
            )
        except DemoSessionExpiredError:
            raise
        except Exception as e:
            raise DemoError(f"验证 Demo 会话失败: {str(e)}")

    def end_demo_session(self, user_id: str) -> None:
        """
        结束 Demo 会话

        Args:
            user_id: 用户 ID
        """
        if not self.redis_client:
            return

        try:
            session_key = self._get_session_key(user_id)
            self.redis_client.delete(session_key)
            self.redis_client.srem(self._get_active_sessions_key(), user_id)
        except Exception as e:  # noqa: F841
            pass

    def get_active_session_count(self) -> int:
        """
        获取活跃 Demo 会话数

        Returns:
            int: 活跃会话数
        """
        if not self.redis_client:
            return 0

        try:
            return self.redis_client.scard(self._get_active_sessions_key())
        except Exception as e:  # noqa: F841
            return 0

    def record_api_call(
        self,
        user_id: str,
        action_type: str = "read",
    ) -> bool:
        """
        记录 API 调用并检查限制

        Args:
            user_id: 用户 ID
            action_type: 操作类型

        Returns:
            bool: 是否允许调用

        Raises:
            DemoRateLimitError: 调用超限
        """
        allowed = self.check_rate_limit(user_id, action_type, increment=True)
        if not allowed:
            raise DemoRateLimitError()
        return True

    def create_fastapi_dependency(
        self,
        check_rate_limit: bool = True,
        action_type: str = "read",
    ):
        """
        创建 FastAPI 依赖注入函数

        Args:
            check_rate_limit: 是否检查频率限制
            action_type: 操作类型

        Returns:
            可用于 FastAPI Depends 的函数
        """
        try:
            from fastapi import Header, HTTPException, status

            def dependency(
                x_demo_user_id: Optional[str] = Header(None),
                x_demo_session_id: Optional[str] = Header(None),
            ):
                if not x_demo_user_id:
                    return None

                try:
                    session_info = self.validate_demo_session(
                        x_demo_user_id,
                        x_demo_session_id,
                    )

                    if check_rate_limit:
                        self.record_api_call(x_demo_user_id, action_type)

                    return session_info
                except DemoError as e:
                    status_code = status.HTTP_429_TOO_MANY_REQUESTS
                    if e.error_code == "AUTH_010":
                        status_code = status.HTTP_401_UNAUTHORIZED
                    raise HTTPException(
                        status_code=status_code,
                        detail={
                            "code": e.error_code,
                            "message": e.message
                        },
                    )

            return dependency
        except ImportError:

            def dependency(user_id: str, session_id: Optional[str] = None):
                session_info = self.validate_demo_session(user_id, session_id)
                if check_rate_limit:
                    self.record_api_call(user_id, action_type)
                return session_info
            return dependency

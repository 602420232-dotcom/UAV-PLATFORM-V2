"""
JWT 认证模块

提供 JWT 验证、黑名单检查和用户信息提取功能。
与 Java 后端的 JWT 格式兼容，支持 HS512 算法。


使用示例:
    from common_utils.jwt_auth import JwtAuth, TokenType

    # 初始化
    # 生产环境应从环境变量读取密钥: auth = JwtAuth(secret_key=os.getenv("JWT_SECRET_KEY"))
    auth = JwtAuth(secret_key=os.getenv("JWT_SECRET_KEY", ""))

    # 验证令牌
    claims = auth.verify_token(token)

    # FastAPI 依赖注入
    from fastapi import Depends
    user = Depends(auth.get_current_user)
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

import jwt
from jwt import ExpiredSignatureError, InvalidSignatureError, DecodeError


class TokenType(Enum):
    """Token 类型枚举"""

    ACCESS = "access"
    REFRESH = "refresh"


class JwtAuthError(Exception):
    """JWT 认证基础异常"""

    def __init__(self, message: str, error_code: str = "AUTH_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class TokenMissingError(JwtAuthError):
    """Token 缺失异常"""

    def __init__(self, message: str = "Token 缺失"):
        super().__init__(message, "AUTH_001")


class TokenInvalidError(JwtAuthError):
    """Token 格式错误异常"""

    def __init__(self, message: str = "Token 格式错误"):
        super().__init__(message, "AUTH_002")


class TokenExpiredError(JwtAuthError):
    """Token 已过期异常"""

    def __init__(self, message: str = "Token 已过期"):
        super().__init__(message, "AUTH_003")


class TokenSignatureError(JwtAuthError):
    """Token 签名无效异常"""

    def __init__(self, message: str = "Token 签名无效"):
        super().__init__(message, "AUTH_004")


class TokenBlacklistError(JwtAuthError):
    """Token 已被撤销异常"""

    def __init__(self, message: str = "Token 已被撤销"):
        super().__init__(message, "AUTH_005")


class RefreshTokenInvalidError(JwtAuthError):
    """Refresh Token 无效异常"""

    def __init__(self, message: str = "Refresh Token 无效"):
        super().__init__(message, "AUTH_006")


@dataclass
class UserClaims:
    """用户声明数据类"""

    user_id: str
    username: str
    roles: List[str]
    tenant_id: Optional[str] = None
    token_type: Optional[str] = None
    token_id: Optional[str] = None
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_demo: bool = False
    extra: Dict[str, Any] | None = None

    def __post_init__(self):
        if self.extra is None:
            self.extra = {}
        if self.roles is None:
            self.roles = []


class JwtAuth:
    """JWT 认证主类"""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS512",
        issuer: Optional[str] = None,
        audience: Optional[str] = None,
        redis_client: Any = None,
        access_token_ttl: int = 7200,
        refresh_token_ttl: int = 2592000,
    ):
        """
        初始化 JWT 认证器

        Args:
            secret_key: JWT 密钥
            algorithm: 加密算法，默认 HS512
            issuer: 签发者
            audience: 受众
            redis_client: Redis 客户端（用于黑名单）
            access_token_ttl: Access Token 有效期（秒）
            refresh_token_ttl: Refresh Token 有效期（秒）
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.issuer = issuer
        self.audience = audience
        self.redis_client = redis_client
        self.access_token_ttl = access_token_ttl
        self.refresh_token_ttl = refresh_token_ttl

    def _get_blacklist_key(self, token_type: TokenType, token_id: str) -> str:
        """获取黑名单 Redis 键"""
        return f"blacklist:{token_type.value}:{token_id}"

    def _get_user_blacklist_key(self, user_id: str) -> str:
        """获取用户黑名单 Redis 键"""
        return f"blacklist:user:{user_id}"

    def add_to_blacklist(
        self,
        token_id: str,
        token_type: TokenType,
        user_id: str,
        expires_in: int,
        reason: Optional[str] = None,
    ) -> None:
        """
        将 Token 添加到黑名单

        Args:
            token_id: Token ID (JTI)
            token_type: Token 类型
            user_id: 用户 ID
            expires_in: 剩余有效期（秒）
            reason: 撤销原因
        """
        if not self.redis_client:
            return

        try:
            key = self._get_blacklist_key(token_type, token_id)
            value = {"user_id": user_id, "reason": reason or ""}
            self.redis_client.setex(key, expires_in, str(value))

            user_key = self._get_user_blacklist_key(user_id)
            self.redis_client.sadd(user_key, token_id)
            self.redis_client.expire(user_key, expires_in)
        except Exception as e:
            raise JwtAuthError(f"添加黑名单失败: {str(e)}")

    def is_blacklisted(self, token_id: str, token_type: TokenType) -> bool:
        """
        检查 Token 是否在黑名单中

        Args:
            token_id: Token ID (JTI)
            token_type: Token 类型

        Returns:
            bool: 是否在黑名单中
        """
        if not self.redis_client:
            return False

        try:
            key = self._get_blacklist_key(token_type, token_id)
            return self.redis_client.exists(key) > 0
        except Exception as e:  # noqa: F841
            return False

    def verify_token(
        self,
        token: str,
        token_type: Optional[TokenType] = None,
        check_blacklist: bool = True,
    ) -> Dict[str, Any]:
        """
        验证 JWT Token

        Args:
            token: JWT Token
            token_type: 预期的 Token 类型，None 表示不检查
            check_blacklist: 是否检查黑名单

        Returns:
            Dict[str, Any]: 解码后的声明

        Raises:
            TokenMissingError: Token 缺失
            TokenInvalidError: Token 格式错误
            TokenExpiredError: Token 已过期
            TokenSignatureError: Token 签名无效
            TokenBlacklistError: Token 已被撤销
        """
        if not token:
            raise TokenMissingError()

        try:
            options = {}
            if self.issuer:
                options["iss"] = self.issuer
            if self.audience:
                options["aud"] = self.audience

            claims = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_aud": self.audience is not None},
                **options,
            )

            if token_type and claims.get("token_type") != token_type.value:
                raise TokenInvalidError(f"Token 类型不匹配，期望 {token_type.value}")

            token_id = claims.get("jti")
            if token_id and check_blacklist:
                actual_type = TokenType(claims.get("token_type", "access"))
                if self.is_blacklisted(token_id, actual_type):
                    raise TokenBlacklistError()

            return claims

        except ExpiredSignatureError:
            raise TokenExpiredError()
        except InvalidSignatureError:
            raise TokenSignatureError()
        except DecodeError:
            raise TokenInvalidError()
        except TokenBlacklistError:
            raise
        except Exception as e:
            raise JwtAuthError(f"Token 验证失败: {str(e)}")

    def extract_user_claims(self, claims: Dict[str, Any]) -> UserClaims:
        """
        从声明中提取用户信息

        Args:
            claims: JWT 声明

        Returns:
            UserClaims: 用户声明对象
        """
        return UserClaims(
            user_id=str(claims.get("sub", "")),
            username=claims.get("username", ""),
            roles=claims.get("roles", []),
            tenant_id=claims.get("tenant_id"),
            token_type=claims.get("token_type"),
            token_id=claims.get("jti"),
            issued_at=(
                datetime.fromtimestamp(claims["iat"]) if claims.get("iat") else None
            ),
            expires_at=(
                datetime.fromtimestamp(claims["exp"]) if claims.get("exp") else None
            ),
            is_demo=any("ROLE_DEMO" in str(role) for role in claims.get("roles", [])),
            extra={k: v for k, v in claims.items() if k not in [
                "sub", "username", "roles", "tenant_id", "token_type", "jti", "iat", "exp"
            ]},
        )

    def get_current_user(
        self,
        token: str,
        required_roles: Optional[List[str]] = None,
    ) -> UserClaims:
        """
        获取当前用户（用于 FastAPI 依赖注入）

        Args:
            token: JWT Token
            required_roles: 必需的角色列表

        Returns:
            UserClaims: 用户声明对象

        Raises:
            JwtAuthError: 认证失败
        """
        claims = self.verify_token(token, TokenType.ACCESS)
        user_claims = self.extract_user_claims(claims)

        if required_roles:
            user_roles = set(user_claims.roles)
            required = set(required_roles)
            if not required.issubset(user_roles):
                raise JwtAuthError("权限不足", "AUTH_ERROR")

        return user_claims

    def extract_token_from_header(self, auth_header: Optional[str]) -> Optional[str]:
        """
        从 Authorization 头中提取 Token

        Args:
            auth_header: Authorization 头

        Returns:
            Optional[str]: Token，None 表示未找到
        """
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        return parts[1]

    def create_fastapi_dependency(
        self,
        required_roles: Optional[List[str]] = None,
    ):
        """
        创建 FastAPI 依赖注入函数

        Args:
            required_roles: 必需的角色列表

        Returns:
            可用于 FastAPI Depends 的函数
        """
        try:
            from fastapi import Header, HTTPException, status

            def dependency(  # type: ignore[reportRedeclaration]
                    authorization: Optional[str] = Header(None)):
                token = self.extract_token_from_header(authorization)
                if not token:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail={
                            "code": "AUTH_001",
                            "message": "Token 缺失"
                        },
                        headers={"WWW-Authenticate": "Bearer"},
                    )

                try:
                    return self.get_current_user(token, required_roles)
                except JwtAuthError as e:
                    status_code = status.HTTP_401_UNAUTHORIZED
                    if e.error_code == "AUTH_ERROR":
                        status_code = status.HTTP_403_FORBIDDEN
                    raise HTTPException(
                        status_code=status_code,
                        detail={
                            "code": e.error_code,
                            "message": e.message
                        },
                        headers={"WWW-Authenticate": "Bearer"},
                    )

            return dependency
        except ImportError:

            def dependency(token: str):  # type: ignore[reportRedeclaration]
                return self.get_current_user(token, required_roles)
            return dependency

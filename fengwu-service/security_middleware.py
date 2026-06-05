"""
风乌服务安全中间件

提供 API Key 和 JWT 双重认证机制。
"""
import logging
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from typing import Optional

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


class SecurityMiddleware:
    """
    安全中间件 - API Key + JWT 双重验证

    认证顺序：
    1. 检查 X-API-Key 头（简单场景）
    2. 检查 Authorization: Bearer <jwt> 头（标准场景）
    """

    def __init__(self):
        self.api_key = os.getenv("FENGWU_API_KEY", "")
        self.jwt_secret = os.getenv("FENGWU_JWT_SECRET", "")
        self.enabled = os.getenv("FENGWU_AUTH_ENABLED", "true").lower() == "true"

        if not self.enabled:
            logger.warning("⚠️ 安全认证已禁用，服务端点将对外开放")

    async def verify(
        self,
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
    ) -> bool:
        """验证请求认证"""
        if not self.enabled:
            return True

        # 健康检查端点不需要认证
        if request.url.path in ["/health", "/health/ready", "/actuator/health"]:
            return True

        # 方式 1: API Key 认证
        api_key = request.headers.get("X-API-Key")
        if api_key and api_key == self.api_key:
            return True

        # 方式 2: JWT 认证
        if credentials and self.jwt_secret:
            try:
                import jwt
                payload = jwt.decode(
                    credentials.credentials,
                    self.jwt_secret,
                    algorithms=["HS256"]
                )
                # 将用户信息注入请求状态
                request.state.user = payload.get("sub", "unknown")
                request.state.roles = payload.get("roles", [])
                return True
            except jwt.ExpiredSignatureError:
                logger.warning("JWT token expired")
                raise HTTPException(status_code=401, detail="Token已过期")
            except jwt.InvalidTokenError as e:
                logger.warning(f"Invalid JWT token: {e}")
                raise HTTPException(status_code=401, detail="无效的Token")
            except ImportError:
                logger.warning("PyJWT not installed, falling back to API Key only")
                pass

        raise HTTPException(
            status_code=401,
            detail="未授权访问，请提供有效的 API Key 或 JWT Token"
        )

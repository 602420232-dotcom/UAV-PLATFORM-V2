"""
统一 FastAPI 安全中间件

提供 JWT 认证 + Demo 模式支持，与 Java 后端共享 JWT Secret。
统一使用 HS512 算法。


使用示例:
    from security_middleware import SecurityMiddleware

    middleware = SecurityMiddleware(secret_key=os.getenv("JWT_SECRET", ""))
    middleware.protect_app(app, public_paths=["/health", "/docs", "/openapi.json"])

    # 在路由中使用细粒度角色控制
    @app.get("/api/admin", dependencies=[Depends(middleware.require_roles(["ADMIN"]))])
"""

import logging
import os
from typing import List, Optional

logger = logging.getLogger(__name__)


class SecurityMiddleware:
    """统一安全中间件"""

    def __init__(
        self,
        secret_key: str = "",
        algorithm: str = "HS512",
        demo_enabled: bool = False,
        redis_url: Optional[str] = None,
    ):
        self._jwt_auth = None
        self._demo_service = None
        self._jwt_secret = (
            secret_key or os.getenv("JWT_SECRET", "") or os.getenv("JWT_SECRET_KEY", "")
        )
        self._algorithm = algorithm
        self._demo_enabled = demo_enabled
        self._redis_url = redis_url or os.getenv("REDIS_URL", "")

        if not self._jwt_secret:
            logger.warning(
                "JWT_SECRET not configured — authentication DISABLED. "
                "Set JWT_SECRET or JWT_SECRET_KEY environment variable."
            )

    @property
    def jwt_auth(self):
        if self._jwt_auth is None and self._jwt_secret:
            from common_utils.jwt_auth import JwtAuth
            redis_client = self._get_redis_client()
            self._jwt_auth = JwtAuth(
                secret_key=self._jwt_secret,
                algorithm=self._algorithm,
                redis_client=redis_client,
            )
        return self._jwt_auth

    @property
    def demo_service(self):
        if self._demo_service is None and self._demo_enabled:
            from common_utils.demo_mode import DemoModeService
            redis_client = self._get_redis_client()
            if redis_client:
                self._demo_service = DemoModeService(redis_client=redis_client)
        return self._demo_service

    def _get_redis_client(self):
        try:
            if self._redis_url:
                import redis
                return redis.from_url(self._redis_url, decode_responses=True)
        except Exception as e:
            logger.warning("Redis not available: %s", e)
        return None

    def protect_app(
        self,
        app,
        public_paths: Optional[List[str]] = None,
        health_paths: Optional[List[str]] = None,
    ):
        """
        为 FastAPI 应用添加全局认证保护。

        Args:
            app: FastAPI 应用实例
            public_paths: 额外的公开路径列表（不需要认证）
            health_paths: 健康检查路径列表（始终公开）
        """
        from fastapi import Depends

        public = set(
            health_paths
            or ["/health", "/actuator/health", "/health/ready", "/healthz"]
        )
        if public_paths:
            public.update(public_paths)

        original_route_handler = app.router.add_api_route

        def auth_wrapper(route_path, *args, **kwargs):
            if "dependencies" not in kwargs:
                kwargs["dependencies"] = []
            if route_path not in public:
                kwargs["dependencies"].append(Depends(self._create_auth_check()))
            return original_route_handler(route_path, *args, **kwargs)

        app.router.add_api_route = auth_wrapper

    def _create_auth_check(self):
        """创建认证检查依赖"""
        from fastapi import Header, HTTPException, status

        def check_auth(authorization: Optional[str] = Header(None)):
            if not self._jwt_secret:
                return {"user_id": "anonymous", "roles": ["ANONYMOUS"], "is_demo": False}

            token = None
            auth_type = "none"

            if authorization:
                parts = authorization.split()
                if len(parts) == 2 and parts[0].lower() == "bearer":
                    token = parts[1]
                    auth_type = "jwt"

            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "code": "AUTH_001",
                        "message": "Missing or invalid Authorization header",
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )

            try:
                claims = self.jwt_auth.verify_token(token)
                user_claims = self.jwt_auth.extract_user_claims(claims)

                if user_claims.is_demo and self.demo_service:
                    try:
                        self.demo_service.record_api_call(user_claims.user_id)
                    except Exception:
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail={
                                "code": "AUTH_008",
                                "message": "Demo rate limit exceeded",
                            },
                        )

                return {
                    "user_id": user_claims.user_id,
                    "username": user_claims.username,
                    "roles": user_claims.roles,
                    "is_demo": user_claims.is_demo,
                    "auth_type": auth_type,
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={"code": "AUTH_002", "message": str(e)},
                    headers={"WWW-Authenticate": "Bearer"},
                )

        return check_auth

    def require_roles(self, roles: List[str]):
        """
        创建角色检查依赖。

        Args:
            roles: 必需的角色列表

        Returns:
            FastAPI Depends 可用的依赖函数
        """
        from fastapi import Header, HTTPException, status

        def check_role(authorization: Optional[str] = Header(None)):
            if not self._jwt_secret:
                return {"user_id": "anonymous", "roles": ["ANONYMOUS"]}

            token = None
            if authorization:
                parts = authorization.split()
                if len(parts) == 2 and parts[0].lower() == "bearer":
                    token = parts[1]

            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "code": "AUTH_003",
                        "message": "Missing authorization",
                    },
                )

            try:
                claims = self.jwt_auth.verify_token(token)
                user_claims = self.jwt_auth.extract_user_claims(claims)

                user_roles = set(user_claims.roles)
                required = set(roles)
                if not required.issubset(user_roles):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail={
                            "code": "AUTH_005",
                            "message": f"Requires roles: {roles}",
                        },
                    )

                return {
                    "user_id": user_claims.user_id,
                    "username": user_claims.username,
                    "roles": user_claims.roles,
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={"code": "AUTH_004", "message": str(e)},
                )

        return check_role

    def optional_auth(self):
        """
        可选认证依赖 — 有 token 则验证，没有则继续。
        """
        from fastapi import Header

        def check(authorization: Optional[str] = Header(None)):
            result = {"user_id": "anonymous", "roles": [], "authenticated": False}

            if not authorization or not self._jwt_secret:
                return result

            parts = authorization.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                return result

            try:
                claims = self.jwt_auth.verify_token(parts[1])
                user_claims = self.jwt_auth.extract_user_claims(claims)
                result.update({
                    "user_id": user_claims.user_id,
                    "username": user_claims.username,
                    "roles": user_claims.roles,
                    "authenticated": True,
                })
            except Exception:
                pass

            return result

        return check

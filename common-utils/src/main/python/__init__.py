"""
Common Utils - Python Modules

This package provides shared utilities for Python services,
including JWT authentication and Demo mode functionality.
"""

__version__ = "1.0.0"

# Export JWT auth components


from .jwt_auth import (
    TokenType,
    JwtAuthError,
    TokenMissingError,
    TokenInvalidError,
    TokenExpiredError,
    TokenSignatureError,
    TokenBlacklistError,
    RefreshTokenInvalidError,
    UserClaims,
    JwtAuth,
)

# Export Demo mode components


from .demo_mode import (
    DemoError,
    DemoRateLimitError,
    DemoSessionLimitError,
    DemoSessionExpiredError,
    DemoSessionInfo,
    RateLimitConfig,
    DemoModeService,
)


__all__ = [
    # JWT auth
    "TokenType",
    "JwtAuthError",
    "TokenMissingError",
    "TokenInvalidError",
    "TokenExpiredError",
    "TokenSignatureError",
    "TokenBlacklistError",
    "RefreshTokenInvalidError",
    "UserClaims",
    "JwtAuth",
    # Demo mode
    "DemoError",
    "DemoRateLimitError",
    "DemoSessionLimitError",
    "DemoSessionExpiredError",
    "DemoSessionInfo",
    "RateLimitConfig",
    "DemoModeService",
]

"""
SDK configuration module.
"""

from pydantic import BaseModel, Field


class UavPlatformConfig(BaseModel):
    """Configuration for the UAV Platform client."""

    base_url: str = Field(..., description="API gateway base URL, e.g. http://localhost:8080")
    api_key: str = Field(..., description="API key for HMAC-SHA256 signing")
    api_secret: str = Field(..., description="API secret for HMAC-SHA256 signing")
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    api_version: str = Field(default="1.0", description="API version header value")
    api_prefix: str = Field(default="/api", description="API path prefix")

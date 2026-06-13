"""
HTTP client module wrapping httpx for both sync and async usage.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from uav_platform.auth import sign_request
from uav_platform.config import UavPlatformConfig


class ApiResponseError(Exception):
    """Raised when the API returns a non-success response."""

    def __init__(self, status_code: int, code: int, message: str, request_id: str = ""):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.request_id = request_id
        super().__init__(f"[{status_code}] code={code} message={message} request_id={request_id}")


class HttpClient:
    """
    Synchronous HTTP client with automatic HMAC signing and response unwrapping.

    The backend returns responses in the unified ``Result<T>`` envelope:
        {"code": 0, "message": "ok", "data": <T>, "requestId": "...", "timestamp": ...}
    """

    def __init__(self, config: UavPlatformConfig) -> None:
        self._config = config
        self._client = httpx.Client(
            base_url=config.base_url,
            timeout=config.timeout,
            headers={"Content-Type": "application/json"},
        )

    @property
    def client(self) -> httpx.Client:
        return self._client

    def _build_url(self, path: str) -> str:
        """Build full URL with API prefix."""
        return f"{self._config.api_prefix}{path}"

    def _sign(self, method: str, path: str, body: str = "") -> dict[str, str]:
        """Generate signed headers."""
        return sign_request(
            method=method,
            path=self._build_url(path),
            api_key=self._config.api_key,
            api_secret=self._config.api_secret,
            body=body,
            api_version=self._config.api_version,
        )

    @staticmethod
    def _unwrap(response: httpx.Response) -> Any:
        """Unwrap the unified Result<T> envelope and return the data field."""
        try:
            body = response.json()
        except Exception:
            response.raise_for_status()
            raise

        if response.status_code >= 400:
            code = body.get("code", response.status_code)
            message = body.get("message", response.reason_phrase or "Unknown error")
            request_id = body.get("requestId", "")
            raise ApiResponseError(response.status_code, code, message, request_id)

        code = body.get("code", -1)
        if code not in (0, 200):
            message = body.get("message", "Unknown business error")
            request_id = body.get("requestId", "")
            raise ApiResponseError(response.status_code, code, message, request_id)

        return body.get("data")

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Send a signed GET request and return unwrapped data."""
        url = self._build_url(path)
        headers = self._sign("GET", path)
        response = self._client.get(url, headers=headers, params=params)
        return self._unwrap(response)

    def post(self, path: str, data: dict[str, Any] | None = None) -> Any:
        """Send a signed POST request and return unwrapped data."""
        url = self._build_url(path)
        body = json.dumps(data, ensure_ascii=False) if data is not None else ""
        headers = self._sign("POST", path, body)
        response = self._client.post(url, headers=headers, content=body)
        return self._unwrap(response)

    def put(self, path: str, data: dict[str, Any] | None = None) -> Any:
        """Send a signed PUT request and return unwrapped data."""
        url = self._build_url(path)
        body = json.dumps(data, ensure_ascii=False) if data is not None else ""
        headers = self._sign("PUT", path, body)
        response = self._client.put(url, headers=headers, content=body)
        return self._unwrap(response)

    def delete(self, path: str) -> Any:
        """Send a signed DELETE request and return unwrapped data."""
        url = self._build_url(path)
        headers = self._sign("DELETE", path)
        response = self._client.delete(url, headers=headers)
        return self._unwrap(response)

    def close(self) -> None:
        """Close the underlying httpx client."""
        self._client.close()


class AsyncHttpClient:
    """
    Asynchronous HTTP client with automatic HMAC signing and response unwrapping.
    """

    def __init__(self, config: UavPlatformConfig) -> None:
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout,
            headers={"Content-Type": "application/json"},
        )

    @property
    def client(self) -> httpx.AsyncClient:
        return self._client

    def _build_url(self, path: str) -> str:
        return f"{self._config.api_prefix}{path}"

    def _sign(self, method: str, path: str, body: str = "") -> dict[str, str]:
        return sign_request(
            method=method,
            path=self._build_url(path),
            api_key=self._config.api_key,
            api_secret=self._config.api_secret,
            body=body,
            api_version=self._config.api_version,
        )

    @staticmethod
    def _unwrap(response: httpx.Response) -> Any:
        try:
            body = response.json()
        except Exception:
            response.raise_for_status()
            raise

        if response.status_code >= 400:
            code = body.get("code", response.status_code)
            message = body.get("message", response.reason_phrase or "Unknown error")
            request_id = body.get("requestId", "")
            raise ApiResponseError(response.status_code, code, message, request_id)

        code = body.get("code", -1)
        if code not in (0, 200):
            message = body.get("message", "Unknown business error")
            request_id = body.get("requestId", "")
            raise ApiResponseError(response.status_code, code, message, request_id)

        return body.get("data")

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = self._build_url(path)
        headers = self._sign("GET", path)
        response = await self._client.get(url, headers=headers, params=params)
        return self._unwrap(response)

    async def post(self, path: str, data: dict[str, Any] | None = None) -> Any:
        url = self._build_url(path)
        body = json.dumps(data, ensure_ascii=False) if data is not None else ""
        headers = self._sign("POST", path, body)
        response = await self._client.post(url, headers=headers, content=body)
        return self._unwrap(response)

    async def put(self, path: str, data: dict[str, Any] | None = None) -> Any:
        url = self._build_url(path)
        body = json.dumps(data, ensure_ascii=False) if data is not None else ""
        headers = self._sign("PUT", path, body)
        response = await self._client.put(url, headers=headers, content=body)
        return self._unwrap(response)

    async def delete(self, path: str) -> Any:
        url = self._build_url(path)
        headers = self._sign("DELETE", path)
        response = await self._client.delete(url, headers=headers)
        return self._unwrap(response)

    async def close(self) -> None:
        await self._client.aclose()

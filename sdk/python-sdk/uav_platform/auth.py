"""
HMAC-SHA256 request signing module.

Generates authentication headers for API requests using the HMAC-SHA256 algorithm.
"""

from __future__ import annotations

import hashlib
import hmac
import time


def sign_request(
    method: str,
    path: str,
    api_key: str,
    api_secret: str,
    body: str = "",
    api_version: str = "1.0",
) -> dict[str, str]:
    """
    Generate HMAC-SHA256 signature headers for an API request.

    The signature is computed over the string:
        METHOD\\nPATH\\nTIMESTAMP\\nAPI_KEY\\nBODY

    Args:
        method: HTTP method (GET, POST, PUT, DELETE).
        path: URL path including query string (e.g. /api/v1/weather/point).
        api_key: API key identifier.
        api_secret: API secret used as HMAC key.
        body: JSON-encoded request body (empty string for GET requests).
        api_version: API version header value.

    Returns:
        Dictionary of headers to attach to the request.
    """
    timestamp = str(int(time.time()))
    string_to_sign = f"{method.upper()}\n{path}\n{timestamp}\n{api_key}\n{body}"
    signature = hmac.new(
        api_secret.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return {
        "X-API-Key": api_key,
        "X-Signature": signature,
        "X-Timestamp": timestamp,
        "X-API-Version": api_version,
    }

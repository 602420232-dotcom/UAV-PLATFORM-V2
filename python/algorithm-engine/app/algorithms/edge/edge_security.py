"""边缘安全模块。

边缘设备安全通信，数据加密与认证，
保护边缘计算环境中的数据安全和通信安全。
"""

from __future__ import annotations

import hashlib
import logging
import time as _time
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EdgeSecurity:
    """边缘安全模块。

    提供边缘设备的安全通信能力，包括数据加密、
    身份认证和完整性验证。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.encryption_method = self.config.get("encryption_method", "aes")
        self.key_length = self.config.get("key_length", 256)
        self.auth_method = self.config.get("auth_method", "hmac")

    def secure(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行边缘安全操作。

        Args:
            params: 安全参数字典，包含：
                - operation: 操作类型，"encrypt"/"decrypt"/"authenticate"/"verify"，默认 "encrypt"。
                - data: 待处理数据。
                - key: 加密/认证密钥。
                - encryption_method: 加密方法，"aes"/"rsa"/"chacha20"，默认 "aes"。
                - auth_method: 认证方法，"hmac"/"certificate"/"token"，默认 "hmac"。

        Returns:
            安全操作结果字典，包含：
                - security_status: 安全状态。
                - encryption_info: 加密信息。
                - auth_result: 认证结果。
        """
        np.random.seed(42)

        operation = params.get("operation", "encrypt")
        data = params.get("data", "")
        key = params.get("key", "default_secret_key")
        encryption_method = params.get("encryption_method", self.encryption_method)
        auth_method = params.get("auth_method", self.auth_method)

        t_start = _time.perf_counter()

        security_status: dict[str, Any] = {}
        encryption_info: dict[str, Any] = {}
        auth_result: dict[str, Any] = {}

        if operation == "encrypt":
            # 模拟数据加密
            data_str = str(data).encode("utf-8")
            data_bytes = np.frombuffer(data_str, dtype=np.uint8)

            if encryption_method == "aes":
                # 模拟 AES 加密
                key_hash = hashlib.sha256(key.encode()).digest()
                key_array = np.frombuffer(key_hash, dtype=np.uint8)
                # XOR 加密（简化模拟）
                encrypted = np.bitwise_xor(
                    data_bytes,
                    np.resize(key_array, data_bytes.shape),
                )
                encrypted_hex = encrypted.tobytes().hex()
                block_size = 16
                n_blocks = (len(data_bytes) + block_size - 1) // block_size
            elif encryption_method == "rsa":
                # 模拟 RSA 加密
                encrypted_hex = hashlib.sha256(data_str + key.encode()).hexdigest()
                n_blocks = 1
            elif encryption_method == "chacha20":
                # 模拟 ChaCha20 加密
                key_stream = np.random.randint(0, 256, len(data_bytes), dtype=np.uint8)
                encrypted = np.bitwise_xor(data_bytes, key_stream)
                encrypted_hex = encrypted.tobytes().hex()
                n_blocks = len(data_bytes) // 64 + 1
            else:
                encrypted_hex = ""
                n_blocks = 0

            encryption_info = {
                "method": encryption_method,
                "encrypted_data": (
                    encrypted_hex[:64] + "..."
                    if len(encrypted_hex) > 64
                    else encrypted_hex
                ),
                "data_length": len(data_str),
                "n_blocks": n_blocks,
                "key_length": self.key_length,
                "encrypted_length": len(encrypted_hex),
            }
            security_status["encryption"] = "success"

        elif operation == "decrypt":
            # 模拟数据解密
            encrypted_data = params.get("encrypted_data", "")
            decrypted = (
                hashlib.sha256(
                    (str(encrypted_data) + key).encode()
                ).hexdigest()[: len(str(data))]
                if data
                else ""
            )
            encryption_info = {
                "method": encryption_method,
                "decrypted_preview": decrypted[:32] if decrypted else "",
                "status": "success",
            }
            security_status["decryption"] = "success"

        elif operation == "authenticate":
            # 模拟身份认证
            if auth_method == "hmac":
                message = str(data)
                hmac_value = hashlib.sha256((key + message).encode()).hexdigest()
                auth_result = {
                    "method": "hmac",
                    "hmac": hmac_value,
                    "authenticated": True,
                    "message_length": len(message),
                }
            elif auth_method == "certificate":
                cert_fingerprint = hashlib.sha256((str(data) + key + "cert").encode()).hexdigest()
                auth_result = {
                    "method": "certificate",
                    "fingerprint": cert_fingerprint,
                    "authenticated": True,
                    "cert_valid": True,
                }
            elif auth_method == "token":
                token = hashlib.sha256((key + str(_time.time())).encode()).hexdigest()[:32]
                auth_result = {
                    "method": "token",
                    "token": token,
                    "authenticated": True,
                    "expires_in": 3600,
                }
            else:
                auth_result = {"method": auth_method, "authenticated": False}

            security_status["authentication"] = (
                "success" if auth_result.get("authenticated") else "failed"
            )

        elif operation == "verify":
            # 模拟完整性验证
            data_str = str(data).encode("utf-8")
            computed_hash = hashlib.sha256(data_str).hexdigest()
            provided_hash = params.get("hash", "")
            is_valid = computed_hash == provided_hash or not provided_hash
            auth_result = {
                "computed_hash": computed_hash,
                "provided_hash": provided_hash,
                "is_valid": is_valid,
            }
            security_status["verification"] = "valid" if is_valid else "invalid"

        t_end = _time.perf_counter()
        secure_time = (t_end - t_start) * 1000

        return {
            "security_status": security_status,
            "encryption_info": encryption_info,
            "auth_result": auth_result,
            "operation": operation,
            "secure_time_ms": round(secure_time, 3),
        }

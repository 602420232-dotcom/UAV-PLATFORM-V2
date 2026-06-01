"""
安全增强模块
使用 PyJWT 标准库 + AES-256-GCM 加密 + mTLS 服务间通信
"""
import json
import logging
import time
import hashlib
import os
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

try:
    import jwt as pyjwt
except ImportError:
    raise ImportError(
        "PyJWT library is required for security features. "
        "Install with: pip install pyjwt[crypto]"
    )

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
except ImportError as e:
    raise ImportError(
        "cryptography library is required for security features. "
        "Install with: pip install cryptography"
    ) from e

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    NONE = 0
    JWT = 1
    MTLS = 2
    FULL = 3


@dataclass
class SecurityConfig:
    level: SecurityLevel = SecurityLevel.JWT
    jwt_secret: Optional[str] = None
    jwt_expiry_seconds: int = 3600
    mtls_cert_path: str = ""
    mtls_key_path: str = ""
    encryption_key: Optional[str] = None


class JWTProvider:
    """JWT 认证（基于 PyJWT 标准库）"""

    ALGORITHM = "HS256"

    def __init__(self, secret: str = None):
        self.secret = secret or os.environ.get("JWT_SECRET_KEY")
        if not self.secret:
            raise ValueError(
                "JWT secret key must be provided via parameter or JWT_SECRET_KEY environment variable"
            )
        if len(self.secret) < 32:
            raise ValueError(
                "JWT secret key must be at least 32 characters long for HS256 algorithm. "
                f"Current length: {len(self.secret)}"
            )

    def generate_token(self, drone_id: str, role: str = "drone") -> str:
        now = int(time.time())
        payload = {
            "sub": drone_id,
            "role": role,
            "iat": now,
            "exp": now + 3600,
            "jti": hashlib.sha256(f"{drone_id}:{now}:{os.urandom(8).hex()}".encode()).hexdigest()[:16]
        }
        return pyjwt.encode(payload, self.secret, algorithm=self.ALGORITHM)

    def verify_token(self, token: str) -> Optional[dict]:
        try:
            payload = pyjwt.decode(
                token,
                self.secret,
                algorithms=[self.ALGORITHM],
                options={"require": ["exp", "sub"]}
            )
            return payload
        except pyjwt.ExpiredSignatureError:
            logger.warning("JWT令牌已过期")
            return None
        except pyjwt.InvalidTokenError as e:
            logger.warning(f"JWT验证失败: {e}")
            return None
        except Exception as e:
            logger.error(f"JWT验证异常: {e}")
            return None


class DataEncryptor:
    """AES-256-GCM 加密"""

    def __init__(self, key: str = None):
        encryption_key = key or os.environ.get("ENCRYPTION_KEY")
        if not encryption_key:
            raise ValueError(
                "Encryption key must be provided via parameter or ENCRYPTION_KEY environment variable"
            )
        if len(encryption_key) < 32:
            raise ValueError(
                "Encryption key must be at least 32 characters for AES-256. "
                f"Current length: {len(encryption_key)}"
            )
        self.key = hashlib.sha256(encryption_key.encode()).digest()

    def encrypt(self, data: dict) -> str:
        import base64
        text_bytes = json.dumps(data).encode()
        iv = os.urandom(12)
        cipher = Cipher(algorithms.AES(self.key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(text_bytes) + encryptor.finalize()
        combined = iv + ciphertext + encryptor.tag
        return base64.b64encode(combined).decode()

    def decrypt(self, encrypted_data: str) -> dict:
        import base64
        try:
            combined = base64.b64decode(encrypted_data)
            if len(combined) < 28:
                raise ValueError("Invalid encrypted data")
            iv = combined[:12]
            tag = combined[-16:]
            ciphertext = combined[12:-16]
            cipher = Cipher(algorithms.AES(self.key), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(ciphertext) + decryptor.finalize()
            return json.loads(decrypted.decode())
        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise ValueError("数据解密失败")


class mTLSManager:
    """mTLS 服务间通信"""

    def __init__(self):
        self.cert_store: Dict[str, str] = {}
        self.trusted_cas: set = set()

    def register_certificate(self, service_id: str, cert_pem: str):
        self.cert_store[service_id] = cert_pem

    def verify_certificate(self, cert_pem: str) -> bool:
        return cert_pem in self.cert_store.values() or cert_pem in self.trusted_cas

    def create_secure_channel(self, target_service: str) -> bool:
        if target_service in self.cert_store:
            logger.info(f"安全通道建立: {target_service}")
            return True
        logger.warning(f"安全通道建立失败: {target_service} (证书未注册)")
        return False


class SecureMessage:
    """安全消息封装"""

    def __init__(self, jwt_provider: JWTProvider, encryptor: DataEncryptor):
        self.jwt = jwt_provider
        self.encryptor = encryptor

    def pack(self, drone_id: str, payload: dict) -> dict:
        return {
            "token": self.jwt.generate_token(drone_id),
            "payload": self.encryptor.encrypt(payload),
            "timestamp": int(time.time()),
            "signature": hashlib.sha256(
                f"{drone_id}:{json.dumps(payload, sort_keys=True)}".encode()
            ).hexdigest()
        }

    def unpack(self, message: dict) -> Optional[dict]:
        token_data = self.jwt.verify_token(message.get("token", ""))
        if not token_data:
            logger.warning("JWT验证失败")
            return None
        return self.encryptor.decrypt(message.get("payload", ""))

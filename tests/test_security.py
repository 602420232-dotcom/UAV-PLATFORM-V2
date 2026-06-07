"""
安全模块单元测试 - mTLS + JWT + 数据加密
"""
import logging
import os
import sys
import unittest

logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'edge-cloud-coordinator'))

from security import (  # type: ignore[import-not-found]  # noqa: E402
    JWTProvider, MtlsManager, DataEncryptor,
    SecureMessage, SecurityConfig, SecurityLevel
)


class TestJWTProvider(unittest.TestCase):
    """JWT 认证提供者测试"""

    def setUp(self):
        self.provider = JWTProvider()

    def test_generate_token(self):
        token = self.provider.generate_token("drone_001", "uav")
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)
        self.assertEqual(len(token.split(".")), 3)

    def test_verify_valid_token(self):
        token = self.provider.generate_token("drone_001", "uav")
        payload = self.provider.verify_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "drone_001")
        self.assertEqual(payload["role"], "uav")

    def test_verify_invalid_token(self):
        payload = self.provider.verify_token("invalid.token.here")
        self.assertIsNone(payload)

    def test_verify_tampered_token(self):
        token = self.provider.generate_token("drone_001", "uav")
        parts = token.split(".")
        parts[2] = "bad_signature"
        payload = self.provider.verify_token(".".join(parts))
        self.assertIsNone(payload)


class TestDataEncryptor(unittest.TestCase):
    """数据加密器测试"""

    def setUp(self):
        self.encryptor = DataEncryptor()

    def test_encrypt_decrypt(self):
        original = {"temperature": 25.5, "humidity": 60}
        encrypted = self.encryptor.encrypt(original)
        self.assertIsNotNone(encrypted)
        self.assertIsInstance(encrypted, str)

        decrypted = self.encryptor.decrypt(encrypted)
        self.assertEqual(decrypted["temperature"], 25.5)

    def test_encrypt_decrypt_complex(self):
        original = {"id": "uav_001", "lat": 39.9, "lng": 116.4, "alt": 100}
        encrypted = self.encryptor.encrypt(original)
        decrypted = self.encryptor.decrypt(encrypted)
        self.assertEqual(decrypted["id"], "uav_001")


class TestSecureMessage(unittest.TestCase):
    """安全消息测试"""

    def setUp(self):
        self.jwt = JWTProvider()
        self.encryptor = DataEncryptor()
        self.messenger = SecureMessage(self.jwt, self.encryptor)

    def test_pack_unpack(self):
        packed = self.messenger.pack("drone_001", {"temperature": 22.0})
        self.assertIn("token", packed)
        self.assertIn("payload", packed)
        self.assertIn("timestamp", packed)
        self.assertIn("signature", packed)

        unpacked = self.messenger.unpack(packed)
        self.assertIsNotNone(unpacked)
        self.assertEqual(unpacked["temperature"], 22.0)

    def test_unpack_invalid_token(self):
        packed = {"token": "bad", "payload": "bad"}
        result = self.messenger.unpack(packed)
        self.assertIsNone(result)


class TestMtlsManager(unittest.TestCase):
    """mTLS管理器测试"""

    def setUp(self):
        self.manager = MtlsManager()

    def test_register_and_verify(self):
        self.manager.register_certificate("service_a", "cert_pem_data")
        self.assertTrue(self.manager.verify_certificate("cert_pem_data"))
        self.assertFalse(self.manager.verify_certificate("unknown_cert"))

    def test_create_secure_channel(self):
        self.manager.register_certificate("service_b", "cert_b")
        result = self.manager.create_secure_channel("service_b")
        self.assertTrue(result)

        result = self.manager.create_secure_channel("unknown_service")
        self.assertFalse(result)


class TestSecurityConfig(unittest.TestCase):
    """安全配置测试"""

    def test_default_config(self):
        config = SecurityConfig()
        self.assertEqual(config.level, SecurityLevel.JWT)
        self.assertEqual(config.jwt_expiry_seconds, 3600)

    def test_high_security(self):
        config = SecurityConfig(level=SecurityLevel.FULL, encryption_key="test_key")
        self.assertEqual(config.level, SecurityLevel.FULL)
        self.assertEqual(config.encryption_key, "test_key")


if __name__ == '__main__':
    unittest.main()

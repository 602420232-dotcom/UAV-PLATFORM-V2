package com.uav.common.security;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("AuthEventLogger 认证事件日志测试")
class AuthEventLoggerTest {

    private AuthEventLogger authEventLogger;

    @BeforeEach
    void setUp() {
        authEventLogger = new AuthEventLogger();
    }

    @Test
    @DisplayName("记录登录成功事件")
    void onLoginSuccess_shouldIncrementCounter() {
        authEventLogger.onLoginSuccess("admin", "192.168.1.100", "Mozilla/5.0");

        var metrics = authEventLogger.getMetrics();
        assertEquals(1L, metrics.get("loginSuccess"));
        assertEquals(1L, metrics.get("activeUsers"));
    }

    @Test
    @DisplayName("记录登录失败事件")
    void onLoginFailure_shouldIncrementCounter() {
        authEventLogger.onLoginFailure("unknown_user", "10.0.0.1", "wrong password");

        var metrics = authEventLogger.getMetrics();
        assertEquals(1L, metrics.get("loginFailure"));
    }

    @Test
    @DisplayName("记录 Token 刷新事件")
    void onTokenRefresh_shouldIncrementCounter() {
        authEventLogger.onTokenRefresh("admin", "old-jti-001", "new-jti-002");

        var metrics = authEventLogger.getMetrics();
        assertEquals(1L, metrics.get("tokenRefresh"));
    }

    @Test
    @DisplayName("记录 Token 撤销事件应移除活跃用户")
    void onTokenBlacklisted_shouldRemoveActiveUser() {
        authEventLogger.onLoginSuccess("admin", "192.168.1.1", "test");
        authEventLogger.onTokenBlacklisted("admin", "jti-001", "logout");

        var metrics = authEventLogger.getMetrics();
        assertEquals(1L, metrics.get("tokenBlacklist"));
        assertEquals(0L, metrics.get("activeUsers"));
    }

    @Test
    @DisplayName("记录无效 Token 事件")
    void onInvalidToken_shouldIncrementCounter() {
        authEventLogger.onInvalidToken("bad-token", "/api/drones", "signature mismatch");

        var metrics = authEventLogger.getMetrics();
        assertEquals(1L, metrics.get("tokenInvalid"));
    }

    @Test
    @DisplayName("重置指标应清空所有计数器和活跃用户")
    void resetMetrics_shouldClearAll() {
        authEventLogger.onLoginSuccess("admin", "1.2.3.4", "test");
        authEventLogger.onLoginFailure("user", "1.2.3.4", "bad pwd");
        authEventLogger.onTokenRefresh("admin", "old", "new");

        authEventLogger.resetMetrics();

        var metrics = authEventLogger.getMetrics();
        assertEquals(0L, metrics.get("loginSuccess"));
        assertEquals(0L, metrics.get("loginFailure"));
        assertEquals(0L, metrics.get("tokenRefresh"));
        assertEquals(0L, metrics.get("activeUsers"));
    }

    @Test
    @DisplayName("同一用户多次登录只计一个活跃用户")
    void multipleLogins_sameUser_shouldCountOnce() {
        authEventLogger.onLoginSuccess("admin", "10.0.0.1", "device1");
        authEventLogger.onLoginSuccess("admin", "10.0.0.2", "device2");

        var metrics = authEventLogger.getMetrics();
        assertEquals(2L, metrics.get("loginSuccess"));
        assertEquals(1L, metrics.get("activeUsers"));
    }

    @Test
    @DisplayName("多个用户登录应正确统计活跃用户数")
    void multipleLogins_differentUsers_shouldCountAll() {
        authEventLogger.onLoginSuccess("admin", "10.0.0.1", "device1");
        authEventLogger.onLoginSuccess("operator", "10.0.0.2", "device2");
        authEventLogger.onLoginSuccess("viewer", "10.0.0.3", "device3");

        var metrics = authEventLogger.getMetrics();
        assertEquals(3L, metrics.get("activeUsers"));
    }
}

package com.uav.common.security;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 认证事件日志/监控服务。
 * <p>
 * 记录所有认证相关事件到日志，并提供运行时指标查询。
 * 生产环境可对接 ELK / Prometheus / Grafana 进行可视化监控。
 * </p>
 *
 * 监控指标（可通过 /actuator/metrics 导出）:
 * - auth.login.success: 登录成功次数
 * - auth.login.failure: 登录失败次数
 * - auth.token.refresh: Token 刷新次数
 * - auth.token.blacklist: Token 撤销次数
 * - auth.token.invalid: 无效 Token 次数
 * - auth.concurrent.users: 当前活跃用户数
 */
@Slf4j
@Component
public class AuthEventLogger {

    private static final DateTimeFormatter FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'");

    // ─── 计数器 ────────────────────────────────────────────────────
    private final AtomicLong loginSuccessCount = new AtomicLong(0);
    private final AtomicLong loginFailureCount = new AtomicLong(0);
    private final AtomicLong tokenRefreshCount = new AtomicLong(0);
    private final AtomicLong tokenBlacklistCount = new AtomicLong(0);
    private final AtomicLong tokenInvalidCount = new AtomicLong(0);
    private final Map<String, LocalDateTime> activeUsers = new ConcurrentHashMap<>();

    // ─── 登录事件 ──────────────────────────────────────────────────
    public void onLoginSuccess(String username, String ip, String userAgent) {
        loginSuccessCount.incrementAndGet();
        activeUsers.put(username, LocalDateTime.now());
        log.info("[AUTH] LOGIN_SUCCESS | user={} | ip={} | agent={} | time={}",
                username, maskIp(ip), truncate(userAgent, 80), now());
    }

    public void onLoginFailure(String username, String ip, String reason) {
        loginFailureCount.incrementAndGet();
        log.warn("[AUTH] LOGIN_FAILURE | user={} | ip={} | reason={} | time={}",
                username, maskIp(ip), reason, now());
    }

    // ─── Token 事件 ────────────────────────────────────────────────
    public void onTokenRefresh(String username, String oldJti, String newJti) {
        tokenRefreshCount.incrementAndGet();
        log.info("[AUTH] TOKEN_REFRESH | user={} | old_jti={} | new_jti={} | time={}",
                username, maskJti(oldJti), maskJti(newJti), now());
    }

    public void onTokenBlacklisted(String username, String jti, String reason) {
        tokenBlacklistCount.incrementAndGet();
        activeUsers.remove(username);
        log.info("[AUTH] TOKEN_BLACKLIST | user={} | jti={} | reason={} | time={}",
                username, maskJti(jti), reason, now());
    }

    public void onInvalidToken(String token, String path, String reason) {
        tokenInvalidCount.incrementAndGet();
        log.warn("[AUTH] TOKEN_INVALID | path={} | reason={} | token_prefix={} | time={}",
                path, reason, safeTokenPrefix(token), now());
    }

    // ─── 登出事件 ──────────────────────────────────────────────────
    public void onLogout(String username, String jti) {
        activeUsers.remove(username);
        log.info("[AUTH] LOGOUT | user={} | jti={} | time={}", username, maskJti(jti), now());
    }

    // ─── 指标查询 ──────────────────────────────────────────────────
    public Map<String, Object> getMetrics() {
        return Map.of(
                "loginSuccess", loginSuccessCount.get(),
                "loginFailure", loginFailureCount.get(),
                "tokenRefresh", tokenRefreshCount.get(),
                "tokenBlacklist", tokenBlacklistCount.get(),
                "tokenInvalid", tokenInvalidCount.get(),
                "activeUsers", (long) activeUsers.size(),
                "timestamp", now()
        );
    }

    public void resetMetrics() {
        loginSuccessCount.set(0);
        loginFailureCount.set(0);
        tokenRefreshCount.set(0);
        tokenBlacklistCount.set(0);
        tokenInvalidCount.set(0);
        activeUsers.clear();
        log.info("[AUTH] METRICS_RESET | time={}", now());
    }

    // ─── 辅助方法 ──────────────────────────────────────────────────
    private String now() {
        return LocalDateTime.now().format(FORMATTER);
    }

    private String maskIp(String ip) {
        if (ip == null) return "unknown";
        int lastDot = ip.lastIndexOf('.');
        if (lastDot > 0) {
            return ip.substring(0, lastDot) + ".xxx";
        }
        return ip;
    }

    private String maskJti(String jti) {
        if (jti == null || jti.length() < 8) return "****";
        return jti.substring(0, 4) + "****" + jti.substring(jti.length() - 4);
    }

    private String truncate(String s, int maxLen) {
        if (s == null) return "";
        return s.length() <= maxLen ? s : s.substring(0, maxLen) + "...";
    }

    private String safeTokenPrefix(String token) {
        if (token == null || token.length() < 20) return "invalid";
        return token.substring(0, 10) + "****";
    }
}

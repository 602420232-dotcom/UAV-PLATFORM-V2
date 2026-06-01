package com.uav.common.security;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

/**
 * 认证事件监控 REST 端点。
 * <p>
 * 提供认证指标查询和管理功能，仅限 ADMIN 角色访问。
 * 生产环境建议通过 management.server.port 使用独立端口。
 * </p>
 */
@RestController
@RequestMapping("/api/admin/auth-events")
@RequiredArgsConstructor
public class AuthEventController {

    private final AuthEventLogger authEventLogger;

    @GetMapping("/metrics")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Map<String, Object>> getMetrics() {
        return ResponseEntity.ok(authEventLogger.getMetrics());
    }

    @PostMapping("/metrics/reset")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Map<String, Object>> resetMetrics() {
        authEventLogger.resetMetrics();
        return ResponseEntity.ok(Map.of("code", 200, "message", "认证指标已重置"));
    }
}

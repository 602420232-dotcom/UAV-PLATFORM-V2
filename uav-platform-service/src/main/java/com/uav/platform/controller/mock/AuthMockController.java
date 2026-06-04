package com.uav.platform.controller.mock;

import com.uav.common.annotation.StubController;
import com.uav.common.security.JwtTokenProvider;
import com.uav.platform.dto.LoginRequest;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@StubController(
    reason = "前端联调和演示环境使用",
    plannedReplacement = "backend-spring 真实 auth 端点",
    plannedBy = "Q3-2026"
)
@RestController
@RequestMapping("/api/v1/auth")
public class AuthMockController {

    private final JwtTokenProvider jwtTokenProvider;

    public AuthMockController(JwtTokenProvider jwtTokenProvider) {
        this.jwtTokenProvider = jwtTokenProvider;
    }

    @PostMapping("/login")
    public ResponseEntity<Map<String, Object>> login(@Valid @RequestBody LoginRequest loginReq) {
        throw new UnsupportedOperationException(
            "Demo login disabled for security. Use the real auth endpoint at backend-spring:8089/api/v1/auth/login"
        );
    }

    @PostMapping("/logout")
    public ResponseEntity<Map<String, Object>> logout() {
        return ResponseEntity.ok(Map.of("code", 200, "message", "logout success"));
    }

    @PostMapping("/refresh")
    public ResponseEntity<Map<String, Object>> refresh(@RequestBody Map<String, Object> req) {
        try {
            String refreshToken = (String) req.get("refresh_token");
            String newToken = jwtTokenProvider.refreshAccessToken(refreshToken);
            return ResponseEntity.ok(Map.of(
                "code", 200,
                "token", newToken,
                "message", "token refreshed"
            ));
        } catch (Exception e) {
            return ResponseEntity.status(401).body(Map.of(
                "code", 401, "message", "Invalid refresh token"
            ));
        }
    }

    @GetMapping("/me")
    public ResponseEntity<Map<String, Object>> currentUser() {
        return ResponseEntity.ok(Map.of(
            "id", "U001", "username", "admin", "role", "admin", "name", "管理员"
        ));
    }
}
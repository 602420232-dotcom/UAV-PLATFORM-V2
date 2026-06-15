package com.uav.platform.controller;

import com.uav.common.core.result.Result;
import com.uav.common.security.service.JwtService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

/**
 * 认证控制器
 * <p>
 * 提供 JWT Token 刷新端点。
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
public class AuthController {

    private final JwtService jwtService;

    /**
     * 刷新 Access Token
     * <p>
     * 使用有效的 Refresh Token 换取新的 Access Token。
     *
     * @param request 包含 refreshToken 的请求体
     * @return 新的 accessToken
     */
    @PostMapping("/refresh")
    public Result<Map<String, String>> refreshToken(@Valid @RequestBody RefreshTokenRequest request) {
        String refreshToken = request.getRefreshToken();
        String username = jwtService.extractUsername(refreshToken);

        if (!jwtService.validateRefreshToken(refreshToken, username)) {
            log.warn("Refresh token 验证失败: username={}", username);
            return Result.error(401, "无效或已过期的 refresh token");
        }

        String newAccessToken = jwtService.generateToken(username);
        log.info("Access token 刷新成功: username={}", username);

        return Result.success(Map.of("accessToken", newAccessToken, "tokenType", "Bearer"));
    }

    @Data
    public static class RefreshTokenRequest {
        @NotBlank(message = "refreshToken 不能为空")
        private String refreshToken;
    }
}

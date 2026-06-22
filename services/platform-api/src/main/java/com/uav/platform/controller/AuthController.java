package com.uav.platform.controller;

import com.uav.common.core.result.Result;
import com.uav.common.security.service.JwtService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 认证控制器
 * <p>
 * 提供登录、注册和 JWT Token 刷新端点。
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
public class AuthController {

    private final JwtService jwtService;
    private final JdbcTemplate jdbcTemplate;
    private final PasswordEncoder passwordEncoder;

    /**
     * 用户登录
     * <p>
     * 验证用户名密码，生成 JWT Token 返回。
     *
     * @param request 登录请求（username, password）
     * @return token, userId, role, tenantId, tenantName
     */
    @PostMapping("/login")
    public Result<Map<String, Object>> login(@Valid @RequestBody LoginRequest request) {
        String username = request.getUsername();
        String password = request.getPassword();

        // 查询用户信息（关联角色和租户）
        List<Map<String, Object>> users = jdbcTemplate.query(
                "SELECT u.id, u.username, u.password, u.status, " +
                        "r.role_code, r.role_name, " +
                        "t.id AS tenant_id, t.tenant_name " +
                        "FROM sys_user u " +
                        "LEFT JOIN sys_user_role ur ON u.id = ur.user_id " +
                        "LEFT JOIN sys_role r ON ur.role_id = r.id " +
                        "LEFT JOIN sys_tenant t ON u.tenant_id = t.id " +
                        "WHERE u.username = ? AND u.status = 1",
                (rs, rowNum) -> {
                    Map<String, Object> row = new HashMap<>();
                    row.put("id", rs.getLong("id"));
                    row.put("username", rs.getString("username"));
                    row.put("password", rs.getString("password"));
                    row.put("status", rs.getInt("status"));
                    row.put("roleCode", rs.getString("role_code"));
                    row.put("roleName", rs.getString("role_name"));
                    row.put("tenantId", rs.getObject("tenant_id"));
                    row.put("tenantName", rs.getString("tenant_name"));
                    return row;
                },
                username
        );

        if (users.isEmpty()) {
            log.warn("登录失败: 用户不存在或已禁用 - username={}", username);
            return Result.error(401, "用户名或密码错误");
        }

        Map<String, Object> user = users.get(0);

        // 验证密码
        String storedPassword = user.get("password") != null ? user.get("password").toString() : "";
        log.info("DEBUG login: username={}, storedPassword startsWith=$2a$={}, encoderType={}",
                username, storedPassword.startsWith("$2a$"), passwordEncoder.getClass().getName());
        boolean matches = passwordEncoder.matches(password, storedPassword);
        log.info("DEBUG login: password matches={}", matches);
        if (!matches) {
            log.warn("登录失败: 密码错误 - username={}", username);
            return Result.error(401, "用户名或密码错误");
        }

        // 提取角色并生成带角色的 JWT Token
        String roleCode = (String) user.get("roleCode");
        List<String> roles;
        if ("SUPER_ADMIN".equals(roleCode)) {
            // 超级管理员拥有所有角色权限
            roles = Arrays.asList("SUPER_ADMIN", "ADMIN", "OPERATOR", "USER");
        } else {
            roles = roleCode != null ? Arrays.asList(roleCode) : Arrays.asList("USER");
        }
        String token = jwtService.generateToken(username, roles);
        String refreshToken = jwtService.generateRefreshToken(username);

        log.info("登录成功: username={}, role={}", username, user.get("roleCode"));

        Map<String, Object> data = new HashMap<>();
        data.put("token", token);
        data.put("refreshToken", refreshToken);
        data.put("tokenType", "Bearer");
        data.put("userId", user.get("id"));
        data.put("username", user.get("username"));
        data.put("role", user.get("roleCode"));
        if (user.get("tenantId") != null) {
            data.put("tenantId", user.get("tenantId"));
            data.put("tenantName", user.get("tenantName"));
        }

        return Result.success(data);
    }

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
    public static class LoginRequest {
        @NotBlank(message = "用户名不能为空")
        private String username;
        @NotBlank(message = "密码不能为空")
        private String password;
    }

    @Data
    public static class RefreshTokenRequest {
        @NotBlank(message = "refreshToken 不能为空")
        private String refreshToken;
    }

    /**
     * 重置密码（仅限SUPER_ADMIN和TENANT_ADMIN）
     */
    @PostMapping("/reset-password")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN')")
    public Result<String> resetPassword(@RequestBody Map<String, String> body) {
        String username = body.get("username");
        String newPassword = body.get("newPassword");
        if (username == null || newPassword == null) {
            return Result.error(400, "username 和 newPassword 不能为空");
        }

        // 获取当前操作者信息
        String operatorUsername = SecurityContextHolder.getContext().getAuthentication().getName();

        // 查询目标用户的租户ID
        List<Map<String, Object>> targetUsers = jdbcTemplate.query(
                "SELECT u.id, u.tenant_id, t.tenant_name " +
                "FROM sys_user u LEFT JOIN sys_tenant t ON u.tenant_id = t.id " +
                "WHERE u.username = ?",
                (rs, rowNum) -> {
                    Map<String, Object> row = new HashMap<>();
                    row.put("id", rs.getLong("id"));
                    row.put("tenantId", rs.getObject("tenant_id"));
                    row.put("tenantName", rs.getString("tenant_name"));
                    return row;
                },
                username
        );

        if (targetUsers.isEmpty()) {
            return Result.error(404, "用户不存在");
        }

        Map<String, Object> targetUser = targetUsers.get(0);
        Long targetTenantId = (Long) targetUser.get("tenantId");

        // 查询操作者的租户ID和角色
        List<Map<String, Object>> operators = jdbcTemplate.query(
                "SELECT u.tenant_id, r.role_code " +
                "FROM sys_user u " +
                "LEFT JOIN sys_user_role ur ON u.id = ur.user_id " +
                "LEFT JOIN sys_role r ON ur.role_id = r.id " +
                "WHERE u.username = ?",
                (rs, rowNum) -> {
                    Map<String, Object> row = new HashMap<>();
                    row.put("tenantId", rs.getObject("tenant_id"));
                    row.put("roleCode", rs.getString("role_code"));
                    return row;
                },
                operatorUsername
        );

        if (operators.isEmpty()) {
            return Result.error(403, "操作者信息异常");
        }

        Map<String, Object> operator = operators.get(0);
        Long operatorTenantId = (Long) operator.get("tenantId");
        String operatorRole = (String) operator.get("roleCode");

        // 租户隔离：TENANT_ADMIN只能重置同租户用户密码
        if (!"SUPER_ADMIN".equals(operatorRole)) {
            if (targetTenantId == null || !targetTenantId.equals(operatorTenantId)) {
                log.warn("密码重置失败: 无权重置其他租户用户密码 - operator={}, target={}",
                        operatorUsername, username);
                return Result.error(403, "无权重置其他租户用户密码");
            }
        }

        String encodedPassword = passwordEncoder.encode(newPassword);
        int updated = jdbcTemplate.update(
                "UPDATE sys_user SET password = ? WHERE username = ?",
                encodedPassword, username
        );
        if (updated > 0) {
            log.info("密码已重置: targetUser={}, operator={}, tenantId={}",
                    username, operatorUsername, targetTenantId);
            return Result.success("密码重置成功");
        }
        return Result.error(404, "用户不存在");
    }
}

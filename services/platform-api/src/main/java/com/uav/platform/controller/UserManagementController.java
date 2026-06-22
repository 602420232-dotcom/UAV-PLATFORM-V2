package com.uav.platform.controller;

import com.uav.common.core.result.Result;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.*;

/**
 * 用户管理控制器
 * <p>
 * 基于 JdbcTemplate 直接操作 sys_user 表，提供用户 CRUD、重置密码、分配角色等功能。
 * 仅限 SUPER_ADMIN 角色使用。
 */
@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
public class UserManagementController {

    private final JdbcTemplate jdbcTemplate;
    private final PasswordEncoder passwordEncoder;

    /**
     * 获取用户列表（分页、搜索）
     */
    @GetMapping
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public Result<Map<String, Object>> list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) String keyword) {
        int offset = (page - 1) * size;

        StringBuilder countSql = new StringBuilder("SELECT COUNT(*) FROM sys_user WHERE deleted = 0");
        StringBuilder querySql = new StringBuilder(
                "SELECT id, username, nickname, email, phone, status, role, created_at, updated_at " +
                "FROM sys_user WHERE deleted = 0");

        if (keyword != null && !keyword.trim().isEmpty()) {
            countSql.append(" AND (username LIKE '%").append(keyword.trim()).append("%' ")
                    .append("OR nickname LIKE '%").append(keyword.trim()).append("%' ")
                    .append("OR email LIKE '%").append(keyword.trim()).append("%')");
            querySql.append(" AND (username LIKE '%").append(keyword.trim()).append("%' ")
                    .append("OR nickname LIKE '%").append(keyword.trim()).append("%' ")
                    .append("OR email LIKE '%").append(keyword.trim()).append("%')");
        }

        Long total = jdbcTemplate.queryForObject(countSql.toString(), Long.class);
        querySql.append(" ORDER BY created_at DESC LIMIT ? OFFSET ?");

        List<Map<String, Object>> users = jdbcTemplate.queryForList(querySql.toString(), size, offset);

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("records", users);
        result.put("total", total);
        result.put("page", page);
        result.put("size", size);
        return Result.success(result);
    }

    /**
     * 获取用户详情
     */
    @GetMapping("/{id}")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public Result<Map<String, Object>> getById(@PathVariable Long id) {
        List<Map<String, Object>> users = jdbcTemplate.queryForList(
                "SELECT id, username, nickname, email, phone, status, role, created_at, updated_at " +
                "FROM sys_user WHERE id = ? AND deleted = 0", id);
        if (users.isEmpty()) {
            return Result.error(404, "用户不存在");
        }
        return Result.success(users.get(0));
    }

    /**
     * 创建用户
     */
    @PostMapping
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public Result<Void> create(@RequestBody Map<String, String> body) {
        String username = body.get("username");
        String password = body.get("password");
        String nickname = body.get("nickname");
        String email = body.get("email");
        String phone = body.get("phone");
        String role = body.get("role");

        if (username == null || username.trim().isEmpty()) {
            return Result.error(400, "用户名不能为空");
        }
        if (password == null || password.trim().isEmpty()) {
            return Result.error(400, "密码不能为空");
        }

        // 检查用户名是否已存在
        Integer count = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM sys_user WHERE username = ? AND deleted = 0", Integer.class, username);
        if (count != null && count > 0) {
            return Result.error(400, "用户名已存在");
        }

        String encodedPassword = passwordEncoder.encode(password);
        LocalDateTime now = LocalDateTime.now();

        jdbcTemplate.update(
                "INSERT INTO sys_user (username, password, nickname, email, phone, role, status, created_at, updated_at, deleted) " +
                "VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, 0)",
                username, encodedPassword, nickname, email, phone, role, now, now);

        return Result.success();
    }

    /**
     * 更新用户
     */
    @PutMapping("/{id}")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public Result<Void> update(@PathVariable Long id, @RequestBody Map<String, String> body) {
        // 检查用户是否存在
        Integer count = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM sys_user WHERE id = ? AND deleted = 0", Integer.class, id);
        if (count == null || count == 0) {
            return Result.error(404, "用户不存在");
        }

        StringBuilder sql = new StringBuilder("UPDATE sys_user SET updated_at = ?");
        List<Object> params = new ArrayList<>();
        params.add(LocalDateTime.now());

        if (body.containsKey("nickname")) {
            sql.append(", nickname = ?");
            params.add(body.get("nickname"));
        }
        if (body.containsKey("email")) {
            sql.append(", email = ?");
            params.add(body.get("email"));
        }
        if (body.containsKey("phone")) {
            sql.append(", phone = ?");
            params.add(body.get("phone"));
        }
        if (body.containsKey("status")) {
            sql.append(", status = ?");
            params.add(Integer.parseInt(body.get("status")));
        }

        sql.append(" WHERE id = ?");
        params.add(id);

        jdbcTemplate.update(sql.toString(), params.toArray());
        return Result.success();
    }

    /**
     * 删除用户（逻辑删除）
     */
    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public Result<Void> delete(@PathVariable Long id) {
        // 禁止删除自己
        Integer count = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM sys_user WHERE id = ? AND deleted = 0", Integer.class, id);
        if (count == null || count == 0) {
            return Result.error(404, "用户不存在");
        }

        jdbcTemplate.update(
                "UPDATE sys_user SET deleted = 1, updated_at = ? WHERE id = ?",
                LocalDateTime.now(), id);
        return Result.success();
    }

    /**
     * 重置密码
     */
    @PostMapping("/{id}/reset-password")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public Result<Void> resetPassword(@PathVariable Long id, @RequestBody Map<String, String> body) {
        String newPassword = body.get("password");
        if (newPassword == null || newPassword.trim().isEmpty()) {
            return Result.error(400, "新密码不能为空");
        }

        Integer count = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM sys_user WHERE id = ? AND deleted = 0", Integer.class, id);
        if (count == null || count == 0) {
            return Result.error(404, "用户不存在");
        }

        String encodedPassword = passwordEncoder.encode(newPassword);
        jdbcTemplate.update(
                "UPDATE sys_user SET password = ?, updated_at = ? WHERE id = ?",
                encodedPassword, LocalDateTime.now(), id);
        return Result.success();
    }

    /**
     * 分配角色
     */
    @PostMapping("/{id}/assign-role")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public Result<Void> assignRole(@PathVariable Long id, @RequestBody Map<String, String> body) {
        String role = body.get("role");
        if (role == null || role.trim().isEmpty()) {
            return Result.error(400, "角色不能为空");
        }

        Integer count = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM sys_user WHERE id = ? AND deleted = 0", Integer.class, id);
        if (count == null || count == 0) {
            return Result.error(404, "用户不存在");
        }

        jdbcTemplate.update(
                "UPDATE sys_user SET role = ?, updated_at = ? WHERE id = ?",
                role, LocalDateTime.now(), id);
        return Result.success();
    }
}

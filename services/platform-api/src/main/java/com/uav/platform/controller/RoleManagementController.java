package com.uav.platform.controller;

import com.uav.common.core.result.Result;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.*;

/**
 * 角色管理控制器
 * <p>
 * 基于 JdbcTemplate 直接操作 sys_role 表，提供角色 CRUD 功能。
 * 仅限 SUPER_ADMIN 角色使用。
 */
@RestController
@RequestMapping("/api/v1/roles")
@RequiredArgsConstructor
public class RoleManagementController {

    private final JdbcTemplate jdbcTemplate;

    /**
     * 获取角色列表
     */
    @GetMapping
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public Result<List<Map<String, Object>>> list() {
        List<Map<String, Object>> roles = jdbcTemplate.queryForList(
                "SELECT id, role_name, role_code, description, status, created_at, updated_at " +
                "FROM sys_role WHERE deleted = 0 ORDER BY created_at DESC");
        return Result.success(roles);
    }

    /**
     * 获取角色详情
     */
    @GetMapping("/{id}")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public Result<Map<String, Object>> getById(@PathVariable Long id) {
        List<Map<String, Object>> roles = jdbcTemplate.queryForList(
                "SELECT id, role_name, role_code, description, status, created_at, updated_at " +
                "FROM sys_role WHERE id = ? AND deleted = 0", id);
        if (roles.isEmpty()) {
            return Result.error(404, "角色不存在");
        }
        return Result.success(roles.get(0));
    }

    /**
     * 创建角色
     */
    @PostMapping
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public Result<Void> create(@RequestBody Map<String, String> body) {
        String roleName = body.get("roleName");
        String roleCode = body.get("roleCode");
        String description = body.get("description");

        if (roleName == null || roleName.trim().isEmpty()) {
            return Result.error(400, "角色名称不能为空");
        }
        if (roleCode == null || roleCode.trim().isEmpty()) {
            return Result.error(400, "角色编码不能为空");
        }

        // 检查角色编码是否已存在
        Integer count = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM sys_role WHERE role_code = ? AND deleted = 0", Integer.class, roleCode);
        if (count != null && count > 0) {
            return Result.error(400, "角色编码已存在");
        }

        LocalDateTime now = LocalDateTime.now();
        jdbcTemplate.update(
                "INSERT INTO sys_role (role_name, role_code, description, status, created_at, updated_at, deleted) " +
                "VALUES (?, ?, ?, 1, ?, ?, 0)",
                roleName, roleCode, description, now, now);

        return Result.success();
    }

    /**
     * 更新角色
     */
    @PutMapping("/{id}")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public Result<Void> update(@PathVariable Long id, @RequestBody Map<String, String> body) {
        Integer count = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM sys_role WHERE id = ? AND deleted = 0", Integer.class, id);
        if (count == null || count == 0) {
            return Result.error(404, "角色不存在");
        }

        StringBuilder sql = new StringBuilder("UPDATE sys_role SET updated_at = ?");
        List<Object> params = new ArrayList<>();
        params.add(LocalDateTime.now());

        if (body.containsKey("roleName")) {
            sql.append(", role_name = ?");
            params.add(body.get("roleName"));
        }
        if (body.containsKey("description")) {
            sql.append(", description = ?");
            params.add(body.get("description"));
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
     * 删除角色（逻辑删除）
     */
    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public Result<Void> delete(@PathVariable Long id) {
        Integer count = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM sys_role WHERE id = ? AND deleted = 0", Integer.class, id);
        if (count == null || count == 0) {
            return Result.error(404, "角色不存在");
        }

        jdbcTemplate.update(
                "UPDATE sys_role SET deleted = 1, updated_at = ? WHERE id = ?",
                LocalDateTime.now(), id);
        return Result.success();
    }
}

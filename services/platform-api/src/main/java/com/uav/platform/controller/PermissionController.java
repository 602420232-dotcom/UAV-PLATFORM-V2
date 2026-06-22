package com.uav.platform.controller;

import com.uav.common.core.result.Result;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.*;

/**
 * 权限管理控制器
 * <p>
 * 基于 JdbcTemplate 直接操作 sys_permission 表，提供权限列表查询功能。
 * 仅限 SUPER_ADMIN 角色使用。
 */
@RestController
@RequestMapping("/api/v1/permissions")
@RequiredArgsConstructor
public class PermissionController {

    private final JdbcTemplate jdbcTemplate;

    /**
     * 获取权限列表
     */
    @GetMapping
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public Result<List<Map<String, Object>>> list() {
        List<Map<String, Object>> permissions = jdbcTemplate.queryForList(
                "SELECT id, permission_name, permission_code, resource_type, parent_id, " +
                "path, method, description, status, created_at, updated_at " +
                "FROM sys_permission WHERE deleted = 0 ORDER BY parent_id, sort_order");
        return Result.success(permissions);
    }

    /**
     * 获取权限详情
     */
    @GetMapping("/{id}")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public Result<Map<String, Object>> getById(@PathVariable Long id) {
        List<Map<String, Object>> permissions = jdbcTemplate.queryForList(
                "SELECT id, permission_name, permission_code, resource_type, parent_id, " +
                "path, method, description, status, created_at, updated_at " +
                "FROM sys_permission WHERE id = ? AND deleted = 0", id);
        if (permissions.isEmpty()) {
            return Result.error(404, "权限不存在");
        }
        return Result.success(permissions.get(0));
    }
}

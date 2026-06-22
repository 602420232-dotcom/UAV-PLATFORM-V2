package com.uav.platform.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.uav.common.core.result.Result;
import com.uav.platform.entity.Tenant;
import com.uav.platform.service.TenantService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;

@RestController
@RequestMapping("/api/v1/tenants")
@RequiredArgsConstructor
@Validated
public class TenantController {

    private final TenantService tenantService;

    /**
     * 创建租户 - 仅 ADMIN 角色可操作
     */
    @PostMapping
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN')")
    public Result<Tenant> create(@Valid @RequestBody CreateTenantRequest request) {
        Tenant tenant = tenantService.createTenant(
                request.getName(),
                request.getSchemaName(),
                request.getQuotaConfig()
        );
        return Result.success(tenant);
    }

    /**
     * 查询租户详情 - ADMIN 或 OPERATOR 可查看
     */
    @GetMapping("/{id}")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN', 'OPERATOR')")
    public Result<Tenant> getById(@PathVariable Long id) {
        return Result.success(tenantService.getById(id));
    }

    /**
     * 分页查询租户列表 - ADMIN 或 OPERATOR 可查看
     */
    @GetMapping
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN', 'OPERATOR')")
    public Result<Page<Tenant>> list(
            @RequestParam(defaultValue = "1") Integer current,
            @RequestParam(defaultValue = "10") Integer size) {
        Page<Tenant> page = tenantService.page(new Page<>(current, size));
        return Result.success(page);
    }

    /**
     * 更新租户 - 仅 ADMIN 角色可操作
     */
    @PutMapping("/{id}")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN')")
    public Result<Void> update(@PathVariable Long id, @Valid @RequestBody UpdateTenantRequest request) {
        Tenant tenant = new Tenant();
        tenant.setId(id);
        tenant.setName(request.getName());
        tenant.setQuotaConfig(request.getQuotaConfig());
        tenantService.updateById(tenant);
        return Result.success();
    }

    /**
     * 禁用租户 - 仅 ADMIN 角色可操作
     */
    @PostMapping("/{id}/disable")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN')")
    public Result<Void> disable(@PathVariable Long id) {
        tenantService.disableTenant(id);
        return Result.success();
    }

    /**
     * 启用租户 - 仅 ADMIN 角色可操作
     */
    @PostMapping("/{id}/enable")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN')")
    public Result<Void> enable(@PathVariable Long id) {
        tenantService.enableTenant(id);
        return Result.success();
    }

    /**
     * 删除租户 - 仅 ADMIN 角色（SUPER_ADMIN 权限）可操作
     */
    @DeleteMapping("/{id}")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN')")
    public Result<Void> delete(@PathVariable Long id) {
        tenantService.removeById(id);
        return Result.success();
    }

    @lombok.Data
    public static class CreateTenantRequest {
        @NotBlank
        private String name;
        @NotBlank
        private String schemaName;
        private String quotaConfig;
    }

    @lombok.Data
    public static class UpdateTenantRequest {
        private String name;
        private String quotaConfig;
    }
}

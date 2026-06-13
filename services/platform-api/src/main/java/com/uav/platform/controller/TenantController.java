package com.uav.platform.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.uav.common.core.result.Result;
import com.uav.platform.entity.Tenant;
import com.uav.platform.service.TenantService;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;

@RestController
@RequestMapping("/api/v1/tenants")
@RequiredArgsConstructor
@Validated
public class TenantController {

    private final TenantService tenantService;

    @PostMapping
    public Result<Tenant> create(@Valid @RequestBody CreateTenantRequest request) {
        Tenant tenant = tenantService.createTenant(
                request.getName(),
                request.getSchemaName(),
                request.getQuotaConfig()
        );
        return Result.success(tenant);
    }

    @GetMapping("/{id}")
    public Result<Tenant> getById(@PathVariable Long id) {
        return Result.success(tenantService.getById(id));
    }

    @GetMapping
    public Result<Page<Tenant>> list(
            @RequestParam(defaultValue = "1") Integer current,
            @RequestParam(defaultValue = "10") Integer size) {
        Page<Tenant> page = tenantService.page(new Page<>(current, size));
        return Result.success(page);
    }

    @PutMapping("/{id}")
    public Result<Void> update(@PathVariable Long id, @Valid @RequestBody UpdateTenantRequest request) {
        Tenant tenant = new Tenant();
        tenant.setId(id);
        tenant.setName(request.getName());
        tenant.setQuotaConfig(request.getQuotaConfig());
        tenantService.updateById(tenant);
        return Result.success();
    }

    @PostMapping("/{id}/disable")
    public Result<Void> disable(@PathVariable Long id) {
        tenantService.disableTenant(id);
        return Result.success();
    }

    @PostMapping("/{id}/enable")
    public Result<Void> enable(@PathVariable Long id) {
        tenantService.enableTenant(id);
        return Result.success();
    }

    @DeleteMapping("/{id}")
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

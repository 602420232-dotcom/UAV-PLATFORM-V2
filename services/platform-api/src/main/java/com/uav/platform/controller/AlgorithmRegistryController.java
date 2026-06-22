package com.uav.platform.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.uav.common.core.result.Result;
import com.uav.platform.entity.AlgorithmRegistration;
import com.uav.platform.service.AlgorithmRegistryService;
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
import jakarta.validation.constraints.Pattern;
import java.util.List;
import java.util.Map;

/**
 * 算法注册中心控制器
 * 提供算法注册、查询、注销、版本管理等功能
 */
@RestController
@RequestMapping("/api/v1/algorithms")
@RequiredArgsConstructor
@Validated
public class AlgorithmRegistryController {

    private final AlgorithmRegistryService algorithmRegistryService;

    /**
     * 注册新算法
     * POST /api/v1/algorithms/register
     */
    @PostMapping("/register")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'ALGORITHM_ADMIN', 'OPERATOR')")
    public Result<AlgorithmRegistration> register(@Valid @RequestBody RegisterAlgorithmRequest request) {
        AlgorithmRegistration registration = new AlgorithmRegistration();
        registration.setName(request.getName());
        registration.setType(request.getType());
        registration.setVersion(request.getVersion());
        registration.setEndpoint(request.getEndpoint());
        registration.setParamSchema(request.getParamSchema());
        registration.setDescription(request.getDescription());

        AlgorithmRegistration saved = algorithmRegistryService.register(registration);
        return Result.success(saved);
    }

    /**
     * 列出所有已注册算法（支持分页和筛选）
     * GET /api/v1/algorithms
     */
    @GetMapping({"", "/list"})
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'ALGORITHM_ADMIN', 'OPERATOR', 'TENANT_ADMIN')")
    public Result<Page<AlgorithmRegistration>> list(
            @RequestParam(defaultValue = "1") Integer current,
            @RequestParam(defaultValue = "20") Integer size,
            @RequestParam(required = false) String type,
            @RequestParam(required = false) Integer status,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String algorithmType,
            @RequestParam(required = false) String algorithmLevel) {
        Page<AlgorithmRegistration> page = algorithmRegistryService.listAlgorithms(current, size, type, status, keyword, algorithmType, algorithmLevel);
        return Result.success(page);
    }

    /**
     * 获取算法详情
     * GET /api/v1/algorithms/{id}
     */
    @GetMapping("/{id}")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'ALGORITHM_ADMIN', 'OPERATOR', 'TENANT_ADMIN')")
    public Result<AlgorithmRegistration> getById(@PathVariable Long id) {
        AlgorithmRegistration registration = algorithmRegistryService.getById(id);
        if (registration == null) {
            return Result.error(404, "算法不存在: " + id);
        }
        return Result.success(registration);
    }

    /**
     * 注销算法
     * DELETE /api/v1/algorithms/{id}
     */
    @DeleteMapping("/{id}")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'ALGORITHM_ADMIN')")
    public Result<Void> delete(@PathVariable Long id) {
        algorithmRegistryService.unregister(id);
        return Result.success();
    }

    /**
     * 发布新版本
     * POST /api/v1/algorithms/{id}/versions
     */
    @PostMapping("/{id}/versions")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'ALGORITHM_ADMIN', 'OPERATOR')")
    public Result<AlgorithmRegistration> publishVersion(
            @PathVariable Long id,
            @Valid @RequestBody PublishVersionRequest request) {
        AlgorithmRegistration newVersion = algorithmRegistryService.publishVersion(
                id, request.getVersion(), request.getEndpoint(), request.getParamSchema());
        return Result.success(newVersion);
    }

    /**
     * 获取指定算法的所有版本
     * GET /api/v1/algorithms/{id}/versions
     */
    @GetMapping("/{id}/versions")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'ALGORITHM_ADMIN', 'OPERATOR', 'TENANT_ADMIN')")
    public Result<List<AlgorithmRegistration>> getVersions(@PathVariable Long id) {
        AlgorithmRegistration base = algorithmRegistryService.getById(id);
        if (base == null) {
            return Result.error(404, "算法不存在: " + id);
        }
        List<AlgorithmRegistration> versions = algorithmRegistryService.getVersions(base.getName());
        return Result.success(versions);
    }

    /**
     * 执行算法健康检查
     * POST /api/v1/algorithms/{id}/health-check
     */
    @PostMapping("/{id}/health-check")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'ALGORITHM_ADMIN', 'OPERATOR')")
    public Result<Boolean> healthCheck(@PathVariable Long id) {
        boolean healthy = algorithmRegistryService.healthCheck(id);
        return Result.success(healthy);
    }

    /**
     * 批量健康检查所有已启用算法
     * POST /api/v1/algorithms/health-check-all
     */
    @PostMapping("/health-check-all")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'ALGORITHM_ADMIN')")
    public Result<Void> healthCheckAll() {
        algorithmRegistryService.healthCheckAll();
        return Result.success();
    }

    // ==================== Phase 8 新增端点 ====================

    /**
     * 算法统计（按分类统计数量）
     * GET /api/v1/algorithms/registry/stats
     */
    @GetMapping("/registry/stats")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'ALGORITHM_ADMIN', 'OPERATOR', 'TENANT_ADMIN')")
    public Result<Map<String, Object>> getRegistryStats() {
        Map<String, Object> stats = algorithmRegistryService.getCategoryStats();
        return Result.success(stats);
    }

    /**
     * 按分类查询算法列表
     * GET /api/v1/algorithms/registry/{category}
     */
    @GetMapping("/registry/{category}")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'ALGORITHM_ADMIN', 'OPERATOR', 'TENANT_ADMIN')")
    public Result<List<AlgorithmRegistration>> listByCategory(@PathVariable String category) {
        List<AlgorithmRegistration> list = algorithmRegistryService.listByCategory(category);
        return Result.success(list);
    }

    /**
     * 启用/禁用算法
     * PUT /api/v1/algorithms/registry/{id}/status
     */
    @PutMapping("/registry/{id}/status")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'ALGORITHM_ADMIN')")
    public Result<Void> toggleStatus(
            @PathVariable Long id,
            @RequestParam boolean enable) {
        algorithmRegistryService.toggleStatus(id, enable);
        return Result.success();
    }

    /**
     * 测试算法运行（调用Python引擎）
     * POST /api/v1/algorithms/registry/{id}/test
     */
    @PostMapping("/registry/{id}/test")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'ALGORITHM_ADMIN', 'OPERATOR')")
    public Result<Map<String, Object>> testAlgorithm(
            @PathVariable Long id,
            @RequestBody(required = false) Map<String, Object> params) {
        Map<String, Object> result = algorithmRegistryService.testAlgorithm(id, params);
        return Result.success(result);
    }

    /**
     * 更新算法状态
     * POST /api/v1/algorithms/{id}/status
     */
    @PostMapping("/{id}/status")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'ALGORITHM_ADMIN')")
    public Result<Void> updateStatus(
            @PathVariable Long id,
            @RequestParam Integer status) {
        algorithmRegistryService.updateStatus(id, status);
        return Result.success();
    }

    // ==================== 请求 DTO ====================

    @lombok.Data
    public static class RegisterAlgorithmRequest {
        @NotBlank(message = "算法名称不能为空")
        private String name;

        @NotBlank(message = "算法类型不能为空")
        @Pattern(regexp = "planning|observation|assimilation|risk|weather|fusion|generic",
                message = "不支持的算法类型")
        private String type;

        @NotBlank(message = "版本号不能为空")
        @Pattern(regexp = "^(0|[1-9]\\d*)\\.(0|[1-9]\\d*)\\.(0|[1-9]\\d*)(?:-.*)?$",
                message = "版本号格式不正确，请使用语义化版本格式（如：1.0.0）")
        private String version;

        @NotBlank(message = "端点不能为空")
        private String endpoint;

        private String paramSchema;

        private String description;
    }

    @lombok.Data
    public static class PublishVersionRequest {
        @NotBlank(message = "版本号不能为空")
        @Pattern(regexp = "^(0|[1-9]\\d*)\\.(0|[1-9]\\d*)\\.(0|[1-9]\\d*)(?:-.*)?$",
                message = "版本号格式不正确，请使用语义化版本格式（如：1.0.0）")
        private String version;

        private String endpoint;

        private String paramSchema;
    }
}

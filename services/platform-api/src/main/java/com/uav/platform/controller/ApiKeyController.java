package com.uav.platform.controller;

import com.uav.common.core.result.Result;
import com.uav.platform.entity.ApiKey;
import com.uav.platform.service.ApiKeyServiceImpl;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.util.List;

@RestController
@RequestMapping("/api/v1/api-keys")
@RequiredArgsConstructor
@Validated
public class ApiKeyController {

    private final ApiKeyServiceImpl apiKeyService;

    @PostMapping
    public Result<ApiKey> generate(@Valid @RequestBody GenerateApiKeyRequest request) {
        ApiKey apiKey = apiKeyService.generateApiKey(
                request.getTenantId(),
                request.getName(),
                request.getRateLimit(),
                request.getExpiresInDays()
        );
        return Result.success(apiKey);
    }

    @GetMapping("/{id}")
    public Result<ApiKey> getById(@PathVariable Long id) {
        return Result.success(apiKeyService.getById(id));
    }

    @GetMapping("/tenant/{tenantId}")
    public Result<List<ApiKey>> listByTenant(@PathVariable Long tenantId) {
        return Result.success(apiKeyService.listByTenant(tenantId));
    }

    @PostMapping("/{id}/enable")
    public Result<Void> enable(@PathVariable Long id) {
        apiKeyService.enableApiKey(id);
        return Result.success();
    }

    @PostMapping("/{id}/disable")
    public Result<Void> disable(@PathVariable Long id) {
        apiKeyService.disableApiKey(id);
        return Result.success();
    }

    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable Long id) {
        apiKeyService.removeApiKey(id);
        return Result.success();
    }

    @lombok.Data
    public static class GenerateApiKeyRequest {
        @NotNull
        private Long tenantId;
        @NotBlank
        private String name;
        private Integer rateLimit;
        private Integer expiresInDays;
    }
}

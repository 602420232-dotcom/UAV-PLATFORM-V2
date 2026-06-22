package com.uav.utm.controller;

import com.uav.common.core.result.Result;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

/**
 * UTM 环境配置控制器
 * <p>
 * 提供 UTM 双环境（模拟/真实）的配置查询和切换接口。
 * 仅 SUPER_ADMIN 和 TENANT_ADMIN 可修改配置。
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/utm/environment")
@RequiredArgsConstructor
public class UtmEnvironmentController {

    @Value("${uav.mock.enabled:true}")
    private boolean mockEnabled;

    @Value("${uav.utm.external.enabled:false}")
    private boolean externalUtmEnabled;

    @Value("${uav.utm.external.base-url:http://external-utm-api:8080}")
    private String externalUtmBaseUrl;

    @Value("${uav.utm.external.api-key:}")
    private String externalUtmApiKey;

    /**
     * 获取当前 UTM 环境配置
     */
    @GetMapping("/config")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN', 'OPERATOR')")
    public Result<UtmEnvironmentConfig> getConfig() {
        UtmEnvironmentConfig config = new UtmEnvironmentConfig();
        config.setMockEnabled(mockEnabled);
        config.setExternalUtmEnabled(externalUtmEnabled);
        config.setExternalUtmBaseUrl(externalUtmBaseUrl);
        config.setExternalUtmApiKey(maskApiKey(externalUtmApiKey));
        config.setCurrentMode(detectCurrentMode());
        return Result.success(config);
    }

    /**
     * 切换 UTM 环境模式
     * <p>
     * 模式说明：
     * <ul>
     *   <li>MOCK: 模拟模式 - 使用本地模拟数据，不连接外部UTM</li>
     *   <li>EXTERNAL: 真实模式 - 连接外部UTM系统</li>
     * </ul>
     */
    @PostMapping("/switch")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN')")
    public Result<Map<String, String>> switchMode(@RequestBody SwitchModeRequest request) {
        String mode = request.getMode();
        Map<String, String> result = new HashMap<>();

        switch (mode.toUpperCase()) {
            case "MOCK":
                // 模拟模式：mock=true, external=false
                result.put("mockEnabled", "true");
                result.put("externalUtmEnabled", "false");
                result.put("mode", "MOCK");
                result.put("message", "已切换到模拟模式：使用本地模拟数据，不连接外部UTM");
                log.info("UTM环境已切换到模拟模式 (操作者: {})",
                        org.springframework.security.core.context.SecurityContextHolder.getContext().getAuthentication().getName());
                break;

            case "EXTERNAL":
                // 真实模式：mock=false, external=true
                result.put("mockEnabled", "false");
                result.put("externalUtmEnabled", "true");
                result.put("mode", "EXTERNAL");
                result.put("message", "已切换到真实模式：连接外部UTM系统");
                log.info("UTM环境已切换到真实模式 (操作者: {})",
                        org.springframework.security.core.context.SecurityContextHolder.getContext().getAuthentication().getName());
                break;

            case "HYBRID":
                // 混合模式：mock=false, external=true（本地处理+外部同步）
                result.put("mockEnabled", "false");
                result.put("externalUtmEnabled", "true");
                result.put("mode", "HYBRID");
                result.put("message", "已切换到混合模式：本地处理+外部UTM同步");
                log.info("UTM环境已切换到混合模式 (操作者: {})",
                        org.springframework.security.core.context.SecurityContextHolder.getContext().getAuthentication().getName());
                break;

            default:
                return Result.error(400, "无效模式: " + mode + ". 支持模式: MOCK, EXTERNAL, HYBRID");
        }

        return Result.success(result);
    }

    /**
     * 测试外部 UTM 连接
     */
    @PostMapping("/test-connection")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN')")
    public Result<Map<String, Object>> testExternalConnection() {
        Map<String, Object> result = new HashMap<>();

        if (!externalUtmEnabled) {
            result.put("success", false);
            result.put("message", "外部UTM未启用，请先切换到 EXTERNAL 或 HYBRID 模式");
            return Result.success(result);
        }

        try {
            // 简单的连接测试（HEAD请求）
            org.springframework.web.client.RestTemplate restTemplate = new org.springframework.web.client.RestTemplate();
            org.springframework.http.ResponseEntity<Void> response = restTemplate.exchange(
                    externalUtmBaseUrl + "/health",
                    org.springframework.http.HttpMethod.HEAD,
                    null,
                    Void.class
            );

            result.put("success", true);
            result.put("statusCode", response.getStatusCode().value());
            result.put("message", "外部UTM连接成功");
            log.info("外部UTM连接测试成功: {}", externalUtmBaseUrl);
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", "连接失败: " + e.getMessage());
            log.warn("外部UTM连接测试失败: {}", e.getMessage());
        }

        return Result.success(result);
    }

    /**
     * 获取当前运行模式
     */
    private String detectCurrentMode() {
        if (mockEnabled && !externalUtmEnabled) {
            return "MOCK";
        } else if (!mockEnabled && externalUtmEnabled) {
            return "EXTERNAL";
        } else if (!mockEnabled) {
            return "HYBRID";
        }
        return "UNKNOWN";
    }

    private String maskApiKey(String apiKey) {
        if (apiKey == null || apiKey.length() < 8) {
            return "***";
        }
        return apiKey.substring(0, 4) + "****" + apiKey.substring(apiKey.length() - 4);
    }

    @Data
    public static class UtmEnvironmentConfig {
        private boolean mockEnabled;
        private boolean externalUtmEnabled;
        private String externalUtmBaseUrl;
        private String externalUtmApiKey;
        private String currentMode;
    }

    @Data
    public static class SwitchModeRequest {
        private String mode;
    }
}

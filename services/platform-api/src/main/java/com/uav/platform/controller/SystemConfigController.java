package com.uav.platform.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.uav.common.core.result.Result;
import com.uav.platform.entity.SystemConfig;
import com.uav.platform.mapper.SystemConfigMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 系统配置控制器
 * <p>
 * 提供系统级配置管理，包括演示模式开关等功能。
 */
@RestController
@RequestMapping("/api/v1/system/config")
@RequiredArgsConstructor
@Slf4j
public class SystemConfigController {

    private final SystemConfigMapper systemConfigMapper;

    private static final String DEMO_MODE_KEY = "is_demo_mode";

    /**
     * 获取当前演示模式状态（公开接口，不需要认证）
     */
    @GetMapping("/demo-mode")
    public Result<Map<String, Object>> getDemoMode() {
        LambdaQueryWrapper<SystemConfig> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(SystemConfig::getConfigKey, DEMO_MODE_KEY);
        SystemConfig config = systemConfigMapper.selectOne(wrapper);

        Map<String, Object> result = new LinkedHashMap<>();
        if (config == null) {
            result.put("demoMode", false);
        } else {
            result.put("demoMode", "true".equalsIgnoreCase(config.getConfigValue()));
        }
        return Result.success(result);
    }

    /**
     * 切换演示模式（需要 SUPER_ADMIN 或 TENANT_ADMIN 角色）
     */
    @PutMapping("/demo-mode")
    @PreAuthorize("hasAnyRole('SUPER_ADMIN', 'TENANT_ADMIN')")
    public Result<Void> updateDemoMode(@RequestBody Map<String, Boolean> body) {
        Boolean enabled = body.get("enabled");
        if (enabled == null) {
            return Result.error(400, "enabled 参数不能为空");
        }

        // 获取当前用户名
        String username = getCurrentUsername();

        // 查询是否已存在该配置
        LambdaQueryWrapper<SystemConfig> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(SystemConfig::getConfigKey, DEMO_MODE_KEY);
        SystemConfig existing = systemConfigMapper.selectOne(wrapper);

        LocalDateTime now = LocalDateTime.now();

        if (existing != null) {
            // 更新
            existing.setConfigValue(String.valueOf(enabled));
            existing.setDescription("系统演示模式开关");
            existing.setUpdatedBy(username);
            existing.setUpdatedAt(now);
            systemConfigMapper.updateById(existing);
        } else {
            // 插入
            SystemConfig newConfig = new SystemConfig();
            newConfig.setConfigKey(DEMO_MODE_KEY);
            newConfig.setConfigValue(String.valueOf(enabled));
            newConfig.setDescription("系统演示模式开关");
            newConfig.setUpdatedBy(username);
            newConfig.setCreatedAt(now);
            newConfig.setUpdatedAt(now);
            systemConfigMapper.insert(newConfig);
        }

        log.info("演示模式已由 {} 设置为 {}", username, enabled);
        return Result.success();
    }

    /**
     * 获取所有系统配置（需要认证）
     */
    @GetMapping
    public Result<List<SystemConfig>> getAllConfigs() {
        List<SystemConfig> configs = systemConfigMapper.selectList(null);
        return Result.success(configs);
    }

    /**
     * 从 SecurityContext 获取当前用户名
     */
    private String getCurrentUsername() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !authentication.isAuthenticated()) {
            return "system";
        }
        Object principal = authentication.getPrincipal();
        if (principal instanceof String) {
            return (String) principal;
        }
        return authentication.getName();
    }
}

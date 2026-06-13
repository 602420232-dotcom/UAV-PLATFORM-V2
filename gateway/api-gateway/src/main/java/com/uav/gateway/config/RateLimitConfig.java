package com.uav.gateway.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

import java.util.HashMap;
import java.util.Map;

/**
 * Rate Limit Configuration
 * Defines different rate limit thresholds for different API endpoints and tenants
 */
@Data
@Configuration
@ConfigurationProperties(prefix = "gateway.rate-limit")
public class RateLimitConfig {

    /**
     * Default QPS limit for tenants
     */
    private long defaultTenantQps = 1000;

    /**
     * Default QPS limit for API keys
     */
    private long defaultApiKeyQps = 100;

    /**
     * Default WebSocket connection limit per tenant
     */
    private long defaultWsConnections = 50;

    /**
     * Rate limit window in seconds
     */
    private int windowSeconds = 1;

    /**
     * Per-tenant QPS overrides
     * Key: tenant ID, Value: QPS limit
     */
    private Map<String, Long> tenantLimits = new HashMap<>();

    /**
     * Per-API-key QPS overrides
     * Key: API key, Value: QPS limit
     */
    private Map<String, Long> apiKeyLimits = new HashMap<>();

    /**
     * Per-path QPS overrides
     * Key: path pattern, Value: QPS limit
     */
    private Map<String, Long> pathLimits = new HashMap<>();

    /**
     * WebSocket connection limits per tenant
     * Key: tenant ID, Value: connection limit
     */
    private Map<String, Long> wsConnectionLimits = new HashMap<>();

    /**
     * Get tenant QPS limit with fallback to default
     */
    public long getTenantQps(String tenantId) {
        return tenantLimits.getOrDefault(tenantId, defaultTenantQps);
    }

    /**
     * Get API key QPS limit with fallback to default
     */
    public long getApiKeyQps(String apiKey) {
        return apiKeyLimits.getOrDefault(apiKey, defaultApiKeyQps);
    }

    /**
     * Get path-specific QPS limit with fallback to tenant default
     */
    public long getPathLimit(String path, String tenantId) {
        // Check exact path match first
        if (pathLimits.containsKey(path)) {
            return pathLimits.get(path);
        }
        // Check prefix matches
        for (Map.Entry<String, Long> entry : pathLimits.entrySet()) {
            if (path.startsWith(entry.getKey().replace("/**", ""))) {
                return entry.getValue();
            }
        }
        // Fall back to tenant limit
        return getTenantQps(tenantId);
    }

    /**
     * Get WebSocket connection limit with fallback to default
     */
    public long getWsConnectionLimit(String tenantId) {
        return wsConnectionLimits.getOrDefault(tenantId, defaultWsConnections);
    }
}

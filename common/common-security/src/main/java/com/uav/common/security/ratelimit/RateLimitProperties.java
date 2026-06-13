package com.uav.common.security.ratelimit;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;

/**
 * 限流配置属性
 * <p>
 * 从 application.yml 中读取限流相关配置，支持按 API 路径自定义限流规则。
 * <p>
 * 配置示例：
 * <pre>
 * security:
 *   ratelimit:
 *     enabled: true
 *     default-max-requests: 100
 *     default-window-seconds: 60
 *     key-prefix: "uav:ratelimit"
 *     api-rules:
 *       "/api/v1/planning/**": 50
 *       "/api/v1/weather/**": 200
 * </pre>
 */
@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "security.ratelimit")
public class RateLimitProperties {

    /** 是否启用限流 */
    private boolean enabled = true;

    /** 默认最大请求数（每个时间窗口） */
    private int defaultMaxRequests = 100;

    /** 默认时间窗口（秒） */
    private int defaultWindowSeconds = 60;

    /** Redis key 前缀 */
    private String keyPrefix = "uav:ratelimit";

    /** 按 API 路径自定义限流规则（路径 -> 最大请求数） */
    private Map<String, Integer> apiRules = new HashMap<>();

    /**
     * 获取指定 API 路径的最大请求数
     *
     * @param apiPath API 路径
     * @return 最大请求数，未配置则返回默认值
     */
    public int getMaxRequestsForPath(String apiPath) {
        return apiRules.entrySet().stream()
                .filter(entry -> pathMatches(apiPath, entry.getKey()))
                .map(Map.Entry::getValue)
                .findFirst()
                .orElse(defaultMaxRequests);
    }

    /**
     * 简单的路径匹配（支持 * 通配符）
     *
     * @param path     实际路径
     * @param pattern  匹配模式
     * @return 是否匹配
     */
    private boolean pathMatches(String path, String pattern) {
        if (pattern.equals(path)) {
            return true;
        }
        if (pattern.endsWith("/**")) {
            String prefix = pattern.substring(0, pattern.length() - 3);
            return path.startsWith(prefix) || path.equals(prefix.substring(0, prefix.length() - 1));
        }
        if (pattern.endsWith("/*")) {
            String prefix = pattern.substring(0, pattern.length() - 2);
            return path.startsWith(prefix);
        }
        return false;
    }
}

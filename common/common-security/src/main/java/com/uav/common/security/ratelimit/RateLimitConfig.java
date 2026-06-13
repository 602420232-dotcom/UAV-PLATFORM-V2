package com.uav.common.security.ratelimit;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 限流配置
 * <p>
 * 定义单个限流规则的参数，包括限流类型、时间窗口和最大请求数。
 */
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RateLimitConfig {

    /** 限流类型 */
    private RateLimitType type;

    /** 时间窗口（秒） */
    @Builder.Default
    private long windowSeconds = 60;

    /** 时间窗口内最大请求数 */
    @Builder.Default
    private int maxRequests = 100;

    /** Redis key 前缀 */
    @Builder.Default
    private String keyPrefix = "ratelimit";

    /**
     * 创建全局限流配置
     *
     * @param maxRequests  最大请求数
     * @param windowSeconds 时间窗口（秒）
     * @return 限流配置
     */
    public static RateLimitConfig global(int maxRequests, long windowSeconds) {
        return RateLimitConfig.builder()
                .type(RateLimitType.GLOBAL)
                .maxRequests(maxRequests)
                .windowSeconds(windowSeconds)
                .build();
    }

    /**
     * 创建用户级限流配置
     *
     * @param maxRequests  最大请求数
     * @param windowSeconds 时间窗口（秒）
     * @return 限流配置
     */
    public static RateLimitConfig perUser(int maxRequests, long windowSeconds) {
        return RateLimitConfig.builder()
                .type(RateLimitType.USER)
                .maxRequests(maxRequests)
                .windowSeconds(windowSeconds)
                .build();
    }

    /**
     * 创建接口级限流配置
     *
     * @param maxRequests  最大请求数
     * @param windowSeconds 时间窗口（秒）
     * @return 限流配置
     */
    public static RateLimitConfig perApi(int maxRequests, long windowSeconds) {
        return RateLimitConfig.builder()
                .type(RateLimitType.API)
                .maxRequests(maxRequests)
                .windowSeconds(windowSeconds)
                .build();
    }
}

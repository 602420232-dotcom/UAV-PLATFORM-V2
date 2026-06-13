package com.uav.common.resilience.enums;

import lombok.Getter;

/**
 * 限流等级枚举
 */
@Getter
public enum RateLimitTier {

    /** 默认等级 */
    DEFAULT("default", 100, 1000),

    /** 飞行关键操作 */
    FLIGHT_CRITICAL("flight-critical", 50, 500),

    /** 重度计算 */
    HEAVY_COMPUTATION("heavy-computation", 20, 200);

    private final String name;
    private final int limitForPeriod;
    private final int limitRefreshPeriodMs;

    RateLimitTier(String name, int limitForPeriod, int limitRefreshPeriodMs) {
        this.name = name;
        this.limitForPeriod = limitForPeriod;
        this.limitRefreshPeriodMs = limitRefreshPeriodMs;
    }
}

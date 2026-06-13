package com.uav.common.security.ratelimit;

/**
 * 限流类型枚举
 * <p>
 * 定义三种限流维度：
 * <ul>
 *     <li>GLOBAL — 全局限流，所有用户共享配额</li>
 *     <li>USER — 用户级限流，按用户ID分别计数</li>
 *     <li>API — 接口级限流，按 API 路径分别计数</li>
 * </ul>
 */
public enum RateLimitType {

    /** 全局限流：所有请求共享同一个计数器 */
    GLOBAL("全局限流"),

    /** 用户级限流：按用户ID分别计数 */
    USER("用户级限流"),

    /** 接口级限流：按 API 路径分别计数 */
    API("接口级限流");

    private final String description;

    RateLimitType(String description) {
        this.description = description;
    }

    public String getDescription() {
        return description;
    }
}

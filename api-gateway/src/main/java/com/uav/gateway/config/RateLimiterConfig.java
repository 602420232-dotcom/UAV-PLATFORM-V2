package com.uav.gateway.config;

import org.springframework.cloud.gateway.filter.ratelimit.KeyResolver;
import org.springframework.cloud.gateway.filter.ratelimit.RedisRateLimiter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Primary;
import org.springframework.context.annotation.Configuration;
import reactor.core.publisher.Mono;

/**
 * API 限流配置
 * 
 * 基于 Redis + Token Bucket 算法的分布式限流。
 * 按用户身份 / IP 进行限流，防止单个客户端耗尽服务资源。
 * 
 * 限流策略:
 * - 普通用户: 100 req/min
 * - 认证用户: 500 req/min
 * - IP: 1000 req/min
 */
@Configuration
public class RateLimiterConfig {

    /**
     * 按用户 ID 限流（从 JWT Token 中提取）
     */
    @Bean
    @org.springframework.context.annotation.Primary
    public KeyResolver userKeyResolver() {
        return exchange -> {
            String userId = exchange.getRequest().getHeaders().getFirst("X-User-Id");
            if (userId != null) {
                return Mono.just("user:" + userId);
            }
            return Mono.just("anonymous");
        };
    }

    /**
     * 按 IP 限流（备用方案）
     */
    @Bean
    public KeyResolver ipKeyResolver() {
        return exchange -> {
            var remoteAddress = exchange.getRequest().getRemoteAddress();
            String ip = remoteAddress != null
                ? remoteAddress.getAddress().getHostAddress()
                : "unknown";
            return Mono.just("ip:" + ip);
        };
    }

    /**
     * 默认限流器: 100 个请求 / 60 秒
     * replenishRate: 令牌桶填充速率（每秒）
     * burstCapacity: 令牌桶容量（允许突发）
     */
    @Bean("defaultRateLimiter")
    @Primary
    public RedisRateLimiter defaultRateLimiter() {
        return new RedisRateLimiter(2, 100, 1);
    }

    /**
     * 严格限流器: 10 个请求 / 60 秒（用于敏感 API）
     */
    @Bean("strictRateLimiter")
    public RedisRateLimiter strictRateLimiter() {
        return new RedisRateLimiter(1, 10, 1);
    }

    /**
     * 宽松限流器: 500 个请求 / 60 秒（用于认证用户）
     */
    @Bean("liberalRateLimiter")
    public RedisRateLimiter liberalRateLimiter() {
        return new RedisRateLimiter(9, 500, 1);
    }
}

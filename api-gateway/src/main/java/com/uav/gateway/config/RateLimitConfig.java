package com.uav.gateway.config;

import org.springframework.cloud.gateway.filter.ratelimit.KeyResolver;
import org.springframework.cloud.gateway.filter.ratelimit.RedisRateLimiter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.util.Optional;

/**
 * Gateway 限流配置。
 * <p>
 * 支持三级限流策略：
 * 1. Demo 用户：最低阈值（5 req/min）— 限制演示用户测试
 * 2. 普通用户：中等阈值（60 req/min per user）
 * 3. IP 级别：基础防护（1000 req/min per IP）
 * </p>
 *
 * 使用方式 (application.yml):
 * <pre>{@code
 * filters:
 *   - name: RequestRateLimiter
 *     args:
 *       key-resolver: "#{@demoUserKeyResolver}"
 *       redis-rate-limiter:
 *         replenishRate: 5
 *         burstCapacity: 10
 * }</pre>
 */
@Configuration
public class RateLimitConfig {

    // ─── Demo 用户限流（最严格）─────────────────────────────────────
    @Bean
    public KeyResolver demoUserKeyResolver() {
        return exchange -> {
            String userId = exchange.getRequest().getHeaders().getFirst("X-User-Id");
            if ("demo_user".equals(userId) || "anonymous".equals(userId)) {
                return Mono.just("demo:" + (userId != null ? userId : "unknown"));
            }
            return Mono.just("not_demo");
        };
    }

    // ─── 基于用户 ID 限流 ───────────────────────────────────────────
    @Bean
    public KeyResolver userKeyResolver() {
        return exchange -> {
            String userId = exchange.getRequest().getHeaders().getFirst("X-User-Id");
            if (userId != null && !userId.isEmpty()) {
                return Mono.just("user:" + userId);
            }
            // 如果 JWT 已解析但未注入，尝试从 Authorization 头提取
            String token = extractToken(exchange);
            if (token != null) {
                return Mono.just("token:" + token.hashCode());
            }
            return Mono.just("anonymous");
        };
    }

    // ─── 基于 IP 限流（基础防护）─────────────────────────────────────
    @Bean
    @Primary
    public KeyResolver ipKeyResolver() {
        return exchange -> Mono.just(
            Optional.ofNullable(exchange.getRequest().getRemoteAddress())
                .flatMap(addr -> Optional.ofNullable(addr.getAddress()))
                .map(java.net.InetAddress::getHostAddress)
                .orElse("unknown")
        );
    }

    // ─── 基于路径限流（针对计算密集型端点）───────────────────────────
    @Bean
    public KeyResolver pathKeyResolver() {
        return exchange -> Mono.just(
            Optional.of(exchange.getRequest().getURI().getPath())
                .map(path -> {
                    if (path.startsWith("/api/planning") || path.startsWith("/api/forecast")) {
                        return "heavy:" + path;
                    }
                    return "light:" + path;
                })
                .orElse("unknown")
        );
    }

    // ─── 定义各层级限流器 ───────────────────────────────────────────
    @Bean
    public RedisRateLimiter demoUserRateLimiter() {
        // Demo 用户: 每分钟 5 个请求，突发 10 个
        return new RedisRateLimiter(5, 10, 1);
    }

    @Bean
    public RedisRateLimiter defaultUserRateLimiter() {
        // 普通用户: 每分钟 60 个请求，突发 100 个
        return new RedisRateLimiter(60, 100, 1);
    }

    @Bean
    public RedisRateLimiter ipRateLimiter() {
        // IP 级别: 每分钟 1000 个请求，突发 2000 个
        return new RedisRateLimiter(1000, 2000, 1);
    }

    // ─── 辅助方法 ───────────────────────────────────────────────────
    private String extractToken(ServerWebExchange exchange) {
        String authHeader = exchange.getRequest().getHeaders().getFirst("Authorization");
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            return authHeader.substring(7);
        }
        return null;
    }
}

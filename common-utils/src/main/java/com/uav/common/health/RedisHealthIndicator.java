package com.uav.common.health;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.connection.RedisConnection;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Component;

import java.util.Properties;

/**
 * Redis 深度健康检查
 * 
 * 验证 Redis 连接、响应时间和内存使用率。
 * 默认禁用 — 仅当显式设置 uav.redis.health.enabled=true 时启用。
 */
@Component
@ConditionalOnProperty(name = "uav.redis.health.enabled", havingValue = "true")
public class RedisHealthIndicator implements HealthIndicator {

    private static final Logger log = LoggerFactory.getLogger(RedisHealthIndicator.class);
    private final RedisTemplate<String, String> redisTemplate;

    public RedisHealthIndicator(RedisTemplate<String, String> redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    @Override
    public Health health() {
        try {
            long start = System.currentTimeMillis();
            
            RedisConnectionFactory connectionFactory = redisTemplate.getConnectionFactory();
            if (connectionFactory == null) {
                return Health.down()
                    .withDetail("redis", "connection factory is null")
                    .build();
            }
            
            RedisConnection conn = connectionFactory.getConnection();
            
            try {
                String pong = conn.ping();
                long elapsed = System.currentTimeMillis() - start;

                if (!"PONG".equalsIgnoreCase(pong)) {
                    return Health.down()
                        .withDetail("redis", "unexpected response: " + pong)
                        .build();
                }

                Health.Builder builder = Health.up()
                    .withDetail("redis", "reachable")
                    .withDetail("responseTime", Long.valueOf(elapsed) + "ms");

                // 尝试获取内存信息
                try {
                    Properties info = conn.serverCommands().info("memory");
                    if (info != null) {
                        String usedMemory = info.getProperty("used_memory_human", "unknown");
                        String peakMemory = info.getProperty("used_memory_peak_human", "unknown");
                        builder.withDetail("usedMemory", usedMemory);
                        builder.withDetail("peakMemory", peakMemory);
                    }
                } catch (Exception ignored) { }

                return builder.build();
            } finally {
                conn.close();
            }

        } catch (Exception e) {
            log.error("Redis health check failed", e);
            return Health.down()
                .withDetail("redis", "unreachable")
                .withDetail("error", e.getMessage())
                .build();
        }
    }
}

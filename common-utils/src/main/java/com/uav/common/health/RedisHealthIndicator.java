package com.uav.common.health;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Component;

/**
 * Redis 深度健康检查
 * 
 * 验证 Redis 连接、响应时间和内存使用率。
 */
@Component
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
            String pong = redisTemplate.getConnectionFactory().getConnection().ping();
            long elapsed = System.currentTimeMillis() - start;

            if (!"PONG".equalsIgnoreCase(pong)) {
                return Health.down()
                    .withDetail("redis", "unexpected response: " + pong)
                    .build();
            }

            Health.Builder builder = Health.up()
                .withDetail("redis", "reachable")
                .withDetail("responseTime", elapsed + "ms");

            // 尝试获取内存信息
            try {
                var conn = redisTemplate.getConnectionFactory().getConnection();
                var info = conn.info("memory");
                if (info != null) {
                    String infoStr;
                    if (info instanceof byte[]) {
                        infoStr = new String((byte[]) info, java.nio.charset.StandardCharsets.UTF_8);
                    } else {
                        infoStr = info.toString();
                    }
                    builder.withDetail("usedMemory", extractValue(infoStr, "used_memory_human"));
                    builder.withDetail("peakMemory", extractValue(infoStr, "used_memory_peak_human"));
                }
            } catch (Exception ignored) { }

            return builder.build();

        } catch (Exception e) {
            log.error("Redis health check failed", e);
            return Health.down()
                .withDetail("redis", "unreachable")
                .withDetail("error", e.getMessage())
                .build();
        }
    }

    private String extractValue(String info, String key) {
        for (String line : info.split("\n")) {
            if (line.startsWith(key + ":")) {
                return line.substring(key.length() + 1).trim();
            }
        }
        return "unknown";
    }
}

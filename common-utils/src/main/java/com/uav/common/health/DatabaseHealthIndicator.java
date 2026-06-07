package com.uav.common.health;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.context.annotation.Profile;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import javax.sql.DataSource;

/**
 * 数据库深度健康检查
 * 
 * 除基础的连接检测外，增加：
 * - 慢查询检测（超过 5s 的查询标记为 degraded）
 * - 连接池状态（活跃连接数/最大连接数）
 */
@Component
@Profile("datasource")
public class DatabaseHealthIndicator implements HealthIndicator {

    private static final Logger log = LoggerFactory.getLogger(DatabaseHealthIndicator.class);
    private final JdbcTemplate jdbcTemplate;
    private final DataSource dataSource;

    public DatabaseHealthIndicator(JdbcTemplate jdbcTemplate, DataSource dataSource) {
        this.jdbcTemplate = jdbcTemplate;
        this.dataSource = dataSource;
    }

    @Override
    public Health health() {
        try {
            // 1. 基础连接检测
            long start = System.currentTimeMillis();
            Integer result = jdbcTemplate.queryForObject("SELECT 1", Integer.class);
            long elapsed = System.currentTimeMillis() - start;

            if (result == null || result != 1) {
                return Health.down()
                    .withDetail("database", "unexpected response")
                    .build();
            }

            // 2. 性能检测
            Health.Builder builder;
            if (elapsed > 5000) {
                builder = Health.down();
                log.warn("Database slow query detected: {}ms", elapsed);
            } else if (elapsed > 1000) {
                builder = Health.status("DEGRADED");
                log.warn("Database query degraded: {}ms", elapsed);
            } else {
                builder = Health.up();
            }

            builder
                .withDetail("database", "reachable")
                .withDetail("responseTime", elapsed + "ms")
                .withDetail("validationQuery", "SELECT 1");

            // 3. 连接池信息
            if (dataSource instanceof com.zaxxer.hikari.HikariDataSource hikariDS) {
                builder
                    .withDetail("poolActive", hikariDS.getHikariPoolMXBean().getActiveConnections())
                    .withDetail("poolIdle", hikariDS.getHikariPoolMXBean().getIdleConnections())
                    .withDetail("poolMax", hikariDS.getMaximumPoolSize());
            }

            return builder.build();

        } catch (Exception e) {
            log.error("Database health check failed", e);
            return Health.down()
                .withDetail("database", "unreachable")
                .withDetail("error", e.getMessage())
                .build();
        }
    }
}

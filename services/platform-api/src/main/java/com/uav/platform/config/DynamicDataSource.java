package com.uav.platform.config;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Primary;
import org.springframework.jdbc.datasource.lookup.AbstractRoutingDataSource;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;
import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@Component
@Primary
public class DynamicDataSource extends AbstractRoutingDataSource {

    public static final String DEFAULT_SCHEMA = "uav_platform";
    public static final ThreadLocal<String> CONTEXT = new ThreadLocal<>();

    @Value("${spring.datasource.url}")
    private String jdbcUrl;

    @Value("${spring.datasource.username}")
    private String username;

    @Value("${spring.datasource.password}")
    private String password;

    @Value("${spring.datasource.driver-class-name}")
    private String driverClassName;

    private final Map<String, DataSource> dataSourceMap = new ConcurrentHashMap<>();

    @PostConstruct
    public void init() {
        setDefaultTargetDataSource(createDataSource(DEFAULT_SCHEMA));
        setTargetDataSources(new ConcurrentHashMap<>());
    }

    @Override
    protected Object determineCurrentLookupKey() {
        String schema = CONTEXT.get();
        return schema != null ? schema : DEFAULT_SCHEMA;
    }

    @Override
    protected DataSource determineTargetDataSource() {
        String schema = CONTEXT.get();
        if (schema == null || schema.equals(DEFAULT_SCHEMA)) {
            return getResolvedDefaultDataSource();
        }
        return dataSourceMap.computeIfAbsent(schema, this::createDataSource);
    }

    private DataSource createDataSource(String schema) {
        HikariConfig config = new HikariConfig();
        config.setDriverClassName(driverClassName);
        String url = jdbcUrl.replace(DEFAULT_SCHEMA, schema);
        config.setJdbcUrl(url);
        config.setUsername(username);
        config.setPassword(password);
        config.setMaximumPoolSize(5);
        config.setMinimumIdle(1);
        config.setConnectionTimeout(30000);
        config.setIdleTimeout(600000);
        config.setMaxLifetime(1800000);
        log.info("Created datasource for schema: {}", schema);
        return new HikariDataSource(config);
    }

    public void switchSchema(String schema) {
        CONTEXT.set(schema);
    }

    public void clearSchema() {
        CONTEXT.remove();
    }

    public void executeInSchema(String schema, SqlExecutor executor) throws SQLException {
        switchSchema(schema);
        try (Connection conn = determineTargetDataSource().getConnection();
             Statement stmt = conn.createStatement()) {
            executor.execute(stmt);
        } finally {
            clearSchema();
        }
    }

    @FunctionalInterface
    public interface SqlExecutor {
        void execute(Statement stmt) throws SQLException;
    }
}

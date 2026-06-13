package com.uav.platform.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.uav.platform.entity.Tenant;
import com.uav.platform.mapper.TenantMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.SQLException;
import java.sql.Statement;
import java.time.LocalDateTime;

@Slf4j
@Service
@RequiredArgsConstructor
public class TenantService extends ServiceImpl<TenantMapper, Tenant> {

    private final DataSource dataSource;
    private final JdbcTemplate jdbcTemplate;

    private static final String TENANT_TABLES_DDL = """
        CREATE TABLE IF NOT EXISTS %s.sys_device (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            device_sn VARCHAR(64) NOT NULL UNIQUE,
            device_name VARCHAR(128),
            device_type VARCHAR(32),
            status INT DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS %s.sys_flight_mission (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            mission_name VARCHAR(128) NOT NULL,
            device_id BIGINT,
            status INT DEFAULT 0,
            start_time DATETIME,
            end_time DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS %s.sys_media (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            file_name VARCHAR(256),
            file_path VARCHAR(512),
            file_type VARCHAR(32),
            size_bytes BIGINT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """;

    @Transactional(rollbackFor = Exception.class)
    public Tenant createTenant(String name, String schemaName, String quotaConfig) {
        if (lambdaQuery().eq(Tenant::getSchemaName, schemaName).one() != null) {
            throw new IllegalArgumentException("Schema name already exists: " + schemaName);
        }

        Tenant tenant = new Tenant();
        tenant.setName(name);
        tenant.setSchemaName(schemaName);
        tenant.setStatus(1);
        tenant.setQuotaConfig(quotaConfig);
        tenant.setCreatedAt(LocalDateTime.now());
        tenant.setUpdatedAt(LocalDateTime.now());
        save(tenant);

        createSchemaAndTables(schemaName);
        return tenant;
    }

    private void createSchemaAndTables(String schemaName) {
        try (Connection conn = dataSource.getConnection();
             Statement stmt = conn.createStatement()) {

            stmt.executeUpdate("CREATE SCHEMA IF NOT EXISTS `" + schemaName + "`");
            log.info("Created schema: {}", schemaName);

            String ddl = String.format(TENANT_TABLES_DDL, schemaName, schemaName, schemaName);
            for (String sql : ddl.split(";")) {
                String trimmed = sql.trim();
                if (!trimmed.isEmpty()) {
                    stmt.executeUpdate(trimmed);
                }
            }
            log.info("Created tenant tables in schema: {}", schemaName);

        } catch (SQLException e) {
            log.error("Failed to create schema or tables for tenant: {}", schemaName, e);
            throw new RuntimeException("Failed to initialize tenant schema: " + schemaName, e);
        }
    }

    @Transactional(rollbackFor = Exception.class)
    public void disableTenant(Long tenantId) {
        Tenant tenant = getById(tenantId);
        if (tenant == null) {
            throw new IllegalArgumentException("Tenant not found: " + tenantId);
        }
        tenant.setStatus(0);
        tenant.setUpdatedAt(LocalDateTime.now());
        updateById(tenant);
    }

    @Transactional(rollbackFor = Exception.class)
    public void enableTenant(Long tenantId) {
        Tenant tenant = getById(tenantId);
        if (tenant == null) {
            throw new IllegalArgumentException("Tenant not found: " + tenantId);
        }
        tenant.setStatus(1);
        tenant.setUpdatedAt(LocalDateTime.now());
        updateById(tenant);
    }
}

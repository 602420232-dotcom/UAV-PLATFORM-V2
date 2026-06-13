-- ============================================================
-- UAV Platform Public Schema Initialization
-- Platform-level tables: tenant, api_key, usage_record
-- ============================================================

CREATE DATABASE IF NOT EXISTS `uav_platform`
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE `uav_platform`;

-- ----------------------------
-- Table: sys_tenant
-- ----------------------------
CREATE TABLE IF NOT EXISTS `sys_tenant` (
    `id`            BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '租户ID',
    `name`          VARCHAR(128) NOT NULL COMMENT '租户名称',
    `schema_name`   VARCHAR(64)  NOT NULL UNIQUE COMMENT '独立Schema名称',
    `status`        INT DEFAULT 1 COMMENT '状态: 1-启用, 0-禁用',
    `quota_config`  JSON COMMENT '配额配置JSON',
    `created_at`    DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_status` (`status`),
    INDEX `idx_schema_name` (`schema_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='租户表';

-- ----------------------------
-- Table: sys_api_key
-- ----------------------------
CREATE TABLE IF NOT EXISTS `sys_api_key` (
    `id`            BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `tenant_id`     BIGINT NOT NULL COMMENT '所属租户ID',
    `key_value`     VARCHAR(128) NOT NULL UNIQUE COMMENT 'API Key',
    `secret`        VARCHAR(256) NOT NULL COMMENT 'API Secret',
    `name`          VARCHAR(128) COMMENT 'Key名称',
    `status`        INT DEFAULT 1 COMMENT '状态: 1-启用, 0-禁用',
    `rate_limit`    INT DEFAULT 1000 COMMENT '速率限制(请求/分钟)',
    `created_at`    DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `expires_at`    DATETIME COMMENT '过期时间',
    INDEX `idx_tenant_id` (`tenant_id`),
    INDEX `idx_key_value` (`key_value`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='API密钥表';

-- ----------------------------
-- Table: sys_usage_record
-- ----------------------------
CREATE TABLE IF NOT EXISTS `sys_usage_record` (
    `id`                BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `tenant_id`         BIGINT NOT NULL COMMENT '租户ID',
    `api_key`           VARCHAR(128) COMMENT 'API Key',
    `api_path`          VARCHAR(256) COMMENT 'API路径',
    `request_count`     BIGINT DEFAULT 1 COMMENT '请求次数',
    `response_time_ms`  BIGINT COMMENT '响应时间(ms)',
    `status`            INT DEFAULT 200 COMMENT 'HTTP状态码',
    `created_at`        DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX `idx_tenant_id` (`tenant_id`),
    INDEX `idx_api_key` (`api_key`),
    INDEX `idx_created_at` (`created_at`),
    INDEX `idx_tenant_created` (`tenant_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用量记录表';

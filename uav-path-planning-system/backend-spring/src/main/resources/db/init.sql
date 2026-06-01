-- =============================================
-- 无人机路径规划系统 - 数据库初始化脚本
-- 版本: 2.0
-- 创建日期: 2026-06-01
-- =============================================

-- =============================================
-- 1. Token 黑名单表
-- 用于存储已撤销的 Token，防止重复使用
-- =============================================
CREATE TABLE IF NOT EXISTS token_blacklist (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    token_id VARCHAR(255) NOT NULL UNIQUE COMMENT 'Token唯一标识(JTI)',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    token_type ENUM('access', 'refresh', 'all') NOT NULL COMMENT 'Token类型',
    reason VARCHAR(255) COMMENT '撤销原因',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    expires_at TIMESTAMP NOT NULL COMMENT 'Token过期时间',
    INDEX idx_token_id (token_id) COMMENT 'Token ID索引',
    INDEX idx_user_id (user_id) COMMENT '用户ID索引',
    INDEX idx_expires_at (expires_at) COMMENT '过期时间索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Token黑名单表';

-- =============================================
-- 2. Refresh Token 表
-- 用于管理 Refresh Token 的生命周期和使用状态
-- =============================================
CREATE TABLE IF NOT EXISTS refresh_token_family (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    refresh_token_id VARCHAR(255) NOT NULL UNIQUE COMMENT 'Refresh Token唯一标识(JTI)',
    is_used BOOLEAN DEFAULT FALSE COMMENT '是否已使用',
    is_revoked BOOLEAN DEFAULT FALSE COMMENT '是否已撤销',
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '签发时间',
    expires_at TIMESTAMP NOT NULL COMMENT '过期时间',
    device_info VARCHAR(255) COMMENT '设备信息',
    ip_address VARCHAR(45) COMMENT 'IP地址',
    INDEX idx_user_id (user_id) COMMENT '用户ID索引',
    INDEX idx_token_id (refresh_token_id) COMMENT 'Token ID索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Refresh Token表';

-- =============================================
-- 3. Demo 会话表
-- 用于管理演示模式用户的会话信息
-- =============================================
CREATE TABLE IF NOT EXISTS demo_session (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    demo_user_id VARCHAR(255) NOT NULL UNIQUE COMMENT 'Demo用户ID',
    user_id BIGINT COMMENT '关联的真实用户ID',
    tenant_id VARCHAR(255) NOT NULL COMMENT '租户ID',
    session_id VARCHAR(255) NOT NULL UNIQUE COMMENT '会话ID',
    ip_address VARCHAR(45) COMMENT 'IP地址',
    purpose VARCHAR(500) COMMENT '演示目的',
    api_calls INT DEFAULT 0 COMMENT 'API调用次数',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
    expires_at TIMESTAMP NOT NULL COMMENT '过期时间',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否活跃',
    INDEX idx_tenant_id (tenant_id) COMMENT '租户ID索引',
    INDEX idx_expires_at (expires_at) COMMENT '过期时间索引',
    INDEX idx_is_active (is_active) COMMENT '活跃状态索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Demo会话表';

-- =============================================
-- 4. 修改 users 表
-- 添加 tenant_id 列并创建索引
-- =============================================
-- 首先检查列是否存在，如果不存在则添加
SET @column_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'users' 
    AND COLUMN_NAME = 'tenant_id'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE users ADD COLUMN tenant_id VARCHAR(255) COMMENT ''租户ID''',
    'SELECT ''Column tenant_id already exists'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 为 tenant_id 创建索引（如果不存在）
SET @index_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'users' 
    AND INDEX_NAME = 'idx_tenant_id'
);

SET @sql = IF(@index_exists = 0,
    'CREATE INDEX idx_tenant_id ON users(tenant_id)',
    'SELECT ''Index idx_tenant_id already exists'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =============================================
-- 5. 插入演示角色数据
-- =============================================
-- 插入 ROLE_DEMO 角色（如果不存在）
INSERT IGNORE INTO roles (name, description, created_at, updated_at)
VALUES (
    'ROLE_DEMO', 
    '演示用户角色，拥有受限权限',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- =============================================
-- 初始化脚本完成
-- =============================================
SELECT 'Database initialization completed successfully' AS message;

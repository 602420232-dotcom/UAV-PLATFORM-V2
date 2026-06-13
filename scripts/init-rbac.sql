-- ============================================================================
-- UAV Platform V2 - RBAC 初始化脚本
-- ============================================================================
-- 本脚本创建 RBAC 所需的数据库表，并插入默认的 admin 用户和角色。
-- 默认管理员账号：admin / admin123（BCrypt 加密）
--
-- 使用方式：
--   docker exec -i uav-mysql mysql -uroot -prootpass < scripts/init-rbac.sql
--
-- 注意：本脚本应在 init-db.sql 之后执行。
-- ============================================================================

USE `uav_platform`;

-- ============================================================================
-- 1. RBAC 核心表
-- ============================================================================

-- ----------------------------
-- 用户表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `sys_user` (
    `id`                BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    `username`          VARCHAR(64)  NOT NULL UNIQUE COMMENT '用户名',
    `password`          VARCHAR(256) NOT NULL COMMENT '密码（BCrypt加密）',
    `email`             VARCHAR(128) COMMENT '邮箱',
    `phone`             VARCHAR(32)  COMMENT '手机号',
    `real_name`         VARCHAR(64)  COMMENT '真实姓名',
    `status`            TINYINT DEFAULT 1 COMMENT '状态: 1-启用, 0-禁用',
    `tenant_id`         BIGINT COMMENT '所属租户ID',
    `last_login_at`    DATETIME COMMENT '最后登录时间',
    `created_at`        DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`        DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_username` (`username`),
    INDEX `idx_tenant_id` (`tenant_id`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户表';

-- ----------------------------
-- 角色表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `sys_role` (
    `id`                BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '角色ID',
    `role_code`         VARCHAR(64)  NOT NULL UNIQUE COMMENT '角色编码（如 SUPER_ADMIN, OPERATOR）',
    `role_name`         VARCHAR(128) NOT NULL COMMENT '角色名称',
    `description`       VARCHAR(256) COMMENT '角色描述',
    `status`            TINYINT DEFAULT 1 COMMENT '状态: 1-启用, 0-禁用',
    `tenant_id`         BIGINT COMMENT '所属租户ID（NULL 表示系统级角色）',
    `created_at`        DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`        DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_role_code` (`role_code`),
    INDEX `idx_tenant_id` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统角色表';

-- ----------------------------
-- 权限表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `sys_permission` (
    `id`                BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '权限ID',
    `permission_code`   VARCHAR(128) NOT NULL UNIQUE COMMENT '权限编码（如 tenant:create, flight:approve）',
    `permission_name`   VARCHAR(128) NOT NULL COMMENT '权限名称',
    `resource_type`     VARCHAR(32) COMMENT '资源类型（API, MENU, BUTTON）',
    `parent_id`         BIGINT DEFAULT 0 COMMENT '父权限ID（0 表示顶级）',
    `sort_order`        INT DEFAULT 0 COMMENT '排序',
    `created_at`        DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX `idx_permission_code` (`permission_code`),
    INDEX `idx_parent_id` (`parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统权限表';

-- ----------------------------
-- 用户角色关联表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `sys_user_role` (
    `id`                BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `user_id`           BIGINT NOT NULL COMMENT '用户ID',
    `role_id`           BIGINT NOT NULL COMMENT '角色ID',
    `tenant_id`         BIGINT COMMENT '租户ID',
    UNIQUE KEY `uk_user_role` (`user_id`, `role_id`),
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_role_id` (`role_id`),
    INDEX `idx_tenant_id` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户角色关联表';

-- ----------------------------
-- 角色权限关联表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `sys_role_permission` (
    `id`                BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `role_id`           BIGINT NOT NULL COMMENT '角色ID',
    `permission_id`     BIGINT NOT NULL COMMENT '权限ID',
    UNIQUE KEY `uk_role_permission` (`role_id`, `permission_id`),
    INDEX `idx_role_id` (`role_id`),
    INDEX `idx_permission_id` (`permission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色权限关联表';

-- ============================================================================
-- 2. 插入默认角色
-- ============================================================================

INSERT INTO `sys_role` (`role_code`, `role_name`, `description`, `status`) VALUES
    ('SUPER_ADMIN',    '超级管理员', '系统最高权限，可管理租户、用户、系统配置', 1),
    ('TENANT_ADMIN',   '租户管理员', '租户内全部权限，可管理租户内用户和资源', 1),
    ('OPERATOR',       '操作员',     '可执行飞行计划、查看气象数据、提交规划任务', 1),
    ('OBSERVER',       '观察员',     '只读权限，可查看仪表盘、气象数据、任务状态', 1),
    ('ALGORITHM_ADMIN','算法管理员', '管理算法注册、执行、监控算法引擎指标', 1)
ON DUPLICATE KEY UPDATE `role_name` = VALUES(`role_name`);

-- ============================================================================
-- 3. 插入默认权限
-- ============================================================================

INSERT INTO `sys_permission` (`permission_code`, `permission_name`, `resource_type`, `parent_id`, `sort_order`) VALUES
    -- 租户管理
    ('tenant:create',  '创建租户', 'API', 0, 1),
    ('tenant:read',    '查看租户', 'API', 0, 2),
    ('tenant:update',  '更新租户', 'API', 0, 3),
    ('tenant:delete',  '删除租户', 'API', 0, 4),
    ('tenant:enable',  '启用/禁用租户', 'API', 0, 5),
    -- 用户管理
    ('user:create',    '创建用户', 'API', 0, 10),
    ('user:read',      '查看用户', 'API', 0, 11),
    ('user:update',    '更新用户', 'API', 0, 12),
    ('user:delete',    '删除用户', 'API', 0, 13),
    -- 飞行计划
    ('flight:create',  '创建飞行计划', 'API', 0, 20),
    ('flight:read',    '查看飞行计划', 'API', 0, 21),
    ('flight:approve', '审批飞行计划', 'API', 0, 22),
    ('flight:cancel',  '取消飞行计划', 'API', 0, 23),
    -- 气象数据
    ('weather:read',   '查看气象数据', 'API', 0, 30),
    -- 规划任务
    ('planning:create','创建规划任务', 'API', 0, 40),
    ('planning:read',  '查看规划任务', 'API', 0, 41),
    -- 算法管理
    ('algorithm:manage','管理算法', 'API', 0, 50),
    ('algorithm:execute','执行算法', 'API', 0, 51),
    -- 风险评估
    ('risk:read',      '查看风险评估', 'API', 0, 60),
    ('risk:create',    '创建风险评估', 'API', 0, 61)
ON DUPLICATE KEY UPDATE `permission_name` = VALUES(`permission_name`);

-- ============================================================================
-- 4. 为 SUPER_ADMIN 分配全部权限
-- ============================================================================

INSERT IGNORE INTO `sys_role_permission` (`role_id`, `permission_id`)
SELECT 1, `id` FROM `sys_permission`;

-- ============================================================================
-- 5. 为 OPERATOR 分配只读和执行权限
-- ============================================================================

INSERT IGNORE INTO `sys_role_permission` (`role_id`, `permission_id`)
SELECT 3, `id` FROM `sys_permission`
WHERE `permission_code` IN (
    'tenant:read', 'flight:create', 'flight:read', 'flight:cancel',
    'weather:read', 'planning:create', 'planning:read',
    'algorithm:execute', 'risk:read'
);

-- ============================================================================
-- 6. 为 OBSERVER 分配只读权限
-- ============================================================================

INSERT IGNORE INTO `sys_role_permission` (`role_id`, `permission_id`)
SELECT 4, `id` FROM `sys_permission`
WHERE `permission_code` IN (
    'tenant:read', 'flight:read', 'weather:read',
    'planning:read', 'risk:read'
);

-- ============================================================================
-- 7. 为 ALGORITHM_ADMIN 分配算法管理权限
-- ============================================================================

INSERT IGNORE INTO `sys_role_permission` (`role_id`, `permission_id`)
SELECT 5, `id` FROM `sys_permission`
WHERE `permission_code` IN (
    'algorithm:manage', 'algorithm:execute', 'weather:read', 'planning:read'
);

-- ============================================================================
-- 8. 插入默认 admin 用户
-- ============================================================================
-- 密码: admin123 (BCrypt hash, strength=10)
-- $2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy
-- ============================================================================

INSERT INTO `sys_user` (`username`, `password`, `email`, `real_name`, `status`) VALUES
    ('admin', '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', 'admin@uav-platform.local', '系统管理员', 1)
ON DUPLICATE KEY UPDATE `password` = VALUES(`password`);

-- ============================================================================
-- 9. 为 admin 用户分配 SUPER_ADMIN 角色
-- ============================================================================

INSERT IGNORE INTO `sys_user_role` (`user_id`, `role_id`)
SELECT u.`id`, r.`id`
FROM `sys_user` u, `sys_role` r
WHERE u.`username` = 'admin' AND r.`role_code` = 'SUPER_ADMIN';

-- ============================================================================
-- 完成
-- ============================================================================
-- 默认管理员账号信息：
--   用户名: admin
--   密码:   admin123
--   角色:   SUPER_ADMIN（拥有全部权限）
--
-- 激活 RBAC 功能：在各微服务的 application.yml 中添加：
--   security:
--     rbac:
--       enabled: true
-- ============================================================================

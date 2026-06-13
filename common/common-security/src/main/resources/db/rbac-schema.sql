-- ============================================================================
-- UAV Platform V2 - RBAC 安全框架数据库 Schema
-- ============================================================================
-- 包含：用户表、角色表、权限表、关联表、审计日志表
-- 预置数据：4个角色 + 全部 API 端点权限
-- ============================================================================

-- --------------------------------------------------------------------------
-- 1. 用户表
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sys_user (
    id              BIGINT          NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    username        VARCHAR(64)     NOT NULL                COMMENT '用户名',
    password_hash   VARCHAR(256)    NOT NULL                COMMENT '密码哈希（BCrypt）',
    email           VARCHAR(128)    DEFAULT NULL            COMMENT '邮箱',
    phone           VARCHAR(20)     DEFAULT NULL            COMMENT '手机号',
    status          TINYINT         NOT NULL DEFAULT 1       COMMENT '状态：1-启用 0-禁用',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_username (username),
    UNIQUE KEY uk_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统用户表';

-- --------------------------------------------------------------------------
-- 2. 角色表
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sys_role (
    id              BIGINT          NOT NULL AUTO_INCREMENT COMMENT '角色ID',
    role_name       VARCHAR(64)     NOT NULL                COMMENT '角色名称',
    role_code       VARCHAR(64)     NOT NULL                COMMENT '角色编码（唯一标识）',
    description     VARCHAR(256)    DEFAULT NULL            COMMENT '角色描述',
    status          TINYINT         NOT NULL DEFAULT 1       COMMENT '状态：1-启用 0-禁用',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_role_code (role_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统角色表';

-- --------------------------------------------------------------------------
-- 3. 权限表
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sys_permission (
    id              BIGINT          NOT NULL AUTO_INCREMENT COMMENT '权限ID',
    permission_name VARCHAR(128)    NOT NULL                COMMENT '权限名称',
    resource_type   VARCHAR(16)     NOT NULL                COMMENT '资源类型：API / MENU / DATA',
    resource_key    VARCHAR(256)    NOT NULL                COMMENT '资源标识（如 API 路径模式）',
    description     VARCHAR(256)    DEFAULT NULL            COMMENT '权限描述',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_resource (resource_type, resource_key),
    INDEX idx_resource_type (resource_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统权限表';

-- --------------------------------------------------------------------------
-- 4. 用户角色关联表
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sys_user_role (
    user_id         BIGINT          NOT NULL                COMMENT '用户ID',
    role_id         BIGINT          NOT NULL                COMMENT '角色ID',
    PRIMARY KEY (user_id, role_id),
    INDEX idx_role_id (role_id),
    CONSTRAINT fk_user_role_user FOREIGN KEY (user_id) REFERENCES sys_user (id) ON DELETE CASCADE,
    CONSTRAINT fk_user_role_role FOREIGN KEY (role_id) REFERENCES sys_role (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户角色关联表';

-- --------------------------------------------------------------------------
-- 5. 角色权限关联表
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sys_role_permission (
    role_id         BIGINT          NOT NULL                COMMENT '角色ID',
    permission_id   BIGINT          NOT NULL                COMMENT '权限ID',
    PRIMARY KEY (role_id, permission_id),
    INDEX idx_permission_id (permission_id),
    CONSTRAINT fk_role_permission_role FOREIGN KEY (role_id) REFERENCES sys_role (id) ON DELETE CASCADE,
    CONSTRAINT fk_role_permission_permission FOREIGN KEY (permission_id) REFERENCES sys_permission (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色权限关联表';

-- --------------------------------------------------------------------------
-- 6. 审计日志表
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_log (
    id              BIGINT          NOT NULL AUTO_INCREMENT COMMENT '日志ID',
    user_id         BIGINT          DEFAULT NULL            COMMENT '操作用户ID（系统操作可为空）',
    action          VARCHAR(64)     NOT NULL                COMMENT '操作名称',
    resource        VARCHAR(128)    NOT NULL                COMMENT '资源类型',
    detail          TEXT            DEFAULT NULL            COMMENT '操作详情（JSON）',
    ip_address      VARCHAR(45)     DEFAULT NULL            COMMENT '客户端IP地址',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    PRIMARY KEY (id),
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_resource (resource),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审计日志表';


-- ============================================================================
-- 预置数据
-- ============================================================================

-- --------------------------------------------------------------------------
-- 预置角色
-- --------------------------------------------------------------------------
INSERT INTO sys_role (role_name, role_code, description) VALUES
    ('超级管理员',   'ADMIN',           '拥有系统全部权限，可管理用户、角色、权限及所有业务操作'),
    ('操作员',       'OPERATOR',        '可执行核心业务操作（规划、气象、风险、同化、观测、UTM）'),
    ('观察者',       'VIEWER',          '只读权限，可查看各类数据但不能执行写操作'),
    ('外部系统',     'EXTERNAL_SYSTEM', '通过 API Key 访问的受限权限，仅开放必要的只读和状态查询接口');

-- --------------------------------------------------------------------------
-- 预置权限 — Platform 管理
-- --------------------------------------------------------------------------
INSERT INTO sys_permission (permission_name, resource_type, resource_key, description) VALUES
    ('创建租户',           'API', 'api:v1:tenants:POST',           '创建新租户'),
    ('查看租户详情',       'API', 'api:v1:tenants:GET:{id}',       '查看指定租户详情'),
    ('查看租户列表',       'API', 'api:v1:tenants:GET',            '查看租户列表'),
    ('更新租户',           'API', 'api:v1:tenants:PUT:{id}',       '更新租户信息'),
    ('禁用租户',           'API', 'api:v1:tenants:POST:{id}:disable',  '禁用租户'),
    ('启用租户',           'API', 'api:v1:tenants:POST:{id}:enable',   '启用租户'),
    ('删除租户',           'API', 'api:v1:tenants:DELETE:{id}',    '删除租户'),
    ('创建API Key',        'API', 'api:v1:api-keys:POST',         '创建API Key'),
    ('查看API Key详情',    'API', 'api:v1:api-keys:GET:{id}',     '查看API Key详情'),
    ('查看租户API Keys',   'API', 'api:v1:api-keys:GET:tenant',   '查看租户下所有API Key'),
    ('启用API Key',        'API', 'api:v1:api-keys:POST:{id}:enable',  '启用API Key'),
    ('禁用API Key',        'API', 'api:v1:api-keys:POST:{id}:disable', '禁用API Key'),
    ('删除API Key',        'API', 'api:v1:api-keys:DELETE:{id}',  '删除API Key'),
    ('查看每日用量',       'API', 'api:v1:usage:GET:daily',        '查看每日用量统计'),
    ('查看API用量',        'API', 'api:v1:usage:GET:api-path',    '查看API路径用量统计');

-- --------------------------------------------------------------------------
-- 预置权限 — 路径规划 (Planning)
-- --------------------------------------------------------------------------
INSERT INTO sys_permission (permission_name, resource_type, resource_key, description) VALUES
    ('路径规划',           'API', 'api:v1:planning:POST:path',             '执行路径规划'),
    ('任务规划',           'API', 'api:v1:planning:POST:mission',          '执行任务规划'),
    ('查看规划任务详情',   'API', 'api:v1:planning:GET:tasks:{id}',        '查看规划任务详情'),
    ('查看规划任务结果',   'API', 'api:v1:planning:GET:tasks:{id}:result', '查看规划任务结果'),
    ('查看规划任务航线',   'API', 'api:v1:planning:GET:tasks:{id}:mission','查看规划任务航线'),
    ('查看规划任务列表',   'API', 'api:v1:planning:GET:tasks',             '查看规划任务列表'),
    ('取消规划任务',       'API', 'api:v1:planning:POST:tasks:{id}:cancel', '取消规划任务'),
    ('MPC规划提交',        'API', 'api:v1:planning:mpc:POST:submit',       '提交MPC规划任务'),
    ('查看MPC任务详情',   'API', 'api:v1:planning:mpc:GET:tasks:{taskId}', '查看MPC任务详情'),
    ('查看MPC任务结果',   'API', 'api:v1:planning:mpc:GET:tasks:{taskId}:result', '查看MPC任务结果'),
    ('MPC位置更新',       'API', 'api:v1:planning:mpc:POST:update-position', 'MPC实时位置更新'),
    ('取消MPC任务',       'API', 'api:v1:planning:mpc:POST:tasks:{taskId}:cancel', '取消MPC任务');

-- --------------------------------------------------------------------------
-- 预置权限 — 气象服务 (Weather)
-- --------------------------------------------------------------------------
INSERT INTO sys_permission (permission_name, resource_type, resource_key, description) VALUES
    ('查询点气象数据',     'API', 'api:v1:weather:POST:point',       '查询指定坐标点气象数据'),
    ('查询区域气象数据',   'API', 'api:v1:weather:GET:region',      '查询区域气象数据'),
    ('查询风场剖面',       'API', 'api:v1:weather:POST:wind-profile','查询风场剖面数据'),
    ('气象数据融合',       'API', 'api:v1:weather:POST:fusion',     '执行气象数据融合');

-- --------------------------------------------------------------------------
-- 预置权限 — 数据同化 (Assimilation)
-- --------------------------------------------------------------------------
INSERT INTO sys_permission (permission_name, resource_type, resource_key, description) VALUES
    ('创建同化任务',       'API', 'api:v1:assimilation:POST:tasks',           '创建数据同化任务'),
    ('查看同化任务详情',   'API', 'api:v1:assimilation:GET:tasks:{id}',      '查看同化任务详情'),
    ('查看同化任务结果',   'API', 'api:v1:assimilation:GET:tasks:{id}:result','查看同化任务结果'),
    ('查看同化任务列表',   'API', 'api:v1:assimilation:GET:tasks',           '查看同化任务列表'),
    ('取消同化任务',       'API', 'api:v1:assimilation:POST:tasks:{id}:cancel','取消同化任务');

-- --------------------------------------------------------------------------
-- 预置权限 — 观测服务 (Observation)
-- --------------------------------------------------------------------------
INSERT INTO sys_permission (permission_name, resource_type, resource_key, description) VALUES
    ('创建观测任务',       'API', 'api:v1:observation:tasks:POST',              '创建观测任务'),
    ('查看观测任务详情',   'API', 'api:v1:observation:tasks:GET:{id}',           '查看观测任务详情'),
    ('查看观测任务列表',   'API', 'api:v1:observation:tasks:GET',               '查看观测任务列表'),
    ('更新观测任务状态',   'API', 'api:v1:observation:tasks:POST:{id}:status',   '更新观测任务状态'),
    ('创建观测决策',       'API', 'api:v1:observation:decisions:POST',           '创建观测决策'),
    ('查看观测决策详情',   'API', 'api:v1:observation:decisions:GET:{id}',       '查看观测决策详情'),
    ('查看观测决策列表',   'API', 'api:v1:observation:decisions:GET',           '查看观测决策列表');

-- --------------------------------------------------------------------------
-- 预置权限 — UTM 管制 (UTM)
-- --------------------------------------------------------------------------
INSERT INTO sys_permission (permission_name, resource_type, resource_key, description) VALUES
    ('上报无人机位置',     'API', 'api:v1:tracking:POST:positions',              '上报无人机实时位置'),
    ('查询无人机位置',     'API', 'api:v1:tracking:GET:uavs:{uavId}:position',    '查询无人机当前位置'),
    ('查询位置历史',       'API', 'api:v1:tracking:GET:uavs:{uavId}:history',     '查询无人机位置历史'),
    ('冲突检测',           'API', 'api:v1:tracking:POST:conflicts:check',         '执行冲突检测'),
    ('订阅实时位置',       'API', 'api:v1:tracking:GET:ws:subscriptions',        '订阅WebSocket实时位置'),
    ('创建飞行计划',       'API', 'api:v1:flight-plans:POST',                    '创建飞行计划'),
    ('查看飞行计划详情',   'API', 'api:v1:flight-plans:GET:{id}',                '查看飞行计划详情'),
    ('审批飞行计划',       'API', 'api:v1:flight-plans:POST:{id}:approve',       '审批通过飞行计划'),
    ('驳回飞行计划',       'API', 'api:v1:flight-plans:POST:{id}:reject',        '驳回飞行计划'),
    ('启动飞行计划',       'API', 'api:v1:flight-plans:POST:{id}:start',         '启动飞行计划'),
    ('完成飞行计划',       'API', 'api:v1:flight-plans:POST:{id}:complete',       '完成飞行计划'),
    ('查看飞行计划列表',   'API', 'api:v1:flight-plans:GET',                    '查看飞行计划列表'),
    ('查看空域列表',       'API', 'api:v1:airspaces:GET',                        '查看空域列表'),
    ('创建空域',           'API', 'api:v1:airspaces:POST',                       '创建空域'),
    ('空域可用性检查',     'API', 'api:v1:airspaces:GET:check',                  '检查空域可用性');

-- --------------------------------------------------------------------------
-- 预置权限 — 风险评估 (Risk)
-- --------------------------------------------------------------------------
INSERT INTO sys_permission (permission_name, resource_type, resource_key, description) VALUES
    ('风险评估',           'API', 'api:v1:risk:POST:assess',       '执行风险评估'),
    ('查看风险地图',       'API', 'api:v1:risk:GET:map',           '查看风险地图'),
    ('查看风险历史',       'API', 'api:v1:risk:GET:history',      '查看风险历史记录'),
    ('适航性评估',         'API', 'api:v1:airworthiness:POST:assess',          '执行适航性评估'),
    ('查看适航标准',       'API', 'api:v1:airworthiness:GET:standards:{uavModel}', '查看适航标准');

-- --------------------------------------------------------------------------
-- 预置权限 — 菜单权限 (MENU)
-- --------------------------------------------------------------------------
INSERT INTO sys_permission (permission_name, resource_type, resource_key, description) VALUES
    ('平台管理菜单',       'MENU', 'menu:platform',       '平台管理模块菜单入口'),
    ('路径规划菜单',       'MENU', 'menu:planning',        '路径规划模块菜单入口'),
    ('气象服务菜单',       'MENU', 'menu:weather',         '气象服务模块菜单入口'),
    ('数据同化菜单',       'MENU', 'menu:assimilation',    '数据同化模块菜单入口'),
    ('观测服务菜单',       'MENU', 'menu:observation',      '观测服务模块菜单入口'),
    ('UTM管制菜单',        'MENU', 'menu:utm',             'UTM管制模块菜单入口'),
    ('风险评估菜单',       'MENU', 'menu:risk',             '风险评估模块菜单入口'),
    ('系统管理菜单',       'MENU', 'menu:system',          '系统管理模块菜单入口');

-- --------------------------------------------------------------------------
-- 预置权限 — 数据权限 (DATA)
-- --------------------------------------------------------------------------
INSERT INTO sys_permission (permission_name, resource_type, resource_key, description) VALUES
    ('查看全部租户数据',   'DATA', 'data:tenant:all',       '可查看所有租户的数据'),
    ('查看本租户数据',     'DATA', 'data:tenant:self',      '仅可查看本租户的数据'),
    ('导出数据',           'DATA', 'data:export',           '数据导出权限'),
    ('删除历史数据',       'DATA', 'data:delete-history',  '删除历史数据权限');


-- ============================================================================
-- 角色权限分配
-- ============================================================================

-- ADMIN：拥有全部权限（所有 API + MENU + DATA）
INSERT INTO sys_role_permission (role_id, permission_id)
SELECT 1, id FROM sys_permission;

-- OPERATOR：拥有全部 API 写权限 + 全部菜单 + 本租户数据权限
INSERT INTO sys_role_permission (role_id, permission_id)
SELECT 2, id FROM sys_permission
WHERE resource_type IN ('API', 'MENU')
   OR resource_key IN ('data:tenant:self');

-- VIEWER：仅拥有 GET 类型的 API 权限 + 全部菜单 + 本租户只读数据权限
INSERT INTO sys_role_permission (role_id, permission_id)
SELECT 3, id FROM sys_permission
WHERE (resource_type = 'API' AND resource_key LIKE '%:GET%')
   OR resource_type = 'MENU'
   OR resource_key IN ('data:tenant:self');

-- EXTERNAL_SYSTEM：仅限只读查询和状态上报接口
INSERT INTO sys_role_permission (role_id, permission_id)
SELECT 4, id FROM sys_permission
WHERE resource_key IN (
    -- 气象只读
    'api:v1:weather:POST:point',
    'api:v1:weather:GET:region',
    'api:v1:weather:POST:wind-profile',
    -- 风险只读
    'api:v1:risk:GET:map',
    'api:v1:risk:GET:history',
    -- 位置上报与查询
    'api:v1:tracking:POST:positions',
    'api:v1:tracking:GET:uavs:{uavId}:position',
    'api:v1:tracking:GET:uavs:{uavId}:history',
    'api:v1:tracking:POST:conflicts:check',
    -- 飞行计划只读
    'api:v1:flight-plans:GET',
    'api:v1:flight-plans:GET:{id}',
    -- 空域只读
    'api:v1:airspaces:GET',
    'api:v1:airspaces:GET:check',
    -- 规划任务只读
    'api:v1:planning:GET:tasks',
    'api:v1:planning:GET:tasks:{id}',
    'api:v1:planning:GET:tasks:{id}:result',
    'api:v1:planning:GET:tasks:{id}:mission',
    -- 数据权限
    'data:tenant:self'
);

-- --------------------------------------------------------------------------
-- 预置默认管理员账户（密码：admin123，BCrypt 哈希）
-- --------------------------------------------------------------------------
INSERT INTO sys_user (username, password_hash, email, phone, status) VALUES
    ('admin', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iAt6Z5EH', 'admin@uav-platform.local', NULL, 1);

-- 将 admin 用户关联到 ADMIN 角色
INSERT INTO sys_user_role (user_id, role_id) VALUES (1, 1);

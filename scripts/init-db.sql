-- UAV Platform V2 Database Initialization
-- This script is executed when MySQL container starts for the first time.

-- ============================================================
-- 1. Create databases
-- ============================================================
CREATE DATABASE IF NOT EXISTS uav_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS uav_assimilation CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS uav_observation CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS uav_planning CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS uav_utm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- ============================================================
-- 2. Grant privileges
-- ============================================================
GRANT ALL PRIVILEGES ON uav_platform.* TO 'root'@'%';
GRANT ALL PRIVILEGES ON uav_assimilation.* TO 'root'@'%';
GRANT ALL PRIVILEGES ON uav_observation.* TO 'root'@'%';
GRANT ALL PRIVILEGES ON uav_planning.* TO 'root'@'%';
GRANT ALL PRIVILEGES ON uav_utm.* TO 'root'@'%';
FLUSH PRIVILEGES;

-- ============================================================
-- 3. Platform tables (uav_platform)
-- ============================================================
USE `uav_platform`;

-- ----------------------------
-- Table: sys_tenant
-- ----------------------------
CREATE TABLE IF NOT EXISTS `sys_tenant` (
    `id`            BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '租户ID',
    `tenant_name`   VARCHAR(128) NOT NULL COMMENT '租户名称',
    `schema_name`   VARCHAR(64)  NOT NULL UNIQUE COMMENT '独立Schema名称',
    `status`        INT DEFAULT 1 COMMENT '状态: 1-启用, 0-禁用',
    `quota_config`  JSON COMMENT '配额配置JSON',
    `created_at`    DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_status` (`status`),
    INDEX `idx_schema_name` (`schema_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='租户表';

-- ----------------------------
-- Table: sys_user (用户表)
-- ----------------------------
CREATE TABLE IF NOT EXISTS `sys_user` (
    `id`            BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    `username`      VARCHAR(64) NOT NULL UNIQUE COMMENT '用户名',
    `password`      VARCHAR(255) NOT NULL COMMENT '密码(BCrypt加密)',
    `nickname`      VARCHAR(100) COMMENT '昵称',
    `email`         VARCHAR(100) COMMENT '邮箱',
    `phone`         VARCHAR(20) COMMENT '手机号',
    `status`        INT DEFAULT 1 COMMENT '状态: 1-启用, 0-禁用',
    `tenant_id`     BIGINT COMMENT '所属租户ID',
    `created_at`    DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_username` (`username`),
    INDEX `idx_tenant` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- ----------------------------
-- Table: sys_role (角色表)
-- ----------------------------
CREATE TABLE IF NOT EXISTS `sys_role` (
    `id`            BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '角色ID',
    `role_name`     VARCHAR(64) NOT NULL UNIQUE COMMENT '角色名称',
    `role_code`     VARCHAR(64) NOT NULL UNIQUE COMMENT '角色编码',
    `description`   VARCHAR(200) COMMENT '描述',
    `created_at`    DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';

-- ----------------------------
-- Table: sys_user_role (用户角色关联表)
-- ----------------------------
CREATE TABLE IF NOT EXISTS `sys_user_role` (
    `user_id`       BIGINT NOT NULL COMMENT '用户ID',
    `role_id`       BIGINT NOT NULL COMMENT '角色ID',
    PRIMARY KEY (`user_id`, `role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户角色关联表';

-- 初始化角色数据
INSERT INTO `sys_role` (`role_name`, `role_code`) VALUES
('超级管理员', 'SUPER_ADMIN'),
('租户管理员', 'TENANT_ADMIN'),
('操作员', 'OPERATOR'),
('观察员', 'OBSERVER'),
('算法管理员', 'ALGORITHM_ADMIN');

-- 初始化用户数据 (密码: admin123, BCrypt加密)
INSERT INTO `sys_user` (`username`, `password`, `nickname`, `status`) VALUES
('admin', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iAt6Z5EO', '系统管理员', 1);

-- 关联用户角色
INSERT INTO `sys_user_role` (`user_id`, `role_id`) VALUES
(1, 1);

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

-- ----------------------------
-- Table: risk_assessment_history
-- ----------------------------
CREATE TABLE IF NOT EXISTS `risk_assessment_history` (
    `id`                BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `type`              VARCHAR(16) NOT NULL COMMENT '评估类型',
    `level`             INT COMMENT '风险等级',
    `score`             DECIMAL(5,2) COMMENT '风险评分',
    `factors_json`      TEXT COMMENT '风险因子 JSON',
    `location_json`     TEXT COMMENT '位置信息 JSON',
    `tenant_id`         VARCHAR(64) NOT NULL COMMENT '租户ID',
    `created_at`        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX `idx_tenant_time` (`tenant_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='风险评估历史表';

-- ----------------------------
-- Table: airworthiness_history
-- ----------------------------
CREATE TABLE IF NOT EXISTS `airworthiness_history` (
    `id`                    BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `uav_model`             VARCHAR(64) NOT NULL COMMENT '无人机型号',
    `overall_score`          DECIMAL(5,2) COMMENT '综合评分',
    `dimension_scores_json`  TEXT COMMENT '各维度评分 JSON',
    `status`                VARCHAR(16) NOT NULL COMMENT '适航状态',
    `recommendations_json`  TEXT COMMENT '建议 JSON',
    `tenant_id`             VARCHAR(64) NOT NULL COMMENT '租户ID',
    `created_at`            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX `idx_tenant_time` (`tenant_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='适航评估历史表';

-- ----------------------------
-- Table: weather_record
-- ----------------------------
CREATE TABLE IF NOT EXISTS `weather_record` (
    `id`                BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `lat`               DOUBLE NOT NULL COMMENT '纬度',
    `lon`               DOUBLE NOT NULL COMMENT '经度',
    `altitude`          DOUBLE COMMENT '海拔高度(m)',
    `temperature`       DOUBLE COMMENT '气温(°C)',
    `humidity`          DOUBLE COMMENT '相对湿度(%)',
    `wind_speed`        DOUBLE COMMENT '风速(m/s)',
    `wind_direction`    DOUBLE COMMENT '风向(°)',
    `pressure`          DOUBLE COMMENT '气压(hPa)',
    `visibility`        DOUBLE COMMENT '能见度(km)',
    `data_source`       VARCHAR(32) COMMENT '数据源',
    `observation_time`  DATETIME COMMENT '观测时间',
    `tenant_id`         BIGINT COMMENT '租户ID',
    `created_at`        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX `idx_location` (`lat`, `lon`),
    INDEX `idx_observation_time` (`observation_time`),
    INDEX `idx_tenant_time` (`tenant_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='气象数据记录表';

-- ----------------------------
-- Table: sys_experiment (算法实验表)
-- ----------------------------
CREATE TABLE IF NOT EXISTS `sys_experiment` (
    `id`                  BIGINT AUTO_INCREMENT PRIMARY KEY,
    `experiment_name`     VARCHAR(200) NOT NULL COMMENT '实验名称',
    `algorithm_name`      VARCHAR(100) NOT NULL COMMENT '算法名称',
    `algorithm_category`  VARCHAR(50) COMMENT '算法分类',
    `status`              VARCHAR(20) NOT NULL DEFAULT 'RUNNING' COMMENT '状态: RUNNING/COMPLETED/FAILED/CANCELLED',
    `config_json`         TEXT COMMENT '算法参数JSON',
    `result_json`         TEXT COMMENT '结果JSON',
    `metrics_json`        TEXT COMMENT '指标JSON',
    `snapshot_hash`       VARCHAR(64) COMMENT '快照SHA256',
    `snapshot_data`       MEDIUMTEXT COMMENT '快照数据JSON',
    `weather_context`     TEXT COMMENT '气象上下文JSON',
    `duration_ms`         BIGINT COMMENT '执行耗时(ms)',
    `created_by`           VARCHAR(100) COMMENT '创建者',
    `tenant_id`           BIGINT COMMENT '租户ID',
    `created_at`           DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`           DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted`              TINYINT NOT NULL DEFAULT 0 COMMENT '逻辑删除',
    INDEX `idx_status` (`status`),
    INDEX `idx_tenant_id` (`tenant_id`),
    INDEX `idx_algorithm_category` (`algorithm_category`),
    INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='算法实验表';

-- ----------------------------
-- Table: sys_config (系统配置表)
-- ----------------------------
CREATE TABLE IF NOT EXISTS `sys_config` (
    `id`            BIGINT AUTO_INCREMENT PRIMARY KEY,
    `config_key`    VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
    `config_value`  VARCHAR(500) NOT NULL COMMENT '配置值',
    `description`   VARCHAR(200) COMMENT '配置描述',
    `updated_by`    VARCHAR(100) COMMENT '最后更新人',
    `created_at`    DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_config_key` (`config_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- ----------------------------
-- Table: sys_algorithm_registration (算法注册表)
-- ----------------------------
CREATE TABLE IF NOT EXISTS `sys_algorithm_registration` (
    `id`              BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '算法ID',
    `name`            VARCHAR(200) NOT NULL COMMENT '算法名称',
    `type`            VARCHAR(50) COMMENT '算法类型',
    `version`         VARCHAR(20) DEFAULT '1.0.0' COMMENT '版本号',
    `description`     TEXT COMMENT '算法描述',
    `endpoint`        VARCHAR(500) COMMENT '算法引擎端点地址',
    `status`          INT DEFAULT 1 COMMENT '状态: 1-启用, 0-禁用, 2-维护中',
    `param_schema`    TEXT COMMENT '参数JSON Schema定义',
    `created_at`      DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_type` (`type`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='算法注册表';

-- 初始化算法数据 (63个算法)
INSERT INTO `sys_algorithm_registration` (`name`, `type`, `version`, `description`, `endpoint`, `status`) VALUES
('3D-VAR-数据同化', 'assimilation', '2.1.0', '三维变分同化算法', 'http://algorithm-engine:9095', 1),
('3D-VAR-数据同化 (高性能版)', 'assimilation', '2.2.0', '三维变分同化算法-高性能版本', 'http://algorithm-engine:9095', 1),
('4D-VAR-数据同化', 'assimilation', '1.8.0', '四维变分同化算法', 'http://algorithm-engine:9095', 1),
('4D-VAR-数据同化 (高精度版)', 'assimilation', '1.9.0', '四维变分同化算法-高精度版本', 'http://algorithm-engine:9095', 1),
('5D-VAR-数据同化', 'assimilation', '1.5.0', '五维变分同化算法', 'http://algorithm-engine:9095', 1),
('5D-VAR-数据同化 (快速版)', 'assimilation', '1.6.0', '五维变分同化算法-快速版本', 'http://algorithm-engine:9095', 1),
('EnKF-集合卡尔曼滤波', 'assimilation', '2.0.0', '集合卡尔曼滤波算法', 'http://algorithm-engine:9095', 1),
('EnKF-集合卡尔曼滤波 (大集合版)', 'assimilation', '2.1.0', '集合卡尔曼滤波算法-大集合版本', 'http://algorithm-engine:9095', 1),
('Hybrid-EnVar-混合同化', 'assimilation', '1.7.0', '混合同化算法', 'http://algorithm-engine:9095', 1),
('Hybrid-EnVar-混合同化 (自适应版)', 'assimilation', '1.8.0', '混合同化算法-自适应版本', 'http://algorithm-engine:9095', 1),
('VarBC-偏差校正', 'assimilation', '1.4.0', '偏差校正算法', 'http://algorithm-engine:9095', 1),
('VarBC-偏差校正 (多变量版)', 'assimilation', '1.5.0', '偏差校正算法-多变量版本', 'http://algorithm-engine:9095', 1),
('3D-RTPP-松弛到倾向逼近', 'assimilation', '1.3.0', '松弛到倾向逼近算法', 'http://algorithm-engine:9095', 1),
('3D-RTPP-松弛到倾向逼近 (增强版)', 'assimilation', '1.4.0', '松弛到倾向逼近算法-增强版本', 'http://algorithm-engine:9095', 1),
('MPC-Path-路径规划', 'planning', '2.3.0', '模型预测控制路径规划', 'http://algorithm-engine:9095', 1),
('MPC-Path-路径规划 (实时版)', 'planning', '2.4.0', '模型预测控制路径规划-实时版本', 'http://algorithm-engine:9095', 1),
('MPC-Path-路径规划 (多目标版)', 'planning', '2.5.0', '模型预测控制路径规划-多目标版本', 'http://algorithm-engine:9095', 1),
('A-Star-路径搜索', 'planning', '1.9.0', 'A*路径搜索算法', 'http://algorithm-engine:9095', 1),
('A-Star-路径搜索 (3D版)', 'planning', '2.0.0', 'A*路径搜索算法-3D版本', 'http://algorithm-engine:9095', 1),
('A-Star-路径搜索 (动态避障版)', 'planning', '2.1.0', 'A*路径搜索算法-动态避障版本', 'http://algorithm-engine:9095', 1),
('RRT-Connect-快速随机树', 'planning', '1.6.0', '快速随机树路径规划', 'http://algorithm-engine:9095', 1),
('RRT-Connect-快速随机树 (高速版)', 'planning', '1.7.0', '快速随机树路径规划-高速版本', 'http://algorithm-engine:9095', 1),
('RRT-Connect-快速随机树 (窄通道版)', 'planning', '1.8.0', '快速随机树路径规划-窄通道版本', 'http://algorithm-engine:9095', 1),
('Dijkstra-3D-三维最短路径', 'planning', '1.5.0', '三维Dijkstra最短路径', 'http://algorithm-engine:9095', 1),
('Dijkstra-3D-三维最短路径 (加权版)', 'planning', '1.6.0', '三维Dijkstra最短路径-加权版本', 'http://algorithm-engine:9095', 1),
('GA-Route-遗传算法路径', 'planning', '1.8.0', '遗传算法路径规划', 'http://algorithm-engine:9095', 1),
('GA-Route-遗传算法路径 (多约束版)', 'planning', '1.9.0', '遗传算法路径规划-多约束版本', 'http://algorithm-engine:9095', 1),
('PSO-Opt-粒子群优化', 'planning', '1.7.0', '粒子群优化路径规划', 'http://algorithm-engine:9095', 1),
('PSO-Opt-粒子群优化 (全局优化版)', 'planning', '1.8.0', '粒子群优化路径规划-全局优化版本', 'http://algorithm-engine:9095', 1),
('RiskAssess-风险评估', 'risk', '2.0.0', '气象风险评估算法', 'http://algorithm-engine:9095', 1),
('RiskAssess-风险评估 (综合版)', 'risk', '2.1.0', '气象风险评估算法-综合版本', 'http://algorithm-engine:9095', 1),
('RiskAssess-风险评估 (实时版)', 'risk', '2.2.0', '气象风险评估算法-实时版本', 'http://algorithm-engine:9095', 1),
('AirsafeEval-适航评估', 'risk', '1.8.0', '适航安全评估算法', 'http://algorithm-engine:9095', 1),
('AirsafeEval-适航评估 (适航版)', 'risk', '1.9.0', '适航安全评估算法-适航版本', 'http://algorithm-engine:9095', 1),
('TurbulenceDetect-湍流检测', 'risk', '1.6.0', '湍流检测算法', 'http://algorithm-engine:9095', 1),
('TurbulenceDetect-湍流检测 (预测版)', 'risk', '1.7.0', '湍流检测算法-预测版本', 'http://algorithm-engine:9095', 1),
('IcingPredict-积冰预测', 'risk', '1.5.0', '积冰预测算法', 'http://algorithm-engine:9095', 1),
('IcingPredict-积冰预测 (精确版)', 'risk', '1.6.0', '积冰预测算法-精确版本', 'http://algorithm-engine:9095', 1),
('WindShear-风切变检测', 'risk', '1.4.0', '风切变检测算法', 'http://algorithm-engine:9095', 1),
('ConvectiveRisk-对流风险', 'risk', '1.3.0', '对流风险评估算法', 'http://algorithm-engine:9095', 1),
('ActiveObs-主动观测', 'observation', '1.9.0', '主动观测决策算法', 'http://algorithm-engine:9095', 1),
('ActiveObs-主动观测 (自适应版)', 'observation', '2.0.0', '主动观测决策算法-自适应版本', 'http://algorithm-engine:9095', 1),
('ActiveObs-主动观测 (多目标版)', 'observation', '2.1.0', '主动观测决策算法-多目标版本', 'http://algorithm-engine:9095', 1),
('SensorPlace-传感器布局', 'observation', '1.7.0', '传感器布局优化', 'http://algorithm-engine:9095', 1),
('SensorPlace-传感器布局 (覆盖优化版)', 'observation', '1.8.0', '传感器布局优化-覆盖优化版本', 'http://algorithm-engine:9095', 1),
('AdaptiveSample-自适应采样', 'observation', '1.6.0', '自适应采样算法', 'http://algorithm-engine:9095', 1),
('AdaptiveSample-自适应采样 (在线版)', 'observation', '1.7.0', '自适应采样算法-在线版本', 'http://algorithm-engine:9095', 1),
('TargetTrack-目标跟踪', 'observation', '1.5.0', '目标跟踪算法', 'http://algorithm-engine:9095', 1),
('UTM-Collision-冲突检测', 'observation', '1.4.0', 'UTM冲突检测算法', 'http://algorithm-engine:9095', 1),
('WRF-3km-区域预报', 'model', '3.0.0', 'WRF 3km区域预报', 'http://algorithm-engine:9095', 1),
('WRF-3km-区域预报 (快速积分版)', 'model', '3.1.0', 'WRF 3km区域预报-快速积分版本', 'http://algorithm-engine:9095', 1),
('WRF-1km-城市预报', 'model', '2.5.0', 'WRF 1km城市预报', 'http://algorithm-engine:9095', 1),
('WRF-1km-城市预报 (城市版)', 'model', '2.6.0', 'WRF 1km城市预报-城市版本', 'http://algorithm-engine:9095', 1),
('WRF-9km-大尺度预报', 'model', '2.0.0', 'WRF 9km大尺度预报', 'http://algorithm-engine:9095', 1),
('ML-Surrogate-机器学习替代', 'model', '1.8.0', '机器学习替代模型', 'http://algorithm-engine:9095', 1),
('ML-Surrogate-机器学习替代 (深度学习版)', 'model', '1.9.0', '机器学习替代模型-深度学习版本', 'http://algorithm-engine:9095', 1),
('NWP-PostProcess-后处理', 'model', '1.5.0', '数值预报后处理', 'http://algorithm-engine:9095', 1),
('EdgeInfer-边缘推理', 'edge', '1.6.0', '边缘推理算法', 'http://algorithm-engine:9095', 1),
('EdgeInfer-边缘推理 (轻量版)', 'edge', '1.7.0', '边缘推理算法-轻量版本', 'http://algorithm-engine:9095', 1),
('FederatedLearn-联邦学习', 'edge', '1.4.0', '联邦学习算法', 'http://algorithm-engine:9095', 1),
('SplitCompute-分割计算', 'edge', '1.3.0', '分割计算算法', 'http://algorithm-engine:9095', 1),
('SplitCompute-分割计算 (低延迟版)', 'edge', '1.4.0', '分割计算算法-低延迟版本', 'http://algorithm-engine:9095', 1),
('OnDeviceAI-端侧AI', 'edge', '1.2.0', '端侧AI算法', 'http://algorithm-engine:9095', 1);

-- 补充逻辑删除列（仅在列不存在时添加）
-- 使用存储过程来安全地添加列，避免重复添加错误
DELIMITER //
CREATE PROCEDURE AddColumnIfNotExists(IN tableName VARCHAR(64), IN colName VARCHAR(64), IN colDef VARCHAR(255))
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = tableName
          AND column_name = colName
    ) THEN
        SET @sql = CONCAT('ALTER TABLE ', tableName, ' ADD COLUMN ', colName, ' ', colDef);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END //
DELIMITER ;

CALL AddColumnIfNotExists('sys_tenant', 'deleted', 'TINYINT NOT NULL DEFAULT 0 COMMENT "逻辑删除" AFTER `updated_at`');
CALL AddColumnIfNotExists('sys_api_key', 'deleted', 'TINYINT NOT NULL DEFAULT 0 COMMENT "逻辑删除" AFTER `expires_at`');
CALL AddColumnIfNotExists('sys_usage_record', 'deleted', 'TINYINT NOT NULL DEFAULT 0 COMMENT "逻辑删除" AFTER `created_at`');

DROP PROCEDURE IF EXISTS AddColumnIfNotExists;

-- ============================================================
-- 4. Assimilation tables (uav_assimilation)
-- ============================================================
USE `uav_assimilation`;

-- ----------------------------
-- Table: assimilation_task
-- ----------------------------
CREATE TABLE IF NOT EXISTS `assimilation_task` (
    `id`                BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `task_id`           VARCHAR(64) NOT NULL UNIQUE COMMENT '任务唯一标识',
    `algorithm_type`    VARCHAR(32) NOT NULL COMMENT '算法类型: 3DVAR/4DVAR/5DVAR/ENKF/HYBRID/ENHANCED_BAYESIAN',
    `status`            VARCHAR(16) NOT NULL DEFAULT 'QUEUED' COMMENT '状态: QUEUED/RUNNING/SUCCESS/FAILED/TIMEOUT/CANCELLED',
    `params_json`       TEXT COMMENT '输入参数 JSON',
    `result_json`       TEXT COMMENT '输出结果 JSON',
    `progress`          INT NOT NULL DEFAULT 0 COMMENT '进度 0-100',
    `error_msg`         TEXT COMMENT '错误信息',
    `tenant_id`         VARCHAR(64) NOT NULL COMMENT '租户ID',
    `created_at`        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `started_at`        DATETIME COMMENT '开始时间',
    `completed_at`      DATETIME COMMENT '完成时间',
    INDEX `idx_tenant_status` (`tenant_id`, `status`),
    INDEX `idx_status` (`status`),
    INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据同化任务表';

-- ----------------------------
-- Table: assimilation_result
-- ----------------------------
CREATE TABLE IF NOT EXISTS `assimilation_result` (
    `id`                    BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `task_id`               VARCHAR(64) NOT NULL UNIQUE COMMENT '关联任务ID',
    `analysis_field_json`   TEXT COMMENT '分析场 JSON',
    `uncertainty_json`      TEXT COMMENT '不确定性场 JSON',
    `convergence_info`      TEXT COMMENT '收敛信息 JSON',
    `created_at`            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX `idx_task_id` (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据同化结果表';

-- ============================================================
-- 5. Observation tables (uav_observation)
-- ============================================================
USE `uav_observation`;

-- ----------------------------
-- Table: observation_task
-- ----------------------------
CREATE TABLE IF NOT EXISTS `observation_task` (
    `id`                        BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `task_id`                   VARCHAR(64) NOT NULL UNIQUE COMMENT '任务唯一标识',
    `type`                      VARCHAR(32) NOT NULL COMMENT 'ADAPTIVE/PLANNED/EMERGENCY',
    `status`                    VARCHAR(16) NOT NULL DEFAULT 'QUEUED' COMMENT '状态: QUEUED/RUNNING/SUCCESS/FAILED/TIMEOUT/CANCELLED',
    `sensor_config_json`        TEXT COMMENT '传感器配置 JSON',
    `planned_path_json`         TEXT COMMENT '规划路径 JSON',
    `actual_path_json`          TEXT COMMENT '实际路径 JSON',
    `data_quality`              DECIMAL(5,2) COMMENT '数据质量评分',
    `assimilation_feedback_json` TEXT COMMENT '同化反馈 JSON',
    `tenant_id`                 VARCHAR(64) NOT NULL COMMENT '租户ID',
    `created_at`                DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `started_at`                DATETIME COMMENT '开始时间',
    `completed_at`              DATETIME COMMENT '完成时间',
    INDEX `idx_tenant_status` (`tenant_id`, `status`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='观测任务表';

-- ----------------------------
-- Table: observation_decision
-- ----------------------------
CREATE TABLE IF NOT EXISTS `observation_decision` (
    `id`                    BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `task_id`               VARCHAR(64) NOT NULL COMMENT '关联任务ID',
    `decision_type`         VARCHAR(32) NOT NULL COMMENT 'HIGH_VALUE_TARGET/ADAPTIVE_SCAN/ROUTINE_MONITOR/DEFERRED',
    `target_area_json`      TEXT COMMENT '目标区域 JSON',
    `priority`              INT NOT NULL DEFAULT 0 COMMENT '优先级',
    `expected_info_gain`    DECIMAL(10,4) COMMENT '期望信息增益',
    `executed_at`           DATETIME COMMENT '执行时间',
    `created_at`            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX `idx_task_id` (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='观测决策表';

-- ============================================================
-- 6. Planning tables (uav_planning)
-- ============================================================
USE `uav_planning`;

-- ----------------------------
-- Table: planning_task
-- ----------------------------
CREATE TABLE IF NOT EXISTS `planning_task` (
    `id`                BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `task_id`           VARCHAR(64) NOT NULL UNIQUE COMMENT '任务唯一标识',
    `algorithm_type`    VARCHAR(32) NOT NULL COMMENT '算法类型: VRPTW/DERRTSTAR/DWA/MPC/A_STAR/DIJKSTRA/RRTSTAR',
    `status`            VARCHAR(16) NOT NULL DEFAULT 'QUEUED' COMMENT '状态: QUEUED/RUNNING/SUCCESS/FAILED/TIMEOUT/CANCELLED',
    `params_json`       TEXT COMMENT '输入参数 JSON',
    `result_json`       TEXT COMMENT '输出结果 JSON',
    `progress`          INT NOT NULL DEFAULT 0 COMMENT '进度 0-100',
    `error_msg`         TEXT COMMENT '错误信息',
    `tenant_id`         VARCHAR(64) NOT NULL COMMENT '租户ID',
    `created_at`        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `started_at`        DATETIME COMMENT '开始时间',
    `completed_at`      DATETIME COMMENT '完成时间',
    INDEX `idx_tenant_status` (`tenant_id`, `status`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='路径规划任务表';

-- ----------------------------
-- Table: path_result
-- ----------------------------
CREATE TABLE IF NOT EXISTS `path_result` (
    `id`                    BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `task_id`               VARCHAR(64) NOT NULL UNIQUE COMMENT '关联任务ID',
    `waypoints_json`        TEXT NOT NULL COMMENT '航点列表 JSON',
    `total_distance`         DECIMAL(12,2) COMMENT '总距离(m)',
    `estimated_time`        INT COMMENT '预计时间(s)',
    `risk_score`            DECIMAL(5,2) COMMENT '风险评分',
    `energy_consumption`    DECIMAL(10,2) COMMENT '能耗(Wh)',
    `created_at`            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX `idx_task_id` (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='路径结果表';

-- ----------------------------
-- Table: mission_plan
-- ----------------------------
CREATE TABLE IF NOT EXISTS `mission_plan` (
    `id`                BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `task_id`           VARCHAR(64) NOT NULL UNIQUE COMMENT '关联任务ID',
    `uavs_json`         TEXT COMMENT '无人机分配 JSON',
    `tasks_json`        TEXT COMMENT '任务分配 JSON',
    `schedule_json`     TEXT COMMENT '调度方案 JSON',
    `overall_score`     DECIMAL(5,2) COMMENT '综合评分',
    `tenant_id`         VARCHAR(64) NOT NULL COMMENT '租户ID',
    `created_at`        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX `idx_task_id` (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务规划表';

-- ============================================================
-- 7. UTM tables (uav_utm)
-- ============================================================
USE `uav_utm`;

-- ----------------------------
-- Table: airspace
-- ----------------------------
CREATE TABLE IF NOT EXISTS `airspace` (
    `id`                    BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `type`                  VARCHAR(16) NOT NULL COMMENT 'STATIC/DYNAMIC/RESTRICTED',
    `bounds_json`           TEXT NOT NULL COMMENT '边界多边形 JSON',
    `altitude_min`          DECIMAL(8,2) COMMENT '最低高度(m)',
    `altitude_max`          DECIMAL(8,2) COMMENT '最高高度(m)',
    `effective_time_start`  DATETIME COMMENT '生效开始时间',
    `effective_time_end`    DATETIME COMMENT '生效结束时间',
    `status`                VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' COMMENT '状态',
    `tenant_id`             VARCHAR(64) COMMENT '租户ID',
    `created_at`            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_status` (`status`),
    INDEX `idx_tenant` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='空域表';

-- ----------------------------
-- Table: flight_plan
-- ----------------------------
CREATE TABLE IF NOT EXISTS `flight_plan` (
    `id`                    BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `plan_id`               VARCHAR(64) NOT NULL UNIQUE COMMENT '飞行计划唯一标识',
    `uav_id`                VARCHAR(64) NOT NULL COMMENT '无人机ID',
    `operator_id`           VARCHAR(64) NOT NULL COMMENT '操作员ID',
    `waypoints_json`        TEXT NOT NULL COMMENT '航点列表 JSON',
    `planned_start_time`    DATETIME COMMENT '计划开始时间',
    `planned_end_time`      DATETIME COMMENT '计划结束时间',
    `actual_start_time`     DATETIME COMMENT '实际开始时间',
    `actual_end_time`       DATETIME COMMENT '实际结束时间',
    `status`                VARCHAR(16) NOT NULL DEFAULT 'SUBMITTED' COMMENT 'SUBMITTED/APPROVED/REJECTED/ACTIVE/COMPLETED/CANCELLED',
    `approval_code`         VARCHAR(64) COMMENT '审批编号',
    `emergency_flag`        TINYINT(1) NOT NULL DEFAULT 0 COMMENT '紧急标志: 0-否, 1-是',
    `tenant_id`             VARCHAR(64) NOT NULL COMMENT '租户ID',
    `created_at`            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX `idx_uav` (`uav_id`),
    INDEX `idx_status` (`status`),
    INDEX `idx_tenant_status` (`tenant_id`, `status`),
    INDEX `idx_planned_time` (`planned_start_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='飞行计划表';

-- ----------------------------
-- Table: uav_position
-- ----------------------------
CREATE TABLE IF NOT EXISTS `uav_position` (
    `id`                BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `uav_id`            VARCHAR(64) NOT NULL COMMENT '无人机ID',
    `longitude`         DECIMAL(10,7) NOT NULL COMMENT '经度',
    `latitude`          DECIMAL(10,7) NOT NULL COMMENT '纬度',
    `altitude`          DECIMAL(8,2) NOT NULL COMMENT '高度(m)',
    `speed`             DECIMAL(6,2) COMMENT '速度(m/s)',
    `heading`           DECIMAL(6,2) COMMENT '航向(度)',
    `flight_plan_id`    VARCHAR(64) COMMENT '关联飞行计划ID',
    `recorded_at`       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
    INDEX `idx_uav_time` (`uav_id`, `recorded_at`),
    INDEX `idx_flight_plan` (`flight_plan_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='无人机位置记录表';

-- ----------------------------
-- Table: conflict_alert
-- ----------------------------
CREATE TABLE IF NOT EXISTS `conflict_alert` (
    `id`                        BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `type`                      VARCHAR(16) NOT NULL COMMENT 'GEOFENCE/UAV',
    `severity`                  VARCHAR(16) NOT NULL COMMENT 'LOW/MEDIUM/HIGH/CRITICAL',
    `involved_entities_json`    TEXT NOT NULL COMMENT '关联实体 JSON',
    `resolution_advice_json`    TEXT COMMENT '处置建议 JSON',
    `status`                    VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' COMMENT '状态',
    `created_at`                DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `resolved_at`               DATETIME COMMENT '解决时间',
    INDEX `idx_status` (`status`),
    INDEX `idx_severity` (`severity`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='冲突告警表';

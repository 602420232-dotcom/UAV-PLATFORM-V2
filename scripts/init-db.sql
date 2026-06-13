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

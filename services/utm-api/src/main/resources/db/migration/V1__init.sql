-- ============================================================
-- UAV UTM Service - Database Initialization
-- Database: uav_utm
-- ============================================================

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

-- ============================================================
-- UAV Observation Service - Database Initialization
-- Database: uav_observation
-- ============================================================

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

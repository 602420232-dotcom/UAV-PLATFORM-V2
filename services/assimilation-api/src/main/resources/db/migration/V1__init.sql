-- ============================================================
-- UAV Assimilation Service - Database Initialization
-- Database: uav_assimilation
-- ============================================================

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

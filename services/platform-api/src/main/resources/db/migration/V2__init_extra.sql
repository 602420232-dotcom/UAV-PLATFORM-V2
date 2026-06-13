-- ============================================================
-- UAV Platform Service - Additional Tables (V2)
-- Database: uav_platform
-- Risk assessment history and airworthiness history
-- ============================================================

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

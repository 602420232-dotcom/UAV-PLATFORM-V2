-- ============================================================
-- UAV Platform Service - Experiment Management (V3)
-- Database: uav_platform
-- Experiment records, snapshots, and metrics for research reproducibility
-- ============================================================

-- ----------------------------
-- Table: sys_experiment
-- ----------------------------
CREATE TABLE IF NOT EXISTS `sys_experiment` (
    `id`                BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT 'Primary key',
    `experiment_name`   VARCHAR(128) NOT NULL COMMENT 'Experiment name',
    `algorithm_name`    VARCHAR(64) NOT NULL COMMENT 'Algorithm name',
    `algorithm_category` VARCHAR(32) NOT NULL COMMENT 'Algorithm category (assimilation/planning/risk/observation/model_engine/edge)',
    `status`            VARCHAR(16) NOT NULL DEFAULT 'RUNNING' COMMENT 'Status: RUNNING/COMPLETED/FAILED/CANCELLED',
    `config_json`       TEXT COMMENT 'Algorithm parameters JSON',
    `result_json`       LONGTEXT COMMENT 'Execution result JSON',
    `metrics_json`      TEXT COMMENT 'Metrics JSON (RMSE, execution time, convergence, etc.)',
    `snapshot_hash`     VARCHAR(64) DEFAULT NULL COMMENT 'Snapshot SHA256 hash',
    `snapshot_data`     LONGTEXT COMMENT 'Snapshot data JSON for reproducibility',
    `weather_context`   TEXT COMMENT 'Weather context JSON (wind, temperature, pressure)',
    `duration_ms`       BIGINT DEFAULT NULL COMMENT 'Execution duration in milliseconds',
    `created_by`        VARCHAR(64) NOT NULL COMMENT 'Creator username',
    `tenant_id`         BIGINT NOT NULL DEFAULT 0 COMMENT 'Tenant ID',
    `created_at`        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Created at',
    `updated_at`        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Updated at',
    INDEX `idx_algorithm` (`algorithm_name`),
    INDEX `idx_status` (`status`),
    INDEX `idx_tenant_time` (`tenant_id`, `created_at`),
    INDEX `idx_category_status` (`algorithm_category`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Experiment records for research reproducibility';

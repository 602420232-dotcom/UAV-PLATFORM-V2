-- ============================================================
-- UAV Planning Service - Database Initialization
-- Database: uav_planning
-- ============================================================

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

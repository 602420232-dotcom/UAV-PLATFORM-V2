# UAV Platform V2 数据库优化指南

> 最后更新：2026-06-15

## 1. 数据库概览

### 1.1 数据库分布

| 数据库 | 服务 | 用途 | 数据特征 |
|--------|------|------|---------|
| `uav_platform` | platform-api, risk-api | 租户管理、API Key、用量统计、风险评估、气象记录 | 读多写少，JSON 字段多 |
| `uav_assimilation` | assimilation-api | 数据同化任务和结果 | 写入后不更新，JSON 大字段 |
| `uav_observation` | observation-api | 观测任务和决策 | 中等读写，JSON 字段 |
| `uav_planning` | planning-api | 路径规划任务和结果 | 写入后不更新，JSON 大字段 |
| `uav_utm` | utm-api | 空域、飞行计划、位置记录、冲突告警 | 位置表高频写入 |
| `nacos` | Nacos | 配置中心和服务发现 | Nacos 自管理 |

### 1.2 表清单与数据量预估

| 数据库 | 表名 | 预估行数/月 | 增长模式 |
|--------|------|------------|---------|
| uav_platform | sys_tenant | < 100 | 低频 |
| uav_platform | sys_api_key | < 1000 | 低频 |
| uav_platform | sys_usage_record | 10K - 100K | 高频 |
| uav_platform | risk_assessment_history | 1K - 10K | 中频 |
| uav_platform | airworthiness_history | 1K - 10K | 中频 |
| uav_platform | weather_record | 10K - 100K | 高频 |
| uav_assimilation | assimilation_task | 1K - 10K | 中频 |
| uav_assimilation | assimilation_result | 1K - 10K | 中频 |
| uav_observation | observation_task | 1K - 10K | 中频 |
| uav_observation | observation_decision | 1K - 10K | 中频 |
| uav_planning | planning_task | 1K - 10K | 中频 |
| uav_planning | path_result | 1K - 10K | 中频 |
| uav_planning | mission_plan | 1K - 10K | 中频 |
| uav_utm | airspace | < 1000 | 低频 |
| uav_utm | flight_plan | 1K - 10K | 中频 |
| uav_utm | uav_position | 100K - 1M | 高频 |
| uav_utm | conflict_alert | 1K - 10K | 中频 |

## 2. 索引优化建议

### 2.1 现有索引评估

当前 `init-db.sql` 已创建的索引基本合理，但存在以下优化空间：

### 2.2 建议新增索引

```sql
-- ============================================================
-- uav_platform 数据库
-- ============================================================
USE `uav_platform`;

-- sys_usage_record: 按时间范围查询用量统计（高频查询）
ALTER TABLE `sys_usage_record`
  ADD INDEX `idx_created_at` (`created_at`);

-- sys_usage_record: 按状态码统计（监控面板）
ALTER TABLE `sys_usage_record`
  ADD INDEX `idx_status` (`status`);

-- weather_record: 按数据源筛选
ALTER TABLE `weather_record`
  ADD INDEX `idx_data_source` (`data_source`);

-- weather_record: 复合索引（按时间范围 + 数据源查询）
ALTER TABLE `weather_record`
  ADD INDEX `idx_source_time` (`data_source`, `observation_time`);

-- ============================================================
-- uav_planning 数据库
-- ============================================================
USE `uav_planning`;

-- planning_task: 按算法类型筛选
ALTER TABLE `planning_task`
  ADD INDEX `idx_algorithm_type` (`algorithm_type`);

-- planning_task: 按创建时间排序（列表查询）
ALTER TABLE `planning_task`
  ADD INDEX `idx_created_at` (`created_at`);

-- ============================================================
-- uav_utm 数据库
-- ============================================================
USE `uav_utm`;

-- uav_position: 按时间范围查询轨迹（高频查询）
ALTER TABLE `uav_position`
  ADD INDEX `idx_recorded_at` (`recorded_at`);

-- flight_plan: 按计划时间范围查询
ALTER TABLE `flight_plan`
  ADD INDEX `idx_planned_time_range` (`planned_start_time`, `planned_end_time`);

-- conflict_alert: 按严重程度 + 状态筛选
ALTER TABLE `conflict_alert`
  ADD INDEX `idx_severity_status` (`severity`, `status`);
```

### 2.3 索引使用原则

| 原则 | 说明 |
|------|------|
| 复合索引最左前缀 | 查询条件应从索引最左列开始 |
| 覆盖索引优先 | 尽量让查询只访问索引，避免回表 |
| 避免过度索引 | 每个索引增加 10-15% 写入开销 |
| 定期分析 | 使用 `ANALYZE TABLE` 更新统计信息 |

## 3. 慢查询优化方案

### 3.1 常见慢查询场景

#### 场景 1: 用量统计查询

```sql
-- 慢查询：全表扫描统计
SELECT api_path, COUNT(*), AVG(response_time_ms)
FROM sys_usage_record
WHERE created_at >= '2026-06-01'
GROUP BY api_path;
```

**优化方案**：
- 确保 `idx_created_at` 索引存在
- 考虑按月分区（见 3.3 节）
- 对历史数据使用汇总表

```sql
-- 创建月度汇总表
CREATE TABLE `usage_summary_monthly` (
    `month` VARCHAR(7) NOT NULL COMMENT '月份 YYYY-MM',
    `tenant_id` BIGINT NOT NULL,
    `api_path` VARCHAR(256),
    `request_count` BIGINT DEFAULT 0,
    `avg_response_time_ms` DOUBLE,
    `error_count` BIGINT DEFAULT 0,
    PRIMARY KEY (`month`, `tenant_id`, `api_path`(64)),
    INDEX `idx_tenant_month` (`tenant_id`, `month`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='月度用量汇总表';
```

#### 场景 2: 无人机轨迹查询

```sql
-- 慢查询：大范围时间扫描
SELECT * FROM uav_position
WHERE uav_id = 'UAV-001'
  AND recorded_at BETWEEN '2026-06-15 00:00:00' AND '2026-06-15 23:59:59'
ORDER BY recorded_at;
```

**优化方案**：
- 现有 `idx_uav_time` 索引已覆盖此查询
- 如数据量极大，考虑按 `uav_id` 分区或使用时序数据库

#### 场景 3: 风险评估历史查询

```sql
-- 慢查询：复合条件筛选
SELECT * FROM risk_assessment_history
WHERE tenant_id = '1'
  AND type = 'WEATHER'
  AND created_at >= '2026-06-01'
ORDER BY created_at DESC
LIMIT 20;
```

**优化方案**：

```sql
-- 添加复合索引
ALTER TABLE `risk_assessment_history`
  ADD INDEX `idx_type_tenant_time` (`type`, `tenant_id`, `created_at`);
```

### 3.2 慢查询监控

```sql
-- 开启慢查询日志（MySQL 配置）
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1.0;  -- 超过 1 秒记录
SET GLOBAL slow_query_log_file = '/var/lib/mysql/slow.log';

-- 查看当前慢查询配置
SHOW VARIABLES LIKE 'slow_query%';
SHOW VARIABLES LIKE 'long_query_time';

-- 使用 mysqldumpslow 分析
-- docker exec uav-mysql mysqldumpslow -s t -t 10 /var/lib/mysql/slow.log
```

### 3.3 分区表建议

对高频增长的大表建议使用分区：

```sql
-- uav_position 按月分区（RANGE 分区）
ALTER TABLE `uav_position`
PARTITION BY RANGE (TO_DAYS(recorded_at)) (
    PARTITION p202606 VALUES LESS THAN (TO_DAYS('2026-07-01')),
    PARTITION p202607 VALUES LESS THAN (TO_DAYS('2026-08-01')),
    PARTITION p202608 VALUES LESS THAN (TO_DAYS('2026-09-01')),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- sys_usage_record 按月分区
ALTER TABLE `sys_usage_record`
PARTITION BY RANGE (TO_DAYS(created_at)) (
    PARTITION p202606 VALUES LESS THAN (TO_DAYS('2026-07-01')),
    PARTITION p202607 VALUES LESS THAN (TO_DAYS('2026-08-01')),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);
```

## 4. 连接池配置建议

### 4.1 Spring Boot HikariCP 配置

```yaml
# application-docker.yml
spring:
  datasource:
    hikari:
      minimum-idle: 5
      maximum-pool-size: 20
      idle-timeout: 300000       # 5 分钟
      max-lifetime: 1800000      # 30 分钟
      connection-timeout: 30000  # 30 秒
      leak-detection-threshold: 60000  # 连接泄漏检测 60 秒
      pool-name: ${spring.application.name}-pool
```

### 4.2 各服务连接池建议

| 服务 | 最小连接 | 最大连接 | 说明 |
|------|---------|---------|------|
| platform-api | 5 | 20 | 租户管理，中等并发 |
| weather-api | 5 | 15 | 气象查询，读多写少 |
| assimilation-api | 3 | 10 | 同化任务，低频写入 |
| risk-api | 3 | 10 | 风险评估，中等并发 |
| observation-api | 3 | 10 | 观测任务，中等并发 |
| planning-api | 5 | 15 | 路径规划，中等并发 |
| utm-api | 5 | 20 | UTM 管理，高频位置写入 |

### 4.3 连接池监控

```sql
-- 查看当前连接数
SHOW STATUS LIKE 'Threads_connected';
SHOW STATUS LIKE 'Max_used_connections';

-- 查看活跃连接
SHOW PROCESSLIST;

-- 查看连接详情
SELECT * FROM information_schema.PROCESSLIST
WHERE DB = 'uav_platform'
ORDER BY TIME DESC;
```

## 5. 数据归档策略

### 5.1 归档规则

| 表 | 保留周期 | 归档策略 |
|----|---------|---------|
| sys_usage_record | 90 天 | 超过 90 天的数据归档到 `usage_archive` |
| uav_position | 30 天 | 超过 30 天的位置数据归档 |
| risk_assessment_history | 180 天 | 超过 180 天归档 |
| airworthiness_history | 180 天 | 超过 180 天归档 |
| conflict_alert | 90 天 | 已解决的告警 90 天后归档 |
| *_task 表 | 365 天 | 已完成任务 1 年后归档 |

### 5.2 归档脚本示例

```sql
-- 归档用量记录（每月执行一次）
CREATE TABLE IF NOT EXISTS `sys_usage_record_archive` LIKE `sys_usage_record`;

INSERT INTO `sys_usage_record_archive`
SELECT * FROM `sys_usage_record`
WHERE `created_at` < DATE_SUB(NOW(), INTERVAL 90 DAY)
LIMIT 10000;

-- 确认归档后删除
DELETE FROM `sys_usage_record`
WHERE `created_at` < DATE_SUB(NOW(), INTERVAL 90 DAY)
LIMIT 10000;
```

## 6. 定期维护任务

| 任务 | 频率 | 命令 |
|------|------|------|
| 更新统计信息 | 每周 | `ANALYZE TABLE table_name` |
| 优化表碎片 | 每月 | `OPTIMIZE TABLE table_name` |
| 检查表完整性 | 每月 | `CHECK TABLE table_name` |
| 慢查询分析 | 每周 | `mysqldumpslow -s t -t 20` |
| 索引使用分析 | 每月 | 查询 `performance_schema.table_io_waits_summary_by_index_usage` |
| 数据归档 | 每月 | 执行归档脚本 |
| 备份验证 | 每周 | 恢复测试到测试环境 |

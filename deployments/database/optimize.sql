-- 数据库性能优化脚本
-- 添加索引和优化配置

-- 用户表索引
CREATE INDEX IF NOT EXISTS idx_user_username ON user(username);
CREATE INDEX IF NOT EXISTS idx_user_email ON user(email);
CREATE INDEX IF NOT EXISTS idx_user_status ON user(enabled);

-- 角色表索引
CREATE INDEX IF NOT EXISTS idx_role_name ON role(name);

-- 任务表索引
CREATE INDEX IF NOT EXISTS idx_task_status ON task(status);
CREATE INDEX IF NOT EXISTS idx_task_start_time ON task(start_time);
CREATE INDEX IF NOT EXISTS idx_task_end_time ON task(end_time);
CREATE INDEX IF NOT EXISTS idx_task_created_at ON task(created_at);

-- 无人机表索引
CREATE INDEX IF NOT EXISTS idx_drone_status ON drone(status);
CREATE INDEX IF NOT EXISTS idx_drone_battery ON drone(battery_level);

-- 路径规划表索引
CREATE INDEX IF NOT EXISTS idx_path_task_id ON path_planning(task_id);
CREATE INDEX IF NOT EXISTS idx_path_drone_id ON path_planning(drone_id);
CREATE INDEX IF NOT EXISTS idx_path_status ON path_planning(status);
CREATE INDEX IF NOT EXISTS idx_path_created_at ON path_planning(created_at);

-- 历史记录表索引
CREATE INDEX IF NOT EXISTS idx_history_task_id ON task_history(task_id);
CREATE INDEX IF NOT EXISTS idx_history_drone_id ON task_history(drone_id);
CREATE INDEX IF NOT EXISTS idx_history_status ON task_history(status);
CREATE INDEX IF NOT EXISTS idx_history_start_time ON task_history(start_time);
CREATE INDEX IF NOT EXISTS idx_history_end_time ON task_history(end_time);

-- 气象数据表索引
CREATE INDEX IF NOT EXISTS idx_weather_location ON weather_data(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_weather_timestamp ON weather_data(timestamp);

-- 优化数据库配置
SET GLOBAL innodb_buffer_pool_size = 1G;
SET GLOBAL innodb_flush_log_at_trx_commit = 2;
SET GLOBAL innodb_log_buffer_size = 16M;
SET GLOBAL innodb_log_file_size = 256M;
SET GLOBAL innodb_stats_on_metadata = OFF;

-- 优化查询缓存
SET GLOBAL query_cache_size = 64M;
SET GLOBAL query_cache_type = 1;
SET GLOBAL query_cache_limit = 2M;

-- 优化连接池
SET GLOBAL max_connections = 200;
SET GLOBAL wait_timeout = 300;
SET GLOBAL interactive_timeout = 300;

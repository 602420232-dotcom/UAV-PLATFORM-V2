-- ============================================================
-- V2: 添加索引和约束
-- 基于 V1 迁移后的性能优化和完整性改进
-- 已根据 V1 实际表结构调整：添加缺失的索引，跳过 V1 已有的索引和不存在的列/表
-- ============================================================

-- 1. users 表索引（补充 V1 中缺失的）
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_enabled ON users(enabled);

-- 2. user_roles 关联表索引
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);

-- 3. weather_data 表索引
-- 注: V1 已存在 idx_source, idx_recorded_at, idx_source_recorded
CREATE INDEX idx_weather_data_location ON weather_data(latitude, longitude);
CREATE INDEX idx_weather_data_drone_id ON weather_data(drone_id);

-- 4. path_plans 表索引
-- 注: V1 已存在 idx_drone_id, idx_status
CREATE INDEX idx_path_plans_created ON path_plans(created_at);

-- 5. data_sources 表索引
CREATE INDEX idx_data_sources_type ON data_sources(type);
CREATE INDEX idx_data_sources_status ON data_sources(status);

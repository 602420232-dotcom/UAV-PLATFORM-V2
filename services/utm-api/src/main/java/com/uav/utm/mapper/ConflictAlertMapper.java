package com.uav.utm.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.uav.utm.entity.ConflictAlert;
import org.apache.ibatis.annotations.Mapper;

/**
 * 冲突告警 Mapper
 */
@Mapper
public interface ConflictAlertMapper extends BaseMapper<ConflictAlert> {
}

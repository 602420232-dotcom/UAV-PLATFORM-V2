package com.uav.utm.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.uav.utm.entity.FlightPlan;
import org.apache.ibatis.annotations.Mapper;

/**
 * 飞行计划 Mapper
 */
@Mapper
public interface FlightPlanMapper extends BaseMapper<FlightPlan> {
}

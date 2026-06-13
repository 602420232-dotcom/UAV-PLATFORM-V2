package com.uav.planning.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.uav.planning.entity.MissionPlan;
import org.apache.ibatis.annotations.Mapper;

/**
 * 任务规划 Mapper
 */
@Mapper
public interface MissionPlanMapper extends BaseMapper<MissionPlan> {
}

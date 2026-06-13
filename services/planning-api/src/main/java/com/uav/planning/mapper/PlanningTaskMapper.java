package com.uav.planning.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.uav.planning.entity.PlanningTask;
import org.apache.ibatis.annotations.Mapper;

/**
 * 规划任务 Mapper
 */
@Mapper
public interface PlanningTaskMapper extends BaseMapper<PlanningTask> {
}

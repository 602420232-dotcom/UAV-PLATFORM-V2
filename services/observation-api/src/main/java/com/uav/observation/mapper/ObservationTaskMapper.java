package com.uav.observation.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.uav.observation.entity.ObservationTask;
import org.apache.ibatis.annotations.Mapper;

/**
 * 观测任务 Mapper
 */
@Mapper
public interface ObservationTaskMapper extends BaseMapper<ObservationTask> {
}

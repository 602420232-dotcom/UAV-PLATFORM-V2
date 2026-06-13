package com.uav.assimilation.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.uav.assimilation.entity.AssimilationTask;
import org.apache.ibatis.annotations.Mapper;

/**
 * 同化任务 Mapper
 */
@Mapper
public interface AssimilationTaskMapper extends BaseMapper<AssimilationTask> {
}

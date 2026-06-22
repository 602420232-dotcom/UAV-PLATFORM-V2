package com.uav.platform.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.uav.platform.entity.Experiment;
import org.apache.ibatis.annotations.Mapper;

/**
 * 实验管理数据访问层
 */
@Mapper
public interface ExperimentMapper extends BaseMapper<Experiment> {
}

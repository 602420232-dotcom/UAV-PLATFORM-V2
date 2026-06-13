package com.uav.observation.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.uav.observation.entity.ObservationDecision;
import org.apache.ibatis.annotations.Mapper;

/**
 * 观测决策 Mapper
 */
@Mapper
public interface ObservationDecisionMapper extends BaseMapper<ObservationDecision> {
}

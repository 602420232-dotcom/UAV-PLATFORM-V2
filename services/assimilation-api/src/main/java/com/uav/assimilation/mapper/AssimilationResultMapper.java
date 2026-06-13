package com.uav.assimilation.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.uav.assimilation.entity.AssimilationResult;
import org.apache.ibatis.annotations.Mapper;

/**
 * 同化结果 Mapper
 */
@Mapper
public interface AssimilationResultMapper extends BaseMapper<AssimilationResult> {
}

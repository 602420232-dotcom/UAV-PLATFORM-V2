package com.uav.utm.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.uav.utm.entity.UavPosition;
import org.apache.ibatis.annotations.Mapper;

/**
 * 无人机位置记录 Mapper
 */
@Mapper
public interface UavPositionMapper extends BaseMapper<UavPosition> {
}

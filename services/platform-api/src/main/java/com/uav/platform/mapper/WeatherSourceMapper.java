package com.uav.platform.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.uav.platform.entity.WeatherSource;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface WeatherSourceMapper extends BaseMapper<WeatherSource> {
}

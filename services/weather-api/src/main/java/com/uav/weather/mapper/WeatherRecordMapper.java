package com.uav.weather.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.uav.weather.entity.WeatherRecord;
import org.apache.ibatis.annotations.Mapper;

/**
 * 气象数据记录 Mapper
 */
@Mapper
public interface WeatherRecordMapper extends BaseMapper<WeatherRecord> {
}

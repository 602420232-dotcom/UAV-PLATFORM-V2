package com.uav.weather.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 气象数据记录实体（数据库持久化）
 */
@Data
@TableName("weather_record")
public class WeatherRecord {

    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    /** 经度 */
    private Double lat;

    /** 纬度 */
    private Double lon;

    /** 海拔高度(m) */
    private Double altitude;

    /** 气温(°C) */
    private Double temperature;

    /** 相对湿度(%) */
    private Double humidity;

    /** 风速(m/s) */
    private Double windSpeed;

    /** 风向(°) */
    private Double windDirection;

    /** 气压(hPa) */
    private Double pressure;

    /** 能见度(km) */
    private Double visibility;

    /** 数据源 */
    private String dataSource;

    /** 观测时间 */
    private LocalDateTime observationTime;

    /** 租户ID */
    private Long tenantId;

    /** 创建时间 */
    private LocalDateTime createdAt;
}

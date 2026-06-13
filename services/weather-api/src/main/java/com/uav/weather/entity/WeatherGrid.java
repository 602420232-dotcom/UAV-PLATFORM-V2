package com.uav.weather.entity;

import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 气象格点数据
 */
@Data
public class WeatherGrid implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;

    /** 数据源: WRF, FENGWU_GHR, TIANZI, FENGLEI */
    private String source;

    /** 经度 */
    private Double longitude;

    /** 纬度 */
    private Double latitude;

    /** 海拔高度(m) */
    private Double altitude;

    /** 预报时间 */
    private LocalDateTime forecastTime;

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

    /** 降水量(mm) */
    private Double precipitation;

    /** 能见度(km) */
    private Double visibility;

    /** 云量(%) */
    private Double cloudCover;

    /** 创建时间 */
    private LocalDateTime createdAt;
}

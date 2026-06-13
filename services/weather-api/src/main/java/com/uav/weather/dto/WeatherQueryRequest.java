package com.uav.weather.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 气象数据查询请求
 */
@Data
public class WeatherQueryRequest {

    @NotNull
    private Double longitude;

    @NotNull
    private Double latitude;

    /** 海拔高度，null 表示地面层 */
    private Double altitude;

    /** 数据源，null 表示多源融合 */
    private String source;

    /** 预报时间，null 表示最新 */
    private LocalDateTime forecastTime;

    /** 查询半径(m)，用于格点插值 */
    private Integer radius = 5000;
}

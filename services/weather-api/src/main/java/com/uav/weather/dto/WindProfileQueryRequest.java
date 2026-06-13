package com.uav.weather.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 风场剖面查询请求
 */
@Data
public class WindProfileQueryRequest {

    @NotNull
    private Double longitude;

    @NotNull
    private Double latitude;

    /** 最低高度(m) */
    private Double minAltitude = 0.0;

    /** 最高高度(m) */
    private Double maxAltitude = 1000.0;

    /** 高度层间隔(m) */
    private Double interval = 50.0;

    /** 数据源 */
    private String source;

    /** 预报时间 */
    private LocalDateTime forecastTime;
}

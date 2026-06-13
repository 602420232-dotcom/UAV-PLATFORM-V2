package com.uav.weather.entity;

import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 风场剖面数据
 */
@Data
public class WindProfile implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;

    private String source;

    private Double longitude;

    private Double latitude;

    private LocalDateTime forecastTime;

    /** 各高度层风场数据 */
    private List<WindLayer> layers;

    private LocalDateTime createdAt;

    @Data
    public static class WindLayer implements Serializable {
        private static final long serialVersionUID = 1L;

        /** 高度(m) */
        private Double altitude;

        /** 风速(m/s) */
        private Double windSpeed;

        /** 风向(°) */
        private Double windDirection;

        /** 垂直风速(m/s) */
        private Double verticalWindSpeed;

        /** 湍流强度 */
        private Double turbulence;
    }
}

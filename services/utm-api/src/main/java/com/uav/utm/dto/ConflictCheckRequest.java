package com.uav.utm.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

@Data
public class ConflictCheckRequest {

    @NotBlank
    private String uavId;

    @NotNull
    private List<PlannedPathPoint> plannedPath;

    @NotNull
    private TimeWindow timeWindow;

    @Data
    public static class PlannedPathPoint {
        private Double lon;
        private Double lat;
        private Double alt;
        private LocalDateTime eta;
    }

    @Data
    public static class TimeWindow {
        private LocalDateTime start;
        private LocalDateTime end;
    }
}

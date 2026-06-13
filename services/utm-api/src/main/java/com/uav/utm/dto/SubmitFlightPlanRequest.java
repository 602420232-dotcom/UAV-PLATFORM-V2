package com.uav.utm.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

@Data
public class SubmitFlightPlanRequest {

    @NotBlank
    private String uavId;

    @NotNull
    private List<Waypoint> waypoints;

    @NotNull
    private LocalDateTime plannedStartTime;

    @NotNull
    private LocalDateTime plannedEndTime;

    private String purpose;

    @Data
    public static class Waypoint {
        private Double lon;
        private Double lat;
        private Double alt;
    }
}

package com.uav.utm.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.time.LocalDateTime;

@Data
public class UavPositionReport {

    @NotBlank
    private String uavId;

    @NotNull
    private Double lon;

    @NotNull
    private Double lat;

    @NotNull
    private Double alt;

    private Double speed;

    private Double heading;

    @NotNull
    private LocalDateTime timestamp;
}

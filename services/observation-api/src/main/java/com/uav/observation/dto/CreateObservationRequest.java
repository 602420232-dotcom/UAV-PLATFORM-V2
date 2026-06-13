package com.uav.observation.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

/**
 * 创建观测任务请求
 */
@Data
public class CreateObservationRequest {

    /**
     * 任务类型: ADAPTIVE, PLANNED, EMERGENCY
     */
    @NotNull
    private String type;

    /**
     * 目标区域 JSON
     */
    @NotNull
    private String targetArea;

    /**
     * 传感器类型
     */
    @NotNull
    private String sensorType;

    /**
     * 优先级 (1-10)
     */
    @NotNull
    private Integer priority;
}

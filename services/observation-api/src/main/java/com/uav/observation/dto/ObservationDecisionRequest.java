package com.uav.observation.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.List;

/**
 * 观测决策请求
 */
@Data
public class ObservationDecisionRequest {

    /**
     * 当前状态 JSON
     */
    @NotNull
    private String currentState;

    /**
     * 可用传感器列表 JSON
     */
    @NotNull
    private String availableSensors;

    /**
     * 约束条件 JSON
     */
    private String constraints;
}

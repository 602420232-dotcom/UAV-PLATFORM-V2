package com.uav.planning.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.List;
import java.util.Map;

/**
 * 路径规划请求
 */
@Data
public class PlanPathRequest {

    /** 起点坐标 {lon, lat, alt} */
    @NotNull
    private Map<String, Double> start;

    /** 终点坐标 {lon, lat, alt} */
    @NotNull
    private Map<String, Double> end;

    /** 途经点列表 [{lon, lat, alt}] */
    private List<Map<String, Double>> waypoints;

    /** 无人机型号 */
    private String uavModel;

    /** 约束条件: 高度/速度/时间窗等 */
    private Map<String, Object> constraints;

    /** 优化目标: RISK, ENERGY, TIME, BALANCED */
    @NotBlank
    private String optimizationTarget;
}

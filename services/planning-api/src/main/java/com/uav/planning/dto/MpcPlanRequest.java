package com.uav.planning.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.List;

/**
 * MPC 滚动规划请求
 */
@Data
public class MpcPlanRequest {

    @NotNull(message = "UAV ID 不能为空")
    private String uavId;

    @NotNull(message = "航点列表不能为空")
    private List<Waypoint> waypoints;

    @NotNull(message = "约束条件不能为空")
    private MpcConstraints constraints;

    /** 优化目标: RISK/ENERGY/TIME */
    private String optimizationTarget;

    @Data
    public static class Waypoint {
        private Double longitude;
        private Double latitude;
        private Double altitude;
        private Double speed;
    }

    @Data
    public static class MpcConstraints {
        private Double maxAltitude;
        private Double minAltitude;
        private Double maxSpeed;
        private Double weatherRiskThreshold;
        /** 重规划间隔（秒），默认 30 秒 */
        private Double replanIntervalSeconds = 30.0;
        /** MPC 预测步数，默认 10 */
        private Integer horizonSteps = 10;
    }
}

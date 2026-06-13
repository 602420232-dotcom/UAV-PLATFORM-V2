package com.uav.planning.dto;

import lombok.Data;

import java.util.List;

/**
 * MPC 规划结果
 */
@Data
public class MpcResult {

    private String taskId;
    /** 当前最优航段 */
    private List<MpcSegment> segments;
    /** 总风险值 */
    private Double totalRisk;
    /** 预估能耗 */
    private Double estimatedEnergy;
    /** 剩余航点数 */
    private Integer remainingWaypoints;
    /** 下次重规划时间 */
    private String nextReplanTime;

    @Data
    public static class MpcSegment {
        private Double startLon;
        private Double startLat;
        private Double endLon;
        private Double endLat;
        private Double altitude;
        private Double speed;
        private Double riskScore;
    }
}

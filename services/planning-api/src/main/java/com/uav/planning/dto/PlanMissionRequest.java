package com.uav.planning.dto;

import jakarta.validation.constraints.NotEmpty;
import lombok.Data;

import java.util.List;
import java.util.Map;

/**
 * 任务规划请求
 */
@Data
public class PlanMissionRequest {

    /** 无人机列表 */
    @NotEmpty
    private List<Map<String, Object>> uavList;

    /** 任务列表 */
    @NotEmpty
    private List<Map<String, Object>> taskList;

    /** 区域边界 {minLon, minLat, maxLon, maxLat} */
    private Map<String, Double> areaBounds;

    /** 优先级配置 */
    private Map<String, Integer> priorities;
}

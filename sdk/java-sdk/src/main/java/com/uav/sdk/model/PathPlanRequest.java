package com.uav.sdk.model;

import java.util.List;
import java.util.Map;

/**
 * 路径规划请求
 */
public class PathPlanRequest {

    private Map<String, Double> start;
    private Map<String, Double> end;
    private List<Map<String, Double>> waypoints;
    private String uavModel;
    private Map<String, Object> constraints;
    private String optimizationTarget;

    public PathPlanRequest() {}

    public Map<String, Double> getStart() { return start; }
    public void setStart(Map<String, Double> start) { this.start = start; }
    public Map<String, Double> getEnd() { return end; }
    public void setEnd(Map<String, Double> end) { this.end = end; }
    public List<Map<String, Double>> getWaypoints() { return waypoints; }
    public void setWaypoints(List<Map<String, Double>> waypoints) { this.waypoints = waypoints; }
    public String getUavModel() { return uavModel; }
    public void setUavModel(String uavModel) { this.uavModel = uavModel; }
    public Map<String, Object> getConstraints() { return constraints; }
    public void setConstraints(Map<String, Object> constraints) { this.constraints = constraints; }
    public String getOptimizationTarget() { return optimizationTarget; }
    public void setOptimizationTarget(String optimizationTarget) { this.optimizationTarget = optimizationTarget; }
}

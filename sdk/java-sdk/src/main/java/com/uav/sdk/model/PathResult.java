package com.uav.sdk.model;

/**
 * 路径规划结果
 */
public class PathResult {

    private Long id;
    private String taskId;
    private String waypointsJson;
    private Double totalDistance;
    private Integer estimatedTime;
    private Double riskScore;
    private Double energyConsumption;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getTaskId() { return taskId; }
    public void setTaskId(String taskId) { this.taskId = taskId; }
    public String getWaypointsJson() { return waypointsJson; }
    public void setWaypointsJson(String waypointsJson) { this.waypointsJson = waypointsJson; }
    public Double getTotalDistance() { return totalDistance; }
    public void setTotalDistance(Double totalDistance) { this.totalDistance = totalDistance; }
    public Integer getEstimatedTime() { return estimatedTime; }
    public void setEstimatedTime(Integer estimatedTime) { this.estimatedTime = estimatedTime; }
    public Double getRiskScore() { return riskScore; }
    public void setRiskScore(Double riskScore) { this.riskScore = riskScore; }
    public Double getEnergyConsumption() { return energyConsumption; }
    public void setEnergyConsumption(Double energyConsumption) { this.energyConsumption = energyConsumption; }
}

package com.uav.sdk.model;

import java.util.Map;

/**
 * 风险评估结果
 */
public class RiskAssessmentResult {

    private String taskId;
    private Double overallRiskScore;
    private Map<String, Object> weatherRisk;
    private Map<String, Object> terrainRisk;
    private Map<String, Object> airspaceRisk;
    private Map<String, Object> compositeRisk;
    private String riskLevel;
    private String recommendation;

    public String getTaskId() { return taskId; }
    public void setTaskId(String taskId) { this.taskId = taskId; }
    public Double getOverallRiskScore() { return overallRiskScore; }
    public void setOverallRiskScore(Double overallRiskScore) { this.overallRiskScore = overallRiskScore; }
    public Map<String, Object> getWeatherRisk() { return weatherRisk; }
    public void setWeatherRisk(Map<String, Object> weatherRisk) { this.weatherRisk = weatherRisk; }
    public Map<String, Object> getTerrainRisk() { return terrainRisk; }
    public void setTerrainRisk(Map<String, Object> terrainRisk) { this.terrainRisk = terrainRisk; }
    public Map<String, Object> getAirspaceRisk() { return airspaceRisk; }
    public void setAirspaceRisk(Map<String, Object> airspaceRisk) { this.airspaceRisk = airspaceRisk; }
    public Map<String, Object> getCompositeRisk() { return compositeRisk; }
    public void setCompositeRisk(Map<String, Object> compositeRisk) { this.compositeRisk = compositeRisk; }
    public String getRiskLevel() { return riskLevel; }
    public void setRiskLevel(String riskLevel) { this.riskLevel = riskLevel; }
    public String getRecommendation() { return recommendation; }
    public void setRecommendation(String recommendation) { this.recommendation = recommendation; }
}

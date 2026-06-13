package com.uav.sdk.model;

import java.util.Map;

/**
 * 风险评估请求
 */
public class RiskAssessmentRequest {

    private Map<String, Double> start;
    private Map<String, Double> end;
    private Double altitude;
    private String uavModel;
    private String assessmentType;

    public RiskAssessmentRequest() {}

    public Map<String, Double> getStart() { return start; }
    public void setStart(Map<String, Double> start) { this.start = start; }
    public Map<String, Double> getEnd() { return end; }
    public void setEnd(Map<String, Double> end) { this.end = end; }
    public Double getAltitude() { return altitude; }
    public void setAltitude(Double altitude) { this.altitude = altitude; }
    public String getUavModel() { return uavModel; }
    public void setUavModel(String uavModel) { this.uavModel = uavModel; }
    public String getAssessmentType() { return assessmentType; }
    public void setAssessmentType(String assessmentType) { this.assessmentType = assessmentType; }
}

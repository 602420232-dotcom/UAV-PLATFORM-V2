package com.bayesian.dto.response;

import java.util.Map;

public class AssimilationResponse {
    private String status;
    private Map<String, Object> analysis;
    private Map<String, Object> variance;
    private Map<String, Object> metrics;
    private String message;

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public Map<String, Object> getAnalysis() { return analysis; }
    public void setAnalysis(Map<String, Object> analysis) { this.analysis = analysis; }
    public Map<String, Object> getVariance() { return variance; }
    public void setVariance(Map<String, Object> variance) { this.variance = variance; }
    public Map<String, Object> getMetrics() { return metrics; }
    public void setMetrics(Map<String, Object> metrics) { this.metrics = metrics; }
    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }
}

package com.bayesian.dto.request;

import java.util.List;
import java.util.Map;

public class AssimilationRequest {
    private String algorithm;
    private Map<String, Object> background;
    private List<Map<String, Object>> observations;
    private Map<String, Object> config;

    public String getAlgorithm() { return algorithm; }
    public void setAlgorithm(String algorithm) { this.algorithm = algorithm; }
    public Map<String, Object> getBackground() { return background; }
    public void setBackground(Map<String, Object> background) { this.background = background; }
    public List<Map<String, Object>> getObservations() { return observations; }
    public void setObservations(List<Map<String, Object>> observations) { this.observations = observations; }
    public Map<String, Object> getConfig() { return config; }
    public void setConfig(Map<String, Object> config) { this.config = config; }
}

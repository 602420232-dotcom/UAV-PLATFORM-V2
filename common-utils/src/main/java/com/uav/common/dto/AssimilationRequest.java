package com.uav.common.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.util.Map;

public class AssimilationRequest {

    @NotBlank(message = "算法名称不能为空")
    @Size(max = 50, message = "算法名称最长50字符")
    private String algorithm;

    private Map<String, Object> background;

    @Size(max = 10000, message = "观测数据量过大")
    private Map<String, Object> observations;

    private Map<String, Object> config;

    public AssimilationRequest() {}

    public String getAlgorithm() { return algorithm; }
    public void setAlgorithm(String algorithm) { this.algorithm = algorithm; }
    public Map<String, Object> getBackground() { return background; }
    public void setBackground(Map<String, Object> background) { this.background = background; }
    public Map<String, Object> getObservations() { return observations; }
    public void setObservations(Map<String, Object> observations) { this.observations = observations; }
    public Map<String, Object> getConfig() { return config; }
    public void setConfig(Map<String, Object> config) { this.config = config; }
}

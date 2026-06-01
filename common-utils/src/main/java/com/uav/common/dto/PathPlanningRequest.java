package com.uav.common.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.util.Map;

public class PathPlanningRequest {

    @NotBlank(message = "规划算法不能为空")
    @Size(max = 50, message = "算法名称最长50字符")
    private String algorithm;

    private Map<String, Object> drones;

    private Map<String, Object> tasks;

    private Map<String, Object> weatherData;

    private Map<String, Object> constraints;

    public PathPlanningRequest() {}

    public String getAlgorithm() { return algorithm; }
    public void setAlgorithm(String algorithm) { this.algorithm = algorithm; }
    public Map<String, Object> getDrones() { return drones; }
    public void setDrones(Map<String, Object> drones) { this.drones = drones; }
    public Map<String, Object> getTasks() { return tasks; }
    public void setTasks(Map<String, Object> tasks) { this.tasks = tasks; }
    public Map<String, Object> getWeatherData() { return weatherData; }
    public void setWeatherData(Map<String, Object> weatherData) { this.weatherData = weatherData; }
    public Map<String, Object> getConstraints() { return constraints; }
    public void setConstraints(Map<String, Object> constraints) { this.constraints = constraints; }
}

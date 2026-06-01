package com.uav.common.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.util.Map;

public class ForecastRequest {

    @NotBlank(message = "预测方法不能为空")
    @Size(max = 50, message = "方法名称最长50字符")
    private String method;

    private Map<String, Object> data;

    private Map<String, Object> config;

    public ForecastRequest() {}

    public String getMethod() { return method; }
    public void setMethod(String method) { this.method = method; }
    public Map<String, Object> getData() { return data; }
    public void setData(Map<String, Object> data) { this.data = data; }
    public Map<String, Object> getConfig() { return config; }
    public void setConfig(Map<String, Object> config) { this.config = config; }
}

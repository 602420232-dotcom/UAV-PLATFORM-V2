package com.uav.sdk.model;

import java.util.Map;

/**
 * 数据同化任务请求
 */
public class AssimilationTaskRequest {

    private String algorithmType;
    private Map<String, Object> params;
    private Long tenantId;

    public AssimilationTaskRequest() {}

    public AssimilationTaskRequest(String algorithmType, Map<String, Object> params) {
        this.algorithmType = algorithmType;
        this.params = params;
    }

    public String getAlgorithmType() { return algorithmType; }
    public void setAlgorithmType(String algorithmType) { this.algorithmType = algorithmType; }
    public Map<String, Object> getParams() { return params; }
    public void setParams(Map<String, Object> params) { this.params = params; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
}

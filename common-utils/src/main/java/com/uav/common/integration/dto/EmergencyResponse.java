package com.uav.common.integration.dto;

import java.time.LocalDateTime;

/**
 * 紧急情况响应 - UTM系统返回
 */
public class EmergencyResponse {

    private String alertId;
    private String droneId;
    private String type;
    private String severity;
    private LocalDateTime timestamp;
    private String instructions;

    public EmergencyResponse() {}

    public EmergencyResponse(String alertId, String droneId, String type,
                             String severity, LocalDateTime timestamp,
                             String instructions) {
        this.alertId = alertId;
        this.droneId = droneId;
        this.type = type;
        this.severity = severity;
        this.timestamp = timestamp;
        this.instructions = instructions;
    }

    public String getAlertId() {
        return alertId;
    }

    public void setAlertId(String alertId) {
        this.alertId = alertId;
    }

    public String getDroneId() {
        return droneId;
    }

    public void setDroneId(String droneId) {
        this.droneId = droneId;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public String getSeverity() {
        return severity;
    }

    public void setSeverity(String severity) {
        this.severity = severity;
    }

    public LocalDateTime getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(LocalDateTime timestamp) {
        this.timestamp = timestamp;
    }

    public String getInstructions() {
        return instructions;
    }

    public void setInstructions(String instructions) {
        this.instructions = instructions;
    }
}

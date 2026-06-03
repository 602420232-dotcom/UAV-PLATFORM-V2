package com.uav.common.integration.dto;

/**
 * 无人机注册信息 - 用于UTM系统注册
 */
public class DroneInfo {

    private String droneId;
    private String model;
    private String serialNumber;
    private String operatorName;
    private String operatorPhone;
    private Double maxAltitude;
    private Integer maxFlightTime;

    public DroneInfo() {}

    public DroneInfo(String droneId, String model, String serialNumber,
                     String operatorName, String operatorPhone,
                     Double maxAltitude, Integer maxFlightTime) {
        this.droneId = droneId;
        this.model = model;
        this.serialNumber = serialNumber;
        this.operatorName = operatorName;
        this.operatorPhone = operatorPhone;
        this.maxAltitude = maxAltitude;
        this.maxFlightTime = maxFlightTime;
    }

    public String getDroneId() {
        return droneId;
    }

    public void setDroneId(String droneId) {
        this.droneId = droneId;
    }

    public String getModel() {
        return model;
    }

    public void setModel(String model) {
        this.model = model;
    }

    public String getSerialNumber() {
        return serialNumber;
    }

    public void setSerialNumber(String serialNumber) {
        this.serialNumber = serialNumber;
    }

    public String getOperatorName() {
        return operatorName;
    }

    public void setOperatorName(String operatorName) {
        this.operatorName = operatorName;
    }

    public String getOperatorPhone() {
        return operatorPhone;
    }

    public void setOperatorPhone(String operatorPhone) {
        this.operatorPhone = operatorPhone;
    }

    public Double getMaxAltitude() {
        return maxAltitude;
    }

    public void setMaxAltitude(Double maxAltitude) {
        this.maxAltitude = maxAltitude;
    }

    public Integer getMaxFlightTime() {
        return maxFlightTime;
    }

    public void setMaxFlightTime(Integer maxFlightTime) {
        this.maxFlightTime = maxFlightTime;
    }
}

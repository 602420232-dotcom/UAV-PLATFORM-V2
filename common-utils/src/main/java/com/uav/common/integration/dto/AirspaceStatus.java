package com.uav.common.integration.dto;

/**
 * 空域状态 - UTM系统返回
 */
public class AirspaceStatus {

    public enum Status {
        ACTIVE,
        RESTRICTED,
        CLOSED
    }

    private String zoneId;
    private Status status;
    private String restrictions;
    private String weatherAlert;
    private int droneCount;
    private int maxDronesAllowed;

    public AirspaceStatus() {}

    public AirspaceStatus(String zoneId, Status status, String restrictions,
                          String weatherAlert, int droneCount, int maxDronesAllowed) {
        this.zoneId = zoneId;
        this.status = status;
        this.restrictions = restrictions;
        this.weatherAlert = weatherAlert;
        this.droneCount = droneCount;
        this.maxDronesAllowed = maxDronesAllowed;
    }

    public String getZoneId() {
        return zoneId;
    }

    public void setZoneId(String zoneId) {
        this.zoneId = zoneId;
    }

    public Status getStatus() {
        return status;
    }

    public void setStatus(Status status) {
        this.status = status;
    }

    public String getRestrictions() {
        return restrictions;
    }

    public void setRestrictions(String restrictions) {
        this.restrictions = restrictions;
    }

    public String getWeatherAlert() {
        return weatherAlert;
    }

    public void setWeatherAlert(String weatherAlert) {
        this.weatherAlert = weatherAlert;
    }

    public int getDroneCount() {
        return droneCount;
    }

    public void setDroneCount(int droneCount) {
        this.droneCount = droneCount;
    }

    public int getMaxDronesAllowed() {
        return maxDronesAllowed;
    }

    public void setMaxDronesAllowed(int maxDronesAllowed) {
        this.maxDronesAllowed = maxDronesAllowed;
    }
}

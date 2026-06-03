package com.uav.common.integration.dto;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 飞行计划 - 提交至UTM系统
 */
public class FlightPlan {

    private String planId;
    private String droneId;
    private LocalDateTime departureTime;
    private LocalDateTime arrivalTime;
    private List<LatLng> waypoints;
    private Double maxAltitude;
    private String missionType;

    public FlightPlan() {}

    public FlightPlan(String planId, String droneId, LocalDateTime departureTime,
                      LocalDateTime arrivalTime, List<LatLng> waypoints,
                      Double maxAltitude, String missionType) {
        this.planId = planId;
        this.droneId = droneId;
        this.departureTime = departureTime;
        this.arrivalTime = arrivalTime;
        this.waypoints = waypoints;
        this.maxAltitude = maxAltitude;
        this.missionType = missionType;
    }

    public String getPlanId() {
        return planId;
    }

    public void setPlanId(String planId) {
        this.planId = planId;
    }

    public String getDroneId() {
        return droneId;
    }

    public void setDroneId(String droneId) {
        this.droneId = droneId;
    }

    public LocalDateTime getDepartureTime() {
        return departureTime;
    }

    public void setDepartureTime(LocalDateTime departureTime) {
        this.departureTime = departureTime;
    }

    public LocalDateTime getArrivalTime() {
        return arrivalTime;
    }

    public void setArrivalTime(LocalDateTime arrivalTime) {
        this.arrivalTime = arrivalTime;
    }

    public List<LatLng> getWaypoints() {
        return waypoints;
    }

    public void setWaypoints(List<LatLng> waypoints) {
        this.waypoints = waypoints;
    }

    public Double getMaxAltitude() {
        return maxAltitude;
    }

    public void setMaxAltitude(Double maxAltitude) {
        this.maxAltitude = maxAltitude;
    }

    public String getMissionType() {
        return missionType;
    }

    public void setMissionType(String missionType) {
        this.missionType = missionType;
    }
}

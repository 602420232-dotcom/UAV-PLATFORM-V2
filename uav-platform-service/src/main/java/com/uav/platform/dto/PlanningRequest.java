package com.uav.platform.dto;

import jakarta.validation.constraints.NotBlank;

public class PlanningRequest {

    @NotBlank(message = "算法类型不能为空")
    private String algorithm;

    private Object drones;

    private Object tasks;

    private Object waypoints;

    private Object obstacles;

    private Object noFlyZones;

    public String getAlgorithm() {
        return algorithm;
    }

    public void setAlgorithm(String algorithm) {
        this.algorithm = algorithm;
    }

    public Object getDrones() {
        return drones;
    }

    public void setDrones(Object drones) {
        this.drones = drones;
    }

    public Object getTasks() {
        return tasks;
    }

    public void setTasks(Object tasks) {
        this.tasks = tasks;
    }

    public Object getWaypoints() {
        return waypoints;
    }

    public void setWaypoints(Object waypoints) {
        this.waypoints = waypoints;
    }

    public Object getObstacles() {
        return obstacles;
    }

    public void setObstacles(Object obstacles) {
        this.obstacles = obstacles;
    }

    public Object getNoFlyZones() {
        return noFlyZones;
    }

    public void setNoFlyZones(Object noFlyZones) {
        this.noFlyZones = noFlyZones;
    }
}

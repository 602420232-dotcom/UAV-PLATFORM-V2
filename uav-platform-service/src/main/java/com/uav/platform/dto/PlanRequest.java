package com.uav.platform.dto;

import jakarta.validation.constraints.NotNull;

public class PlanRequest {

    @NotNull(message = "无人机列表不能为空")
    private Object drones;

    @NotNull(message = "任务列表不能为空")
    private Object tasks;

    private Object weatherData;

    private Object obstacles;

    private Object noFlyZones;

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

    public Object getWeatherData() {
        return weatherData;
    }

    public void setWeatherData(Object weatherData) {
        this.weatherData = weatherData;
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

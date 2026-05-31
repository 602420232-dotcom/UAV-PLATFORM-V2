package com.uav.platform.dto;

import jakarta.validation.constraints.*;
import java.util.List;

public class TaskRequest {

    @NotBlank(message = "任务名称不能为空")
    @Size(max = 200, message = "任务名称长度不能超过200个字符")
    private String name;

    @Pattern(regexp = "^(delivery|inspection|patrol|emergency|surveillance)$", message = "无效的任务类型")
    private String type;

    @Pattern(regexp = "^(low|medium|high|critical)$", message = "优先级必须是: low, medium, high, critical")
    private String priority;

    private String description;

    private List<Waypoint> waypoints;

    public static class Waypoint {
        @NotNull(message = "纬度不能为空")
        @DecimalMin(value = "-90.0", message = "纬度范围: -90到90")
        @DecimalMax(value = "90.0", message = "纬度范围: -90到90")
        private Double lat;

        @NotNull(message = "经度不能为空")
        @DecimalMin(value = "-180.0", message = "经度范围: -180到180")
        @DecimalMax(value = "180.0", message = "经度范围: -180到180")
        private Double lng;

        @Min(value = 0, message = "高度不能为负数")
        @Max(value = 10000, message = "高度不能超过10000米")
        private Double altitude;

        private String name;

        private Integer order;

        public Double getLat() { return lat; }
        public void setLat(Double lat) { this.lat = lat; }

        public Double getLng() { return lng; }
        public void setLng(Double lng) { this.lng = lng; }

        public Double getAltitude() { return altitude; }
        public void setAltitude(Double altitude) { this.altitude = altitude; }

        public String getName() { return name; }
        public void setName(String name) { this.name = name; }

        public Integer getOrder() { return order; }
        public void setOrder(Integer order) { this.order = order; }
    }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public String getPriority() { return priority; }
    public void setPriority(String priority) { this.priority = priority; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public List<Waypoint> getWaypoints() { return waypoints; }
    public void setWaypoints(List<Waypoint> waypoints) { this.waypoints = waypoints; }
}

package com.uav.platform.dto;

import jakarta.validation.constraints.*;

public class DroneRequest {

    @NotBlank(message = "无人机名称不能为空")
    @Size(max = 100, message = "名称长度不能超过100个字符")
    private String name;

    @Size(max = 100, message = "型号长度不能超过100个字符")
    private String model;

    @Pattern(regexp = "^(多旋翼|固定翼|垂直起降)$", message = "类型必须是: 多旋翼, 固定翼, 垂直起降")
    private String type;

    @DecimalMin(value = "0.0", message = "最大载荷不能为负数")
    @DecimalMax(value = "100.0", message = "最大载荷不能超过100kg")
    private Double maxPayload;

    @Min(value = 0, message = "最大飞行时间不能为负数")
    @Max(value = 480, message = "最大飞行时间不能超过480分钟")
    private Integer maxFlightTime;

    @Min(value = 0, message = "最大速度不能为负数")
    @Max(value = 200, message = "最大速度不能超过200m/s")
    private Integer maxSpeed;

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getModel() { return model; }
    public void setModel(String model) { this.model = model; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public Double getMaxPayload() { return maxPayload; }
    public void setMaxPayload(Double maxPayload) { this.maxPayload = maxPayload; }

    public Integer getMaxFlightTime() { return maxFlightTime; }
    public void setMaxFlightTime(Integer maxFlightTime) { this.maxFlightTime = maxFlightTime; }

    public Integer getMaxSpeed() { return maxSpeed; }
    public void setMaxSpeed(Integer maxSpeed) { this.maxSpeed = maxSpeed; }
}

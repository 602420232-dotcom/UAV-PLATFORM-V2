package com.uav.utm.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("flight_plan")
public class FlightPlan {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 飞行计划唯一标识 */
    @TableField("plan_id")
    private String planId;

    @NotBlank
    private String uavId;

    @NotBlank
    private String operatorId;

    @NotBlank
    private String waypointsJson;

    @NotNull
    private LocalDateTime plannedStartTime;

    @NotNull
    private LocalDateTime plannedEndTime;

    private LocalDateTime actualStartTime;

    private LocalDateTime actualEndTime;

    @NotNull
    private FlightPlanStatus status;

    private String approvalCode;

    private Boolean emergencyFlag;

    @NotBlank
    private String tenantId;

    private LocalDateTime createdAt;

    public enum FlightPlanStatus {
        SUBMITTED,
        APPROVED,
        REJECTED,
        ACTIVE,
        COMPLETED,
        CANCELLED
    }
}

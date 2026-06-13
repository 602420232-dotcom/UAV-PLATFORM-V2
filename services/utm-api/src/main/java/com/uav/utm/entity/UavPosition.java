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
@TableName("uav_position")
public class UavPosition {

    @TableId(type = IdType.AUTO)
    private Long id;

    @NotBlank
    private String uavId;

    @NotNull
    private Double longitude;

    @NotNull
    private Double latitude;

    @NotNull
    private Double altitude;

    private Double speed;

    private Double heading;

    @TableField("flight_plan_id")
    private String flightPlanId;

    /** 记录时间（数据库列名 recorded_at） */
    @TableField("recorded_at")
    private LocalDateTime recordedAt;
}

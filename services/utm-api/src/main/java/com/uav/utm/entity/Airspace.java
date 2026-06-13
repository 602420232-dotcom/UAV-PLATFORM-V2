package com.uav.utm.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("airspace")
public class Airspace {

    @TableId(type = IdType.AUTO)
    private Long id;

    @NotNull
    private AirspaceType type;

    @NotBlank
    private String boundsJson;

    @NotNull
    private Double altitudeMin;

    @NotNull
    private Double altitudeMax;

    private LocalDateTime effectiveTimeStart;

    private LocalDateTime effectiveTimeEnd;

    @NotNull
    private AirspaceStatus status;

    private String tenantId;

    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;

    public enum AirspaceType {
        STATIC,
        DYNAMIC,
        RESTRICTED
    }

    public enum AirspaceStatus {
        ACTIVE,
        INACTIVE
    }
}

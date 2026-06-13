package com.uav.utm.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("conflict_alert")
public class ConflictAlert {

    @TableId(type = IdType.AUTO)
    private Long id;

    @NotNull
    private ConflictType type;

    @NotNull
    private Severity severity;

    @NotBlank
    private String involvedEntitiesJson;

    private String resolutionAdviceJson;

    @NotNull
    private AlertStatus status;

    @NotNull
    private LocalDateTime createdAt;

    private LocalDateTime resolvedAt;

    public enum ConflictType {
        GEOFENCE,
        UAV
    }

    public enum Severity {
        LOW,
        MEDIUM,
        HIGH,
        CRITICAL
    }

    public enum AlertStatus {
        ACTIVE,
        RESOLVED
    }
}

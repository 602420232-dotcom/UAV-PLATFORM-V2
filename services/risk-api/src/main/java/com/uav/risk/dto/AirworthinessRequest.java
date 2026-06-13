package com.uav.risk.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

import java.util.Map;

/**
 * 适航评估请求
 */
@Data
public class AirworthinessRequest {

    @NotBlank
    private String uavModel;

    /** 重量(kg) */
    private Double weight;

    /** 翼展(m) */
    private Double wingspan;

    /** 电池容量(mAh) */
    private Integer batteryCapacity;

    /** 任务类型 */
    private String missionType;

    /** 气象条件 */
    private Map<String, Object> weatherConditions;
}

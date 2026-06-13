package com.uav.risk.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

/**
 * 风险查询请求
 */
@Data
public class RiskQueryRequest {

    @NotNull
    private Double longitude;

    @NotNull
    private Double latitude;

    /** 海拔高度 */
    private Double altitude;

    /** 无人机型号 */
    private String uavModel;

    /** 任务类型 */
    private String missionType;
}

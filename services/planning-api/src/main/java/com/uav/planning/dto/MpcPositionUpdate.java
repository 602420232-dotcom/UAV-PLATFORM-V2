package com.uav.planning.dto;

import lombok.Data;

/**
 * MPC 实时位置更新请求
 */
@Data
public class MpcPositionUpdate {

    private String uavId;
    private String taskId;
    private Double longitude;
    private Double latitude;
    private Double altitude;
    private Double speed;
    private Double heading;
}

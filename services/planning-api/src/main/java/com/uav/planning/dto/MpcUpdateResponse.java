package com.uav.planning.dto;

import lombok.Data;

/**
 * MPC 位置更新响应
 */
@Data
public class MpcUpdateResponse {

    /** 是否触发了重规划 */
    private boolean replanTriggered;
    /** 触发原因 */
    private String reason;
    /** 下次重规划时间 */
    private String nextReplanTime;
}

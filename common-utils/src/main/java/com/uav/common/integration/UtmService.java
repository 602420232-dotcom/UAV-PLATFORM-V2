package com.uav.common.integration;

import com.uav.common.integration.dto.AirspaceStatus;
import com.uav.common.integration.dto.DroneInfo;
import com.uav.common.integration.dto.EmergencyResponse;
import com.uav.common.integration.dto.FlightApproval;
import com.uav.common.integration.dto.FlightPlan;

/**
 * UTM (Unmanned Traffic Management) 系统集成接口
 * 用于与无人机交通管理系统进行通信
 */
public interface UtmService {

    /**
     * 在UTM系统中注册无人机
     *
     * @param droneInfo 无人机信息
     * @return 注册ID
     */
    String registerDrone(DroneInfo droneInfo);

    /**
     * 提交飞行计划至UTM系统
     *
     * @param plan 飞行计划
     * @return true表示提交成功
     */
    boolean submitFlightPlan(FlightPlan plan);

    /**
     * 查询飞行计划审批状态
     *
     * @param planId 计划ID
     * @return 审批结果
     */
    FlightApproval getFlightApproval(String planId);

    /**
     * 查询指定空域状态
     *
     * @param lat    纬度
     * @param lon    经度
     * @param radius 查询半径（米）
     * @return 空域状态
     */
    AirspaceStatus queryAirspace(double lat, double lon, double radius);

    /**
     * 发送紧急警报
     *
     * @param droneId 无人机ID
     * @param type    紧急事件类型
     * @return 紧急响应
     */
    EmergencyResponse sendEmergencyAlert(String droneId, EmergencyType type);

    /**
     * 紧急事件类型枚举
     */
    enum EmergencyType {
        BATTERY_LOW,
        SIGNAL_LOST,
        GEOFENCE_VIOLATION,
        MECHANICAL_FAILURE,
        WEATHER_EMERGENCY,
        COLLISION_RISK,
        OTHER
    }
}

package com.uav.sdk.api;

import com.fasterxml.jackson.core.type.TypeReference;
import com.uav.sdk.config.ClientConfig;
import com.uav.sdk.http.HttpClientWrapper;
import com.uav.sdk.http.HttpClientWrapper.SdkResponse;

import java.io.IOException;
import java.util.Map;

/**
 * UTM 管理 API
 * <p>
 * 提供空域管理、飞行计划审批、冲突检测等 UTM（无人机交通管理）功能。
 */
public class UtmApi {

    private static final String BASE_PATH = "/api/v1/utm";

    private final HttpClientWrapper httpClient;
    private final ClientConfig config;

    public UtmApi(HttpClientWrapper httpClient, ClientConfig config) {
        this.httpClient = httpClient;
        this.config = config;
    }

    /**
     * 提交飞行计划
     *
     * @param flightPlan 飞行计划
     * @return 审批结果
     */
    public Map<String, Object> submitFlightPlan(Map<String, Object> flightPlan)
            throws IOException, InterruptedException {
        SdkResponse<Map<String, Object>> response = httpClient.postAndDeserialize(
                BASE_PATH + "/flight-plans", flightPlan,
                new TypeReference<SdkResponse<Map<String, Object>>>() {});
        return response.getData();
    }

    /**
     * 查询飞行计划状态
     *
     * @param planId 飞行计划 ID
     * @return 飞行计划详情
     */
    public Map<String, Object> getFlightPlan(String planId)
            throws IOException, InterruptedException {
        SdkResponse<Map<String, Object>> response = httpClient.getAndDeserialize(
                BASE_PATH + "/flight-plans/" + planId,
                new TypeReference<SdkResponse<Map<String, Object>>>() {});
        return response.getData();
    }

    /**
     * 查询空域状态
     *
     * @param areaId 空域 ID
     * @return 空域状态信息
     */
    public Map<String, Object> getAirspaceStatus(String areaId)
            throws IOException, InterruptedException {
        SdkResponse<Map<String, Object>> response = httpClient.getAndDeserialize(
                BASE_PATH + "/airspace/" + areaId + "/status",
                new TypeReference<SdkResponse<Map<String, Object>>>() {});
        return response.getData();
    }

    /**
     * 冲突检测
     *
     * @param flightPlan 飞行计划
     * @return 冲突检测结果
     */
    public Map<String, Object> checkConflict(Map<String, Object> flightPlan)
            throws IOException, InterruptedException {
        SdkResponse<Map<String, Object>> response = httpClient.postAndDeserialize(
                BASE_PATH + "/conflict-check", flightPlan,
                new TypeReference<SdkResponse<Map<String, Object>>>() {});
        return response.getData();
    }
}

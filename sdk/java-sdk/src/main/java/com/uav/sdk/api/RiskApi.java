package com.uav.sdk.api;

import com.fasterxml.jackson.core.type.TypeReference;
import com.uav.sdk.config.ClientConfig;
import com.uav.sdk.http.HttpClientWrapper;
import com.uav.sdk.http.HttpClientWrapper.SdkResponse;
import com.uav.sdk.model.RiskAssessmentRequest;
import com.uav.sdk.model.RiskAssessmentResult;
import com.uav.sdk.model.TaskResult;

import java.io.IOException;

/**
 * 风险评估 API
 * <p>
 * 提供航线风险评估功能，包括天气风险、地形风险、空域风险和综合风险评估。
 */
public class RiskApi {

    private static final String BASE_PATH = "/api/v1/risk";

    private final HttpClientWrapper httpClient;
    private final ClientConfig config;

    public RiskApi(HttpClientWrapper httpClient, ClientConfig config) {
        this.httpClient = httpClient;
        this.config = config;
    }

    /**
     * 提交风险评估任务
     *
     * @param request 风险评估请求
     * @return 任务结果
     */
    public TaskResult submitAssessment(RiskAssessmentRequest request)
            throws IOException, InterruptedException {
        SdkResponse<TaskResult> response = httpClient.postAndDeserialize(
                BASE_PATH + "/assess", request,
                new TypeReference<SdkResponse<TaskResult>>() {});
        return response.getData();
    }

    /**
     * 获取风险评估结果
     *
     * @param taskId 任务 ID
     * @return 风险评估结果
     */
    public RiskAssessmentResult getResult(Long taskId) throws IOException, InterruptedException {
        SdkResponse<RiskAssessmentResult> response = httpClient.getAndDeserialize(
                BASE_PATH + "/assess/" + taskId + "/result",
                new TypeReference<SdkResponse<RiskAssessmentResult>>() {});
        return response.getData();
    }

    /**
     * 获取任务状态
     *
     * @param taskId 任务 ID
     * @return 任务结果
     */
    public TaskResult getTaskStatus(Long taskId) throws IOException, InterruptedException {
        SdkResponse<TaskResult> response = httpClient.getAndDeserialize(
                BASE_PATH + "/assess/" + taskId,
                new TypeReference<SdkResponse<TaskResult>>() {});
        return response.getData();
    }
}

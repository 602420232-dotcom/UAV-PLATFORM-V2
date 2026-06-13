package com.uav.sdk.api;

import com.fasterxml.jackson.core.type.TypeReference;
import com.uav.sdk.config.ClientConfig;
import com.uav.sdk.http.HttpClientWrapper;
import com.uav.sdk.http.HttpClientWrapper.SdkResponse;
import com.uav.sdk.model.AssimilationTaskRequest;
import com.uav.sdk.model.TaskResult;

import java.io.IOException;

/**
 * 数据同化 API
 * <p>
 * 提供数据同化任务的提交、状态查询和结果获取功能。
 * 支持 3D-VAR、4D-VAR、5D-VAR、EnKF、Hybrid、Enhanced Bayesian 等算法。
 */
public class AssimilationApi {

    private static final String BASE_PATH = "/api/v1/assimilation";

    private final HttpClientWrapper httpClient;
    private final ClientConfig config;

    public AssimilationApi(HttpClientWrapper httpClient, ClientConfig config) {
        this.httpClient = httpClient;
        this.config = config;
    }

    /**
     * 提交数据同化任务
     *
     * @param algorithmType 算法类型（如 5DVAR、ENKF、HYBRID 等）
     * @param params        算法参数
     * @return 任务 ID
     */
    public Long submitTask(String algorithmType, java.util.Map<String, Object> params)
            throws IOException, InterruptedException {
        AssimilationTaskRequest request = new AssimilationTaskRequest(algorithmType, params);
        SdkResponse<Long> response = httpClient.postAndDeserialize(
                BASE_PATH + "/tasks", request,
                new TypeReference<SdkResponse<Long>>() {});
        return response.getData();
    }

    /**
     * 提交数据同化任务（完整请求对象）
     *
     * @param request 同化任务请求
     * @return 任务 ID
     */
    public Long submitTask(AssimilationTaskRequest request)
            throws IOException, InterruptedException {
        SdkResponse<Long> response = httpClient.postAndDeserialize(
                BASE_PATH + "/tasks", request,
                new TypeReference<SdkResponse<Long>>() {});
        return response.getData();
    }

    /**
     * 查询任务状态
     *
     * @param taskId 任务 ID
     * @return 任务结果
     */
    public TaskResult getTaskStatus(Long taskId) throws IOException, InterruptedException {
        SdkResponse<TaskResult> response = httpClient.getAndDeserialize(
                BASE_PATH + "/tasks/" + taskId,
                new TypeReference<SdkResponse<TaskResult>>() {});
        return response.getData();
    }

    /**
     * 获取任务结果
     *
     * @param taskId 任务 ID
     * @return 任务结果
     */
    public TaskResult getTaskResult(Long taskId) throws IOException, InterruptedException {
        SdkResponse<TaskResult> response = httpClient.getAndDeserialize(
                BASE_PATH + "/tasks/" + taskId + "/result",
                new TypeReference<SdkResponse<TaskResult>>() {});
        return response.getData();
    }

    /**
     * 取消任务
     *
     * @param taskId 任务 ID
     */
    public void cancelTask(Long taskId) throws IOException, InterruptedException {
        httpClient.post(BASE_PATH + "/tasks/" + taskId + "/cancel", null);
    }
}

package com.uav.sdk.api;

import com.fasterxml.jackson.core.type.TypeReference;
import com.uav.sdk.config.ClientConfig;
import com.uav.sdk.http.HttpClientWrapper;
import com.uav.sdk.http.HttpClientWrapper.SdkResponse;
import com.uav.sdk.model.PathPlanRequest;
import com.uav.sdk.model.PathResult;
import com.uav.sdk.model.TaskResult;

import java.io.IOException;
import java.util.List;
import java.util.Map;

/**
 * 路径规划 API
 * <p>
 * 提供路径规划和任务规划功能，支持多种优化目标（风险、能耗、时间、均衡）。
 */
public class PlanningApi {

    private static final String BASE_PATH = "/api/v1/planning";

    private final HttpClientWrapper httpClient;
    private final ClientConfig config;

    public PlanningApi(HttpClientWrapper httpClient, ClientConfig config) {
        this.httpClient = httpClient;
        this.config = config;
    }

    /**
     * 提交路径规划任务
     *
     * @param request 路径规划请求
     * @return 任务结果
     */
    public TaskResult submitPathPlanning(PathPlanRequest request)
            throws IOException, InterruptedException {
        SdkResponse<TaskResult> response = httpClient.postAndDeserialize(
                BASE_PATH + "/path", request,
                new TypeReference<SdkResponse<TaskResult>>() {});
        return response.getData();
    }

    /**
     * 提交任务规划
     *
     * @param uavList   无人机列表
     * @param taskList  任务列表
     * @param areaBounds 区域边界
     * @return 任务结果
     */
    public TaskResult submitMissionPlanning(List<Map<String, Object>> uavList,
                                             List<Map<String, Object>> taskList,
                                             Map<String, Object> areaBounds)
            throws IOException, InterruptedException {
        Map<String, Object> request = Map.of(
                "uavList", uavList,
                "taskList", taskList,
                "areaBounds", areaBounds
        );
        SdkResponse<TaskResult> response = httpClient.postAndDeserialize(
                BASE_PATH + "/mission", request,
                new TypeReference<SdkResponse<TaskResult>>() {});
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
                BASE_PATH + "/tasks/" + taskId,
                new TypeReference<SdkResponse<TaskResult>>() {});
        return response.getData();
    }

    /**
     * 获取路径规划结果
     *
     * @param taskId 任务 ID
     * @return 路径结果
     */
    public PathResult getPathResult(Long taskId) throws IOException, InterruptedException {
        SdkResponse<PathResult> response = httpClient.getAndDeserialize(
                BASE_PATH + "/tasks/" + taskId + "/result",
                new TypeReference<SdkResponse<PathResult>>() {});
        return response.getData();
    }

    /**
     * 列出所有任务
     *
     * @return 任务列表
     */
    public List<TaskResult> listTasks() throws IOException, InterruptedException {
        SdkResponse<List<TaskResult>> response = httpClient.getAndDeserialize(
                BASE_PATH + "/tasks",
                new TypeReference<SdkResponse<List<TaskResult>>>() {});
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

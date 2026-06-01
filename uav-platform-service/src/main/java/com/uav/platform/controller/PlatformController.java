package com.uav.platform.controller;

import com.uav.common.annotation.StubController;
import com.uav.common.exception.ServiceUnavailableException;
import com.uav.common.feign.DataAssimilationClient;
import com.uav.common.feign.HealthCheckable;
import com.uav.common.feign.MeteorForecastClient;
import com.uav.common.feign.PathPlanningClient;
import com.uav.common.feign.WrfProcessorClient;
import com.uav.platform.dto.PlanRequest;
import jakarta.validation.Valid;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

/**
 * 平台主控制器
 * 
 * 整合气象处理、贝叶斯同化、气象预测和路径规划服务，
 * 提供统一的无人机路径规划API。
 * 
 * 已重构为使用Feign Client进行服务间调用，
 * 相比RestTemplate具有以下优势：
 * - 声明式API，更清晰
 * - 内置负载均衡
 * - 内置熔断支持
 * - 更易测试
 */
@RestController
@RequestMapping("/api/platform")
@Slf4j
public class PlatformController {

    private final WrfProcessorClient wrfProcessorClient;
    private final DataAssimilationClient dataAssimilationClient;
    private final MeteorForecastClient meteorForecastClient;
    private final PathPlanningClient pathPlanningClient;

    /**
     * 构造函数注入所有Feign Client
     * 
     * @param wrfProcessorClient WRF处理器客户端
     * @param dataAssimilationClient 数据同化客户端
     * @param meteorForecastClient 气象预测客户端
     * @param pathPlanningClient 路径规划客户端
     */
    public PlatformController(
            WrfProcessorClient wrfProcessorClient,
            DataAssimilationClient dataAssimilationClient,
            MeteorForecastClient meteorForecastClient,
            PathPlanningClient pathPlanningClient) {
        this.wrfProcessorClient = wrfProcessorClient;
        this.dataAssimilationClient = dataAssimilationClient;
        this.meteorForecastClient = meteorForecastClient;
        this.pathPlanningClient = pathPlanningClient;
    }

    /**
     * 综合路径规划接口
     * 
     * 整合气象数据获取、贝叶斯同化、气象预测和路径规划的全流程
     * 
     * @param request 包含drones、tasks、weatherData、obstacles、noFlyZones的请求
     * @return 路径规划结果
     */
    @PostMapping("/plan")
    public Map<String, Object> plan(@Valid @RequestBody PlanRequest request) {
        log.info("Received path planning request: drones={}, tasks={}", 
                getCollectionSize(request.getDrones()),
                getCollectionSize(request.getTasks()));

        try {
            Object weatherPayload = request.getWeatherData();
            if (weatherPayload == null) {
                return Map.of("code", 400, "message", "气象数据不能为空");
            }
            @SuppressWarnings("unchecked")
            Map<String, Object> weatherData = (Map<String, Object>) weatherPayload;
            Map<String, Object> weatherResponse = wrfProcessorClient.parseWrfData(weatherData);
            if (!isSuccess(weatherResponse)) {
                log.warn("Failed to get weather data: {}", weatherResponse.get("message"));
                return weatherResponse;
            }

            // 2. 执行贝叶斯同化
            Map<String, Object> assimilationResponse = dataAssimilationClient.executeAssimilation(
                    Map.of("background_field", weatherResponse.get("data"),
                           "method", "3dvar"));
            if (!isSuccess(assimilationResponse)) {
                log.warn("Failed to execute assimilation: {}", assimilationResponse.get("message"));
                return assimilationResponse;
            }

            // 3. 执行气象预测
            Map<String, Object> forecastResponse = meteorForecastClient.getDetailedForecast(
                    Map.of("analysis_field", assimilationResponse.get("data"),
                           "hours", 24));
            if (!isSuccess(forecastResponse)) {
                log.warn("Failed to get forecast: {}", forecastResponse.get("message"));
                return forecastResponse;
            }

            // 4. 执行路径规划
            Map<String, Object> planningRequest = Map.of(
                    "drones", request.getDrones(),
                    "tasks", request.getTasks(),
                    "weather_data", forecastResponse.get("data"),
                    "obstacles", request.getObstacles(),
                    "no_fly_zones", request.getNoFlyZones()
            );
            Map<String, Object> planningResponse = pathPlanningClient.planFull(planningRequest);
            if (!isSuccess(planningResponse)) {
                log.warn("Failed to plan path: {}", planningResponse.get("message"));
                return planningResponse;
            }

            log.info("Path planning completed successfully");
            return Map.of("code", 200, "message", "路径规划成功", "data", planningResponse.get("data"));

        } catch (Exception e) {
            log.error("Path planning failed", e);
            throw ServiceUnavailableException.serviceDown("path-planning", 
                    "路径规划服务暂时不可用: " + e.getMessage());
        }
    }

    /**
     * 获取气象数据
     * 
     * @param fileId WRF文件ID
     * @return 气象数据
     */
    @GetMapping("/weather")
    public Map<String, Object> getWeather(@RequestParam("fileId") String fileId) {
        log.debug("Getting weather data for fileId={}", fileId);
        
        try {
            Map<String, Object> response = wrfProcessorClient.getWeatherData(fileId);
            if (!isSuccess(response)) {
                return Map.of("code", 500, "message", "获取气象数据失败");
            }
            return response;
        } catch (Exception e) {
            log.error("Failed to get weather data", e);
            throw ServiceUnavailableException.serviceDown("wrf-processor", 
                    "气象数据服务暂时不可用");
        }
    }

    /**
     * 任务管理接口
     * 
     * @param request 任务请求
     * @return 操作结果
     */
    @StubController(reason = "任务管理功能待集成真实服务", plannedReplacement = "uav-task-service", plannedBy = "Q3-2026")
    @PostMapping("/task")
    public Map<String, Object> manageTask(@RequestBody Map<String, Object> request) {
        log.warn("[STUB] manageTask called - returning mock success");
        return Map.of("code", 200, "message", "任务管理成功");
    }

    /**
     * 获取无人机列表
     * 
     * @return 无人机列表
     */
    @StubController(reason = "无人机列表数据待对接持久化层", plannedReplacement = "uav-drone-service", plannedBy = "Q3-2026")
    @GetMapping("/drones")
    public Map<String, Object> getDrones() {
        log.warn("[STUB] getDrones called - returning empty list");
        return Map.of("code", 200, "data", Map.of("drones", List.of()));
    }

    /**
     * 健康检查接口
     * 
     * @return 所有依赖服务的健康状态
     */
    @GetMapping("/health")
    public Map<String, Object> healthCheck() {
        boolean wrfHealthy = checkServiceHealth(wrfProcessorClient);
        boolean assimilationHealthy = checkServiceHealth(dataAssimilationClient);
        boolean forecastHealthy = checkServiceHealth(meteorForecastClient);
        boolean planningHealthy = checkServiceHealth(pathPlanningClient);

        boolean allHealthy = wrfHealthy && assimilationHealthy && forecastHealthy && planningHealthy;

        return Map.of(
                "status", allHealthy ? "UP" : "DEGRADED",
                "services", Map.of(
                        "wrf-processor", wrfHealthy ? "UP" : "DOWN",
                        "data-assimilation", assimilationHealthy ? "UP" : "DOWN",
                        "meteor-forecast", forecastHealthy ? "UP" : "DOWN",
                        "path-planning", planningHealthy ? "UP" : "DOWN"
                )
        );
    }

    // ==================== 私有辅助方法 ====================

    private boolean isSuccess(Map<String, Object> response) {
        if (response == null) return false;
        Object code = response.get("code");
        return code instanceof Number && ((Number) code).intValue() == 200;
    }

    private int getCollectionSize(Object collection) {
        if (collection == null) return 0;
        if (collection instanceof java.util.Collection) {
            return ((java.util.Collection<?>) collection).size();
        }
        return 1;
    }

    private boolean checkServiceHealth(HealthCheckable client) {
        try {
            Map<String, Object> response = client.health();
            return response.get("status") != null;
        } catch (Exception e) {
            log.warn("Health check failed for {}: {}", client.getClass().getSimpleName(), e.getMessage());
            return false;
        }
    }
}

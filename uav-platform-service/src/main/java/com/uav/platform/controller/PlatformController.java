package com.uav.platform.controller;
import com.uav.common.exception.ServiceUnavailableException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.server.ResponseStatusException;
import jakarta.annotation.Resource;
import java.net.ConnectException;
import java.util.Map;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/platform")
public class PlatformController {

    private static final Logger log = LoggerFactory.getLogger(PlatformController.class);

    @Resource
    private org.springframework.web.client.RestTemplate restTemplate;

    @Value("${services.wrf-processor.url}")
    private String wrfProcessorUrl;

    @Value("${services.data-assimilation.url}")
    private String dataAssimilationUrl;

    @Value("${services.meteor-forecast.url}")
    private String meteorForecastUrl;

    @Value("${services.path-planning.url}")
    private String pathPlanningUrl;

    private Map<String, Object> callService(String url, Object request, String errorMsg) {
        try {
            Map<String, Object> response = restTemplate.postForObject(url, request, Map.class);
            if (response == null || !Boolean.TRUE.equals(response.get("success"))) {
                return Map.of("success", false, "error", errorMsg);
            }
            return response;
        } catch (ResourceAccessException e) {
            if (e.getCause() instanceof ConnectException) {
                throw new ServiceUnavailableException("wrf-processor", "无法连接到气象数据处理服务");
            }
            throw new ServiceUnavailableException("unknown", "服务连接失败: " + e.getMessage());
        } catch (RestClientException e) {
            throw new ServiceUnavailableException("unknown", "服务调用失败: " + e.getMessage());
        }
    }

    @PostMapping("/plan")
    public Map<String, Object> plan(@RequestBody Map<String, Object> request) {
        Object weatherPayload = request.get("weatherData");
        Map<String, Object> weatherResponse = callService(
            wrfProcessorUrl + "/parse", weatherPayload, "获取气象数据失败");
        if (!Boolean.TRUE.equals(weatherResponse.get("success"))) return weatherResponse;

        Map<String, Object> assimilationResponse = callService(
            dataAssimilationUrl + "/execute", weatherResponse.get("data"), "执行贝叶斯同化失败");
        if (!Boolean.TRUE.equals(assimilationResponse.get("success"))) return assimilationResponse;

        Map<String, Object> forecastResponse = callService(
            meteorForecastUrl + "/predict", assimilationResponse.get("data"), "执行气象预测失败");
        if (!Boolean.TRUE.equals(forecastResponse.get("success"))) return forecastResponse;

        Map<String, Object> planningRequest = Map.of(
            "drones", request.get("drones"),
            "tasks", request.get("tasks"),
            "weather_data", forecastResponse.get("data"),
            "obstacles", request.get("obstacles"),
            "no_fly_zones", request.get("noFlyZones")
        );

        Map<String, Object> planningResponse = callService(
            pathPlanningUrl + "/full", planningRequest, "执行路径规划失败");
        if (!Boolean.TRUE.equals(planningResponse.get("success"))) return planningResponse;

        return Map.of("success", true, "data", planningResponse.get("data"));
    }

    @GetMapping("/weather")
    public Map<String, Object> getWeather(@RequestParam("fileId") String fileId) {
        try {
            Map<String, Object> response = restTemplate.getForObject(
                wrfProcessorUrl + "/data?fileId={fileId}", Map.class, fileId);
            if (response == null || !Boolean.TRUE.equals(response.get("success"))) {
                return Map.of("success", false, "error", "获取气象数据失败");
            }
            return response;
        } catch (ResourceAccessException e) {
            if (e.getCause() instanceof ConnectException) {
                throw new ServiceUnavailableException("wrf-processor", "无法连接到气象数据服务");
            }
            throw new ServiceUnavailableException("wrf-processor", "服务连接失败");
        } catch (RestClientException e) {
            throw new ServiceUnavailableException("wrf-processor", "服务调用失败");
        }
    }

    @PostMapping("/task")
    public Map<String, Object> manageTask(@RequestBody Map<String, Object> request) {
        return Map.of("success", true, "message", "任务管理成功");
    }

    @GetMapping("/drones")
    public Map<String, Object> getDrones() {
        return Map.of("success", true, "data", Map.of("drones", Map.of()));
    }
}

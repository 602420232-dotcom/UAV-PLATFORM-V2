package com.uav.common.feign;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import java.util.Map;

/**
 * 气象预测服务Feign Client
 * 用于声明式调用meteor-forecast-service服务
 */
@FeignClient(name = "meteor-forecast-service", url = "${services.meteor-forecast.url:http://meteor-forecast:8082}",
        fallback = MeteorForecastClientFallback.class)
public interface MeteorForecastClient extends HealthCheckable {

    /**
     * 气象预测
     */
    @PostMapping("/api/forecast/predict")
    Map<String, Object> predict(@RequestBody Map<String, Object> request);

    /**
     * 气象数据订正
     */
    @PostMapping("/api/forecast/correct")
    Map<String, Object> correct(@RequestBody Map<String, Object> request);

    /**
     * 获取可用模型
     */
    @GetMapping("/api/forecast/models")
    Map<String, Object> getModels();

    /**
     * 获取气象预测
     */
    @GetMapping("/api/forecast/get")
    Map<String, Object> getForecast(@RequestParam("lat") Double lat, @RequestParam("lng") Double lng, @RequestParam("hours") Integer hours);

    /**
     * 获取详细气象预测
     */
    @PostMapping("/api/forecast/detail")
    Map<String, Object> getDetailedForecast(@RequestBody Map<String, Object> request);

    /**
     * 获取实时天气
     */
    @GetMapping("/api/forecast/realtime")
    Map<String, Object> getRealtimeWeather(@RequestParam("lat") Double lat, @RequestParam("lng") Double lng);

    /**
     * 健康检查
     */
    @GetMapping("/actuator/health")
    Map<String, Object> health();
}

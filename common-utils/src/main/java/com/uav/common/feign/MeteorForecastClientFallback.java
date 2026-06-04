package com.uav.common.feign;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;

/**
 * 气象预测服务降级实现
 * 当meteor-forecast-service不可用时执行降级逻辑
 */
@Slf4j
@Component
public class MeteorForecastClientFallback implements MeteorForecastClient {

    @Override
    public Map<String, Object> predict(Map<String, Object> request) {
        log.warn("MeteorForecastClientFallback: predict降级执行, request={}", request);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "气象预测服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> correct(Map<String, Object> request) {
        log.warn("MeteorForecastClientFallback: correct降级执行, request={}", request);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "气象数据订正服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> getModels() {
        log.warn("MeteorForecastClientFallback: getModels降级执行");
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "模型查询服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> getForecast(Double lat, Double lng, Integer hours) {
        log.warn("MeteorForecastClientFallback: getForecast降级执行, lat={}, lng={}, hours={}", lat, lng, hours);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "气象预报服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> getDetailedForecast(Map<String, Object> request) {
        log.warn("MeteorForecastClientFallback: getDetailedForecast降级执行, request={}", request);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "详细气象预报服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> getRealtimeWeather(Double lat, Double lng) {
        log.warn("MeteorForecastClientFallback: getRealtimeWeather降级执行, lat={}, lng={}", lat, lng);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "实时气象服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> health() {
        log.warn("MeteorForecastClientFallback: health降级执行");
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "DOWN");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }
}

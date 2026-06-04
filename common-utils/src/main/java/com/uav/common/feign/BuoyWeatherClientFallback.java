package com.uav.common.feign;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;

/**
 * 浮标气象服务降级实现
 * 当buoy-weather-service不可用时执行降级逻辑
 */
@Slf4j
@Component
public class BuoyWeatherClientFallback implements BuoyWeatherClient {

    @Override
    public Map<String, Object> getBuoyData(String buoyId) {
        log.warn("BuoyWeatherClientFallback: getBuoyData降级执行, buoyId={}", buoyId);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "浮标数据服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> listBuoys(Integer page, Integer size) {
        log.warn("BuoyWeatherClientFallback: listBuoys降级执行, page={}, size={}", page, size);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "浮标列表服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> getBuoyDetail(Long id) {
        log.warn("BuoyWeatherClientFallback: getBuoyDetail降级执行, id={}", id);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "浮标详情服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> getRealtimeData(String buoyId) {
        log.warn("BuoyWeatherClientFallback: getRealtimeData降级执行, buoyId={}", buoyId);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "浮标实时数据服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> uploadBuoyData(Map<String, Object> request) {
        log.warn("BuoyWeatherClientFallback: uploadBuoyData降级执行, request={}", request);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "浮标数据上传服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> health() {
        log.warn("BuoyWeatherClientFallback: health降级执行");
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "DOWN");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }
}

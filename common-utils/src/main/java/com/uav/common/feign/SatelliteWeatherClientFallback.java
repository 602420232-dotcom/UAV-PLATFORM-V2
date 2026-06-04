package com.uav.common.feign;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;

/**
 * 卫星气象服务降级实现
 * 当satellite-weather-service不可用时执行降级逻辑
 */
@Slf4j
@Component
public class SatelliteWeatherClientFallback implements SatelliteWeatherClient {

    @Override
    public Map<String, Object> getCloudImage(String region, String channel) {
        log.warn("SatelliteWeatherClientFallback: getCloudImage降级执行, region={}, channel={}", region, channel);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "卫星云图服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> listSatelliteImages(Integer page, Integer size) {
        log.warn("SatelliteWeatherClientFallback: listSatelliteImages降级执行, page={}, size={}", page, size);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "卫星云图列表服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> getSatelliteImageDetail(Long id) {
        log.warn("SatelliteWeatherClientFallback: getSatelliteImageDetail降级执行, id={}", id);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "卫星云图详情服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> uploadSatelliteData(Map<String, Object> request) {
        log.warn("SatelliteWeatherClientFallback: uploadSatelliteData降级执行, request={}", request);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "卫星数据上传服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> health() {
        log.warn("SatelliteWeatherClientFallback: health降级执行");
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "DOWN");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }
}

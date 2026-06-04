package com.uav.common.feign;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;

/**
 * 地面气象站服务降级实现
 * 当ground-station-weather-service不可用时执行降级逻辑
 */
@Slf4j
@Component
public class GroundStationWeatherClientFallback implements GroundStationWeatherClient {

    @Override
    public Map<String, Object> getStationData(String stationId) {
        log.warn("GroundStationWeatherClientFallback: getStationData降级执行, stationId={}", stationId);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "地面气象站数据服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> listStations(Integer page, Integer size) {
        log.warn("GroundStationWeatherClientFallback: listStations降级执行, page={}, size={}", page, size);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "地面气象站列表服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> getStationDetail(Long id) {
        log.warn("GroundStationWeatherClientFallback: getStationDetail降级执行, id={}", id);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "地面气象站详情服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> getRealtimeData(String stationId) {
        log.warn("GroundStationWeatherClientFallback: getRealtimeData降级执行, stationId={}", stationId);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "地面气象站实时数据服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> uploadStationData(Map<String, Object> request) {
        log.warn("GroundStationWeatherClientFallback: uploadStationData降级执行, request={}", request);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "地面气象站数据上传服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> health() {
        log.warn("GroundStationWeatherClientFallback: health降级执行");
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "DOWN");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }
}

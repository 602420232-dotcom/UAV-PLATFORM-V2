package com.uav.common.feign;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;

/**
 * 数据同化服务降级实现
 * 当data-assimilation-service不可用时执行降级逻辑
 */
@Slf4j
@Component
public class DataAssimilationClientFallback implements DataAssimilationClient {

    @Override
    public Map<String, Object> executeAssimilation(Map<String, Object> request) {
        log.warn("DataAssimilationClientFallback: executeAssimilation降级执行, request={}", request);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "数据同化服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> executeBatchAssimilation(Map<String, Object> request) {
        log.warn("DataAssimilationClientFallback: executeBatchAssimilation降级执行, request={}", request);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "批量同化服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> getAssimilationStatus(String id) {
        log.warn("DataAssimilationClientFallback: getAssimilationStatus降级执行, id={}", id);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "同化状态查询服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> getAssimilationHistory(Integer page, Integer size) {
        log.warn("DataAssimilationClientFallback: getAssimilationHistory降级执行, page={}, size={}", page, size);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "同化历史查询服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> health() {
        log.warn("DataAssimilationClientFallback: health降级执行");
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "DOWN");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }
}

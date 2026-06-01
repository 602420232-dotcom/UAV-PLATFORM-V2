package com.uav.common.feign;

import com.uav.common.dto.WrfParseRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

import java.util.HashMap;
import java.util.Map;

/**
 * WRF处理器服务降级实现
 * 当wrf-processor-service不可用时执行降级逻辑
 */
@Slf4j
@Component
public class WrfProcessorClientFallback implements WrfProcessorClient {

    @Override
    public Map<String, Object> uploadWrfData(Map<String, Object> request) {
        log.warn("WrfProcessorClientFallback: uploadWrfData降级执行, request={}", request);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "WRF数据上传服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> listWrfData(Integer page, Integer size) {
        log.warn("WrfProcessorClientFallback: listWrfData降级执行, page={}, size={}", page, size);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "WRF数据列表服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> getWrfDataDetail(Long id) {
        log.warn("WrfProcessorClientFallback: getWrfDataDetail降级执行, id={}", id);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "WRF数据详情服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> getWeatherData(String fileId) {
        log.warn("WrfProcessorClientFallback: getWeatherData降级执行, fileId={}", fileId);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "WRF天气数据服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> getStatistics(String fileId) {
        log.warn("WrfProcessorClientFallback: getStatistics降级执行, fileId={}", fileId);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "WRF统计信息服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> parseWrfData(WrfParseRequest request) {
        log.warn("WrfProcessorClientFallback: parseWrfData降级执行, request={}", request);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "WRF数据解析服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> parseWrfData(Map<String, Object> data) {
        log.warn("WrfProcessorClientFallback: parseWrfData降级执行, data={}", data);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "WRF数据解析服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> parseWrfFile(MultipartFile file, int height) {
        log.warn("WrfProcessorClientFallback: parseWrfFile降级执行, file={}, height={}", 
            (file != null ? file.getOriginalFilename() : "null"), height);
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "degraded");
        fallbackResponse.put("message", "WRF数据解析服务暂不可用，请稍后重试");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }

    @Override
    public Map<String, Object> health() {
        log.warn("WrfProcessorClientFallback: health降级执行");
        Map<String, Object> fallbackResponse = new HashMap<>();
        fallbackResponse.put("status", "DOWN");
        fallbackResponse.put("fallback", true);
        return fallbackResponse;
    }
}

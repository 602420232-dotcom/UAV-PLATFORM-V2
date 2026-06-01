package com.uav.common.feign;

import com.uav.common.dto.WrfParseRequest;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.multipart.MultipartFile;
import java.util.Map;

/**
 * WRF处理器服务Feign Client
 * 用于声明式调用wrf-processor-service服务
 */
@FeignClient(name = "wrf-processor-service", url = "${services.wrf-processor.url:http://wrf-processor:8081}",
        fallback = WrfProcessorClientFallback.class)
public interface WrfProcessorClient extends HealthCheckable {

    /**
     * 解析WRF数据 - 文件上传版本
     */
    @PostMapping(value = "/api/wrf/parse", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    Map<String, Object> parseWrfFile(@RequestPart("file") MultipartFile file,
                                     @RequestParam(value = "height", defaultValue = "100") int height);

    /**
     * 解析WRF数据 - 参数化版本（JSON Body）
     * 用于 PlatformController.plan() 的调用场景
     * 接受JSON格式的气象数据，而不是NetCDF文件上传
     */
    @PostMapping(value = "/api/wrf/parse-params", consumes = MediaType.APPLICATION_JSON_VALUE)
    Map<String, Object> parseWrfData(@RequestBody WrfParseRequest request);

    /**
     * 解析WRF数据 - 兼容旧版调用方式（Map参数）
     * 内部转换为WrfParseRequest格式
     */
    default Map<String, Object> parseWrfData(Map<String, Object> data) {
        WrfParseRequest request = new WrfParseRequest();
        request.setData(data);
        
        if (data.containsKey("height")) {
            Object heightValue = data.get("height");
            if (heightValue instanceof Number) {
                request.setHeight(((Number) heightValue).intValue());
            }
        }
        
        if (data.containsKey("bounds")) {
            @SuppressWarnings("unchecked")
            Map<String, Double> bounds = (Map<String, Double>) data.get("bounds");
            request.setBounds(bounds);
        }
        
        if (data.containsKey("filePath")) {
            request.setFilePath(String.valueOf(data.get("filePath")));
        }
        
        return parseWrfData(request);
    }

    /**
     * 获取天气数据
     */
    @GetMapping("/api/wrf/data")
    Map<String, Object> getWeatherData(@RequestParam("fileId") String fileId);

    /**
     * 获取统计信息
     */
    @GetMapping("/api/wrf/stats")
    Map<String, Object> getStatistics(@RequestParam("fileId") String fileId);

    /**
     * 上传WRF数据
     */
    @PostMapping("/api/wrf/upload")
    Map<String, Object> uploadWrfData(@RequestBody Map<String, Object> request);

    /**
     * 列出WRF数据
     */
    @GetMapping("/api/wrf/list")
    Map<String, Object> listWrfData(@RequestParam("page") Integer page, @RequestParam("size") Integer size);

    /**
     * 获取WRF数据详情
     */
    @GetMapping("/api/wrf/detail")
    Map<String, Object> getWrfDataDetail(@RequestParam("id") Long id);

    /**
     * 健康检查
     */
    @GetMapping("/actuator/health")
    Map<String, Object> health();
}

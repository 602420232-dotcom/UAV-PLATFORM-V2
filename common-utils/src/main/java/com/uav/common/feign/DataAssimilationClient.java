package com.uav.common.feign;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import java.util.Map;

/**
 * 数据同化服务Feign Client
 * 用于声明式调用data-assimilation-service服务
 */
@FeignClient(name = "data-assimilation-service", url = "${services.data-assimilation.url:http://data-assimilation:8084}",
        fallback = DataAssimilationClientFallback.class)
public interface DataAssimilationClient extends HealthCheckable {

    /**
     * 执行数据同化
     */
    @PostMapping("/api/assimilation/execute")
    Map<String, Object> executeAssimilation(@RequestBody Map<String, Object> request);

    /**
     * 执行批量同化
     */
    @PostMapping("/api/assimilation/batch")
    Map<String, Object> executeBatchAssimilation(@RequestBody Map<String, Object> request);

    /**
     * 获取同化状态
     */
    @GetMapping("/api/assimilation/status/{id}")
    Map<String, Object> getAssimilationStatus(@PathVariable("id") String id);

    /**
     * 获取同化历史
     */
    @GetMapping("/api/assimilation/history")
    Map<String, Object> getAssimilationHistory(@RequestParam(value = "page", defaultValue = "1") Integer page,
                                               @RequestParam(value = "size", defaultValue = "10") Integer size);

    /**
     * 健康检查
     */
    @GetMapping("/actuator/health")
    Map<String, Object> health();
}

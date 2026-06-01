package com.uav.common.feign;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import java.util.Map;

/**
 * 路径规划服务Feign Client
 * 用于声明式调用path-planning-service服务
 */
@FeignClient(name = "path-planning-service", url = "${services.path-planning.url:http://path-planning:8083}",
        fallback = PathPlanningClientFallback.class)
public interface PathPlanningClient extends HealthCheckable {

    /**
     * VRP路径规划
     */
    @PostMapping("/api/planning/vrptw")
    Map<String, Object> planVRPTW(@RequestBody Map<String, Object> request);

    /**
     * A*路径规划
     */
    @PostMapping("/api/planning/astar")
    Map<String, Object> planAStar(@RequestBody Map<String, Object> request);

    /**
     * DWA动态避障
     */
    @PostMapping("/api/planning/dwa")
    Map<String, Object> planDWA(@RequestBody Map<String, Object> request);

    /**
     * 综合路径规划
     */
    @PostMapping("/api/planning/full")
    Map<String, Object> planFull(@RequestBody Map<String, Object> request);

    /**
     * 健康检查
     */
    @GetMapping("/actuator/health")
    Map<String, Object> health();
}

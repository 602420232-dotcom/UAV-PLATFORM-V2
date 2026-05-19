package com.uav.controller;

import com.uav.common.feign.PythonScriptInvoker;
import com.uav.model.PathPlan;
import lombok.extern.slf4j.Slf4j;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RestController
@RequestMapping("/path-planning")
public class PathPlanningController {

    private final PythonScriptInvoker pythonScriptInvoker;

    public PathPlanningController(PythonScriptInvoker pythonScriptInvoker) {
        this.pythonScriptInvoker = pythonScriptInvoker;
    }
    
    @PostMapping("/plan")
    public Map<String, Object> planPath(@RequestBody Map<String, Object> request) {
        try {
            log.info("收到路径规划请求: {}", request);
            
            Map<String, Object> params = Map.of(
                "tasks", request.getOrDefault("tasks", ""),
                "drones", request.getOrDefault("drones", ""),
                "weather_data", request.getOrDefault("weatherData", "")
            );
            
            Map<String, Object> result = pythonScriptInvoker.executeAsMap(
                "path-planning/three_layer_planner.py", "plan", params);
            
            log.info("路径规划完成，结果: {}", result);
            
            return Map.of(
                "success", true,
                "code", 200,
                "data", result
            );
            
        } catch (Exception e) {
            log.error("路径规划失败", e);
            return Map.of(
                "success", false,
                "code", 500,
                "message", "路径规划处理失败"
            );
        }
    }
    
    @GetMapping("/history")
    public Map<String, Object> getPlanningHistory() {
        return Map.of(
            "success", true,
            "code", 200,
            "data", List.of()
        );
    }
    
    @PostMapping("/save")
    public Map<String, Object> savePathPlan(@RequestBody PathPlan plan) {
        return Map.of(
            "success", true,
            "code", 200,
            "message", "规划方案保存成功"
        );
    }
    
    @GetMapping("/detail/{id}")
    public Map<String, Object> getPathPlanDetail(@PathVariable Long id) {
        return Map.of(
            "success", true,
            "code", 200,
            "data", Map.<String, Object>of()
        );
    }
}

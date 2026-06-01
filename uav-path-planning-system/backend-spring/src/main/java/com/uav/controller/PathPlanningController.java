package com.uav.controller;

import com.uav.common.script.PythonScriptInvoker;
import com.uav.model.PathPlan;
import com.uav.service.DynamicReplannerService;
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
    private final DynamicReplannerService dynamicReplannerService;

    public PathPlanningController(PythonScriptInvoker pythonScriptInvoker, DynamicReplannerService dynamicReplannerService) {
        this.pythonScriptInvoker = pythonScriptInvoker;
        this.dynamicReplannerService = dynamicReplannerService;
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
    
    /**
     * 动态重规划端点
     * @param request 包含当前路径和新气象数据的请求
     * @return 重规划结果
     */
    @PostMapping("/replan")
    public Map<String, Object> dynamicReplan(@RequestBody Map<String, Object> request) {
        try {
            log.info("收到动态重规划请求: {}", request);
            
            Map<String, Object> currentRoute = (Map<String, Object>) request.get("current_route");
            Map<String, Object> newWeatherData = (Map<String, Object>) request.getOrDefault("new_weather_data", Map.of());
            
            // 检查是否需要重规划
            boolean needsReplan = dynamicReplannerService.shouldReplan(newWeatherData);
            
            if (!needsReplan && !request.getOrDefault("force", false).equals(true)) {
                log.info("气象变化未达到重规划阈值，跳过重规划");
                return Map.of(
                    "success", true,
                    "code", 200,
                    "message", "气象变化未达到重规划阈值，使用原路径",
                    "skipped", true
                );
            }
            
            // 执行重规划
            Map<String, Object> result = dynamicReplannerService.executeReplan(currentRoute, newWeatherData);
            
            boolean success = Boolean.TRUE.equals(result.getOrDefault("success", false));
            return Map.of(
                "success", success,
                "code", success ? 200 : 500,
                "data", result
            );
            
        } catch (Exception e) {
            log.error("动态重规划失败", e);
            return Map.of(
                "success", false,
                "code", 500,
                "message", "动态重规划处理失败: " + e.getMessage()
            );
        }
    }
    
    /**
     * 检查是否需要重规划
     * @param request 包含气象数据的请求
     * @return 是否需要重规划的判断结果
     */
    @PostMapping("/check-replan")
    public Map<String, Object> checkShouldReplan(@RequestBody Map<String, Object> request) {
        try {
            Map<String, Object> weatherData = (Map<String, Object>) request.getOrDefault("weather_data", Map.of());
            boolean shouldReplan = dynamicReplannerService.shouldReplan(weatherData);
            
            return Map.of(
                "success", true,
                "code", 200,
                "data", Map.of(
                    "should_replan", shouldReplan
                )
            );
            
        } catch (Exception e) {
            log.error("检查重规划状态失败", e);
            return Map.of(
                "success", false,
                "code", 500,
                "message", "检查重规划状态失败: " + e.getMessage()
            );
        }
    }
}

package com.uav.controller;
import com.uav.model.Task;
import com.uav.model.Drone;
import com.uav.model.PathPlan;
import com.uav.utils.PythonAlgorithmUtil;
import lombok.extern.slf4j.Slf4j;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@RequestMapping("/path-planning")
public class PathPlanningController {

    private final PythonAlgorithmUtil pythonAlgorithmUtil;

    public PathPlanningController(PythonAlgorithmUtil pythonAlgorithmUtil) {
        this.pythonAlgorithmUtil = pythonAlgorithmUtil;
    }
    
    /**
     * 执行路径规划
     * @param request 规划请求
     * @return 规划结果
     */
    @PostMapping("/plan")
    public Map<String, Object> planPath(@RequestBody Map<String, Object> request) {
        try {
            log.info("收到路径规划请求: {}", request);
            
            // 提取参数
            String tasks = request.getOrDefault("tasks", "").toString();
            String drones = request.getOrDefault("drones", "").toString();
            String weatherData = request.getOrDefault("weatherData", "").toString();
            
            // 调用Python算法
            String result = pythonAlgorithmUtil.planPath(tasks, drones, weatherData);
            
            log.info("路径规划完成，结果: {}", result);
            
            // 解析结果
            // 这里可以添加JSON解析逻辑
            
            return Map.of(
                "success", true,
                "data", result
            );
            
        } catch (Exception e) {
            log.error("路径规划失败", e);
            return Map.of(
                "success", false,
                "error", "路径规划处理失败"
            );
        }
    }
    
    /**
     * 获取规划历史
     * @return 规划历史列表
     */
    @GetMapping("/history")
    public Map<String, Object> getPlanningHistory() {
        // 这里可以从数据库查询历史记录
        return Map.of(
            "success", true,
            "data", List.of()
        );
    }
    
    /**
     * 保存规划方案
     * @param plan 规划方案
     * @return 保存结果
     */
    @PostMapping("/save")
    public Map<String, Object> savePathPlan(@RequestBody PathPlan plan) {
        // 这里可以保存到数据库
        return Map.of(
            "success", true,
            "message", "规划方案保存成功"
        );
    }
    
    /**
     * 获取规划方案详情
     * @param id 方案ID
     * @return 方案详情
     */
    @GetMapping("/detail/{id}")
    public Map<String, Object> getPathPlanDetail(@PathVariable Long id) {
        // 这里可以从数据库查询详情
        return Map.of(
            "success", true,
            "data", Map.of()
        );
    }
}
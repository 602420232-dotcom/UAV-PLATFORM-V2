package com.uav.service;

import com.uav.common.script.PythonScriptInvoker;
import com.uav.config.UavProperties;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * 动态重规划服务
 * 监控气象变化并在需要时触发路径重规划
 */
@Slf4j
@Service
public class DynamicReplannerService {

    private final UavProperties uavProperties;
    private final PythonScriptInvoker pythonScriptInvoker;
    
    // 上一次的气象数据，用于检测变化
    private Map<String, Object> lastWeatherData;

    public DynamicReplannerService(UavProperties uavProperties, PythonScriptInvoker pythonScriptInvoker) {
        this.uavProperties = uavProperties;
        this.pythonScriptInvoker = pythonScriptInvoker;
    }

    /**
     * 检查是否需要重规划
     * @param currentWeatherData 当前气象数据
     * @return 是否需要重规划
     */
    public boolean shouldReplan(Map<String, Object> currentWeatherData) {
        if (lastWeatherData == null) {
            return false;
        }
        
        // 计算气象变化程度
        double changeScore = calculateWeatherChangeScore(lastWeatherData, currentWeatherData);
        double threshold = uavProperties.getPathPlanning().getReplanningThreshold();
        
        log.info("气象变化评分: {}, 重规划阈值: {}", changeScore, threshold);
        
        return changeScore > threshold;
    }

    /**
     * 执行动态重规划
     * @param currentRoute 当前路径
     * @param newWeatherData 新的气象数据
     * @return 重规划结果
     */
    public Map<String, Object> executeReplan(Map<String, Object> currentRoute, Map<String, Object> newWeatherData) {
        try {
            log.info("开始执行动态重规划，时间: {}", LocalDateTime.now());

            Map<String, Object> params = Map.of(
                "current_route", currentRoute,
                "new_weather_data", newWeatherData
            );
            
            Map<String, Object> result = pythonScriptInvoker.executeAsMap(
                "path-planning/three_layer_planner.py", "replan", params);
            
            // 更新气象数据缓存
            this.lastWeatherData = newWeatherData;

            log.info("动态重规划完成，结果: {}", result);
            
            return result;
            
        } catch (Exception e) {
            log.error("动态重规划失败", e);
            return Map.of(
                "success", false,
                "error", e.getMessage()
            );
        }
    }

    /**
     * 计算气象变化评分
     * @param oldData 旧气象数据
     * @param newData 新气象数据
     * @return 变化评分
     */
    private double calculateWeatherChangeScore(Map<String, Object> oldData, Map<String, Object> newData) {
        double score = 0.0;
        
        try {
            // 风速变化
            Object oldWind = oldData.get("wind_speed");
            Object newWind = newData.get("wind_speed");
            
            if (oldWind != null && newWind != null) {
                double oldWindVal = ((Number) oldWind).doubleValue();
                double newWindVal = ((Number) newWind).doubleValue();
                score += Math.abs(newWindVal - oldWindVal) * 0.5;
            }
            
            // 温度变化
            Object oldTemp = oldData.get("temperature");
            Object newTemp = newData.get("temperature");
            
            if (oldTemp != null && newTemp != null) {
                double oldTempVal = ((Number) oldTemp).doubleValue();
                double newTempVal = ((Number) newTemp).doubleValue();
                score += Math.abs(newTempVal - oldTempVal) * 0.3;
            }
            
            // 湿度变化
            Object oldHumidity = oldData.get("humidity");
            Object newHumidity = newData.get("humidity");
            
            if (oldHumidity != null && newHumidity != null) {
                double oldHumidityVal = ((Number) oldHumidity).doubleValue();
                double newHumidityVal = ((Number) newHumidity).doubleValue();
                score += Math.abs(newHumidityVal - oldHumidityVal) * 0.2;
            }
            
        } catch (Exception e) {
            log.warn("计算气象变化评分失败", e);
        }
        
        return score;
    }
}

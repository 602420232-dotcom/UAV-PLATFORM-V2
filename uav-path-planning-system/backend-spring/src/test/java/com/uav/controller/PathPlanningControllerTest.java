package com.uav.controller;

import com.uav.common.script.PythonScriptInvoker;
import com.uav.model.PathPlan;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
@DisplayName("PathPlanningController 路径规划测试")
class PathPlanningControllerTest {

    @Mock
    private PythonScriptInvoker pythonScriptInvoker;

    @InjectMocks
    private PathPlanningController pathPlanningController;

    @Test
    @DisplayName("执行路径规划")
    void testPlanPath() {
        Map<String, Object> request = Map.of(
            "tasks", "[{\"id\":1,\"lat\":39.9,\"lon\":116.4}]",
            "drones", "[{\"id\":\"UAV-001\",\"speed\":15}]",
            "weatherData", "{\"wind\":5}"
        );
        when(pythonScriptInvoker.executeAsMap(anyString(), anyString(), anyMap()))
                .thenReturn(Map.of("paths", new Object[]{}));
        Map<String, Object> result = pathPlanningController.planPath(request);
        assertNotNull(result);
        assertTrue((Boolean) result.get("success"));
    }

    @Test
    @DisplayName("路径规划失败返回错误")
    void testPlanPathWithError() {
        Map<String, Object> request = Map.of("tasks", "", "drones", "", "weatherData", "");
        when(pythonScriptInvoker.executeAsMap(anyString(), anyString(), anyMap()))
                .thenThrow(new RuntimeException("Python脚本异常"));
        Map<String, Object> result = pathPlanningController.planPath(request);
        assertNotNull(result);
        assertFalse((Boolean) result.get("success"));
        assertEquals("路径规划处理失败", result.get("message"));
    }

    @Test
    @DisplayName("获取规划历史")
    void testGetPlanningHistory() {
        Map<String, Object> result = pathPlanningController.getPlanningHistory();
        assertTrue((Boolean) result.get("success"));
        assertNotNull(result.get("data"));
    }

    @Test
    @DisplayName("保存规划方案")
    void testSavePathPlan() {
        PathPlan plan = new PathPlan();
        Map<String, Object> result = pathPlanningController.savePathPlan(plan);
        assertTrue((Boolean) result.get("success"));
    }

    @Test
    @DisplayName("获取规划方案详情")
    void testGetPathPlanDetail() {
        Map<String, Object> result = pathPlanningController.getPathPlanDetail(1L);
        assertTrue((Boolean) result.get("success"));
    }
}
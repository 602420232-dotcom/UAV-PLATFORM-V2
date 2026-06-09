package com.uav.path.planning.controller;

import com.uav.common.dto.PathPlanningRequest;
import com.uav.common.script.PythonScriptInvoker;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
@DisplayName("PlanningController 路径规划控制器测试")
class PlanningControllerTest {

    @Mock
    private PythonScriptInvoker pythonScriptInvoker;

    private PlanningController planningController;

    @BeforeEach
    void setUp() {
        planningController = new PlanningController(pythonScriptInvoker);
        ReflectionTestUtils.setField(planningController, "pythonScriptPath", "path_planner.py");
    }

    @Test
    @DisplayName("测试VRPTW路径规划 - 成功")
    void testVrptw() {
        PathPlanningRequest request = createValidRequest();
        when(pythonScriptInvoker.executeAsMap(any(), eq("vrptw"), any()))
                .thenReturn(Map.of("success", true, "paths", "[]"));
        Map<String, Object> result = planningController.vrptw(request);
        assertNotNull(result);
        assertEquals(Boolean.TRUE, result.get("success"));
    }

    @Test
    @DisplayName("测试A*路径规划 - 成功")
    void testAstar() {
        PathPlanningRequest request = createValidRequest();
        when(pythonScriptInvoker.executeAsMap(any(), eq("astar"), any()))
                .thenReturn(Map.of("success", true, "path", "[]"));
        Map<String, Object> result = planningController.astar(request);
        assertNotNull(result);
        assertEquals(Boolean.TRUE, result.get("success"));
    }

    @Test
    @DisplayName("测试DWA局部规划 - 成功")
    void testDwa() {
        PathPlanningRequest request = createValidRequest();
        when(pythonScriptInvoker.executeAsMap(any(), eq("dwa"), any()))
                .thenReturn(Map.of("success", true, "trajectory", "[]"));
        Map<String, Object> result = planningController.dwa(request);
        assertNotNull(result);
        assertEquals(Boolean.TRUE, result.get("success"));
    }

    @Test
    @DisplayName("测试三层完整规划 - 成功")
    void testFullPlanning() {
        PathPlanningRequest request = createValidRequest();
        when(pythonScriptInvoker.executeAsMap(any(), eq("full"), any()))
                .thenReturn(Map.of("success", true, "global_path", "[]", "local_path", "[]"));
        Map<String, Object> result = planningController.full(request);
        assertNotNull(result);
        assertEquals(Boolean.TRUE, result.get("success"));
    }

    @Test
    @DisplayName("测试参数转换 - 算法参数正确传递")
    void testToParamsPreservesAlgorithm() {
        PathPlanningRequest request = createValidRequest();
        request.setAlgorithm("hybrid-ga");
        when(pythonScriptInvoker.executeAsMap(any(), eq("vrptw"), argThat(params ->
                "hybrid-ga".equals(params.get("algorithm"))
        ))).thenReturn(Map.of("success", true));
        planningController.vrptw(request);
    }

    @Test
    @DisplayName("测试VRPTW失败 - Python脚本异常")
    void testVrptwWithPythonError() {
        PathPlanningRequest request = createValidRequest();
        when(pythonScriptInvoker.executeAsMap(any(), any(), any()))
                .thenThrow(new RuntimeException("Python脚本执行超时"));
        assertThrows(RuntimeException.class, () -> planningController.vrptw(request));
    }

    @Test
    @DisplayName("测试VRPTW失败 - 返回错误")
    void testVrptwReturnsError() {
        PathPlanningRequest request = createValidRequest();
        when(pythonScriptInvoker.executeAsMap(any(), any(), any()))
                .thenReturn(Map.of("success", false, "error", "无效的路径约束"));
        Map<String, Object> result = planningController.vrptw(request);
        assertNotNull(result);
        assertEquals(Boolean.FALSE, result.get("success"));
        assertNotNull(result.get("error"));
    }

    @Test
    @DisplayName("测试A*参数传递 - 传递正确的无人机和任务数据")
    void testAstarParams() {
        PathPlanningRequest request = createValidRequest();
        request.setAlgorithm("astar");
        Map<String, Object> drones = new HashMap<>();
        drones.put("count", 5);
        drones.put("max_speed", 15.0);
        request.setDrones(drones);
        Map<String, Object> tasks = new HashMap<>();
        tasks.put("locations", "[[39.9,116.4],[40.0,116.5]]");
        request.setTasks(tasks);

        when(pythonScriptInvoker.executeAsMap(any(), eq("astar"), argThat(params ->
                "astar".equals(params.get("algorithm")) &&
                params.containsKey("drones") &&
                params.containsKey("tasks")
        ))).thenReturn(Map.of("success", true, "path", "[]"));
        Map<String, Object> result = planningController.astar(request);
        assertNotNull(result);
        assertEquals(Boolean.TRUE, result.get("success"));
    }

    private PathPlanningRequest createValidRequest() {
        PathPlanningRequest request = new PathPlanningRequest();
        request.setAlgorithm("vrptw");
        Map<String, Object> drones = new HashMap<>();
        drones.put("count", 3);
        drones.put("start_point", "39.9,116.4,100");
        drones.put("end_point", "40.0,116.5,100");
        request.setDrones(drones);
        request.setTasks(new HashMap<>());
        request.setWeatherData(new HashMap<>());
        request.setConstraints(new HashMap<>());
        return request;
    }
}

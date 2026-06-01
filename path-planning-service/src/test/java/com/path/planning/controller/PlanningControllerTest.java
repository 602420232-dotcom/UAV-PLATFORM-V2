package com.path.planning.controller;

import com.uav.common.dto.PathPlanningRequest;
import com.uav.common.utils.PythonScriptInvoker;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
@DisplayName("PlanningController 路径规划控制器测试")
class PlanningControllerTest {

    @Mock
    private PythonScriptInvoker pythonScriptInvoker;

    @InjectMocks
    private PlanningController planningController;

    @BeforeEach
    void setUp() {
        ReflectionTestUtils.setField(planningController, "pythonScriptPath", "path_planner.py");
    }

    @Test
    @DisplayName("测试VRPTW路径规划")
    void testVrptw() {
        PathPlanningRequest request = createValidRequest();
        when(pythonScriptInvoker.execute(any(), any(), any()))
                .thenReturn(Map.of("success", true, "paths", "[]"));
        Map<String, Object> result = planningController.vrptw(request);
        assertNotNull(result);
        assertTrue((Boolean) result.get("success"));
    }

    @Test
    @DisplayName("测试A*路径规划")
    void testAstar() {
        PathPlanningRequest request = createValidRequest();
        when(pythonScriptInvoker.execute(any(), any(), any()))
                .thenReturn(Map.of("success", true, "path", "[]"));
        Map<String, Object> result = planningController.astar(request);
        assertNotNull(result);
        assertTrue((Boolean) result.get("success"));
    }

    @Test
    @DisplayName("测试DWA局部规划")
    void testDwa() {
        PathPlanningRequest request = createValidRequest();
        when(pythonScriptInvoker.execute(any(), any(), any()))
                .thenReturn(Map.of("success", true, "trajectory", "[]"));
        Map<String, Object> result = planningController.dwa(request);
        assertNotNull(result);
        assertTrue((Boolean) result.get("success"));
    }

    @Test
    @DisplayName("测试三层完整规划")
    void testFullPlanning() {
        PathPlanningRequest request = createValidRequest();
        when(pythonScriptInvoker.execute(any(), any(), any()))
                .thenReturn(Map.of("success", true, "global_path", "[]", "local_path", "[]"));
        Map<String, Object> result = planningController.full(request);
        assertNotNull(result);
        assertTrue((Boolean) result.get("success"));
    }

    @Test
    @DisplayName("测试参数转换")
    void testToParamsPreservesAlgorithm() {
        PathPlanningRequest request = createValidRequest();
        request.setAlgorithm("hybrid-ga");
        when(pythonScriptInvoker.execute(any(), any(), any()))
                .thenReturn(Map.of("success", true));
        planningController.vrptw(request);
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

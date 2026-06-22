package com.uav.planning.controller;

import com.uav.planning.PlanningApplication;
import com.uav.planning.dto.PlanMissionRequest;
import com.uav.planning.dto.PlanPathRequest;
import com.uav.planning.entity.MissionPlan;
import com.uav.planning.entity.PathResult;
import com.uav.planning.entity.PlanningTask;
import com.uav.planning.service.PlanningService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.http.MediaType;

import java.util.List;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Planning 控制器单元测试
 */
@DisplayName("Planning 控制器测试")
@SpringBootTest(classes = PlanningApplication.class)
@AutoConfigureMockMvc(addFilters = false)
@TestPropertySource(locations = "classpath:application-test.yml")
class PlanningControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private PlanningService planningService;

    @Test
    @DisplayName("POST /api/v1/planning/path 应提交路径规划任务")
    @WithMockUser(roles = {"ADMIN"})
    void planPathShouldReturnPlanningTask() throws Exception {
        PlanningTask task = new PlanningTask();
        task.setId(1L);
        task.setTaskId("task-001");
        task.setAlgorithmType("RRTSTAR");
        task.setStatus("QUEUED");
        task.setProgress(0);

        when(planningService.submitPathPlanning(any(PlanPathRequest.class))).thenReturn(task);

        mockMvc.perform(post("/api/v1/planning/path")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"start\":{\"lon\":116.0,\"lat\":39.0,\"alt\":100.0},\"end\":{\"lon\":117.0,\"lat\":40.0,\"alt\":100.0},\"optimizationTarget\":\"BALANCED\"}")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.algorithmType").value("RRTSTAR"))
                .andExpect(jsonPath("$.data.status").value("QUEUED"));
    }

    @Test
    @DisplayName("POST /api/v1/planning/mission 应提交任务规划")
    @WithMockUser(roles = {"ADMIN"})
    void planMissionShouldReturnPlanningTask() throws Exception {
        PlanningTask task = new PlanningTask();
        task.setId(2L);
        task.setAlgorithmType("VRPTW");
        task.setStatus("QUEUED");

        when(planningService.submitMissionPlanning(any(PlanMissionRequest.class))).thenReturn(task);

        mockMvc.perform(post("/api/v1/planning/mission")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"uavList\":[{\"id\":\"uav-1\"}],\"taskList\":[{\"target\":\"point-a\"}]}")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.algorithmType").value("VRPTW"));
    }

    @Test
    @DisplayName("GET /api/v1/planning/tasks/{id} 应返回任务状态")
    @WithMockUser(roles = {"ADMIN"})
    void getTaskShouldReturnTaskStatus() throws Exception {
        PlanningTask task = new PlanningTask();
        task.setId(1L);
        task.setStatus("SUCCESS");
        task.setProgress(100);

        when(planningService.getTaskStatus(anyLong())).thenReturn(task);

        mockMvc.perform(get("/api/v1/planning/tasks/1")
                        .contentType(MediaType.APPLICATION_JSON)
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.status").value("SUCCESS"))
                .andExpect(jsonPath("$.data.progress").value(100));
    }

    @Test
    @DisplayName("GET /api/v1/planning/tasks/{id}/result 应返回路径规划结果")
    @WithMockUser(roles = {"ADMIN"})
    void getPathResultShouldReturnPathData() throws Exception {
        PathResult result = new PathResult();
        result.setId(1L);
        result.setTaskId("task-001");
        result.setWaypointsJson("[{\"lon\":116.0,\"lat\":39.0}]");
        result.setTotalDistance(1500.5);

        when(planningService.getPathResult(anyLong())).thenReturn(result);

        mockMvc.perform(get("/api/v1/planning/tasks/1/result")
                        .contentType(MediaType.APPLICATION_JSON)
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.totalDistance").value(1500.5));
    }

    @Test
    @DisplayName("GET /api/v1/planning/tasks/{id}/mission 应返回任务规划结果")
    @WithMockUser(roles = {"ADMIN"})
    void getMissionPlanShouldReturnMissionData() throws Exception {
        MissionPlan plan = new MissionPlan();
        plan.setId(1L);
        plan.setTaskId("task-001");
        plan.setUavsJson("[{\"id\":\"uav-1\"}]");
        plan.setTasksJson("[{\"target\":\"point-a\"}]");
        plan.setScheduleJson("[{\"taskIndex\":0,\"uavIndex\":0}]");
        plan.setOverallScore(85.0);

        when(planningService.getMissionPlan(anyLong())).thenReturn(plan);

        mockMvc.perform(get("/api/v1/planning/tasks/1/mission")
                        .contentType(MediaType.APPLICATION_JSON)
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.overallScore").value(85.0));
    }

    @Test
    @DisplayName("GET /api/v1/planning/tasks 应返回所有规划任务列表")
    @WithMockUser(roles = {"ADMIN"})
    void listTasksShouldReturnAllTasks() throws Exception {
        PlanningTask task1 = new PlanningTask();
        task1.setId(1L);
        task1.setAlgorithmType("RRTSTAR");

        PlanningTask task2 = new PlanningTask();
        task2.setId(2L);
        task2.setAlgorithmType("DWA");

        when(planningService.listTasks()).thenReturn(List.of(task1, task2));

        mockMvc.perform(get("/api/v1/planning/tasks")
                        .contentType(MediaType.APPLICATION_JSON)
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.length()").value(2));
    }

    @Test
    @DisplayName("POST /api/v1/planning/tasks/{id}/cancel 应取消任务")
    @WithMockUser(roles = {"ADMIN"})
    void cancelTaskShouldReturnSuccess() throws Exception {
        when(planningService.cancelTask(anyLong())).thenReturn(true);

        mockMvc.perform(post("/api/v1/planning/tasks/1/cancel")
                        .contentType(MediaType.APPLICATION_JSON)
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }

    @Test
    @DisplayName("POST /api/v1/planning/tasks/{id}/cancel 取消失败应返回错误码 3000")
    @WithMockUser(roles = {"ADMIN"})
    void cancelTaskFailureShouldReturnError() throws Exception {
        when(planningService.cancelTask(anyLong())).thenReturn(false);

        mockMvc.perform(post("/api/v1/planning/tasks/999/cancel")
                        .contentType(MediaType.APPLICATION_JSON)
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(3000));
    }
}

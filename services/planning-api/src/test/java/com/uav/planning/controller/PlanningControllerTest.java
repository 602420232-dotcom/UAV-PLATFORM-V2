package com.uav.planning.controller;

import com.uav.common.core.result.Result;
import com.uav.planning.dto.PlanMissionRequest;
import com.uav.planning.dto.PlanPathRequest;
import com.uav.planning.entity.MissionPlan;
import com.uav.planning.entity.PathResult;
import com.uav.planning.entity.PlanningTask;
import com.uav.planning.service.PlanningService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;

/**
 * Planning 控制器单元测试
 */
@DisplayName("Planning 控制器测试")
@ExtendWith(MockitoExtension.class)
class PlanningControllerTest {

    @Mock
    private PlanningService planningService;

    @InjectMocks
    private PlanningController planningController;

    @Test
    @DisplayName("POST /api/v1/planning/path 应提交路径规划任务")
    void planPathShouldReturnPlanningTask() {
        PlanningTask task = new PlanningTask();
        task.setId(1L);
        task.setTaskId("task-001");
        task.setAlgorithmType("RRTSTAR");
        task.setStatus("QUEUED");
        task.setProgress(0);

        when(planningService.submitPathPlanning(any(PlanPathRequest.class))).thenReturn(task);

        PlanPathRequest request = new PlanPathRequest();
        Result<PlanningTask> result = planningController.planPath(request);

        assertEquals(200, result.getCode());
        assertNotNull(result.getData());
        assertEquals("RRTSTAR", result.getData().getAlgorithmType());
        assertEquals("QUEUED", result.getData().getStatus());
    }

    @Test
    @DisplayName("POST /api/v1/planning/mission 应提交任务规划")
    void planMissionShouldReturnPlanningTask() {
        PlanningTask task = new PlanningTask();
        task.setId(2L);
        task.setAlgorithmType("VRPTW");
        task.setStatus("QUEUED");

        when(planningService.submitMissionPlanning(any(PlanMissionRequest.class))).thenReturn(task);

        PlanMissionRequest request = new PlanMissionRequest();
        Result<PlanningTask> result = planningController.planMission(request);

        assertEquals(200, result.getCode());
        assertNotNull(result.getData());
        assertEquals("VRPTW", result.getData().getAlgorithmType());
    }

    @Test
    @DisplayName("GET /api/v1/planning/tasks/{id} 应返回任务状态")
    void getTaskShouldReturnTaskStatus() {
        PlanningTask task = new PlanningTask();
        task.setId(1L);
        task.setStatus("SUCCESS");
        task.setProgress(100);

        when(planningService.getTaskStatus(anyLong())).thenReturn(task);

        Result<PlanningTask> result = planningController.getTask(1L);

        assertEquals(200, result.getCode());
        assertNotNull(result.getData());
        assertEquals("SUCCESS", result.getData().getStatus());
        assertEquals(100, result.getData().getProgress());
    }

    @Test
    @DisplayName("GET /api/v1/planning/tasks/{id}/result 应返回路径规划结果")
    void getPathResultShouldReturnPathData() {
        PathResult pathResult = new PathResult();
        pathResult.setId(1L);
        pathResult.setTaskId("task-001");
        pathResult.setWaypointsJson("[{\"lon\":116.0,\"lat\":39.0}]");
        pathResult.setTotalDistance(1500.5);

        when(planningService.getPathResult(anyLong())).thenReturn(pathResult);

        Result<PathResult> result = planningController.getPathResult(1L);

        assertEquals(200, result.getCode());
        assertNotNull(result.getData());
        assertEquals(1500.5, result.getData().getTotalDistance());
    }

    @Test
    @DisplayName("GET /api/v1/planning/tasks/{id}/mission 应返回任务规划结果")
    void getMissionPlanShouldReturnMissionData() {
        MissionPlan plan = new MissionPlan();
        plan.setId(1L);
        plan.setTaskId("task-001");
        plan.setUavsJson("[{\"id\":\"uav-1\"}]");
        plan.setTasksJson("[{\"target\":\"point-a\"}]");
        plan.setScheduleJson("[{\"taskIndex\":0,\"uavIndex\":0}]");
        plan.setOverallScore(85.0);

        when(planningService.getMissionPlan(anyLong())).thenReturn(plan);

        Result<MissionPlan> result = planningController.getMissionPlan(1L);

        assertEquals(200, result.getCode());
        assertNotNull(result.getData());
        assertEquals(85.0, result.getData().getOverallScore());
    }

    @Test
    @DisplayName("GET /api/v1/planning/tasks 应返回所有规划任务列表")
    void listTasksShouldReturnAllTasks() {
        PlanningTask task1 = new PlanningTask();
        task1.setId(1L);
        task1.setAlgorithmType("RRTSTAR");

        PlanningTask task2 = new PlanningTask();
        task2.setId(2L);
        task2.setAlgorithmType("DWA");

        when(planningService.listTasks()).thenReturn(List.of(task1, task2));

        Result<List<PlanningTask>> result = planningController.listTasks();

        assertEquals(200, result.getCode());
        assertNotNull(result.getData());
        assertEquals(2, result.getData().size());
    }

    @Test
    @DisplayName("POST /api/v1/planning/tasks/{id}/cancel 应取消任务")
    void cancelTaskShouldReturnSuccess() {
        when(planningService.cancelTask(anyLong())).thenReturn(true);

        Result<Void> result = planningController.cancelTask(1L);

        assertEquals(200, result.getCode());
    }

    @Test
    @DisplayName("POST /api/v1/planning/tasks/{id}/cancel 取消失败应返回错误码 3000")
    void cancelTaskFailureShouldReturnError() {
        when(planningService.cancelTask(anyLong())).thenReturn(false);

        Result<Void> result = planningController.cancelTask(999L);

        assertEquals(3000, result.getCode());
    }
}

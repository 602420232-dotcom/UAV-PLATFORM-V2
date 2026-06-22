package com.uav.planning.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.common.core.constant.TaskStatus;
import com.uav.common.core.statemachine.TaskStateMachine;
import com.uav.common.kafka.producer.AlgorithmTaskProducer;
import com.uav.common.kafka.service.TaskStatusSyncService;
import com.uav.planning.dto.PlanMissionRequest;
import com.uav.planning.dto.PlanPathRequest;
import com.uav.planning.entity.PlanningTask;
import com.uav.planning.mapper.MissionPlanMapper;
import com.uav.planning.mapper.PathResultMapper;
import com.uav.planning.mapper.PlanningTaskMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Spy;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * PlanningService 单元测试
 * 测试路径规划任务创建、路径结果保存、任务状态管理
 */
@ExtendWith(MockitoExtension.class)
class PlanningServiceTest {

    @Mock
    private PlanningTaskMapper taskMapper;

    @Mock
    private PathResultMapper pathResultMapper;

    @Mock
    private MissionPlanMapper missionPlanMapper;

    @Mock
    private AlgorithmTaskProducer algorithmTaskProducer;

    @Mock
    private TaskStatusSyncService taskStatusSyncService;

    @Mock
    private TaskStateMachine taskStateMachine;

    @Spy
    private ObjectMapper objectMapper = new ObjectMapper().registerModule(new com.fasterxml.jackson.datatype.jsr310.JavaTimeModule());

    @InjectMocks
    private PlanningService planningService;

    private PlanPathRequest pathRequest;
    private PlanMissionRequest missionRequest;

    @BeforeEach
    void setUp() {
        // 启用 mock 模式
        ReflectionTestUtils.setField(planningService, "mockEnabled", true);

        pathRequest = new PlanPathRequest();
        pathRequest.setStart(Map.of("lon", 116.3, "lat", 39.9, "alt", 100.0));
        pathRequest.setEnd(Map.of("lon", 116.5, "lat", 40.0, "alt", 100.0));
        pathRequest.setOptimizationTarget("BALANCED");

        missionRequest = new PlanMissionRequest();
        missionRequest.setUavList(List.of(
                Map.of("id", "uav-001", "model", "DJI-M300", "maxSpeed", 15.0)
        ));
        missionRequest.setTaskList(List.of(
                Map.of("id", "task-001", "location", Map.of("lon", 116.4, "lat", 39.95), "priority", 1)
        ));
    }

    @Test
    void testSubmitPathPlanning_MockMode_ReturnsQueuedTask() {
        PlanningTask result = planningService.submitPathPlanning(pathRequest);

        assertNotNull(result);
        assertNotNull(result.getId());
        assertEquals(TaskStatus.QUEUED.getName(), result.getStatus());
        assertEquals("RRTSTAR", result.getAlgorithmType());
        assertEquals(0, result.getProgress());
        assertNotNull(result.getCreatedAt());
        assertNotNull(result.getParamsJson());
    }

    @Test
    void testSubmitPathPlanning_DetectsAlgorithmByTarget() {
        pathRequest.setOptimizationTarget("RISK");
        PlanningTask result = planningService.submitPathPlanning(pathRequest);
        assertEquals("DERRTSTAR", result.getAlgorithmType());

        pathRequest.setOptimizationTarget("ENERGY");
        PlanningTask result2 = planningService.submitPathPlanning(pathRequest);
        assertEquals("MPC", result2.getAlgorithmType());

        pathRequest.setOptimizationTarget("TIME");
        PlanningTask result3 = planningService.submitPathPlanning(pathRequest);
        assertEquals("A_STAR", result3.getAlgorithmType());
    }

    @Test
    void testSubmitPathPlanning_WithWaypoints_DetectsVRPTW() {
        pathRequest.setWaypoints(List.of(
                Map.of("lon", 116.35, "lat", 39.92, "alt", 100.0)
        ));
        PlanningTask result = planningService.submitPathPlanning(pathRequest);

        assertEquals("VRPTW", result.getAlgorithmType());
    }

    @Test
    void testSubmitMissionPlanning_MockMode_ReturnsQueuedTask() {
        PlanningTask result = planningService.submitMissionPlanning(missionRequest);

        assertNotNull(result);
        assertNotNull(result.getId());
        assertEquals(TaskStatus.QUEUED.getName(), result.getStatus());
        assertEquals("VRPTW", result.getAlgorithmType());
        assertEquals(0, result.getProgress());
        assertNotNull(result.getCreatedAt());
    }

    @Test
    void testListTasks_MockMode_ReturnsAllTasks() {
        // 先提交一个任务
        planningService.submitPathPlanning(pathRequest);
        planningService.submitMissionPlanning(missionRequest);

        List<PlanningTask> tasks = planningService.listTasks();

        assertNotNull(tasks);
        assertFalse(tasks.isEmpty());
        assertEquals(2, tasks.size());
    }

    @Test
    void testCancelTask_MockMode_Success() {
        PlanningTask task = planningService.submitPathPlanning(pathRequest);

        // 模拟状态机允许取消
        when(taskStateMachine.canTransition(any(TaskStatus.class), eq(TaskStatus.CANCELLED)))
                .thenReturn(true);

        boolean cancelled = planningService.cancelTask(task.getId());

        assertTrue(cancelled);
        assertEquals(TaskStatus.CANCELLED.getName(), task.getStatus());
    }

    @Test
    void testGetTaskStatus_MockMode_ReturnsTask() {
        PlanningTask submitted = planningService.submitPathPlanning(pathRequest);

        PlanningTask result = planningService.getTaskStatus(submitted.getId());

        assertNotNull(result);
        assertEquals(submitted.getId(), result.getId());
        assertEquals(submitted.getAlgorithmType(), result.getAlgorithmType());
    }

    @Test
    void testGetTaskStatus_MockMode_NotFound() {
        PlanningTask result = planningService.getTaskStatus(9999L);
        assertNull(result);
    }

    @Test
    void testSubmitPathPlanning_DbMode_UsesKafka() {
        // 切换到数据库模式
        ReflectionTestUtils.setField(planningService, "mockEnabled", false);
        when(taskMapper.insert(any(PlanningTask.class))).thenReturn(1);

        PlanningTask result = planningService.submitPathPlanning(pathRequest);

        assertNotNull(result);
        assertNotNull(result.getTaskId());
        assertEquals(TaskStatus.QUEUED.getName(), result.getStatus());

        verify(taskMapper).insert(any(PlanningTask.class));
        verify(taskStatusSyncService).initTaskStatus(anyString(), anyString(), anyString());
        verify(algorithmTaskProducer).sendTask(any());
    }
}

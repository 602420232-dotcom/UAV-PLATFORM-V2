package com.uav.observation.controller;

import com.uav.common.core.result.Result;
import com.uav.observation.dto.CreateObservationRequest;
import com.uav.observation.entity.ObservationTask;
import com.uav.observation.service.ObservationService;
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
 * Observation 控制器单元测试
 */
@DisplayName("Observation 控制器测试")
@ExtendWith(MockitoExtension.class)
class ObservationControllerTest {

    @Mock
    private ObservationService observationService;

    @InjectMocks
    private ObservationController observationController;

    @Test
    @DisplayName("POST /api/v1/observation/tasks 应创建观测任务")
    void createTaskShouldReturnObservationTask() {
        ObservationTask task = new ObservationTask();
        task.setId(1L);
        task.setType("ADAPTIVE");
        task.setStatus("PENDING");
        task.setDataQuality(0.0);

        when(observationService.createTask(any(CreateObservationRequest.class))).thenReturn(task);

        CreateObservationRequest request = new CreateObservationRequest();
        Result<ObservationTask> result = observationController.createTask(request);

        assertEquals(200, result.getCode());
        assertNotNull(result.getData());
        assertEquals("ADAPTIVE", result.getData().getType());
        assertEquals("PENDING", result.getData().getStatus());
    }

    @Test
    @DisplayName("GET /api/v1/observation/tasks/{id} 应返回观测任务详情")
    void getTaskShouldReturnTaskDetails() {
        ObservationTask task = new ObservationTask();
        task.setId(1L);
        task.setType("PLANNED");
        task.setStatus("RUNNING");

        when(observationService.getTask(anyLong())).thenReturn(task);

        Result<ObservationTask> result = observationController.getTask(1L);

        assertEquals(200, result.getCode());
        assertNotNull(result.getData());
        assertEquals(1L, result.getData().getId());
        assertEquals("PLANNED", result.getData().getType());
    }

    @Test
    @DisplayName("GET /api/v1/observation/tasks/{id} 任务不存在应返回错误码 3000")
    void getNonExistentTaskShouldReturnError() {
        when(observationService.getTask(anyLong())).thenReturn(null);

        Result<ObservationTask> result = observationController.getTask(999L);

        assertEquals(3000, result.getCode());
    }

    @Test
    @DisplayName("GET /api/v1/observation/tasks 应返回所有观测任务列表")
    void listTasksShouldReturnAllTasks() {
        ObservationTask task1 = new ObservationTask();
        task1.setId(1L);
        task1.setType("ADAPTIVE");

        ObservationTask task2 = new ObservationTask();
        task2.setId(2L);
        task2.setType("EMERGENCY");

        when(observationService.listTasks()).thenReturn(List.of(task1, task2));

        Result<List<ObservationTask>> result = observationController.listTasks();

        assertEquals(200, result.getCode());
        assertNotNull(result.getData());
        assertEquals(2, result.getData().size());
        assertEquals("EMERGENCY", result.getData().get(1).getType());
    }

    @Test
    @DisplayName("POST /api/v1/observation/tasks/{id}/status 应更新任务状态")
    void updateTaskStatusShouldReturnUpdatedTask() {
        ObservationTask task = new ObservationTask();
        task.setId(1L);
        task.setStatus("COMPLETED");

        when(observationService.updateTaskStatus(anyLong(), anyString())).thenReturn(task);

        Result<ObservationTask> result = observationController.updateTaskStatus(1L, "COMPLETED");

        assertEquals(200, result.getCode());
        assertNotNull(result.getData());
        assertEquals("COMPLETED", result.getData().getStatus());
    }
}

package com.uav.assimilation.controller;

import com.uav.assimilation.dto.SubmitTaskRequest;
import com.uav.assimilation.dto.TaskQueryRequest;
import com.uav.assimilation.entity.AssimilationResult;
import com.uav.assimilation.entity.AssimilationTask;
import com.uav.assimilation.service.AssimilationService;
import com.uav.common.core.result.Result;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
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
 * Assimilation 控制器单元测试
 */
@DisplayName("Assimilation 控制器测试")
@ExtendWith(MockitoExtension.class)
class AssimilationControllerTest {

    @Mock
    private AssimilationService assimilationService;

    @InjectMocks
    private AssimilationController assimilationController;

    @Test
    @DisplayName("POST /api/v1/assimilation/tasks 应提交同化任务并返回任务ID")
    void submitTaskShouldReturnTaskId() {
        when(assimilationService.submitTask(any(SubmitTaskRequest.class)))
                .thenReturn(Result.success(1001L));

        SubmitTaskRequest request = new SubmitTaskRequest();
        Result<Long> result = assimilationController.submitTask(request);

        assertEquals(200, result.getCode());
        assertEquals(1001L, result.getData());
    }

    @Test
    @DisplayName("GET /api/v1/assimilation/tasks/{id} 应返回任务状态")
    void getTaskStatusShouldReturnTaskInfo() {
        AssimilationTask task = new AssimilationTask();
        task.setId(1L);
        task.setAlgorithmType("ENKF");
        task.setStatus("RUNNING");
        task.setProgress(50);

        when(assimilationService.getTaskStatus(anyLong())).thenReturn(Result.success(task));

        Result<AssimilationTask> result = assimilationController.getTaskStatus(1L);

        assertEquals(200, result.getCode());
        assertNotNull(result.getData());
        assertEquals("ENKF", result.getData().getAlgorithmType());
        assertEquals("RUNNING", result.getData().getStatus());
        assertEquals(50, result.getData().getProgress());
    }

    @Test
    @DisplayName("GET /api/v1/assimilation/tasks/{id}/result 应返回任务结果")
    void getTaskResultShouldReturnResultData() {
        AssimilationResult resultEntity = new AssimilationResult();
        resultEntity.setId(1L);
        resultEntity.setTaskId(1L);
        resultEntity.setAnalysisFieldJson("{\"field\":\"simulated\"}");

        when(assimilationService.getTaskResult(anyLong())).thenReturn(Result.success(resultEntity));

        Result<AssimilationResult> result = assimilationController.getTaskResult(1L);

        assertEquals(200, result.getCode());
        assertNotNull(result.getData());
        assertEquals("{\"field\":\"simulated\"}", result.getData().getAnalysisFieldJson());
    }

    @Test
    @DisplayName("POST /api/v1/assimilation/tasks/{id}/cancel 应取消任务")
    void cancelTaskShouldReturnSuccess() {
        when(assimilationService.cancelTask(anyLong())).thenReturn(Result.success());

        Result<Void> result = assimilationController.cancelTask(1L);

        assertEquals(200, result.getCode());
    }

    @Test
    @DisplayName("GET /api/v1/assimilation/tasks 应返回任务列表")
    void listTasksShouldReturnTaskList() {
        Page<AssimilationTask> page = new Page<>(1, 10, 0);
        page.setRecords(List.of());

        when(assimilationService.listTasks(any(TaskQueryRequest.class))).thenReturn(Result.success(page));

        Result<?> result = assimilationController.listTasks(new TaskQueryRequest());

        assertEquals(200, result.getCode());
    }
}

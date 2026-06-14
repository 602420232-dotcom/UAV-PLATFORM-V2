package com.uav.assimilation.controller;

import com.uav.assimilation.dto.SubmitTaskRequest;
import com.uav.assimilation.entity.AssimilationResult;
import com.uav.assimilation.entity.AssimilationTask;
import com.uav.assimilation.service.AssimilationService;
import com.uav.common.core.result.Result;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Assimilation 控制器单元测试
 */
@DisplayName("Assimilation 控制器测试")
@SpringBootTest(classes = AssimilationController.class)
@AutoConfigureMockMvc(addFilters = false)
@TestPropertySource(locations = "classpath:application-test.yml")
class AssimilationControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private AssimilationService assimilationService;

    @Test
    @DisplayName("POST /api/v1/assimilation/tasks 应提交同化任务并返回任务ID")
    void submitTaskShouldReturnTaskId() throws Exception {
        when(assimilationService.submitTask(any(SubmitTaskRequest.class)))
                .thenReturn(Result.success(1001L));

        mockMvc.perform(post("/api/v1/assimilation/tasks")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"algorithmType\":\"3DVAR\",\"paramsJson\":\"{\\\"key\\\":\\\"value\\\"}\"}")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data").value(1001));
    }

    @Test
    @DisplayName("GET /api/v1/assimilation/tasks/{id} 应返回任务状态")
    void getTaskStatusShouldReturnTaskInfo() throws Exception {
        AssimilationTask task = new AssimilationTask();
        task.setId(1L);
        task.setAlgorithmType("ENKF");
        task.setStatus("RUNNING");
        task.setProgress(50);

        when(assimilationService.getTaskStatus(anyLong())).thenReturn(Result.success(task));

        mockMvc.perform(get("/api/v1/assimilation/tasks/1")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.algorithmType").value("ENKF"))
                .andExpect(jsonPath("$.data.status").value("RUNNING"))
                .andExpect(jsonPath("$.data.progress").value(50));
    }

    @Test
    @DisplayName("GET /api/v1/assimilation/tasks/{id}/result 应返回任务结果")
    void getTaskResultShouldReturnResultData() throws Exception {
        AssimilationResult result = new AssimilationResult();
        result.setId(1L);
        result.setTaskId(1L);
        result.setAnalysisFieldJson("{\"field\":\"simulated\"}");

        when(assimilationService.getTaskResult(anyLong())).thenReturn(Result.success(result));

        mockMvc.perform(get("/api/v1/assimilation/tasks/1/result")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.analysisFieldJson").value("{\"field\":\"simulated\"}"));
    }

    @Test
    @DisplayName("POST /api/v1/assimilation/tasks/{id}/cancel 应取消任务")
    void cancelTaskShouldReturnSuccess() throws Exception {
        when(assimilationService.cancelTask(anyLong())).thenReturn(Result.success());

        mockMvc.perform(post("/api/v1/assimilation/tasks/1/cancel")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }

    @Test
    @DisplayName("GET /api/v1/assimilation/tasks 应返回任务列表")
    void listTasksShouldReturnTaskList() throws Exception {
        when(assimilationService.listTasks(any())).thenReturn(Result.success(new com.baomidou.mybatisplus.extension.plugins.pagination.Page<>()));

        mockMvc.perform(get("/api/v1/assimilation/tasks")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }
}

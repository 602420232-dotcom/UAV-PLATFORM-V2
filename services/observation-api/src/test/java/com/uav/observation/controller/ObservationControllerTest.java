package com.uav.observation.controller;

import com.uav.observation.ObservationApplication;
import com.uav.observation.dto.CreateObservationRequest;
import com.uav.observation.entity.ObservationTask;
import com.uav.observation.service.ObservationService;
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
 * Observation 控制器单元测试
 */
@DisplayName("Observation 控制器测试")
@SpringBootTest(classes = ObservationApplication.class)
@AutoConfigureMockMvc(addFilters = false)
@TestPropertySource(locations = "classpath:application-test.yml")
class ObservationControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private ObservationService observationService;

    @Test
    @DisplayName("POST /api/v1/observation/tasks 应创建观测任务")
    @WithMockUser(roles = {"ADMIN"})
    void createTaskShouldReturnObservationTask() throws Exception {
        ObservationTask task = new ObservationTask();
        task.setId(1L);
        task.setType("ADAPTIVE");
        task.setStatus("PENDING");
        task.setDataQuality(0.0);

        when(observationService.createTask(any(CreateObservationRequest.class))).thenReturn(task);

        mockMvc.perform(post("/api/v1/observation/tasks")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"type\":\"ADAPTIVE\",\"targetArea\":\"{\\\"type\\\":\\\"Polygon\\\"}\",\"sensorType\":\"LIDAR\",\"priority\":5}")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.type").value("ADAPTIVE"))
                .andExpect(jsonPath("$.data.status").value("PENDING"));
    }

    @Test
    @DisplayName("GET /api/v1/observation/tasks/{id} 应返回观测任务详情")
    @WithMockUser(roles = {"ADMIN"})
    void getTaskShouldReturnTaskDetails() throws Exception {
        ObservationTask task = new ObservationTask();
        task.setId(1L);
        task.setType("PLANNED");
        task.setStatus("RUNNING");

        when(observationService.getTask(anyLong())).thenReturn(task);

        mockMvc.perform(get("/api/v1/observation/tasks/1")
                        .contentType(MediaType.APPLICATION_JSON)
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.id").value(1))
                .andExpect(jsonPath("$.data.type").value("PLANNED"));
    }

    @Test
    @DisplayName("GET /api/v1/observation/tasks/{id} 任务不存在应返回错误码 3000")
    @WithMockUser(roles = {"ADMIN"})
    void getNonExistentTaskShouldReturnError() throws Exception {
        when(observationService.getTask(anyLong())).thenReturn(null);

        mockMvc.perform(get("/api/v1/observation/tasks/999")
                        .contentType(MediaType.APPLICATION_JSON)
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(3000));
    }

    @Test
    @DisplayName("GET /api/v1/observation/tasks 应返回所有观测任务列表")
    @WithMockUser(roles = {"ADMIN"})
    void listTasksShouldReturnAllTasks() throws Exception {
        ObservationTask task1 = new ObservationTask();
        task1.setId(1L);
        task1.setType("ADAPTIVE");

        ObservationTask task2 = new ObservationTask();
        task2.setId(2L);
        task2.setType("EMERGENCY");

        when(observationService.listTasks()).thenReturn(List.of(task1, task2));

        mockMvc.perform(get("/api/v1/observation/tasks")
                        .contentType(MediaType.APPLICATION_JSON)
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.length()").value(2))
                .andExpect(jsonPath("$.data[1].type").value("EMERGENCY"));
    }

    @Test
    @DisplayName("POST /api/v1/observation/tasks/{id}/status 应更新任务状态")
    @WithMockUser(roles = {"ADMIN"})
    void updateTaskStatusShouldReturnUpdatedTask() throws Exception {
        ObservationTask task = new ObservationTask();
        task.setId(1L);
        task.setStatus("COMPLETED");

        when(observationService.updateTaskStatus(anyLong(), anyString())).thenReturn(task);

        mockMvc.perform(post("/api/v1/observation/tasks/1/status")
                        .param("status", "COMPLETED")
                        .contentType(MediaType.APPLICATION_JSON)
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.status").value("COMPLETED"));
    }
}

package com.uav.bayesian;

import com.uav.bayesian.dto.request.AssimilationRequest;
import com.uav.bayesian.dto.request.BatchRequest;
import com.uav.bayesian.dto.response.StatusResponse;
import com.uav.bayesian.entity.Job;
import com.uav.bayesian.exception.AssimilationException;
import com.uav.bayesian.exception.DegradedModeException;
import com.uav.bayesian.service.AlertService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.HashMap;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("数据同化平台模型与DTO测试")
class DataAssimilationModelTests {

    @Test
    @DisplayName("AssimilationRequest DTO测试")
    void testAssimilationRequest() {
        AssimilationRequest request = new AssimilationRequest();
        request.setAlgorithm("3dvar");
        request.setBackground(new HashMap<>());
        request.setObservations(new ArrayList<>());
        request.setConfig(new HashMap<>());

        assertEquals("3dvar", request.getAlgorithm());
        assertNotNull(request.getBackground());
        assertNotNull(request.getObservations());
        assertNotNull(request.getConfig());
    }

    @Test
    @DisplayName("BatchRequest DTO测试")
    void testBatchRequest() {
        BatchRequest request = new BatchRequest();
        request.setOption("parallel");
        request.setJobs(new ArrayList<>());
        assertEquals("parallel", request.getOption());
        assertNotNull(request.getJobs());
    }

    @Test
    @DisplayName("StatusResponse DTO测试")
    void testStatusResponse() {
        StatusResponse response = new StatusResponse("running", "1.0.0");
        response.setGpuAvailable(true);
        response.setActiveJobs(3);

        assertEquals("running", response.getStatus());
        assertEquals("1.0.0", response.getVersion());
        assertTrue(response.isGpuAvailable());
        assertEquals(3, response.getActiveJobs());

        StatusResponse emptyResponse = new StatusResponse();
        assertNull(emptyResponse.getStatus());
    }

    @Test
    @DisplayName("Job实体测试")
    void testJobEntity() {
        Job job = new Job();
        job.setJobId("JOB-001");
        job.setAlgorithm("3dvar");
        job.setStatus("running");
        job.setInputData("{\"test\": \"data\"}");
        job.setResultData("{\"result\": \"success\"}");

        assertEquals("JOB-001", job.getJobId());
        assertEquals("3dvar", job.getAlgorithm());
        assertEquals("running", job.getStatus());
        assertNotNull(job.getInputData());
        assertNotNull(job.getResultData());
    }

    @Test
    @DisplayName("AssimilationException测试")
    void testAssimilationException() {
        AssimilationException ex = new AssimilationException("同化计算失败");
        assertEquals("同化计算失败", ex.getMessage());

        Throwable cause = new RuntimeException("根源异常");
        AssimilationException exWithCause = new AssimilationException("计算异常", cause);
        assertEquals("计算异常", exWithCause.getMessage());
        assertSame(cause, exWithCause.getCause());
    }

    @Test
    @DisplayName("DegradedModeException测试")
    void testDegradedModeException() {
        DegradedModeException ex = new DegradedModeException("wrf-processor", "降级模式已启用");
        assertEquals("降级模式已启用", ex.getMessage());
        assertEquals("wrf-processor", ex.getServiceName());

        DegradedModeException exWithCause = new DegradedModeException(
                "data-service", "服务降级");
        assertEquals("服务降级", exWithCause.getMessage());
        assertEquals("data-service", exWithCause.getServiceName());
    }

    @Test
    @DisplayName("AlertService测试")
    void testAlertService() {
        AlertService alertService = new AlertService();
        assertDoesNotThrow(() -> alertService.sendAlert("CRITICAL", "系统异常"));
        assertDoesNotThrow(() -> alertService.notifyDegradedMode("wrf-processor"));
        assertDoesNotThrow(() -> alertService.notifyRecovery("wrf-processor"));
    }
}

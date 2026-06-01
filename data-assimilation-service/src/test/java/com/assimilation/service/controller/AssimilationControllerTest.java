package com.assimilation.service.controller;

import com.uav.common.dto.AssimilationRequest;
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
@DisplayName("AssimilationController 同化控制器测试")
class AssimilationControllerTest {

    @Mock
    private PythonScriptInvoker pythonScriptInvoker;

    @InjectMocks
    private AssimilationController assimilationController;

    @BeforeEach
    void setUp() {
        ReflectionTestUtils.setField(assimilationController, "pythonScriptPath", "assimilation_handler.py");
    }

    private AssimilationRequest createValidRequest() {
        AssimilationRequest request = new AssimilationRequest();
        request.setAlgorithm("3dvar");
        request.setBackground(new HashMap<>());
        request.setObservations(new HashMap<>());
        request.setConfig(new HashMap<>());
        return request;
    }

    @Test
    @DisplayName("测试单次同化执行")
    void testExecute() {
        AssimilationRequest request = createValidRequest();
        when(pythonScriptInvoker.execute(any(), any(), any()))
                .thenReturn(Map.of("success", true, "analysis", "{}"));
        Map<String, Object> result = assimilationController.execute(request);
        assertNotNull(result);
        assertTrue((Boolean) result.get("success"));
    }

    @Test
    @DisplayName("测试方差计算")
    void testGetVariance() {
        AssimilationRequest request = createValidRequest();
        when(pythonScriptInvoker.execute(any(), any(), any()))
                .thenReturn(Map.of("success", true, "variance", "{}"));
        Map<String, Object> result = assimilationController.getVariance(request);
        assertNotNull(result);
        assertTrue((Boolean) result.get("success"));
    }

    @Test
    @DisplayName("测试批量同化处理")
    void testBatchProcess() {
        AssimilationRequest request = createValidRequest();
        when(pythonScriptInvoker.execute(any(), any(), any()))
                .thenReturn(Map.of("success", true, "results", "[]"));
        Map<String, Object> result = assimilationController.batchProcess(request);
        assertNotNull(result);
        assertTrue((Boolean) result.get("success"));
    }

    @Test
    @DisplayName("测试4DVAR算法")
    void testExecuteWith4DVar() {
        AssimilationRequest request = createValidRequest();
        request.setAlgorithm("4dvar");
        when(pythonScriptInvoker.execute(any(), any(), any()))
                .thenReturn(Map.of("success", true, "analysis", "{}"));
        Map<String, Object> result = assimilationController.execute(request);
        assertNotNull(result);
    }

    @Test
    @DisplayName("测试EnKF算法")
    void testExecuteWithEnKF() {
        AssimilationRequest request = createValidRequest();
        request.setAlgorithm("enkf");
        when(pythonScriptInvoker.execute(any(), any(), any()))
                .thenReturn(Map.of("success", true, "ensembles", "[]"));
        Map<String, Object> result = assimilationController.execute(request);
        assertNotNull(result);
    }

    @Test
    @DisplayName("测试同化失败")
    void testExecuteWithPythonError() {
        AssimilationRequest request = createValidRequest();
        when(pythonScriptInvoker.execute(any(), any(), any()))
                .thenThrow(new RuntimeException("Python脚本超时"));
        assertThrows(RuntimeException.class, () -> assimilationController.execute(request));
    }
}

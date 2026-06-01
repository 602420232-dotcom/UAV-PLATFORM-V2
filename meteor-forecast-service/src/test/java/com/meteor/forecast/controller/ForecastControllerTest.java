package com.meteor.forecast.controller;

import com.uav.common.dto.ForecastRequest;
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
@DisplayName("ForecastController 气象预测控制器测试")
class ForecastControllerTest {

    @Mock
    private PythonScriptInvoker pythonScriptInvoker;

    @InjectMocks
    private ForecastController forecastController;

    @BeforeEach
    void setUp() {
        ReflectionTestUtils.setField(forecastController, "pythonScriptPath", "meteor_forecast.py");
    }

    @Test
    @DisplayName("测试LSTM气象预测")
    void testPredict() {
        ForecastRequest request = createValidRequest("lstm");
        when(pythonScriptInvoker.execute(any(), any(), any()))
                .thenReturn(Map.of("success", true, "forecast", "{}"));
        Map<String, Object> result = forecastController.predict(request);
        assertNotNull(result);
        assertTrue((Boolean) result.get("success"));
    }

    @Test
    @DisplayName("测试XGBoost数据订正")
    void testCorrect() {
        ForecastRequest request = createValidRequest("xgb");
        when(pythonScriptInvoker.execute(any(), any(), any()))
                .thenReturn(Map.of("success", true, "corrected", "{}"));
        Map<String, Object> result = forecastController.correct(request);
        assertNotNull(result);
        assertTrue((Boolean) result.get("success"));
    }

    @Test
    @DisplayName("测试获取模型列表")
    void testGetModels() {
        Map<String, Object> result = forecastController.getModels();
        assertNotNull(result);
        assertTrue((Boolean) result.get("success"));
        assertNotNull(result.get("data"));
    }

    @Test
    @DisplayName("测试混合模型预测")
    void testHybridModelPredict() {
        ForecastRequest request = createValidRequest("hybrid");
        when(pythonScriptInvoker.execute(any(), any(), any()))
                .thenReturn(Map.of("success", true, "forecast", "{}"));
        Map<String, Object> result = forecastController.predict(request);
        assertNotNull(result);
    }

    @Test
    @DisplayName("测试修正失败场景")
    void testCorrectWithError() {
        ForecastRequest request = createValidRequest("lstm");
        when(pythonScriptInvoker.execute(any(), any(), any()))
                .thenThrow(new RuntimeException("数据处理失败"));
        assertThrows(RuntimeException.class, () -> forecastController.correct(request));
    }

    private ForecastRequest createValidRequest(String method) {
        ForecastRequest request = new ForecastRequest();
        request.setMethod(method);
        Map<String, Object> data = new HashMap<>();
        data.put("latitude", 39.9);
        data.put("longitude", 116.4);
        data.put("hours", 24);
        request.setData(data);
        request.setConfig(new HashMap<>());
        return request;
    }
}

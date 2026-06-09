package com.uav.meteor.forecast.controller;

import com.uav.common.dto.ForecastRequest;
import com.uav.common.script.PythonScriptInvoker;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
@DisplayName("ForecastController 气象预报控制器测试")
class ForecastControllerTest {

    @Mock
    private PythonScriptInvoker pythonScriptInvoker;

    private ForecastController forecastController;

    @BeforeEach
    void setUp() {
        // 显式构造函数注入
        forecastController = new ForecastController(pythonScriptInvoker);
        ReflectionTestUtils.setField(forecastController, "pythonScriptPath", "meteor_forecast.py");
    }

    private ForecastRequest createValidRequest() {
        ForecastRequest request = new ForecastRequest();
        request.setMethod("lstm");
        request.setData(Map.of("temperature", 25.0, "humidity", 60));
        request.setConfig(Map.of("epochs", 100));
        return request;
    }

    @Test
    @DisplayName("测试单点预测 - 成功")
    void testPredict() {
        ForecastRequest request = createValidRequest();
        when(pythonScriptInvoker.executeAsMap(any(), any(), any()))
                .thenReturn(Map.of("success", true, "forecast", "{}"));
        Map<String, Object> result = forecastController.predict(request);
        assertNotNull(result);
        assertEquals(Boolean.TRUE, result.get("success"));
    }

    @Test
    @DisplayName("测试数据订正 - 成功")
    void testCorrect() {
        ForecastRequest request = createValidRequest();
        when(pythonScriptInvoker.executeAsMap(any(), any(), any()))
                .thenReturn(Map.of("success", true, "corrected", "{}"));
        Map<String, Object> result = forecastController.correct(request);
        assertNotNull(result);
        assertEquals(Boolean.TRUE, result.get("success"));
    }

    @Test
    @DisplayName("测试模型列表 - 成功")
    void testGetModels() {
        when(pythonScriptInvoker.executeAsMap(any(), eq("model_info"), any()))
                .thenReturn(Map.of("success", true, "models", "[]"));
        Map<String, Object> result = forecastController.getModels();
        assertNotNull(result);
        assertEquals(Boolean.TRUE, result.get("success"));
    }

    @Test
    @DisplayName("测试按经纬度获取预报 - 成功")
    void testGetForecast() {
        when(pythonScriptInvoker.executeAsMap(any(), eq("get_forecast"), any()))
                .thenReturn(Map.of("success", true, "forecast", "{}"));
        Map<String, Object> result = forecastController.getForecast(39.9, 116.4, 24);
        assertNotNull(result);
        assertEquals(Boolean.TRUE, result.get("success"));
    }

    @Test
    @DisplayName("测试按经纬度获取预报 - 传递正确参数")
    void testGetForecastParams() {
        when(pythonScriptInvoker.executeAsMap(any(), eq("get_forecast"), argThat(params ->
                39.9 == (double) params.get("lat") && 116.4 == (double) params.get("lng") && 24 == (int) params.get("hours")
        ))).thenReturn(Map.of("success", true));
        Map<String, Object> result = forecastController.getForecast(39.9, 116.4, 24);
        assertNotNull(result);
    }

    @Test
    @DisplayName("测试获取详细预报 - 成功")
    void testGetDetailedForecast() {
        Map<String, Object> request = Map.of("lat", 39.9, "lng", 116.4, "hours", 48, "variables", "temperature,wind");
        when(pythonScriptInvoker.executeAsMap(any(), eq("get_detailed_forecast"), any()))
                .thenReturn(Map.of("success", true, "detailed_forecast", "{}"));
        Map<String, Object> result = forecastController.getDetailedForecast(request);
        assertNotNull(result);
        assertEquals(Boolean.TRUE, result.get("success"));
    }

    @Test
    @DisplayName("测试获取实时天气 - 成功")
    void testGetRealtimeWeather() {
        when(pythonScriptInvoker.executeAsMap(any(), eq("get_realtime_weather"), any()))
                .thenReturn(Map.of("success", true, "temperature", 25.0, "humidity", 60));
        Map<String, Object> result = forecastController.getRealtimeWeather(39.9, 116.4);
        assertNotNull(result);
        assertEquals(Boolean.TRUE, result.get("success"));
    }

    @Test
    @DisplayName("测试获取实时天气 - 传递正确经纬度")
    void testGetRealtimeWeatherParams() {
        when(pythonScriptInvoker.executeAsMap(any(), eq("get_realtime_weather"), argThat(params ->
                39.9 == (double) params.get("lat") && 116.4 == (double) params.get("lng")
        ))).thenReturn(Map.of("success", true));
        Map<String, Object> result = forecastController.getRealtimeWeather(39.9, 116.4);
        assertNotNull(result);
    }

    @Test
    @DisplayName("测试训练模型 - 成功")
    void testTrainModel() {
        Map<String, Object> request = Map.of("epochs", 200, "learning_rate", 0.001);
        when(pythonScriptInvoker.executeAsMap(any(), eq("train_full"), any()))
                .thenReturn(Map.of("success", true, "model_path", "/models/lstm_v2.pt"));
        Map<String, Object> result = forecastController.trainModel(request);
        assertNotNull(result);
        assertEquals(Boolean.TRUE, result.get("success"));
    }

    @Test
    @DisplayName("测试改进模型 - 成功")
    void testImproveModel() {
        Map<String, Object> request = Map.of("model", "lstm", "fine_tune", true);
        when(pythonScriptInvoker.executeAsMap(any(), eq("improve"), any()))
                .thenReturn(Map.of("success", true, "improvement", "15%"));
        Map<String, Object> result = forecastController.improveModel(request);
        assertNotNull(result);
        assertEquals(Boolean.TRUE, result.get("success"));
    }

    @Test
    @DisplayName("测试保存模型（无版本号）- 成功")
    void testSaveModels() {
        when(pythonScriptInvoker.executeAsMap(any(), eq("save_models"), argThat(params -> params.isEmpty())))
                .thenReturn(Map.of("success", true, "message", "模型已保存"));
        Map<String, Object> result = forecastController.saveModels(null);
        assertNotNull(result);
        assertEquals(Boolean.TRUE, result.get("success"));
    }

    @Test
    @DisplayName("测试保存模型（带版本号）- 成功")
    void testSaveModelsWithVersion() {
        Map<String, String> request = Map.of("version", "v2.0");
        when(pythonScriptInvoker.executeAsMap(any(), eq("save_models"), argThat(params ->
                "v2.0".equals(params.get("version"))
        ))).thenReturn(Map.of("success", true, "message", "模型 v2.0 已保存"));
        Map<String, Object> result = forecastController.saveModels(request);
        assertNotNull(result);
        assertEquals(Boolean.TRUE, result.get("success"));
    }

    @Test
    @DisplayName("测试加载模型（无版本号）- 成功")
    void testLoadModels() {
        when(pythonScriptInvoker.executeAsMap(any(), eq("load_models"), argThat(params -> params.isEmpty())))
                .thenReturn(Map.of("success", true, "models", "[]"));
        Map<String, Object> result = forecastController.loadModels(null);
        assertNotNull(result);
        assertEquals(Boolean.TRUE, result.get("success"));
    }

    @Test
    @DisplayName("测试加载模型（带版本号）- 成功")
    void testLoadModelsWithVersion() {
        Map<String, String> request = Map.of("version", "v1.0");
        when(pythonScriptInvoker.executeAsMap(any(), eq("load_models"), argThat(params ->
                "v1.0".equals(params.get("version"))
        ))).thenReturn(Map.of("success", true, "models", "[]"));
        Map<String, Object> result = forecastController.loadModels(request);
        assertNotNull(result);
        assertEquals(Boolean.TRUE, result.get("success"));
    }

    @Test
    @DisplayName("测试预测失败 - Python脚本异常")
    void testPredictWithPythonError() {
        ForecastRequest request = createValidRequest();
        when(pythonScriptInvoker.executeAsMap(any(), any(), any()))
                .thenReturn(Map.of("success", false, "error", "Python script crashed"));
        Map<String, Object> result = forecastController.predict(request);
        assertNotNull(result);
        assertEquals(Boolean.FALSE, result.get("success"));
        assertNotNull(result.get("error"));
    }
}

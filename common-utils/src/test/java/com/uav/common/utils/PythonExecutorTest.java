package com.uav.common.utils;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.common.script.PythonScriptInvoker;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.HashMap;
import java.util.Objects;

import static org.junit.jupiter.api.Assertions.*;

/**
 * PythonExecutor 单元测试（通过委托模式调用 PythonScriptInvoker）
 */
@DisplayName("PythonExecutor测试")
class PythonExecutorTest {

    private PythonExecutor pythonExecutor;
    private PythonScriptInvoker scriptInvoker;

    @BeforeEach
    void setUp() {
        scriptInvoker = new PythonScriptInvoker(new ObjectMapper());
        pythonExecutor = new PythonExecutor(scriptInvoker);
        ReflectionTestUtils.setField(
                Objects.requireNonNull(scriptInvoker), "scriptPath", "src/main/python");
        ReflectionTestUtils.setField(
                Objects.requireNonNull(scriptInvoker), "timeout", 30000);
    }

    @Test
    @DisplayName("测试有效脚本名称验证")
    void testValidateValidScriptName() {
        assertDoesNotThrow(() -> pythonExecutor.execute("meteor_forecast.py", "predict", new HashMap<>()));
    }

    @Test
    @DisplayName("测试空脚本名称验证")
    void testValidateEmptyScriptName() {
        assertThrows(SecurityException.class, () ->
            pythonExecutor.execute("", "predict", new HashMap<>()));
    }

    @Test
    @DisplayName("测试null脚本名称验证")
    void testValidateNullScriptName() {
        assertThrows(SecurityException.class, () ->
            pythonExecutor.execute(null, "predict", new HashMap<>()));
    }

    @Test
    @DisplayName("测试路径遍历脚本名称")
    void testValidatePathTraversalScriptName() {
        assertThrows(SecurityException.class, () ->
            pythonExecutor.execute("../malicious.py", "predict", new HashMap<>()));
    }

    @Test
    @DisplayName("测试无效脚本名称")
    void testValidateInvalidScriptName() {
        assertThrows(SecurityException.class, () ->
            pythonExecutor.execute("malicious.py", "predict", new HashMap<>()));
    }

    @Test
    @DisplayName("测试有效动作验证")
    void testValidateValidAction() {
        assertDoesNotThrow(() -> pythonExecutor.execute("meteor_forecast.py", "predict", new HashMap<>()));
    }

    @Test
    @DisplayName("测试空动作验证")
    void testValidateEmptyAction() {
        assertThrows(SecurityException.class, () ->
            pythonExecutor.execute("meteor_forecast.py", "", new HashMap<>()));
    }

    @Test
    @DisplayName("测试无效动作验证")
    void testValidateInvalidAction() {
        assertThrows(SecurityException.class, () ->
            pythonExecutor.execute("meteor_forecast.py", "rm", new HashMap<>()));
    }

    @Test
    @DisplayName("测试关闭方法")
    void testShutdown() {
        assertDoesNotThrow(() -> pythonExecutor.shutdown());
    }
}

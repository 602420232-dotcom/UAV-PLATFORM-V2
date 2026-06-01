package com.uav.common.utils;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.HashMap;
import java.util.Objects;

import static org.junit.jupiter.api.Assertions.*;

/**
 * PythonExecutor单元测试
 */
@DisplayName("PythonExecutor测试")
class PythonExecutorTest {

    private PythonExecutor pythonExecutor;

    @BeforeEach
    void setUp() {
        pythonExecutor = new PythonExecutor();
        ReflectionTestUtils.setField(
                Objects.requireNonNull(pythonExecutor), "scriptPath", "src/main/python");
        ReflectionTestUtils.setField(
                Objects.requireNonNull(pythonExecutor), "timeout", 30000);
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
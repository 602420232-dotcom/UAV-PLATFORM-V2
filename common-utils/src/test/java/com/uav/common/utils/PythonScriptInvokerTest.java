package com.uav.common.utils;

import com.uav.common.exception.PythonExecutionException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.HashMap;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("PythonScriptInvoker测试")
class PythonScriptInvokerTest {

    private PythonScriptInvoker scriptInvoker;

    @BeforeEach
    void setUp() {
        scriptInvoker = new PythonScriptInvoker();
        ReflectionTestUtils.setField(scriptInvoker, "timeout", 30000);
    }

    @Test
    @DisplayName("测试空路径验证")
    void testValidateEmptyPath() {
        assertThrows(PythonExecutionException.class, () ->
            scriptInvoker.execute("", "test", new HashMap<>()));
    }

    @Test
    @DisplayName("测试路径遍历攻击验证")
    void testValidatePathTraversal() {
        assertThrows(PythonExecutionException.class, () ->
            scriptInvoker.execute("../etc/passwd", "test", new HashMap<>()));
    }

    @Test
    @DisplayName("测试关闭方法")
    void testShutdown() {
        assertDoesNotThrow(() -> scriptInvoker.shutdown());
    }
}

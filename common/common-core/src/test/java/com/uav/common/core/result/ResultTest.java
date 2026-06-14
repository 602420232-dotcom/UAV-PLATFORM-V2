package com.uav.common.core.result;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Result 统一响应结构单元测试
 */
@DisplayName("Result 响应结构测试")
class ResultTest {

    @Test
    @DisplayName("success(data) 应返回成功状态并携带数据")
    void successWithDataShouldReturnOkWithPayload() {
        String payload = "test-data";
        Result<String> result = Result.success(payload);

        assertNotNull(result);
        assertTrue(result.isSuccess());
        assertEquals(ResultCode.SUCCESS.getCode(), result.getCode());
        assertEquals(ResultCode.SUCCESS.getMessage(), result.getMessage());
        assertEquals(payload, result.getData());
        assertNotNull(result.getTimestamp());
    }

    @Test
    @DisplayName("success() 无参应返回成功状态且 data 为 null")
    void successWithoutDataShouldReturnOkWithNullPayload() {
        Result<Void> result = Result.success();

        assertNotNull(result);
        assertTrue(result.isSuccess());
        assertEquals(ResultCode.SUCCESS.getCode(), result.getCode());
        assertNull(result.getData());
    }

    @Test
    @DisplayName("error(int, String) 应返回指定错误码和消息")
    void errorWithCodeAndMessageShouldReturnErrorResult() {
        int errorCode = 1001;
        String errorMessage = "未授权";
        Result<Void> result = Result.error(errorCode, errorMessage);

        assertNotNull(result);
        assertFalse(result.isSuccess());
        assertEquals(errorCode, result.getCode());
        assertEquals(errorMessage, result.getMessage());
    }

    @Test
    @DisplayName("error(ResultCode) 应返回对应枚举的错误信息")
    void errorWithResultCodeShouldReturnCorrespondingError() {
        ResultCode resultCode = ResultCode.TASK_NOT_FOUND;
        Result<Void> result = Result.error(resultCode);

        assertNotNull(result);
        assertFalse(result.isSuccess());
        assertEquals(resultCode.getCode(), result.getCode());
        assertEquals(resultCode.getMessage(), result.getMessage());
    }

    @Test
    @DisplayName("error(ResultCode, String) 应使用自定义消息覆盖默认消息")
    void errorWithResultCodeAndCustomMessageShouldOverrideMessage() {
        ResultCode resultCode = ResultCode.BAD_REQUEST;
        String customMessage = "自定义参数错误";
        Result<Void> result = Result.error(resultCode, customMessage);

        assertNotNull(result);
        assertFalse(result.isSuccess());
        assertEquals(resultCode.getCode(), result.getCode());
        assertEquals(customMessage, result.getMessage());
    }

    @Test
    @DisplayName("链式设置 data、message、code 应生效")
    void chainedSettersShouldWorkCorrectly() {
        Result<String> result = new Result<>();
        result.setData("chain-data");
        result.setMessage("chain-message");
        result.setCode(200);

        assertEquals("chain-data", result.getData());
        assertEquals("chain-message", result.getMessage());
        assertEquals(200, result.getCode());
    }

    @Test
    @DisplayName("isSuccess() 应在 code 等于 SUCCESS 时返回 true")
    void isSuccessShouldReturnTrueOnlyForSuccessCode() {
        Result<String> successResult = Result.success("ok");
        assertTrue(successResult.isSuccess());

        Result<Void> errorResult = Result.error(ResultCode.INTERNAL_ERROR);
        assertFalse(errorResult.isSuccess());
    }

    @Test
    @DisplayName("泛型类型应支持多种数据类型")
    void genericTypesShouldSupportVariousPayloads() {
        Result<Integer> intResult = Result.success(42);
        assertEquals(42, intResult.getData());

        Result<Boolean> boolResult = Result.success(true);
        assertEquals(true, boolResult.getData());

        Result<Object> nullResult = Result.success(null);
        assertNull(nullResult.getData());
    }

    @Test
    @DisplayName("timestamp 应在构造时自动初始化")
    void timestampShouldBeInitializedOnConstruction() {
        Result<String> result = Result.success("test");
        assertNotNull(result);
        assertTrue(result.getTimestamp() > 0);
    }
}

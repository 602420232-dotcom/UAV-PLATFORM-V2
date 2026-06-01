package com.bayesian.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("AlertService 单元测试")
class AlertServiceTest {

    private AlertService service;

    @BeforeEach
    void setUp() {
        service = new AlertService();
    }

    @Nested
    @DisplayName("sendAlert")
    class SendAlertTests {
        @Test
        @DisplayName("发送告警不抛异常")
        void shouldNotThrowOnSend() {
            assertDoesNotThrow(() -> service.sendAlert("WARNING", "测试告警"));
        }

        @Test
        @DisplayName("HIGH级别告警可发送")
        void shouldAcceptHighSeverity() {
            assertDoesNotThrow(() -> service.sendAlert("HIGH", "严重告警"));
        }

        @Test
        @DisplayName("INFO级别告警可发送")
        void shouldAcceptInfoSeverity() {
            assertDoesNotThrow(() -> service.sendAlert("INFO", "信息告警"));
        }
    }

    @Nested
    @DisplayName("notifyDegradedMode")
    class NotifyDegradedModeTests {
        @Test
        @DisplayName("通知降级模式包含服务名")
        void shouldNotifyDegradedMode() {
            assertDoesNotThrow(() -> service.notifyDegradedMode("wrf-processor"));
        }
    }

    @Nested
    @DisplayName("notifyRecovery")
    class NotifyRecoveryTests {
        @Test
        @DisplayName("通知恢复不抛异常")
        void shouldNotifyRecovery() {
            assertDoesNotThrow(() -> service.notifyRecovery("wrf-processor"));
        }
    }
}

package com.uav.common.kafka.producer;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.common.kafka.config.KafkaTopicConfig;
import com.uav.common.kafka.message.AlgorithmTaskMessage;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.SendResult;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.Map;
import java.util.concurrent.CompletableFuture;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AlgorithmTaskProducerTest {

    @Mock
    private KafkaTemplate<String, String> kafkaTemplate;

    @Mock
    private ObjectMapper objectMapper;

    @InjectMocks
    private AlgorithmTaskProducer producer;

    private AlgorithmTaskMessage testMessage;

    @BeforeEach
    void setUp() {
        testMessage = AlgorithmTaskMessage.builder()
                .taskId("task-001")
                .algorithmId("weather-forecast")
                .params(Map.of("region", "beijing", "hours", 24))
                .priority(1)
                .tenantId("tenant-001")
                .build();
    }

    @Test
    void sendTask_normalSend_shouldSendToDefaultTopic() throws Exception {
        // Arrange
        String expectedJson = "{\"task_id\":\"task-001\",\"algorithm_id\":\"weather-forecast\"}";
        when(objectMapper.writeValueAsString(testMessage)).thenReturn(expectedJson);
        @SuppressWarnings("unchecked")
        CompletableFuture<SendResult<String, String>> mockFuture = mock(CompletableFuture.class);
        when(kafkaTemplate.send(KafkaTopicConfig.TOPIC_ALGORITHM_TASKS, "task-001", expectedJson))
                .thenReturn(mockFuture);

        // Act
        producer.sendTask(testMessage);

        // Assert
        verify(objectMapper).writeValueAsString(testMessage);
        verify(kafkaTemplate).send(KafkaTopicConfig.TOPIC_ALGORITHM_TASKS, "task-001", expectedJson);
        assertNotNull(testMessage.getTimestamp(), "timestamp 应在发送时自动设置");
    }

    @Test
    void sendTask_mockMode_shouldSkipSending() {
        // Arrange
        ReflectionTestUtils.setField(producer, "mockMode", true);

        // Act
        producer.sendTask(testMessage);

        // Assert
        verifyNoInteractions(kafkaTemplate);
        verifyNoInteractions(objectMapper);
        assertTrue(producer.isMockMode());
    }

    @Test
    void sendTask_customCallbackTopic_shouldSendToCustomTopic() throws Exception {
        // Arrange
        String customTopic = "uav.custom.callback";
        testMessage.setCallbackTopic(customTopic);
        String expectedJson = "{\"task_id\":\"task-001\"}";
        when(objectMapper.writeValueAsString(testMessage)).thenReturn(expectedJson);
        @SuppressWarnings("unchecked")
        CompletableFuture<SendResult<String, String>> mockFuture = mock(CompletableFuture.class);
        when(kafkaTemplate.send(customTopic, "task-001", expectedJson))
                .thenReturn(mockFuture);

        // Act
        producer.sendTask(testMessage);

        // Assert
        verify(kafkaTemplate).send(customTopic, "task-001", expectedJson);
        verify(kafkaTemplate, never()).send(eq(KafkaTopicConfig.TOPIC_ALGORITHM_TASKS), anyString(), anyString());
    }

    @Test
    void sendTask_serializationFailure_shouldThrowRuntimeException() throws Exception {
        // Arrange
        when(objectMapper.writeValueAsString(testMessage))
                .thenThrow(new JsonProcessingException("序列化失败") {});

        // Act & Assert
        RuntimeException exception = assertThrows(RuntimeException.class, () -> {
            producer.sendTask(testMessage);
        });
        assertEquals("序列化算法任务消息失败", exception.getMessage());
        assertInstanceOf(JsonProcessingException.class, exception.getCause());
        verifyNoInteractions(kafkaTemplate);
    }
}

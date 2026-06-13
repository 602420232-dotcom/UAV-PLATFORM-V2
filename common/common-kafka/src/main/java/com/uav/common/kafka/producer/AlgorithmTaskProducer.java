package com.uav.common.kafka.producer;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.common.kafka.config.KafkaTopicConfig;
import com.uav.common.kafka.message.AlgorithmTaskMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.SendResult;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.concurrent.CompletableFuture;

/**
 * 算法任务 Kafka 生产者
 * <p>
 * 将算法任务消息发送到 Python 引擎。
 * 支持模拟模式：当 {@code uav.kafka.mock=true} 时不发送 Kafka 消息。
 */
@Component
@Slf4j
public class AlgorithmTaskProducer {

    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Value("${uav.kafka.mock:false}")
    private boolean mockMode;

    /**
     * 发送算法任务到 Python 引擎
     *
     * @param message 任务消息
     */
    public void sendTask(AlgorithmTaskMessage message) {
        if (message.getTimestamp() == null) {
            message.setTimestamp(Instant.now().toString());
        }

        if (mockMode) {
            log.info("[MOCK] 跳过 Kafka 发送, taskId={}, algorithmId={}",
                    message.getTaskId(), message.getAlgorithmId());
            return;
        }

        try {
            String json = objectMapper.writeValueAsString(message);
            String topic = message.getCallbackTopic() != null
                    ? message.getCallbackTopic()
                    : KafkaTopicConfig.TOPIC_ALGORITHM_TASKS;

            CompletableFuture<SendResult<String, String>> future =
                    kafkaTemplate.send(topic, message.getTaskId(), json);

            future.whenComplete((result, ex) -> {
                if (ex != null) {
                    log.error("发送算法任务失败, taskId={}, topic={}",
                            message.getTaskId(), topic, ex);
                } else {
                    log.debug("算法任务已发送, taskId={}, topic={}, partition={}, offset={}",
                            message.getTaskId(), topic,
                            result.getRecordMetadata().partition(),
                            result.getRecordMetadata().offset());
                }
            });
        } catch (JsonProcessingException e) {
            log.error("序列化算法任务消息失败, taskId={}", message.getTaskId(), e);
            throw new RuntimeException("序列化算法任务消息失败", e);
        }
    }

    /**
     * 判断当前是否为模拟模式
     */
    public boolean isMockMode() {
        return mockMode;
    }
}

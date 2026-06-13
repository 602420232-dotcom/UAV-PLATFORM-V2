package com.uav.common.kafka.consumer;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.common.kafka.config.KafkaTopicConfig;
import com.uav.common.kafka.message.AlgorithmResultMessage;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.messaging.handler.annotation.Payload;

/**
 * 算法结果消费者抽象基类
 * <p>
 * 各微服务继承此类并实现 {@link #onResult(AlgorithmResultMessage)} 方法来处理算法执行结果。
 * <p>
 * 使用示例:
 * <pre>
 * &#64;Component
 * public class MyResultConsumer extends AbstractAlgorithmResultConsumer {
 *     &#64;Override
 *     protected void onResult(AlgorithmResultMessage message) {
 *         // 处理结果
 *     }
 * }
 * </pre>
 */
@Slf4j
public abstract class AbstractAlgorithmResultConsumer {

    @Autowired
    private ObjectMapper objectMapper;

    /**
     * 消费 Python 引擎返回的算法结果
     *
     * @param record   Kafka 消费记录
     * @param ack      手动确认
     * @param topic    消息来源 Topic
     * @param offset   消息偏移量
     */
    @KafkaListener(
            topics = KafkaTopicConfig.TOPIC_ALGORITHM_RESULTS,
            groupId = "${spring.application.name}-result-group",
            containerFactory = "kafkaListenerContainerFactory"
    )
    public void onMessage(
            @Payload ConsumerRecord<String, String> record,
            Acknowledgment ack,
            @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
            @Header(KafkaHeaders.OFFSET) long offset) {

        log.debug("收到算法结果消息, topic={}, partition={}, offset={}, key={}",
                topic, record.partition(), offset, record.key());

        try {
            AlgorithmResultMessage message = objectMapper.readValue(
                    record.value(), AlgorithmResultMessage.class);

            log.info("算法结果: taskId={}, algorithmId={}, status={}, progress={}",
                    message.getTaskId(), message.getAlgorithmId(),
                    message.getStatus(), message.getProgress());

            onResult(message);
            ack.acknowledge();

        } catch (Exception e) {
            log.error("处理算法结果消息失败, topic={}, offset={}, key={}",
                    topic, offset, record.key(), e);
            // 不确认，消息将重新投递
        }
    }

    /**
     * 子类实现此方法处理算法执行结果
     *
     * @param message 算法结果消息
     */
    protected abstract void onResult(AlgorithmResultMessage message);
}

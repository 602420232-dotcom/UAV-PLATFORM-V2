package com.uav.common.kafka.config;

import org.apache.kafka.clients.admin.NewTopic;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.config.TopicBuilder;

/**
 * Kafka Topic 自动配置
 * <p>
 * 当 {@code uav.kafka.mock=false} 时自动创建 Topic（需要 Kafka Admin 权限）。
 * 模拟模式下不创建 Topic。
 */
@Configuration
@ConditionalOnProperty(name = "uav.kafka.mock", havingValue = "false", matchIfMissing = false)
public class KafkaTopicConfig {

    /** Java -> Python 算法任务 Topic */
    public static final String TOPIC_ALGORITHM_TASKS = "uav.algorithm.tasks";

    /** Python -> Java 算法结果 Topic */
    public static final String TOPIC_ALGORITHM_RESULTS = "uav.algorithm.results";

    @Bean
    public NewTopic algorithmTasksTopic() {
        return TopicBuilder.name(TOPIC_ALGORITHM_TASKS)
                .partitions(6)
                .replicas(1)
                .build();
    }

    @Bean
    public NewTopic algorithmResultsTopic() {
        return TopicBuilder.name(TOPIC_ALGORITHM_RESULTS)
                .partitions(6)
                .replicas(1)
                .build();
    }
}

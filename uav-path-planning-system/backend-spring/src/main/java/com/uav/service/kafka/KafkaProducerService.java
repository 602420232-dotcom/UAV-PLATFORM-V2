package com.uav.service.kafka;

import com.uav.model.Drone;
import com.uav.model.PathPlan;
import com.uav.model.Task;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.SendResult;
import org.springframework.stereotype.Service;

import java.util.concurrent.CompletableFuture;

/**
 * Kafka 消息生产者服务
 * 负责将系统事件和状态变更推送至Kafka消息队列
 */
@Service
public class KafkaProducerService {

    private static final Logger log = LoggerFactory.getLogger(KafkaProducerService.class);

    private static final String TOPIC_TASKS = "uav-tasks";
    private static final String TOPIC_DRONES = "uav-drones";
    private static final String TOPIC_PATH_PLANS = "uav-path-plans";

    private final KafkaTemplate<String, String> kafkaTemplate;

    public KafkaProducerService(KafkaTemplate<String, String> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    /**
     * 发送字符串消息到指定主题
     *
     * @param topic   主题名称
     * @param message 消息内容
     */
    public void sendMessage(String topic, String message) {
        log.info("Sending message to topic '{}': {}", topic, message);
        CompletableFuture<SendResult<String, String>> future = kafkaTemplate.send(topic, message);

        future.whenComplete((result, ex) -> {
            if (ex == null) {
                log.debug("Message sent successfully to topic '{}', offset={}",
                        topic, result.getRecordMetadata().offset());
            } else {
                log.error("Failed to send message to topic '{}': {}", topic, ex.getMessage(), ex);
            }
        });
    }

    /**
     * 发送任务更新事件到 uav-tasks 主题
     *
     * @param task 任务对象
     */
    public void sendTaskEvent(Task task) {
        String message = buildTaskMessage(task);
        log.info("Sending task event: taskId={}, status={}", task.getId(), task.getStatus());
        sendMessage(TOPIC_TASKS, message);
    }

    /**
     * 发送无人机状态事件到 uav-drones 主题
     *
     * @param drone 无人机对象
     */
    public void sendDroneEvent(Drone drone) {
        String message = buildDroneMessage(drone);
        log.info("Sending drone event: droneId={}, status={}", drone.getId(), drone.getStatus());
        sendMessage(TOPIC_DRONES, message);
    }

    /**
     * 发送路径规划事件到 uav-path-plans 主题
     *
     * @param plan 路径规划对象
     */
    public void sendPathPlanEvent(PathPlan plan) {
        String message = buildPathPlanMessage(plan);
        log.info("Sending path plan event: planId={}, status={}", plan.getId(), plan.getStatus());
        sendMessage(TOPIC_PATH_PLANS, message);
    }

    private String buildTaskMessage(Task task) {
        return String.format(
                "{\"eventType\":\"TASK_UPDATE\",\"taskId\":%d,\"name\":\"%s\",\"status\":\"%s\",\"priority\":%d}",
                task.getId(), safeString(task.getName()), task.getStatus(), task.getPriority()
        );
    }

    private String buildDroneMessage(Drone drone) {
        return String.format(
                "{\"eventType\":\"DRONE_UPDATE\",\"droneId\":%d,\"name\":\"%s\",\"model\":\"%s\",\"status\":\"%s\",\"batteryLevel\":%d}",
                drone.getId(), safeString(drone.getName()), safeString(drone.getModel()),
                drone.getStatus(), drone.getBatteryLevel()
        );
    }

    private String buildPathPlanMessage(PathPlan plan) {
        return String.format(
                "{\"eventType\":\"PATH_PLAN_UPDATE\",\"planId\":%d,\"name\":\"%s\",\"status\":\"%s\",\"totalDistance\":%.2f,\"totalRisk\":%.2f}",
                plan.getId(), safeString(plan.getName()), plan.getStatus(),
                plan.getTotalDistance(), plan.getTotalRisk()
        );
    }

    private String safeString(String value) {
        return value != null ? value.replace("\"", "\\\"") : "";
    }
}

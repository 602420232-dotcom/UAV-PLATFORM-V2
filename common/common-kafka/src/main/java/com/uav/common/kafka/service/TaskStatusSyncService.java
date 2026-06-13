package com.uav.common.kafka.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.common.core.constant.TaskStatus;
import com.uav.common.kafka.message.AlgorithmResultMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * 任务状态同步服务
 * <p>
 * 通过 Redis 同步 Java 与 Python 之间的任务状态。
 * Java 提交任务后将初始状态写入 Redis，Python 执行完毕后更新状态，
 * Java 端可通过轮询 Redis 等待结果。
 * <p>
 * Redis Key 规范（与 Python 端 redis_cache.py 对齐）:
 * <ul>
 *   <li>任务状态: {@code task:{taskId}} -> JSON</li>
 *   <li>任务结果: {@code result:{taskId}} -> JSON</li>
 * </ul>
 */
@Service
@Slf4j
public class TaskStatusSyncService {

    private static final String TASK_KEY_PREFIX = "task:";
    private static final String RESULT_KEY_PREFIX = "result:";

    @Autowired
    private StringRedisTemplate redisTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Value("${uav.kafka.task-status-ttl:3600}")
    private int taskStatusTtl;

    /**
     * 初始化任务状态（Java 提交任务后调用）
     *
     * @param taskId      任务ID
     * @param algorithmId 算法ID
     * @param tenantId    租户ID
     */
    public void initTaskStatus(String taskId, String algorithmId, String tenantId) {
        Map<String, Object> status = Map.of(
                "task_id", taskId,
                "algorithm_id", algorithmId,
                "status", TaskStatus.QUEUED.getName(),
                "progress", 0,
                "tenant_id", tenantId != null ? tenantId : ""
        );
        try {
            String json = objectMapper.writeValueAsString(status);
            redisTemplate.opsForValue().set(
                    TASK_KEY_PREFIX + taskId, json, taskStatusTtl, TimeUnit.SECONDS);
            log.debug("任务状态已初始化, taskId={}, status={}", taskId, TaskStatus.QUEUED.getName());
        } catch (JsonProcessingException e) {
            log.error("序列化任务状态失败, taskId={}", taskId, e);
        }
    }

    /**
     * 更新任务状态（Python 结果消费后调用）
     *
     * @param message 算法结果消息
     */
    public void updateTaskStatus(AlgorithmResultMessage message) {
        Map<String, Object> status = Map.of(
                "task_id", message.getTaskId(),
                "algorithm_id", message.getAlgorithmId(),
                "status", message.getStatus(),
                "progress", message.getProgress(),
                "error", message.getError() != null ? message.getError() : "",
                "completed_at", message.getCompletedAt() != null ? message.getCompletedAt() : ""
        );
        try {
            String json = objectMapper.writeValueAsString(status);
            redisTemplate.opsForValue().set(
                    TASK_KEY_PREFIX + message.getTaskId(), json, taskStatusTtl, TimeUnit.SECONDS);
            log.debug("任务状态已更新, taskId={}, status={}", message.getTaskId(), message.getStatus());
        } catch (JsonProcessingException e) {
            log.error("序列化任务状态失败, taskId={}", message.getTaskId(), e);
        }
    }

    /**
     * 缓存算法结果
     *
     * @param message 算法结果消息
     */
    public void cacheResult(AlgorithmResultMessage message) {
        try {
            String json = objectMapper.writeValueAsString(message);
            redisTemplate.opsForValue().set(
                    RESULT_KEY_PREFIX + message.getTaskId(), json, taskStatusTtl, TimeUnit.SECONDS);
        } catch (JsonProcessingException e) {
            log.error("缓存算法结果失败, taskId={}", message.getTaskId(), e);
        }
    }

    /**
     * 等待任务完成（轮询 Redis）
     * <p>
     * 阻塞当前线程直到任务达到终态或超时。
     *
     * @param taskId 任务ID
     * @param timeout 超时时间
     * @param timeUnit 时间单位
     * @return 算法结果消息，超时返回 null
     */
    public AlgorithmResultMessage waitForResult(String taskId, long timeout, TimeUnit timeUnit) {
        long deadlineNanos = System.nanoTime() + timeUnit.toNanos(timeout);
        long pollIntervalMillis = 500;

        while (System.nanoTime() < deadlineNanos) {
            // 先检查结果缓存
            String resultJson = redisTemplate.opsForValue().get(RESULT_KEY_PREFIX + taskId);
            if (resultJson != null) {
                try {
                    AlgorithmResultMessage result = objectMapper.readValue(
                            resultJson, AlgorithmResultMessage.class);
                    log.info("获取到任务结果, taskId={}, status={}", taskId, result.getStatus());
                    return result;
                } catch (JsonProcessingException e) {
                    log.error("解析任务结果失败, taskId={}", taskId, e);
                }
            }

            // 检查任务状态是否已终态
            String statusJson = redisTemplate.opsForValue().get(TASK_KEY_PREFIX + taskId);
            if (statusJson != null) {
                try {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> statusMap = objectMapper.readValue(statusJson, Map.class);
                    String status = String.valueOf(statusMap.getOrDefault("status", ""));
                    TaskStatus taskStatus = TaskStatus.fromName(status);
                    if (taskStatus != null && taskStatus.isTerminal()) {
                        log.info("任务已达终态, taskId={}, status={}", taskId, status);
                        // 终态但无结果缓存，返回失败消息
                        return AlgorithmResultMessage.builder()
                                .taskId(taskId)
                                .status(status)
                                .error(statusJson)
                                .progress(0)
                                .build();
                    }
                } catch (JsonProcessingException e) {
                    log.error("解析任务状态失败, taskId={}", taskId, e);
                }
            }

            try {
                Thread.sleep(pollIntervalMillis);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                log.warn("等待任务结果被中断, taskId={}", taskId);
                return null;
            }
        }

        log.warn("等待任务结果超时, taskId={}, timeout={}{}",
                taskId, timeout, timeUnit);
        return null;
    }

    /**
     * 等待任务完成（默认超时 60 秒）
     *
     * @param taskId 任务ID
     * @return 算法结果消息，超时返回 null
     */
    public AlgorithmResultMessage waitForResult(String taskId) {
        return waitForResult(taskId, 60, TimeUnit.SECONDS);
    }

    /**
     * 获取当前任务状态
     *
     * @param taskId 任务ID
     * @return 任务状态枚举，未找到返回 null
     */
    public TaskStatus getTaskStatus(String taskId) {
        String statusJson = redisTemplate.opsForValue().get(TASK_KEY_PREFIX + taskId);
        if (statusJson == null) {
            return null;
        }
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> statusMap = objectMapper.readValue(statusJson, Map.class);
            String status = String.valueOf(statusMap.getOrDefault("status", ""));
            return TaskStatus.fromName(status);
        } catch (JsonProcessingException e) {
            log.error("解析任务状态失败, taskId={}", taskId, e);
            return null;
        }
    }

    /**
     * 删除任务状态和结果缓存
     *
     * @param taskId 任务ID
     */
    public void cleanup(String taskId) {
        redisTemplate.delete(TASK_KEY_PREFIX + taskId);
        redisTemplate.delete(RESULT_KEY_PREFIX + taskId);
        log.debug("任务缓存已清理, taskId={}", taskId);
    }
}

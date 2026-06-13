package com.uav.observation.consumer;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.common.core.constant.TaskStatus;
import com.uav.common.kafka.consumer.AbstractAlgorithmResultConsumer;
import com.uav.common.kafka.message.AlgorithmResultMessage;
import com.uav.common.kafka.service.TaskStatusSyncService;
import com.uav.observation.entity.ObservationTask;
import com.uav.observation.mapper.ObservationTaskMapper;
import com.uav.observation.service.ObservationService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * 观测任务 Kafka 结果消费者
 * <p>
 * 消费 Python 引擎返回的观测算法执行结果，更新数据库任务状态，
 * 保存观测数据质量结果，并同步 Redis。
 */
@Component
@Slf4j
@RequiredArgsConstructor
public class ObservationResultConsumer extends AbstractAlgorithmResultConsumer {

    private final ObservationTaskMapper taskMapper;
    private final TaskStatusSyncService taskStatusSyncService;
    private final ObjectMapper objectMapper;
    private final RedisTemplate<String, Object> redisTemplate;
    private final ObservationService observationService;

    @Override
    protected void onResult(AlgorithmResultMessage message) {
        log.info("收到观测任务结果: taskId={}, status={}", message.getTaskId(), message.getStatus());

        Long taskId;
        try {
            taskId = Long.parseLong(message.getTaskId());
        } catch (NumberFormatException e) {
            log.error("无效的 taskId: {}", message.getTaskId(), e);
            return;
        }

        // 更新数据库任务状态
        ObservationTask task = taskMapper.selectById(taskId);
        if (task == null) {
            log.warn("观测任务不存在: taskId={}", taskId);
            return;
        }

        task.setStatus(message.getStatus());

        if ("FAILED".equals(message.getStatus()) && message.getError() != null) {
            log.warn("观测任务执行失败, taskId={}, error={}", taskId, message.getError());
        }

        if ("SUCCESS".equals(message.getStatus()) && message.getResult() != null) {
            handleSuccessResult(task, message);
        }

        taskMapper.updateById(task);

        // 更新 Redis 状态
        taskStatusSyncService.updateTaskStatus(message);
        taskStatusSyncService.cacheResult(message);

        // 更新 Redis 缓存中的任务对象
        String cacheKey = "observation:task:" + taskId;
        redisTemplate.opsForValue().set(cacheKey, task);

        log.info("观测任务结果处理完成: taskId={}, status={}", taskId, message.getStatus());
    }

    /**
     * 处理成功的观测结果
     */
    private void handleSuccessResult(ObservationTask task, AlgorithmResultMessage message) {
        Map<String, Object> result = message.getResult();

        try {
            // 提取实际路径
            Object actualPath = result.get("actual_path");
            if (actualPath != null) {
                task.setActualPathJson(objectMapper.writeValueAsString(actualPath));
            }

            // 提取同化反馈
            Object assimilationFeedback = result.get("assimilation_feedback");
            if (assimilationFeedback != null) {
                task.setAssimilationFeedbackJson(objectMapper.writeValueAsString(assimilationFeedback));
            }

            // 提取数据质量评分
            Object dataQuality = result.get("data_quality");
            if (dataQuality instanceof Number) {
                task.setDataQuality(((Number) dataQuality).doubleValue());
            }

            // 如果结果中没有 data_quality，则自动评估
            if (task.getDataQuality() == null || task.getDataQuality() == 0.0) {
                Double quality = observationService.evaluateDataQuality(task.getId());
                if (quality != null) {
                    task.setDataQuality(quality);
                }
            }

            log.info("观测任务结果已保存, taskId={}, dataQuality={}", task.getId(), task.getDataQuality());
        } catch (Exception e) {
            log.warn("处理观测结果字段失败, taskId={}: {}", task.getId(), e.getMessage());
        }
    }
}

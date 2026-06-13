package com.uav.assimilation.consumer;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.assimilation.entity.AssimilationResult;
import com.uav.assimilation.entity.AssimilationTask;
import com.uav.assimilation.mapper.AssimilationResultMapper;
import com.uav.assimilation.mapper.AssimilationTaskMapper;
import com.uav.common.kafka.consumer.AbstractAlgorithmResultConsumer;
import com.uav.common.kafka.message.AlgorithmResultMessage;
import com.uav.common.kafka.service.TaskStatusSyncService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

/**
 * 同化任务 Kafka 结果消费者
 * <p>
 * 消费 Python 引擎返回的同化算法执行结果，更新数据库任务状态和结果，并同步 Redis。
 */
@Component
@Slf4j
@RequiredArgsConstructor
public class AssimilationResultConsumer extends AbstractAlgorithmResultConsumer {

    private final AssimilationTaskMapper taskMapper;
    private final AssimilationResultMapper resultMapper;
    private final TaskStatusSyncService taskStatusSyncService;
    private final ObjectMapper objectMapper;

    @Override
    protected void onResult(AlgorithmResultMessage message) {
        log.info("收到同化任务结果: taskId={}, status={}", message.getTaskId(), message.getStatus());

        Long taskId;
        try {
            taskId = Long.parseLong(message.getTaskId());
        } catch (NumberFormatException e) {
            log.error("无效的 taskId: {}", message.getTaskId(), e);
            return;
        }

        // 更新数据库任务状态
        AssimilationTask task = taskMapper.selectById(taskId);
        if (task == null) {
            log.warn("同化任务不存在: taskId={}", taskId);
            return;
        }

        task.setStatus(message.getStatus());
        task.setProgress(message.getProgress());
        task.setCompletedAt(LocalDateTime.now());

        if ("FAILED".equals(message.getStatus()) && message.getError() != null) {
            task.setErrorMsg(message.getError());
        }

        if ("SUCCESS".equals(message.getStatus()) && message.getResult() != null) {
            try {
                task.setResultJson(objectMapper.writeValueAsString(message.getResult()));
            } catch (Exception e) {
                log.warn("序列化结果 JSON 失败, taskId={}", taskId, e);
            }

            // 保存同化结果到数据库
            AssimilationResult result = new AssimilationResult();
            result.setTaskId(taskId);
            result.setCreatedAt(LocalDateTime.now());

            Object analysisField = message.getResult().get("analysis_field");
            Object uncertainty = message.getResult().get("uncertainty");
            Object convergenceInfo = message.getResult().get("convergence_info");

            try {
                if (analysisField != null) {
                    result.setAnalysisFieldJson(objectMapper.writeValueAsString(analysisField));
                }
                if (uncertainty != null) {
                    result.setUncertaintyJson(objectMapper.writeValueAsString(uncertainty));
                }
                if (convergenceInfo != null) {
                    result.setConvergenceInfo(objectMapper.writeValueAsString(convergenceInfo));
                }
            } catch (Exception e) {
                log.warn("序列化同化结果字段失败, taskId={}", taskId, e);
            }

            // 检查是否已有结果记录
            LambdaQueryWrapper<AssimilationResult> wrapper = new LambdaQueryWrapper<>();
            wrapper.eq(AssimilationResult::getTaskId, taskId);
            AssimilationResult existing = resultMapper.selectOne(wrapper);
            if (existing != null) {
                result.setId(existing.getId());
                resultMapper.updateById(result);
            } else {
                resultMapper.insert(result);
            }
        }

        taskMapper.updateById(task);

        // 更新 Redis 状态
        taskStatusSyncService.updateTaskStatus(message);
        taskStatusSyncService.cacheResult(message);

        log.info("同化任务结果处理完成: taskId={}, status={}", taskId, message.getStatus());
    }
}

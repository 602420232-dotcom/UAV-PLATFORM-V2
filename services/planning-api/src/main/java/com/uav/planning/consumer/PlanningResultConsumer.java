package com.uav.planning.consumer;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.common.kafka.consumer.AbstractAlgorithmResultConsumer;
import com.uav.common.kafka.message.AlgorithmResultMessage;
import com.uav.common.kafka.service.TaskStatusSyncService;
import com.uav.planning.entity.MissionPlan;
import com.uav.planning.entity.PathResult;
import com.uav.planning.entity.PlanningTask;
import com.uav.planning.mapper.MissionPlanMapper;
import com.uav.planning.mapper.PathResultMapper;
import com.uav.planning.mapper.PlanningTaskMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

/**
 * 规划算法结果 Kafka 消费者
 * <p>
 * 消费 Python 引擎返回的算法执行结果，更新 planning_task 状态并保存结果。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class PlanningResultConsumer extends AbstractAlgorithmResultConsumer {

    private final PlanningTaskMapper taskMapper;
    private final PathResultMapper pathResultMapper;
    private final MissionPlanMapper missionPlanMapper;
    private final TaskStatusSyncService taskStatusSyncService;
    private final ObjectMapper objectMapper;

    @Override
    protected void onResult(AlgorithmResultMessage message) {
        String taskIdStr = message.getTaskId();
        log.info("收到规划算法结果, taskId={}, status={}, algorithmId={}",
                taskIdStr, message.getStatus(), message.getAlgorithmId());

        // 更新 Redis 状态
        taskStatusSyncService.updateTaskStatus(message);
        taskStatusSyncService.cacheResult(message);

        // 查找对应的 planning_task
        LambdaQueryWrapper<PlanningTask> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(PlanningTask::getTaskId, taskIdStr);
        PlanningTask task = taskMapper.selectOne(wrapper);

        if (task == null) {
            log.warn("未找到对应的规划任务, taskId={}", taskIdStr);
            return;
        }

        // 更新任务状态
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
                log.warn("序列化结果JSON失败, taskId={}", taskIdStr, e);
            }

            // 根据算法类型保存对应的结果
            String algorithmId = message.getAlgorithmId();
            if ("VRPTW".equalsIgnoreCase(algorithmId)) {
                saveMissionPlanResult(taskIdStr, message);
            } else {
                savePathResult(taskIdStr, message);
            }
        }

        taskMapper.updateById(task);
        log.info("规划任务状态已更新, taskId={}, status={}", taskIdStr, message.getStatus());
    }

    private void savePathResult(String taskIdStr, AlgorithmResultMessage message) {
        try {
            PathResult result = new PathResult();
            result.setTaskId(taskIdStr);

            if (message.getResult() != null) {
                result.setWaypointsJson(objectMapper.writeValueAsString(
                        message.getResult().getOrDefault("waypoints", "[]")));
                Object totalDistance = message.getResult().get("totalDistance");
                if (totalDistance != null) {
                    result.setTotalDistance(((Number) totalDistance).doubleValue());
                }
                Object estimatedTime = message.getResult().get("estimatedTime");
                if (estimatedTime != null) {
                    result.setEstimatedTime(((Number) estimatedTime).intValue());
                }
                Object riskScore = message.getResult().get("riskScore");
                if (riskScore != null) {
                    result.setRiskScore(((Number) riskScore).doubleValue());
                }
                Object energyConsumption = message.getResult().get("energyConsumption");
                if (energyConsumption != null) {
                    result.setEnergyConsumption(((Number) energyConsumption).doubleValue());
                }
            }

            result.setCreatedAt(LocalDateTime.now());
            pathResultMapper.insert(result);
            log.info("路径规划结果已保存, taskId={}", taskIdStr);
        } catch (Exception e) {
            log.error("保存路径规划结果失败, taskId={}", taskIdStr, e);
        }
    }

    private void saveMissionPlanResult(String taskIdStr, AlgorithmResultMessage message) {
        try {
            MissionPlan plan = new MissionPlan();
            plan.setTaskId(taskIdStr);

            if (message.getResult() != null) {
                Object uavs = message.getResult().get("uavs");
                if (uavs != null) {
                    plan.setUavsJson(objectMapper.writeValueAsString(uavs));
                }
                Object tasks = message.getResult().get("tasks");
                if (tasks != null) {
                    plan.setTasksJson(objectMapper.writeValueAsString(tasks));
                }
                Object schedule = message.getResult().get("schedule");
                if (schedule != null) {
                    plan.setScheduleJson(objectMapper.writeValueAsString(schedule));
                }
                Object score = message.getResult().get("overallScore");
                if (score != null) {
                    plan.setOverallScore(((Number) score).doubleValue());
                }
            }

            // 从原始任务获取 tenantId
            LambdaQueryWrapper<PlanningTask> wrapper = new LambdaQueryWrapper<>();
            wrapper.eq(PlanningTask::getTaskId, taskIdStr);
            PlanningTask task = taskMapper.selectOne(wrapper);
            if (task != null) {
                plan.setTenantId(task.getTenantId());
            }

            plan.setCreatedAt(LocalDateTime.now());
            missionPlanMapper.insert(plan);
            log.info("任务规划结果已保存, taskId={}", taskIdStr);
        } catch (Exception e) {
            log.error("保存任务规划结果失败, taskId={}", taskIdStr, e);
        }
    }
}

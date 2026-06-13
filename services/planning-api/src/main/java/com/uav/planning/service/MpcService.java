package com.uav.planning.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.common.core.constant.TaskStatus;
import com.uav.common.core.context.MockContext;
import com.uav.common.core.util.IdUtil;
import com.uav.common.kafka.message.AlgorithmTaskMessage;
import com.uav.common.kafka.producer.AlgorithmTaskProducer;
import com.uav.common.kafka.service.TaskStatusSyncService;
import com.uav.planning.dto.MpcPlanRequest;
import com.uav.planning.dto.MpcPositionUpdate;
import com.uav.planning.dto.MpcResult;
import com.uav.planning.dto.MpcUpdateResponse;
import com.uav.planning.entity.PlanningTask;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ThreadLocalRandom;

/**
 * MPC 实时滚动规划服务
 * <p>
 * 通过 {@code uav.mock.enabled} 开关控制：
 * <ul>
 *   <li>true（默认）: 使用内存模拟</li>
 *   <li>false: 使用数据库持久化 + Kafka 调度算法引擎</li>
 * </ul>
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class MpcService {

    private final ObjectMapper objectMapper;
    private final AlgorithmTaskProducer algorithmTaskProducer;
    private final TaskStatusSyncService taskStatusSyncService;

    @Value("${uav.mock.enabled:true}")
    private boolean mockEnabled;

    // ===== 内存模拟存储（mock=true 时使用） =====
    private final Map<String, MpcTaskContext> taskContextStore = new ConcurrentHashMap<>();

    /**
     * 提交 MPC 滚动规划任务
     *
     * @param request MPC 规划请求
     * @return 任务ID
     */
    public String submitMpcPlanning(MpcPlanRequest request) {
        String taskId = IdUtil.fastUuid();

        if (mockEnabled) {
            MockContext.setMockMode();
            return submitMpcPlanningMock(taskId, request);
        }

        return submitMpcPlanningDb(taskId, request);
    }

    /**
     * 获取 MPC 规划状态
     *
     * @param taskId 任务ID
     * @return 规划任务
     */
    public PlanningTask getMpcStatus(String taskId) {
        if (mockEnabled) {
            MockContext.setMockMode();
            MpcTaskContext ctx = taskContextStore.get(taskId);
            if (ctx == null) {
                return null;
            }
            PlanningTask task = new PlanningTask();
            task.setTaskId(taskId);
            task.setAlgorithmType("MPC");
            task.setStatus(ctx.status.getName());
            task.setProgress(ctx.progress);
            task.setCreatedAt(ctx.createdAt);
            task.setStartedAt(ctx.startedAt);
            task.setCompletedAt(ctx.completedAt);
            return task;
        }

        // 非 mock 模式下从 Redis 获取状态
        TaskStatus status = taskStatusSyncService.getTaskStatus(taskId);
        if (status == null) {
            return null;
        }
        PlanningTask task = new PlanningTask();
        task.setTaskId(taskId);
        task.setAlgorithmType("MPC");
        task.setStatus(status.getName());
        return task;
    }

    /**
     * 获取 MPC 规划结果（最新航段）
     *
     * @param taskId 任务ID
     * @return MPC 结果
     */
    public MpcResult getMpcResult(String taskId) {
        if (mockEnabled) {
            MockContext.setMockMode();
            MpcTaskContext ctx = taskContextStore.get(taskId);
            if (ctx == null) {
                return null;
            }
            return ctx.currentResult;
        }
        // 非 mock 模式下从 Redis 获取结果
        var resultMsg = taskStatusSyncService.waitForResult(taskId, 2, java.util.concurrent.TimeUnit.SECONDS);
        if (resultMsg == null) {
            return null;
        }
        return parseMpcResult(taskId, resultMsg.getResult());
    }

    /**
     * 更新实时位置（判断是否需要重规划）
     *
     * @param request 位置更新请求
     * @return 更新响应
     */
    public MpcUpdateResponse updatePosition(MpcPositionUpdate request) {
        MpcUpdateResponse response = new MpcUpdateResponse();
        String taskId = request.getTaskId();

        if (taskId == null || taskId.isEmpty()) {
            response.setReplanTriggered(false);
            response.setReason("No active MPC task");
            return response;
        }

        MpcTaskContext ctx = mockEnabled ? taskContextStore.get(taskId) : null;
        if (ctx == null && mockEnabled) {
            response.setReplanTriggered(false);
            response.setReason("MPC task not found: " + taskId);
            return response;
        }

        // 判断是否需要重规划
        boolean shouldReplan = evaluateReplanTrigger(request, ctx);
        response.setReplanTriggered(shouldReplan);

        if (shouldReplan) {
            String reason = determineReplanReason(request, ctx);
            response.setReason(reason);

            if (mockEnabled) {
                triggerReplanMock(taskId, request, ctx);
            } else {
                triggerReplanKafka(taskId, request);
            }

            // 计算下次重规划时间
            double interval = ctx != null ? ctx.replanIntervalSeconds : 30.0;
            String nextReplanTime = LocalDateTime.now()
                    .plusSeconds((long) interval)
                    .format(DateTimeFormatter.ISO_LOCAL_DATE_TIME);
            response.setNextReplanTime(nextReplanTime);
        } else {
            response.setReason("No replan needed");
        }

        return response;
    }

    /**
     * 取消 MPC 任务
     *
     * @param taskId 任务ID
     * @return 是否成功取消
     */
    public boolean cancelMpc(String taskId) {
        if (mockEnabled) {
            MockContext.setMockMode();
            MpcTaskContext ctx = taskContextStore.remove(taskId);
            if (ctx == null) {
                return false;
            }
            if (ctx.status.isTerminal()) {
                return false;
            }
            ctx.status = TaskStatus.CANCELLED;
            ctx.completedAt = LocalDateTime.now();
            return true;
        }
        // 非 mock 模式下清理 Redis
        taskStatusSyncService.cleanup(taskId);
        return true;
    }

    // ===== 数据库 + Kafka 路径（mock=false） =====

    private String submitMpcPlanningDb(String taskId, MpcPlanRequest request) {
        // 初始化 Redis 状态
        taskStatusSyncService.initTaskStatus(taskId, "MPC", "1");

        // 构建 Kafka 消息参数
        Map<String, Object> params = new HashMap<>();
        params.put("uavId", request.getUavId());
        params.put("waypoints", request.getWaypoints());
        params.put("constraints", request.getConstraints());
        params.put("optimizationTarget", request.getOptimizationTarget() != null
                ? request.getOptimizationTarget() : "RISK");

        AlgorithmTaskMessage taskMessage = AlgorithmTaskMessage.builder()
                .taskId(taskId)
                .algorithmId("MPC")
                .params(params)
                .tenantId("1")
                .build();
        algorithmTaskProducer.sendTask(taskMessage);

        log.info("MPC 规划任务已提交到 Kafka, taskId={}, uavId={}", taskId, request.getUavId());
        return taskId;
    }

    private void triggerReplanKafka(String taskId, MpcPositionUpdate request) {
        Map<String, Object> params = new HashMap<>();
        params.put("uavId", request.getUavId());
        params.put("taskId", request.getTaskId());
        params.put("currentPosition", Map.of(
                "longitude", request.getLongitude(),
                "latitude", request.getLatitude(),
                "altitude", request.getAltitude(),
                "speed", request.getSpeed(),
                "heading", request.getHeading()
        ));
        params.put("replan", true);

        AlgorithmTaskMessage taskMessage = AlgorithmTaskMessage.builder()
                .taskId(taskId)
                .algorithmId("MPC")
                .params(params)
                .tenantId("1")
                .build();
        algorithmTaskProducer.sendTask(taskMessage);

        log.info("MPC 重规划任务已发送到 Kafka, taskId={}", taskId);
    }

    // ===== 内存模拟路径（mock=true） =====

    private String submitMpcPlanningMock(String taskId, MpcPlanRequest request) {
        MpcTaskContext ctx = new MpcTaskContext();
        ctx.taskId = taskId;
        ctx.uavId = request.getUavId();
        ctx.waypoints = request.getWaypoints();
        ctx.constraints = request.getConstraints();
        ctx.optimizationTarget = request.getOptimizationTarget() != null
                ? request.getOptimizationTarget() : "RISK";
        ctx.replanIntervalSeconds = request.getConstraints().getReplanIntervalSeconds() != null
                ? request.getConstraints().getReplanIntervalSeconds() : 30.0;
        ctx.horizonSteps = request.getConstraints().getHorizonSteps() != null
                ? request.getConstraints().getHorizonSteps() : 10;
        ctx.status = TaskStatus.RUNNING;
        ctx.progress = 0;
        ctx.createdAt = LocalDateTime.now();
        ctx.startedAt = LocalDateTime.now();
        ctx.lastReplanTime = LocalDateTime.now();
        ctx.lastPosition = null;

        taskContextStore.put(taskId, ctx);

        // 异步模拟初始规划
        executeMpcPlanningAsync(taskId, ctx);

        log.info("MPC 规划任务已创建(mock), taskId={}, uavId={}", taskId, request.getUavId());
        return taskId;
    }

    @Async
    public void executeMpcPlanningAsync(String taskId, MpcTaskContext ctx) {
        try {
            for (int i = 10; i <= 90; i += 20) {
                if (ctx.status == TaskStatus.CANCELLED) {
                    return;
                }
                ctx.progress = i;
                Thread.sleep(200);
            }

            // 生成模拟结果
            ctx.currentResult = generateMockResult(taskId, ctx);
            ctx.progress = 100;
            ctx.status = TaskStatus.RUNNING; // MPC 任务保持 RUNNING 状态，等待位置更新触发重规划
            log.info("MPC 初始规划完成(mock), taskId={}", taskId);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            ctx.status = TaskStatus.FAILED;
            log.error("MPC 规划被中断(mock), taskId={}", taskId, e);
        }
    }

    private void triggerReplanMock(String taskId, MpcPositionUpdate request, MpcTaskContext ctx) {
        // 更新上下文
        ctx.lastPosition = request;
        ctx.lastReplanTime = LocalDateTime.now();

        // 异步执行重规划
        Thread.ofVirtual().start(() -> {
            try {
                ctx.progress = 50;
                Thread.sleep(300);
                ctx.currentResult = generateMockResult(taskId, ctx);
                ctx.progress = 100;
                log.info("MPC 重规划完成(mock), taskId={}, reason=position update", taskId);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        });
    }

    // ===== 重规划判断逻辑 =====

    /**
     * 判断是否需要触发重规划
     */
    private boolean evaluateReplanTrigger(MpcPositionUpdate request, MpcTaskContext ctx) {
        if (ctx == null) {
            return false;
        }

        // 检查任务是否已终态
        if (ctx.status.isTerminal()) {
            return false;
        }

        // 1. 时间间隔到达
        if (ctx.lastReplanTime != null) {
            long elapsedSeconds = java.time.Duration.between(ctx.lastReplanTime, LocalDateTime.now()).getSeconds();
            if (elapsedSeconds >= ctx.replanIntervalSeconds) {
                return true;
            }
        }

        // 2. 位置偏离阈值（模拟：偏离超过 0.005 度）
        if (ctx.lastPosition != null && ctx.currentResult != null) {
            MpcResult result = ctx.currentResult;
            if (!result.getSegments().isEmpty()) {
                MpcResult.MpcSegment firstSegment = result.getSegments().get(0);
                double deviation = calculateDeviation(
                        request.getLongitude(), request.getLatitude(),
                        firstSegment.getStartLon(), firstSegment.getStartLat());
                if (deviation > 0.005) {
                    return true;
                }
            }
        }

        // 3. 风险变化（模拟：随机触发）
        if (ThreadLocalRandom.current().nextDouble() < 0.05) {
            return true;
        }

        return false;
    }

    /**
     * 确定重规划原因
     */
    private String determineReplanReason(MpcPositionUpdate request, MpcTaskContext ctx) {
        if (ctx.lastReplanTime != null) {
            long elapsedSeconds = java.time.Duration.between(ctx.lastReplanTime, LocalDateTime.now()).getSeconds();
            if (elapsedSeconds >= ctx.replanIntervalSeconds) {
                return "REPLAN_INTERVAL_REACHED";
            }
        }

        if (ctx.lastPosition != null && ctx.currentResult != null && !ctx.currentResult.getSegments().isEmpty()) {
            MpcResult.MpcSegment firstSegment = ctx.currentResult.getSegments().get(0);
            double deviation = calculateDeviation(
                    request.getLongitude(), request.getLatitude(),
                    firstSegment.getStartLon(), firstSegment.getStartLat());
            if (deviation > 0.005) {
                return "DEVIATION_THRESHOLD_EXCEEDED";
            }
        }

        return "RISK_CHANGE_DETECTED";
    }

    private double calculateDeviation(double lon1, double lat1, double lon2, double lat2) {
        return Math.sqrt(Math.pow(lon1 - lon2, 2) + Math.pow(lat1 - lat2, 2));
    }

    // ===== 模拟结果生成 =====

    private MpcResult generateMockResult(String taskId, MpcTaskContext ctx) {
        MpcResult result = new MpcResult();
        result.setTaskId(taskId);

        List<MpcResult.MpcSegment> segments = new ArrayList<>();
        int steps = Math.min(ctx.horizonSteps, ctx.waypoints.size() - 1);
        if (steps < 1) {
            steps = 1;
        }

        for (int i = 0; i < steps; i++) {
            MpcResult.MpcSegment segment = new MpcResult.MpcSegment();
            if (i < ctx.waypoints.size() - 1) {
                MpcPlanRequest.Waypoint from = ctx.waypoints.get(i);
                MpcPlanRequest.Waypoint to = ctx.waypoints.get(i + 1);
                segment.setStartLon(from.getLongitude() + ThreadLocalRandom.current().nextDouble(-0.001, 0.001));
                segment.setStartLat(from.getLatitude() + ThreadLocalRandom.current().nextDouble(-0.001, 0.001));
                segment.setEndLon(to.getLongitude() + ThreadLocalRandom.current().nextDouble(-0.001, 0.001));
                segment.setEndLat(to.getLatitude() + ThreadLocalRandom.current().nextDouble(-0.001, 0.001));
                segment.setAltitude(from.getAltitude() != null ? from.getAltitude() : 100.0);
                segment.setSpeed(from.getSpeed() != null ? from.getSpeed() : 15.0);
                segment.setRiskScore(ThreadLocalRandom.current().nextDouble(5, 30));
            }
            segments.add(segment);
        }

        result.setSegments(segments);
        result.setTotalRisk(ThreadLocalRandom.current().nextDouble(10, 50));
        result.setEstimatedEnergy(ThreadLocalRandom.current().nextDouble(30, 120));
        result.setRemainingWaypoints(Math.max(0, ctx.waypoints.size() - steps));
        result.setNextReplanTime(LocalDateTime.now()
                .plusSeconds((long) ctx.replanIntervalSeconds)
                .format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));

        return result;
    }

    private MpcResult parseMpcResult(String taskId, Object resultData) {
        try {
            if (resultData == null) {
                return null;
            }
            String json = resultData instanceof String ? (String) resultData : objectMapper.writeValueAsString(resultData);
            return objectMapper.readValue(json, MpcResult.class);
        } catch (JsonProcessingException e) {
            log.error("解析 MPC 结果失败, taskId={}", taskId, e);
            return null;
        }
    }

    // ===== 内部上下文类 =====

    /**
     * MPC 任务运行时上下文（mock 模式使用）
     */
    private static class MpcTaskContext {
        String taskId;
        String uavId;
        List<MpcPlanRequest.Waypoint> waypoints;
        MpcPlanRequest.MpcConstraints constraints;
        String optimizationTarget;
        double replanIntervalSeconds;
        int horizonSteps;
        TaskStatus status;
        int progress;
        LocalDateTime createdAt;
        LocalDateTime startedAt;
        LocalDateTime completedAt;
        LocalDateTime lastReplanTime;
        MpcPositionUpdate lastPosition;
        MpcResult currentResult;
    }
}

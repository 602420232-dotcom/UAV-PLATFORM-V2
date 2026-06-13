package com.uav.planning.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.common.core.constant.TaskStatus;
import com.uav.common.core.context.MockContext;
import com.uav.common.core.result.ResultCode;
import com.uav.common.core.statemachine.TaskStateMachine;
import com.uav.common.core.util.IdUtil;
import com.uav.common.kafka.message.AlgorithmTaskMessage;
import com.uav.common.kafka.producer.AlgorithmTaskProducer;
import com.uav.common.kafka.service.TaskStatusSyncService;
import com.uav.planning.dto.PlanMissionRequest;
import com.uav.planning.dto.PlanPathRequest;
import com.uav.planning.entity.MissionPlan;
import com.uav.planning.entity.PathResult;
import com.uav.planning.entity.PlanningTask;
import com.uav.planning.mapper.MissionPlanMapper;
import com.uav.planning.mapper.PathResultMapper;
import com.uav.planning.mapper.PlanningTaskMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 规划服务
 * <p>
 * 通过 {@code uav.mock.enabled} 开关控制：
 * <ul>
 *   <li>true（默认）: 使用内存模拟（现有逻辑保留）</li>
 *   <li>false: 使用数据库持久化 + Kafka 调度算法引擎</li>
 * </ul>
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class PlanningService {

    private final RedisTemplate<String, Object> redisTemplate;
    private final ObjectMapper objectMapper;
    private final PlanningTaskMapper taskMapper;
    private final PathResultMapper pathResultMapper;
    private final MissionPlanMapper missionPlanMapper;
    private final AlgorithmTaskProducer algorithmTaskProducer;
    private final TaskStatusSyncService taskStatusSyncService;
    private final TaskStateMachine taskStateMachine;

    @Value("${uav.mock.enabled:true}")
    private boolean mockEnabled;

    // ===== 内存模拟存储（mock=true 时使用） =====
    private final AtomicLong idGenerator = new AtomicLong(1);
    private final Map<Long, PlanningTask> taskStore = new ConcurrentHashMap<>();
    private final Map<Long, PathResult> pathResultStore = new ConcurrentHashMap<>();
    private final Map<Long, MissionPlan> missionPlanStore = new ConcurrentHashMap<>();

    /**
     * 提交路径规划任务
     */
    public PlanningTask submitPathPlanning(PlanPathRequest request) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return submitPathPlanningMock(request);
        }
        return submitPathPlanningDb(request);
    }

    /**
     * 提交任务规划
     */
    public PlanningTask submitMissionPlanning(PlanMissionRequest request) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return submitMissionPlanningMock(request);
        }
        return submitMissionPlanningDb(request);
    }

    /**
     * 获取任务状态
     */
    public PlanningTask getTaskStatus(Long taskId) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return taskStore.get(taskId);
        }
        return taskMapper.selectById(taskId);
    }

    /**
     * 通过业务 taskId（String）获取任务状态
     */
    public PlanningTask getTaskStatusByTaskId(String taskIdStr) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return taskStore.values().stream()
                    .filter(t -> String.valueOf(t.getId()).equals(taskIdStr))
                    .findFirst()
                    .orElse(null);
        }
        LambdaQueryWrapper<PlanningTask> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(PlanningTask::getTaskId, taskIdStr);
        return taskMapper.selectOne(wrapper);
    }

    /**
     * 获取路径规划结果
     */
    public PathResult getPathResult(Long taskId) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return pathResultStore.get(taskId);
        }
        PlanningTask task = taskMapper.selectById(taskId);
        if (task == null) {
            return null;
        }
        LambdaQueryWrapper<PathResult> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(PathResult::getTaskId, task.getTaskId());
        return pathResultMapper.selectOne(wrapper);
    }

    /**
     * 获取任务规划结果
     */
    public MissionPlan getMissionPlan(Long taskId) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return missionPlanStore.get(taskId);
        }
        PlanningTask task = taskMapper.selectById(taskId);
        if (task == null) {
            return null;
        }
        LambdaQueryWrapper<MissionPlan> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(MissionPlan::getTaskId, task.getTaskId());
        return missionPlanMapper.selectOne(wrapper);
    }

    /**
     * 列出所有任务
     */
    public List<PlanningTask> listTasks() {
        if (mockEnabled) {
            MockContext.setMockMode();
            return new ArrayList<>(taskStore.values());
        }
        LambdaQueryWrapper<PlanningTask> wrapper = new LambdaQueryWrapper<>();
        wrapper.orderByDesc(PlanningTask::getCreatedAt);
        return taskMapper.selectList(wrapper);
    }

    /**
     * 取消任务
     */
    public boolean cancelTask(Long taskId) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return cancelTaskMock(taskId);
        }
        return cancelTaskDb(taskId);
    }

    // ===== 数据库 + Kafka 路径（mock=false） =====

    private PlanningTask submitPathPlanningDb(PlanPathRequest request) {
        String taskIdStr = IdUtil.fastUuid();
        PlanningTask task = new PlanningTask();
        task.setTaskId(taskIdStr);
        task.setAlgorithmType(detectAlgorithm(request));
        task.setStatus(TaskStatus.QUEUED.getName());
        task.setProgress(0);
        task.setTenantId("1");
        task.setCreatedAt(LocalDateTime.now());

        try {
            task.setParamsJson(objectMapper.writeValueAsString(request));
        } catch (JsonProcessingException e) {
            log.error("序列化路径规划参数失败", e);
            throw new RuntimeException("参数序列化失败", e);
        }

        taskMapper.insert(task);

        // 初始化 Redis 状态
        taskStatusSyncService.initTaskStatus(taskIdStr, task.getAlgorithmType(), task.getTenantId());

        // 发送 Kafka 任务到 Python 引擎
        Map<String, Object> params = new HashMap<>();
        params.put("start", request.getStart());
        params.put("end", request.getEnd());
        params.put("waypoints", request.getWaypoints());
        params.put("uavModel", request.getUavModel());
        params.put("constraints", request.getConstraints());
        params.put("optimizationTarget", request.getOptimizationTarget());

        AlgorithmTaskMessage taskMessage = AlgorithmTaskMessage.builder()
                .taskId(taskIdStr)
                .algorithmId(task.getAlgorithmType())
                .params(params)
                .tenantId(task.getTenantId())
                .build();
        algorithmTaskProducer.sendTask(taskMessage);

        log.info("路径规划任务已提交到数据库和Kafka, taskId={}, algorithm={}", taskIdStr, task.getAlgorithmType());
        return task;
    }

    private PlanningTask submitMissionPlanningDb(PlanMissionRequest request) {
        String taskIdStr = IdUtil.fastUuid();
        PlanningTask task = new PlanningTask();
        task.setTaskId(taskIdStr);
        task.setAlgorithmType("VRPTW");
        task.setStatus(TaskStatus.QUEUED.getName());
        task.setProgress(0);
        task.setTenantId("1");
        task.setCreatedAt(LocalDateTime.now());

        try {
            task.setParamsJson(objectMapper.writeValueAsString(request));
        } catch (JsonProcessingException e) {
            log.error("序列化任务规划参数失败", e);
            throw new RuntimeException("参数序列化失败", e);
        }

        taskMapper.insert(task);

        // 初始化 Redis 状态
        taskStatusSyncService.initTaskStatus(taskIdStr, "VRPTW", task.getTenantId());

        // 发送 Kafka 任务到 Python 引擎
        Map<String, Object> params = new HashMap<>();
        params.put("uavList", request.getUavList());
        params.put("taskList", request.getTaskList());
        params.put("areaBounds", request.getAreaBounds());
        params.put("priorities", request.getPriorities());

        AlgorithmTaskMessage taskMessage = AlgorithmTaskMessage.builder()
                .taskId(taskIdStr)
                .algorithmId("VRPTW")
                .params(params)
                .tenantId(task.getTenantId())
                .build();
        algorithmTaskProducer.sendTask(taskMessage);

        log.info("任务规划已提交到数据库和Kafka, taskId={}", taskIdStr);
        return task;
    }

    private boolean cancelTaskDb(Long taskId) {
        PlanningTask task = taskMapper.selectById(taskId);
        if (task == null) {
            return false;
        }
        TaskStatus currentStatus = TaskStatus.fromName(task.getStatus());
        if (!taskStateMachine.canTransition(currentStatus, TaskStatus.CANCELLED)) {
            return false;
        }
        task.setStatus(TaskStatus.CANCELLED.getName());
        task.setCompletedAt(LocalDateTime.now());
        task.setErrorMsg("任务已被用户取消");
        taskMapper.updateById(task);
        return true;
    }

    // ===== 内存模拟路径（mock=true，保留原有逻辑） =====

    private PlanningTask submitPathPlanningMock(PlanPathRequest request) {
        Long taskId = idGenerator.getAndIncrement();
        PlanningTask task = new PlanningTask();
        task.setId(taskId);
        task.setAlgorithmType(detectAlgorithm(request));
        task.setStatus(TaskStatus.QUEUED.getName());
        task.setParamsJson(toJson(request));
        task.setProgress(0);
        task.setTenantId("1");
        task.setCreatedAt(LocalDateTime.now());

        taskStore.put(taskId, task);
        executePathPlanningAsync(taskId, request);
        return task;
    }

    private PlanningTask submitMissionPlanningMock(PlanMissionRequest request) {
        Long taskId = idGenerator.getAndIncrement();
        PlanningTask task = new PlanningTask();
        task.setId(taskId);
        task.setAlgorithmType("VRPTW");
        task.setStatus(TaskStatus.QUEUED.getName());
        task.setParamsJson(toJson(request));
        task.setProgress(0);
        task.setTenantId("1");
        task.setCreatedAt(LocalDateTime.now());

        taskStore.put(taskId, task);
        executeMissionPlanningAsync(taskId, request);
        return task;
    }

    private boolean cancelTaskMock(Long taskId) {
        PlanningTask task = taskStore.get(taskId);
        if (task == null) {
            return false;
        }
        TaskStatus currentStatus = TaskStatus.fromName(task.getStatus());
        if (!taskStateMachine.canTransition(currentStatus, TaskStatus.CANCELLED)) {
            return false;
        }
        task.setStatus(TaskStatus.CANCELLED.getName());
        task.setCompletedAt(LocalDateTime.now());
        task.setErrorMsg("任务已被用户取消");
        return true;
    }

    // ===== 异步执行（mock 模式） =====

    @Async
    public void executePathPlanningAsync(Long taskId, PlanPathRequest request) {
        PlanningTask task = taskStore.get(taskId);
        if (task == null) {
            return;
        }
        task.setStatus(TaskStatus.RUNNING.getName());
        task.setStartedAt(LocalDateTime.now());

        try {
            for (int i = 10; i <= 90; i += 20) {
                if (TaskStatus.CANCELLED.getName().equals(task.getStatus())) {
                    return;
                }
                task.setProgress(i);
                Thread.sleep(300);
            }

            PathResult result = simulatePathResult(taskId, request);
            pathResultStore.put(taskId, result);

            task.setStatus(TaskStatus.SUCCESS.getName());
            task.setProgress(100);
            task.setResultJson(toJson(result));
            task.setCompletedAt(LocalDateTime.now());
            log.info("路径规划任务完成: taskId={}, algorithm={}", taskId, task.getAlgorithmType());
        } catch (Exception e) {
            task.setStatus(TaskStatus.FAILED.getName());
            task.setErrorMsg(e.getMessage());
            task.setCompletedAt(LocalDateTime.now());
            log.error("路径规划任务失败: taskId={}", taskId, e);
        }
    }

    @Async
    public void executeMissionPlanningAsync(Long taskId, PlanMissionRequest request) {
        PlanningTask task = taskStore.get(taskId);
        if (task == null) {
            return;
        }
        task.setStatus(TaskStatus.RUNNING.getName());
        task.setStartedAt(LocalDateTime.now());

        try {
            for (int i = 10; i <= 90; i += 15) {
                if (TaskStatus.CANCELLED.getName().equals(task.getStatus())) {
                    return;
                }
                task.setProgress(i);
                Thread.sleep(400);
            }

            MissionPlan plan = simulateMissionPlan(taskId, request);
            missionPlanStore.put(taskId, plan);

            task.setStatus(TaskStatus.SUCCESS.getName());
            task.setProgress(100);
            task.setResultJson(toJson(plan));
            task.setCompletedAt(LocalDateTime.now());
            log.info("任务规划完成: taskId={}", taskId);
        } catch (Exception e) {
            task.setStatus(TaskStatus.FAILED.getName());
            task.setErrorMsg(e.getMessage());
            task.setCompletedAt(LocalDateTime.now());
            log.error("任务规划失败: taskId={}", taskId, e);
        }
    }

    // ===== 模拟结果生成 =====

    private PathResult simulatePathResult(Long taskId, PlanPathRequest request) {
        PathResult result = new PathResult();
        result.setId(taskId);
        result.setTaskId(String.valueOf(taskId));

        List<Map<String, Object>> waypoints = new ArrayList<>();
        Map<String, Double> start = request.getStart();
        Map<String, Double> end = request.getEnd();

        int steps = 10;
        for (int i = 0; i <= steps; i++) {
            double t = (double) i / steps;
            Map<String, Object> wp = Map.of(
                    "lon", lerp(start.get("lon"), end.get("lon"), t) + ThreadLocalRandom.current().nextDouble(-0.001, 0.001),
                    "lat", lerp(start.get("lat"), end.get("lat"), t) + ThreadLocalRandom.current().nextDouble(-0.001, 0.001),
                    "alt", lerp(start.getOrDefault("alt", 100.0), end.getOrDefault("alt", 100.0), t),
                    "speed", 15.0 + ThreadLocalRandom.current().nextDouble(-2, 2),
                    "time", t * 300
            );
            waypoints.add(wp);
        }
        result.setWaypointsJson(toJson(waypoints));
        result.setTotalDistance(1500.0 + ThreadLocalRandom.current().nextDouble(500));
        result.setEstimatedTime(300 + (int) ThreadLocalRandom.current().nextDouble(100));
        result.setRiskScore(ThreadLocalRandom.current().nextDouble(10, 40));
        result.setEnergyConsumption(ThreadLocalRandom.current().nextDouble(50, 150));
        return result;
    }

    private MissionPlan simulateMissionPlan(Long taskId, PlanMissionRequest request) {
        MissionPlan plan = new MissionPlan();
        plan.setId(taskId);
        plan.setTaskId(String.valueOf(taskId));
        plan.setUavsJson(toJson(request.getUavList()));
        plan.setTasksJson(toJson(request.getTaskList()));

        List<Map<String, Object>> schedule = new ArrayList<>();
        for (int i = 0; i < request.getTaskList().size(); i++) {
            Map<String, Object> entry = Map.of(
                    "taskIndex", i,
                    "uavIndex", i % request.getUavList().size(),
                    "startTime", i * 600,
                    "endTime", (i + 1) * 600
            );
            schedule.add(entry);
        }
        plan.setScheduleJson(toJson(schedule));
        plan.setOverallScore(85.0 + ThreadLocalRandom.current().nextDouble(10));
        plan.setTenantId("1");
        plan.setCreatedAt(LocalDateTime.now());
        return plan;
    }

    private String detectAlgorithm(PlanPathRequest request) {
        String target = request.getOptimizationTarget();
        if (request.getWaypoints() != null && !request.getWaypoints().isEmpty()) {
            return "VRPTW";
        }
        return switch (target != null ? target.toUpperCase() : "BALANCED") {
            case "RISK" -> "DERRTSTAR";
            case "ENERGY" -> "MPC";
            case "TIME" -> "A_STAR";
            default -> "RRTSTAR";
        };
    }

    private double lerp(double a, double b, double t) {
        return a + (b - a) * t;
    }

    private String toJson(Object obj) {
        try {
            return objectMapper.writeValueAsString(obj);
        } catch (JsonProcessingException e) {
            log.warn("JSON 序列化失败", e);
            return "{}";
        }
    }
}

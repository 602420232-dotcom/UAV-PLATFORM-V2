package com.uav.assimilation.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.assimilation.dto.SubmitTaskRequest;
import com.uav.assimilation.dto.TaskQueryRequest;
import com.uav.assimilation.entity.AssimilationResult;
import com.uav.assimilation.entity.AssimilationTask;
import com.uav.assimilation.mapper.AssimilationResultMapper;
import com.uav.assimilation.mapper.AssimilationTaskMapper;
import com.uav.common.core.constant.TaskStatus;
import com.uav.common.core.context.MockContext;
import com.uav.common.core.result.Result;
import com.uav.common.core.statemachine.TaskStateMachine;
import com.uav.common.kafka.message.AlgorithmTaskMessage;
import com.uav.common.kafka.producer.AlgorithmTaskProducer;
import com.uav.common.kafka.service.TaskStatusSyncService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 数据同化服务
 * <p>
 * 通过 {@code uav.mock.enabled} 控制是否使用模拟数据:
 * <ul>
 *   <li>mock=true: 使用内存存储（现有逻辑保留）</li>
 *   <li>mock=false: 使用数据库持久化 + Kafka 调用 Python 算法引擎</li>
 * </ul>
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AssimilationService {

    private static final String TASK_STATUS_KEY_PREFIX = "assimilation:task:status:";
    private static final String TASK_RESULT_KEY_PREFIX = "assimilation:task:result:";
    private static final long TASK_STATUS_TTL_SECONDS = 3600;

    private final AssimilationTaskMapper taskMapper;
    private final AssimilationResultMapper resultMapper;
    private final StringRedisTemplate redisTemplate;
    private final ObjectMapper objectMapper;
    private final AlgorithmTaskProducer algorithmTaskProducer;
    private final TaskStatusSyncService taskStatusSyncService;
    private final TaskStateMachine taskStateMachine;

    @Value("${uav.mock.enabled:true}")
    private boolean mockEnabled;

    // ========== 内存存储（mock 模式） ==========

    private final ConcurrentHashMap<Long, AssimilationTask> mockTaskStore = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<Long, AssimilationResult> mockResultStore = new ConcurrentHashMap<>();
    private final AtomicLong mockIdGenerator = new AtomicLong(1);

    // ========== 公共方法 ==========

    /**
     * 提交同化任务
     */
    public Result<Long> submitTask(SubmitTaskRequest request) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return submitTaskMock(request);
        }
        return submitTaskReal(request);
    }

    /**
     * 查询任务状态
     */
    public Result<AssimilationTask> getTaskStatus(Long taskId) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return getTaskStatusMock(taskId);
        }
        return getTaskStatusReal(taskId);
    }

    /**
     * 查询任务结果
     */
    public Result<AssimilationResult> getTaskResult(Long taskId) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return getTaskResultMock(taskId);
        }
        return getTaskResultReal(taskId);
    }

    /**
     * 查询任务列表
     */
    public Result<Page<AssimilationTask>> listTasks(TaskQueryRequest request) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return listTasksMock(request);
        }
        return listTasksReal(request);
    }

    /**
     * 取消任务
     */
    public Result<Void> cancelTask(Long taskId) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return cancelTaskMock(taskId);
        }
        return cancelTaskReal(taskId);
    }

    // ========== Mock 模式实现 ==========

    private Result<Long> submitTaskMock(SubmitTaskRequest request) {
        Long taskId = mockIdGenerator.getAndIncrement();

        AssimilationTask task = new AssimilationTask();
        task.setId(taskId);
        task.setAlgorithmType(request.getAlgorithmType().toUpperCase());
        task.setStatus(TaskStatus.QUEUED.getName());
        task.setProgress(0);
        task.setTenantId(request.getTenantId());
        task.setCreatedAt(LocalDateTime.now());

        try {
            task.setParamsJson(objectMapper.writeValueAsString(request.getParams()));
        } catch (JsonProcessingException e) {
            log.error("序列化参数失败", e);
            return Result.error(500, "参数序列化失败: " + e.getMessage());
        }

        mockTaskStore.put(taskId, task);
        simulateAsyncExecution(taskId);

        log.info("[MOCK] 提交同化任务成功, taskId={}, algorithmType={}", taskId, task.getAlgorithmType());
        return Result.success(taskId);
    }

    private Result<AssimilationTask> getTaskStatusMock(Long taskId) {
        AssimilationTask task = mockTaskStore.get(taskId);
        if (task == null) {
            return Result.error(404, "任务不存在");
        }
        return Result.success(task);
    }

    private Result<AssimilationResult> getTaskResultMock(Long taskId) {
        AssimilationTask task = mockTaskStore.get(taskId);
        if (task == null) {
            return Result.error(404, "任务不存在");
        }
        if (!TaskStatus.SUCCESS.getName().equals(task.getStatus())) {
            return Result.error(400, "任务尚未完成，当前状态: " + task.getStatus());
        }
        AssimilationResult result = mockResultStore.get(taskId);
        if (result == null) {
            return Result.error(404, "结果不存在");
        }
        return Result.success(result);
    }

    private Result<Page<AssimilationTask>> listTasksMock(TaskQueryRequest request) {
        List<AssimilationTask> allTasks = mockTaskStore.values().stream()
                .filter(t -> request.getTaskId() == null || t.getId().equals(request.getTaskId()))
                .filter(t -> request.getStatus() == null || request.getStatus().isEmpty()
                        || t.getStatus().equalsIgnoreCase(request.getStatus()))
                .sorted((a, b) -> b.getCreatedAt().compareTo(a.getCreatedAt()))
                .toList();

        int total = allTasks.size();
        int from = (request.getPage() - 1) * request.getSize();
        int to = Math.min(from + request.getSize(), total);
        List<AssimilationTask> pageList = from < total ? allTasks.subList(from, to) : List.of();

        Page<AssimilationTask> page = new Page<>(request.getPage(), request.getSize(), total);
        page.setRecords(pageList);
        return Result.success(page);
    }

    private Result<Void> cancelTaskMock(Long taskId) {
        AssimilationTask task = mockTaskStore.get(taskId);
        if (task == null) {
            return Result.error(404, "任务不存在");
        }
        TaskStatus currentStatus = TaskStatus.fromName(task.getStatus());
        taskStateMachine.validateTransition(currentStatus, TaskStatus.CANCELLED);
        task.setStatus(TaskStatus.CANCELLED.getName());
        task.setCompletedAt(LocalDateTime.now());
        log.info("[MOCK] 取消同化任务, taskId={}", taskId);
        return Result.success();
    }

    private void simulateAsyncExecution(Long taskId) {
        CompletableFuture.runAsync(() -> {
            try {
                TimeUnit.MILLISECONDS.sleep(500);

                AssimilationTask task = mockTaskStore.get(taskId);
                if (task == null || TaskStatus.CANCELLED.getName().equals(task.getStatus())) {
                    return;
                }

                task.setStatus(TaskStatus.RUNNING.getName());
                task.setStartedAt(LocalDateTime.now());
                task.setProgress(30);

                TimeUnit.MILLISECONDS.sleep(2000);

                task = mockTaskStore.get(taskId);
                if (task == null || TaskStatus.CANCELLED.getName().equals(task.getStatus())) {
                    return;
                }

                task.setStatus(TaskStatus.SUCCESS.getName());
                task.setProgress(100);
                task.setCompletedAt(LocalDateTime.now());
                task.setResultJson("{\"message\":\"模拟同化完成\"}");

                AssimilationResult result = new AssimilationResult();
                result.setTaskId(taskId);
                result.setAnalysisFieldJson("{\"field\":\"simulated_analysis_field\"}");
                result.setUncertaintyJson("{\"uncertainty\":\"simulated_uncertainty\"}");
                result.setConvergenceInfo("{\"iterations\":10,\"residual\":1e-6}");
                result.setCreatedAt(LocalDateTime.now());
                mockResultStore.put(taskId, result);

                log.info("[MOCK] 同化任务执行完成, taskId={}", taskId);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                log.warn("[MOCK] 任务执行被中断, taskId={}", taskId);
                AssimilationTask task = mockTaskStore.get(taskId);
                if (task != null) {
                    task.setStatus(TaskStatus.FAILED.getName());
                    task.setErrorMsg("任务执行被中断");
                    task.setCompletedAt(LocalDateTime.now());
                }
            } catch (Exception e) {
                log.error("[MOCK] 任务执行异常, taskId={}", taskId, e);
                AssimilationTask task = mockTaskStore.get(taskId);
                if (task != null) {
                    task.setStatus(TaskStatus.FAILED.getName());
                    task.setErrorMsg(e.getMessage());
                    task.setCompletedAt(LocalDateTime.now());
                }
            }
        });
    }

    // ========== 真实模式实现（数据库 + Kafka） ==========

    private Result<Long> submitTaskReal(SubmitTaskRequest request) {
        AssimilationTask task = new AssimilationTask();
        task.setAlgorithmType(request.getAlgorithmType().toUpperCase());
        task.setStatus(TaskStatus.QUEUED.getName());
        task.setProgress(0);
        task.setTenantId(request.getTenantId());
        task.setCreatedAt(LocalDateTime.now());

        try {
            task.setParamsJson(objectMapper.writeValueAsString(request.getParams()));
        } catch (JsonProcessingException e) {
            log.error("序列化参数失败", e);
            return Result.error(500, "参数序列化失败: " + e.getMessage());
        }

        taskMapper.insert(task);
        String taskIdStr = String.valueOf(task.getId());

        // 初始化 Redis 状态
        taskStatusSyncService.initTaskStatus(
                taskIdStr,
                task.getAlgorithmType(),
                String.valueOf(request.getTenantId()));

        // 通过 Kafka 发送到 Python 引擎
        AlgorithmTaskMessage kafkaMessage = AlgorithmTaskMessage.builder()
                .taskId(taskIdStr)
                .algorithmId(task.getAlgorithmType())
                .params(request.getParams())
                .tenantId(String.valueOf(request.getTenantId()))
                .build();
        algorithmTaskProducer.sendTask(kafkaMessage);

        // 缓存任务状态到本地 Redis
        cacheTaskStatus(task.getId(), task.getStatus(), task.getProgress());

        log.info("提交同化任务成功, taskId={}, algorithmType={}", task.getId(), task.getAlgorithmType());
        return Result.success(task.getId());
    }

    private Result<AssimilationTask> getTaskStatusReal(Long taskId) {
        // 先查 Redis
        String cachedStatus = redisTemplate.opsForValue().get(TASK_STATUS_KEY_PREFIX + taskId);
        String cachedProgress = redisTemplate.opsForValue()
                .get(TASK_STATUS_KEY_PREFIX + taskId + ":progress");

        AssimilationTask task = taskMapper.selectById(taskId);
        if (task == null) {
            return Result.error(404, "任务不存在");
        }

        if (cachedStatus != null) {
            task.setStatus(cachedStatus);
        }
        if (cachedProgress != null) {
            try {
                task.setProgress(Integer.parseInt(cachedProgress));
            } catch (NumberFormatException ignored) {
                // ignore
            }
        }

        return Result.success(task);
    }

    private Result<AssimilationResult> getTaskResultReal(Long taskId) {
        AssimilationTask task = taskMapper.selectById(taskId);
        if (task == null) {
            return Result.error(404, "任务不存在");
        }

        if (!TaskStatus.SUCCESS.getName().equals(task.getStatus())) {
            return Result.error(400, "任务尚未完成，当前状态: " + task.getStatus());
        }

        // 优先从 Redis 缓存读取
        String cachedResult = redisTemplate.opsForValue().get(TASK_RESULT_KEY_PREFIX + taskId);
        if (cachedResult != null) {
            try {
                AssimilationResult cached = objectMapper.readValue(cachedResult, AssimilationResult.class);
                return Result.success(cached);
            } catch (JsonProcessingException e) {
                log.warn("反序列化缓存结果失败, taskId={}", taskId);
            }
        }

        // 查数据库
        LambdaQueryWrapper<AssimilationResult> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(AssimilationResult::getTaskId, taskId);
        AssimilationResult result = resultMapper.selectOne(wrapper);

        if (result == null) {
            return Result.error(404, "结果不存在");
        }

        return Result.success(result);
    }

    private Result<Page<AssimilationTask>> listTasksReal(TaskQueryRequest request) {
        Page<AssimilationTask> page = new Page<>(request.getPage(), request.getSize());
        LambdaQueryWrapper<AssimilationTask> wrapper = new LambdaQueryWrapper<>();

        if (request.getTaskId() != null) {
            wrapper.eq(AssimilationTask::getId, request.getTaskId());
        }
        if (request.getStatus() != null && !request.getStatus().isEmpty()) {
            wrapper.eq(AssimilationTask::getStatus, request.getStatus().toUpperCase());
        }

        wrapper.orderByDesc(AssimilationTask::getCreatedAt);
        Page<AssimilationTask> resultPage = taskMapper.selectPage(page, wrapper);

        return Result.success(resultPage);
    }

    private Result<Void> cancelTaskReal(Long taskId) {
        AssimilationTask task = taskMapper.selectById(taskId);
        if (task == null) {
            return Result.error(404, "任务不存在");
        }

        TaskStatus currentStatus = TaskStatus.fromName(task.getStatus());
        taskStateMachine.validateTransition(currentStatus, TaskStatus.CANCELLED);

        task.setStatus(TaskStatus.CANCELLED.getName());
        task.setCompletedAt(LocalDateTime.now());
        taskMapper.updateById(task);

        // 更新 Redis
        cacheTaskStatus(taskId, TaskStatus.CANCELLED.getName(), task.getProgress());
        taskStatusSyncService.updateTaskStatus(
                com.uav.common.kafka.message.AlgorithmResultMessage.builder()
                        .taskId(String.valueOf(taskId))
                        .status(TaskStatus.CANCELLED.getName())
                        .progress(task.getProgress() != null ? task.getProgress() : 0)
                        .build());

        log.info("取消同化任务, taskId={}", taskId);
        return Result.success();
    }

    private void cacheTaskStatus(Long taskId, String status, Integer progress) {
        try {
            redisTemplate.opsForValue().set(TASK_STATUS_KEY_PREFIX + taskId, status,
                    TASK_STATUS_TTL_SECONDS, TimeUnit.SECONDS);
            redisTemplate.opsForValue().set(TASK_STATUS_KEY_PREFIX + taskId + ":progress",
                    String.valueOf(progress != null ? progress : 0),
                    TASK_STATUS_TTL_SECONDS, TimeUnit.SECONDS);
        } catch (Exception e) {
            log.warn("缓存任务状态失败, taskId={}", taskId, e);
        }
    }
}

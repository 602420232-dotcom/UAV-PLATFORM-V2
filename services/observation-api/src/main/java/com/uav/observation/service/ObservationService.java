package com.uav.observation.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.common.core.constant.TaskStatus;
import com.uav.common.core.context.MockContext;
import com.uav.common.kafka.message.AlgorithmTaskMessage;
import com.uav.common.kafka.producer.AlgorithmTaskProducer;
import com.uav.common.kafka.service.TaskStatusSyncService;
import com.uav.observation.dto.CreateObservationRequest;
import com.uav.observation.entity.ObservationTask;
import com.uav.observation.mapper.ObservationTaskMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 观测任务服务
 * <p>
 * 通过 {@code uav.mock.enabled} 控制是否使用模拟数据:
 * <ul>
 *   <li>mock=true: 使用内存存储（现有逻辑保留）</li>
 *   <li>mock=false: 使用数据库持久化 + Kafka 调用 Python 算法引擎</li>
 * </ul>
 */
@Slf4j
@Service
public class ObservationService {

    private final RedisTemplate<String, Object> redisTemplate;
    private final StringRedisTemplate stringRedisTemplate;
    private final ObservationTaskMapper taskMapper;
    private final AlgorithmTaskProducer algorithmTaskProducer;
    private final TaskStatusSyncService taskStatusSyncService;
    private final ObjectMapper objectMapper;

    @Value("${uav.mock.enabled:true}")
    private boolean mockEnabled;

    // ========== 内存存储（mock 模式） ==========

    private final ConcurrentHashMap<Long, ObservationTask> mockTaskStore = new ConcurrentHashMap<>();
    private final AtomicLong mockIdGenerator = new AtomicLong(1);

    public ObservationService(RedisTemplate<String, Object> redisTemplate,
                              StringRedisTemplate stringRedisTemplate,
                              ObservationTaskMapper taskMapper,
                              AlgorithmTaskProducer algorithmTaskProducer,
                              TaskStatusSyncService taskStatusSyncService,
                              ObjectMapper objectMapper) {
        this.redisTemplate = redisTemplate;
        this.stringRedisTemplate = stringRedisTemplate;
        this.taskMapper = taskMapper;
        this.algorithmTaskProducer = algorithmTaskProducer;
        this.taskStatusSyncService = taskStatusSyncService;
        this.objectMapper = objectMapper;
    }

    // ========== 公共方法 ==========

    /**
     * 创建观测任务
     */
    public ObservationTask createTask(CreateObservationRequest request) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return createTaskMock(request);
        }
        return createTaskReal(request);
    }

    /**
     * 根据ID获取任务
     */
    public ObservationTask getTask(Long id) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return getTaskMock(id);
        }
        return getTaskReal(id);
    }

    /**
     * 列出所有任务
     */
    public List<ObservationTask> listTasks() {
        if (mockEnabled) {
            MockContext.setMockMode();
            return listTasksMock();
        }
        return listTasksReal();
    }

    /**
     * 更新任务状态
     */
    public ObservationTask updateTaskStatus(Long id, String status) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return updateTaskStatusMock(id, status);
        }
        return updateTaskStatusReal(id, status);
    }

    /**
     * 评估观测数据质量
     */
    public Double evaluateDataQuality(Long id) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return evaluateDataQualityMock(id);
        }
        return evaluateDataQualityReal(id);
    }

    // ========== Mock 模式实现 ==========

    private ObservationTask createTaskMock(CreateObservationRequest request) {
        ObservationTask task = new ObservationTask();
        task.setId(mockIdGenerator.getAndIncrement());
        task.setType(request.getType());
        task.setStatus("PENDING");
        task.setSensorConfigJson(buildSensorConfig(request.getSensorType()));
        task.setPlannedPathJson("[]");
        task.setActualPathJson("[]");
        task.setDataQuality(0.0);
        task.setAssimilationFeedbackJson("{}");
        task.setTenantId("default");
        task.setCreatedAt(LocalDateTime.now());

        mockTaskStore.put(task.getId(), task);

        String cacheKey = buildTaskCacheKey(task.getId());
        redisTemplate.opsForValue().set(cacheKey, task);

        log.info("[MOCK] Created observation task: id={}, type={}, priority={}",
                task.getId(), task.getType(), request.getPriority());
        return task;
    }

    private ObservationTask getTaskMock(Long id) {
        String cacheKey = buildTaskCacheKey(id);
        ObservationTask cached = (ObservationTask) redisTemplate.opsForValue().get(cacheKey);
        if (cached != null) {
            return cached;
        }
        return mockTaskStore.get(id);
    }

    private List<ObservationTask> listTasksMock() {
        return new ArrayList<>(mockTaskStore.values());
    }

    private ObservationTask updateTaskStatusMock(Long id, String status) {
        ObservationTask task = mockTaskStore.get(id);
        if (task == null) {
            log.warn("[MOCK] Task not found: id={}", id);
            return null;
        }
        task.setStatus(status);

        String cacheKey = buildTaskCacheKey(id);
        redisTemplate.opsForValue().set(cacheKey, task);

        log.info("[MOCK] Updated task status: id={}, status={}", id, status);
        return task;
    }

    private Double evaluateDataQualityMock(Long id) {
        ObservationTask task = getTaskMock(id);
        if (task == null) {
            log.warn("[MOCK] Task not found for quality evaluation: id={}", id);
            return null;
        }

        double quality = calculateDataQuality(task);
        task.setDataQuality(quality);

        String cacheKey = buildTaskCacheKey(id);
        redisTemplate.opsForValue().set(cacheKey, task);

        log.info("[MOCK] Evaluated data quality: id={}, quality={}", id, quality);
        return quality;
    }

    // ========== 真实模式实现（数据库 + Kafka） ==========

    private ObservationTask createTaskReal(CreateObservationRequest request) {
        ObservationTask task = new ObservationTask();
        task.setType(request.getType());
        task.setStatus(TaskStatus.QUEUED.getName());
        task.setSensorConfigJson(buildSensorConfig(request.getSensorType()));
        task.setPlannedPathJson("[]");
        task.setActualPathJson("[]");
        task.setDataQuality(0.0);
        task.setAssimilationFeedbackJson("{}");
        task.setTenantId("default");
        task.setCreatedAt(LocalDateTime.now());

        taskMapper.insert(task);

        String taskIdStr = String.valueOf(task.getId());

        // 初始化 Redis 状态
        taskStatusSyncService.initTaskStatus(taskIdStr, "OBSERVATION_" + task.getType(), task.getTenantId());

        // 通过 Kafka 发送到 Python 引擎
        Map<String, Object> params = new HashMap<>();
        params.put("type", task.getType());
        params.put("sensor_type", request.getSensorType());
        params.put("target_area", request.getTargetArea());
        params.put("priority", request.getPriority());

        AlgorithmTaskMessage kafkaMessage = AlgorithmTaskMessage.builder()
                .taskId(taskIdStr)
                .algorithmId("OBSERVATION_" + task.getType())
                .params(params)
                .tenantId(task.getTenantId())
                .build();
        algorithmTaskProducer.sendTask(kafkaMessage);

        // 缓存任务状态
        String cacheKey = buildTaskCacheKey(task.getId());
        redisTemplate.opsForValue().set(cacheKey, task);

        log.info("Created observation task: id={}, type={}, priority={}",
                task.getId(), task.getType(), request.getPriority());
        return task;
    }

    private ObservationTask getTaskReal(Long id) {
        // 先查 Redis 缓存
        String cacheKey = buildTaskCacheKey(id);
        ObservationTask cached = (ObservationTask) redisTemplate.opsForValue().get(cacheKey);
        if (cached != null) {
            return cached;
        }
        // 查数据库
        return taskMapper.selectById(id);
    }

    private List<ObservationTask> listTasksReal() {
        LambdaQueryWrapper<ObservationTask> wrapper = new LambdaQueryWrapper<>();
        wrapper.orderByDesc(ObservationTask::getCreatedAt);
        return taskMapper.selectList(wrapper);
    }

    private ObservationTask updateTaskStatusReal(Long id, String status) {
        ObservationTask task = taskMapper.selectById(id);
        if (task == null) {
            log.warn("Task not found: id={}", id);
            return null;
        }
        task.setStatus(status);
        taskMapper.updateById(task);

        // 更新 Redis
        String cacheKey = buildTaskCacheKey(id);
        redisTemplate.opsForValue().set(cacheKey, task);

        // 同步 Redis 状态
        taskStatusSyncService.updateTaskStatus(
                com.uav.common.kafka.message.AlgorithmResultMessage.builder()
                        .taskId(String.valueOf(id))
                        .status(status)
                        .build());

        log.info("Updated task status: id={}, status={}", id, status);
        return task;
    }

    private Double evaluateDataQualityReal(Long id) {
        ObservationTask task = getTaskReal(id);
        if (task == null) {
            log.warn("Task not found for quality evaluation: id={}", id);
            return null;
        }

        double quality = calculateDataQuality(task);
        task.setDataQuality(quality);
        taskMapper.updateById(task);

        String cacheKey = buildTaskCacheKey(id);
        redisTemplate.opsForValue().set(cacheKey, task);

        log.info("Evaluated data quality: id={}, quality={}", id, quality);
        return quality;
    }

    // ========== 公共工具方法 ==========

    private double calculateDataQuality(ObservationTask task) {
        double baseQuality = 60.0;

        if (task.getSensorConfigJson() != null && !task.getSensorConfigJson().isEmpty()
                && !"{}".equals(task.getSensorConfigJson())) {
            baseQuality += 15.0;
        }

        if (task.getActualPathJson() != null && !task.getActualPathJson().isEmpty()
                && !"[]".equals(task.getActualPathJson())) {
            baseQuality += 15.0;
        }

        if (task.getAssimilationFeedbackJson() != null && !task.getAssimilationFeedbackJson().isEmpty()
                && !"{}".equals(task.getAssimilationFeedbackJson())) {
            baseQuality += 10.0;
        }

        return Math.min(100.0, baseQuality);
    }

    private String buildSensorConfig(String sensorType) {
        return String.format("{\"type\":\"%s\",\"resolution\":\"high\",\"calibrated\":true}", sensorType);
    }

    private String buildTaskCacheKey(Long id) {
        return "observation:task:" + id;
    }
}

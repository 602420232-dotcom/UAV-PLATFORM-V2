package com.uav.observation.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.uav.common.core.context.MockContext;
import com.uav.observation.dto.ObservationDecisionRequest;
import com.uav.observation.entity.ObservationDecision;
import com.uav.observation.mapper.ObservationDecisionMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 观测决策服务
 * <p>
 * 基于信息增益的观测决策引擎，支撑 observation-assimilation-planning 闭环。
 * <p>
 * 通过 {@code uav.mock.enabled} 控制是否使用模拟数据:
 * <ul>
 *   <li>mock=true: 使用内存存储（现有逻辑保留）</li>
 *   <li>mock=false: 使用数据库持久化</li>
 * </ul>
 */
@Slf4j
@Service
public class ObservationDecisionService {

    private final RedisTemplate<String, Object> redisTemplate;
    private final ObservationDecisionMapper decisionMapper;

    @Value("${uav.mock.enabled:true}")
    private boolean mockEnabled;

    // ========== 内存存储（mock 模式） ==========

    private final ConcurrentHashMap<Long, ObservationDecision> mockDecisionStore = new ConcurrentHashMap<>();
    private final AtomicLong mockIdGenerator = new AtomicLong(1);

    public ObservationDecisionService(RedisTemplate<String, Object> redisTemplate,
                                      ObservationDecisionMapper decisionMapper) {
        this.redisTemplate = redisTemplate;
        this.decisionMapper = decisionMapper;
    }

    // ========== 公共方法 ==========

    /**
     * 基于信息增益做出观测决策
     */
    public ObservationDecision makeDecision(ObservationDecisionRequest request) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return makeDecisionMock(request);
        }
        return makeDecisionReal(request);
    }

    /**
     * 获取决策历史
     */
    public List<ObservationDecision> getDecisionHistory() {
        if (mockEnabled) {
            MockContext.setMockMode();
            return getDecisionHistoryMock();
        }
        return getDecisionHistoryReal();
    }

    /**
     * 根据ID获取决策
     */
    public ObservationDecision getDecision(Long id) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return getDecisionMock(id);
        }
        return getDecisionReal(id);
    }

    // ========== Mock 模式实现 ==========

    private ObservationDecision makeDecisionMock(ObservationDecisionRequest request) {
        double expectedInfoGain = calculateExpectedInfoGain(request);
        String decisionType = determineDecisionType(expectedInfoGain, request);
        int priority = determinePriority(expectedInfoGain, request);

        ObservationDecision decision = new ObservationDecision();
        decision.setId(mockIdGenerator.getAndIncrement());
        decision.setDecisionType(decisionType);
        decision.setTargetAreaJson(extractTargetArea(request));
        decision.setPriority(priority);
        decision.setExpectedInfoGain(expectedInfoGain);
        decision.setExecutedAt(LocalDateTime.now());

        mockDecisionStore.put(decision.getId(), decision);

        String cacheKey = buildDecisionCacheKey(decision.getId());
        redisTemplate.opsForValue().set(cacheKey, decision);

        log.info("[MOCK] Made observation decision: id={}, type={}, infoGain={}, priority={}",
                decision.getId(), decisionType, expectedInfoGain, priority);
        return decision;
    }

    private List<ObservationDecision> getDecisionHistoryMock() {
        return new ArrayList<>(mockDecisionStore.values());
    }

    private ObservationDecision getDecisionMock(Long id) {
        String cacheKey = buildDecisionCacheKey(id);
        ObservationDecision cached = (ObservationDecision) redisTemplate.opsForValue().get(cacheKey);
        if (cached != null) {
            return cached;
        }
        return mockDecisionStore.get(id);
    }

    // ========== 真实模式实现（数据库） ==========

    private ObservationDecision makeDecisionReal(ObservationDecisionRequest request) {
        double expectedInfoGain = calculateExpectedInfoGain(request);
        String decisionType = determineDecisionType(expectedInfoGain, request);
        int priority = determinePriority(expectedInfoGain, request);

        ObservationDecision decision = new ObservationDecision();
        decision.setDecisionType(decisionType);
        decision.setTargetAreaJson(extractTargetArea(request));
        decision.setPriority(priority);
        decision.setExpectedInfoGain(expectedInfoGain);
        decision.setExecutedAt(LocalDateTime.now());

        decisionMapper.insert(decision);

        String cacheKey = buildDecisionCacheKey(decision.getId());
        redisTemplate.opsForValue().set(cacheKey, decision);

        log.info("Made observation decision: id={}, type={}, infoGain={}, priority={}",
                decision.getId(), decisionType, expectedInfoGain, priority);
        return decision;
    }

    private List<ObservationDecision> getDecisionHistoryReal() {
        LambdaQueryWrapper<ObservationDecision> wrapper = new LambdaQueryWrapper<>();
        wrapper.orderByDesc(ObservationDecision::getExecutedAt);
        return decisionMapper.selectList(wrapper);
    }

    private ObservationDecision getDecisionReal(Long id) {
        String cacheKey = buildDecisionCacheKey(id);
        ObservationDecision cached = (ObservationDecision) redisTemplate.opsForValue().get(cacheKey);
        if (cached != null) {
            return cached;
        }
        return decisionMapper.selectById(id);
    }

    // ========== 公共工具方法 ==========

    private double calculateExpectedInfoGain(ObservationDecisionRequest request) {
        double baseGain = 0.5;

        String sensors = request.getAvailableSensors();
        if (sensors != null && !sensors.isEmpty()) {
            int sensorCount = countSensors(sensors);
            baseGain += Math.min(0.3, sensorCount * 0.05);
        }

        String constraints = request.getConstraints();
        if (constraints == null || constraints.isEmpty() || "{}".equals(constraints)) {
            baseGain += 0.1;
        }

        double noise = ThreadLocalRandom.current().nextDouble(-0.05, 0.05);

        double finalGain = Math.max(0.0, Math.min(1.0, baseGain + noise));
        return Math.round(finalGain * 1000.0) / 1000.0;
    }

    private String determineDecisionType(double expectedInfoGain, ObservationDecisionRequest request) {
        if (expectedInfoGain > 0.8) {
            return "HIGH_VALUE_TARGET";
        } else if (expectedInfoGain > 0.5) {
            return "ADAPTIVE_SCAN";
        } else if (expectedInfoGain > 0.3) {
            return "ROUTINE_MONITOR";
        } else {
            return "DEFERRED";
        }
    }

    private int determinePriority(double expectedInfoGain, ObservationDecisionRequest request) {
        int basePriority = (int) (expectedInfoGain * 10);

        String constraints = request.getConstraints();
        if (constraints != null && constraints.contains("emergency")) {
            basePriority = Math.min(10, basePriority + 2);
        }

        return Math.max(1, Math.min(10, basePriority));
    }

    private String extractTargetArea(ObservationDecisionRequest request) {
        String currentState = request.getCurrentState();
        if (currentState != null && currentState.contains("targetArea")) {
            return currentState;
        }
        return "{\"region\":\"default\",\"bounds\":[0,0,1,1]}";
    }

    private int countSensors(String sensorsJson) {
        int count = 0;
        for (int i = 0; i < sensorsJson.length(); i++) {
            if (sensorsJson.charAt(i) == '{') {
                count++;
            }
        }
        return Math.max(1, count);
    }

    private String buildDecisionCacheKey(Long id) {
        return "observation:decision:" + id;
    }
}

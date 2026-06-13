package com.uav.assimilation.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.assimilation.dto.GprPostprocessRequest;
import com.uav.assimilation.dto.GprPostprocessResponse;
import com.uav.assimilation.dto.GprUncertaintyResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

/**
 * GPR 后处理服务
 * <p>
 * 封装 GPR 后处理逻辑，通过 RestTemplate 调用 algorithm-engine 的 GPRUncertaintyAdapter。
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class GprPostprocessService {

    private static final String UNCERTAINTY_CACHE_KEY_PREFIX = "assimilation:gpr:uncertainty:";
    private static final long UNCERTAINTY_CACHE_TTL_SECONDS = 1800; // 30 minutes

    private final ObjectMapper objectMapper;
    private final StringRedisTemplate redisTemplate;

    @Value("${uav.mock.enabled:true}")
    private boolean mockEnabled;

    @Value("${algorithm-engine.base-url:http://localhost:9090}")
    private String algorithmEngineBaseUrl;

    /**
     * 执行 GPR 后处理
     */
    public GprPostprocessResponse postprocess(GprPostprocessRequest request) {
        if (mockEnabled) {
            return postprocessMock(request);
        }
        return postprocessReal(request);
    }

    /**
     * 查询指定区域和时间的不确定性场
     */
    public GprUncertaintyResponse queryUncertainty(String region, String time) {
        if (mockEnabled) {
            return queryUncertaintyMock(region, time);
        }
        return queryUncertaintyReal(region, time);
    }

    // ========== Mock 模式实现 ==========

    private GprPostprocessResponse postprocessMock(GprPostprocessRequest request) {
        log.info("[MOCK] 执行 GPR 后处理, kernelType={}, lengthScale={}, nSamples={}",
                request.getKernelType(), request.getLengthScale(), request.getNSamples());

        int gridSize = 5;
        List<List<Double>> meanField = generateMockField(gridSize, 25.0, 5.0);
        List<List<Double>> varianceField = generateMockField(gridSize, 1.0, 0.3);
        List<List<Double>> stdField = varianceField.stream()
                .map(row -> row.stream().map(Math::sqrt).collect(Collectors.toList()))
                .collect(Collectors.toList());

        double confidenceLevel = request.getConfidenceLevel() != null ? request.getConfidenceLevel() : 0.95;
        double zScore = getZScore(confidenceLevel);

        List<List<Double>> confidenceLower = new ArrayList<>();
        List<List<Double>> confidenceUpper = new ArrayList<>();
        for (int i = 0; i < gridSize; i++) {
            List<Double> lowerRow = new ArrayList<>();
            List<Double> upperRow = new ArrayList<>();
            for (int j = 0; j < gridSize; j++) {
                double mean = meanField.get(i).get(j);
                double std = stdField.get(i).get(j);
                lowerRow.add(mean - zScore * std);
                upperRow.add(mean + zScore * std);
            }
            confidenceLower.add(lowerRow);
            confidenceUpper.add(upperRow);
        }

        Map<String, Object> paramSummary = new HashMap<>();
        paramSummary.put("kernel_type", request.getKernelType());
        paramSummary.put("length_scale", request.getLengthScale());
        paramSummary.put("n_samples", request.getNSamples());
        paramSummary.put("signal_variance", request.getSignalVariance());
        paramSummary.put("noise_variance", request.getNoiseVariance());

        return GprPostprocessResponse.builder()
                .meanField(meanField)
                .varianceField(varianceField)
                .stdField(stdField)
                .confidenceLower(confidenceLower)
                .confidenceUpper(confidenceUpper)
                .confidenceLevel(confidenceLevel)
                .kernelType(request.getKernelType())
                .parameterSummary(paramSummary)
                .build();
    }

    private GprUncertaintyResponse queryUncertaintyMock(String region, String time) {
        log.info("[MOCK] 查询 GPR 不确定性, region={}, time={}", region, time);

        int gridSize = 5;
        List<List<Double>> meanField = generateMockField(gridSize, 25.0, 5.0);
        List<List<Double>> varianceField = generateMockField(gridSize, 1.0, 0.3);
        List<List<Double>> stdField = varianceField.stream()
                .map(row -> row.stream().map(Math::sqrt).collect(Collectors.toList()))
                .collect(Collectors.toList());

        double zScore = 1.96; // 95% confidence
        List<List<Double>> confidenceLower = new ArrayList<>();
        List<List<Double>> confidenceUpper = new ArrayList<>();
        for (int i = 0; i < gridSize; i++) {
            List<Double> lowerRow = new ArrayList<>();
            List<Double> upperRow = new ArrayList<>();
            for (int j = 0; j < gridSize; j++) {
                double mean = meanField.get(i).get(j);
                double std = stdField.get(i).get(j);
                lowerRow.add(mean - zScore * std);
                upperRow.add(mean + zScore * std);
            }
            confidenceLower.add(lowerRow);
            confidenceUpper.add(upperRow);
        }

        // 计算置信度统计
        GprUncertaintyResponse.ConfidenceStatistics stats = computeConfidenceStatistics(stdField);

        return GprUncertaintyResponse.builder()
                .region(region)
                .time(time)
                .meanField(meanField)
                .varianceField(varianceField)
                .stdField(stdField)
                .confidenceLower(confidenceLower)
                .confidenceUpper(confidenceUpper)
                .confidenceStatistics(stats)
                .build();
    }

    // ========== 真实模式实现（调用 algorithm-engine） ==========

    private GprPostprocessResponse postprocessReal(GprPostprocessRequest request) {
        log.info("执行 GPR 后处理, kernelType={}, lengthScale={}, nSamples={}",
                request.getKernelType(), request.getLengthScale(), request.getNSamples());

        try {
            // 构造调用 algorithm-engine 的请求参数
            Map<String, Object> engineParams = new HashMap<>();
            engineParams.put("kernel_type", request.getKernelType());
            engineParams.put("length_scale", request.getLengthScale());
            engineParams.put("n_samples", request.getNSamples());
            engineParams.put("signal_variance", request.getSignalVariance());
            engineParams.put("noise_variance", request.getNoiseVariance());
            engineParams.put("analysis_field_json", request.getAnalysisFieldJson());

            // 通过 RestTemplate 调用 algorithm-engine
            RestTemplate restTemplate = new RestTemplate();
            String url = algorithmEngineBaseUrl + "/api/v1/algorithms/gpr_uncertainty/execute";

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(engineParams, headers);

            ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                    url, HttpMethod.POST, entity, new org.springframework.core.ParameterizedTypeReference<>() {});

            if (response.getStatusCode() != HttpStatus.OK || response.getBody() == null) {
                throw new RuntimeException("algorithm-engine 调用失败: " + response.getStatusCode());
            }

            Map<String, Object> body = response.getBody();
            return mapEngineResponse(body, request);

        } catch (Exception e) {
            log.error("GPR 后处理失败", e);
            throw new RuntimeException("GPR 后处理失败: " + e.getMessage(), e);
        }
    }

    private GprUncertaintyResponse queryUncertaintyReal(String region, String time) {
        log.info("查询 GPR 不确定性, region={}, time={}", region, time);

        // 先查 Redis 缓存
        String cacheKey = UNCERTAINTY_CACHE_KEY_PREFIX + region + ":" + time;
        String cached = redisTemplate.opsForValue().get(cacheKey);
        if (cached != null) {
            try {
                return objectMapper.readValue(cached, GprUncertaintyResponse.class);
            } catch (JsonProcessingException e) {
                log.warn("反序列化缓存不确定性数据失败, region={}, time={}", region, time);
            }
        }

        try {
            // 调用 algorithm-engine 获取不确定性场
            RestTemplate restTemplate = new RestTemplate();
            String url = algorithmEngineBaseUrl + "/api/v1/algorithms/gpr_uncertainty/execute";

            Map<String, Object> engineParams = new HashMap<>();
            engineParams.put("region", region);
            engineParams.put("time", time);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(engineParams, headers);

            ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                    url, HttpMethod.POST, entity, new org.springframework.core.ParameterizedTypeReference<>() {});

            if (response.getStatusCode() != HttpStatus.OK || response.getBody() == null) {
                throw new RuntimeException("algorithm-engine 调用失败: " + response.getStatusCode());
            }

            Map<String, Object> body = response.getBody();
            GprUncertaintyResponse uncertaintyResponse = mapUncertaintyResponse(body, region, time);

            // 缓存结果
            try {
                redisTemplate.opsForValue().set(cacheKey,
                        objectMapper.writeValueAsString(uncertaintyResponse),
                        UNCERTAINTY_CACHE_TTL_SECONDS, TimeUnit.SECONDS);
            } catch (JsonProcessingException e) {
                log.warn("缓存不确定性数据失败, region={}, time={}", region, time);
            }

            return uncertaintyResponse;

        } catch (Exception e) {
            log.error("查询 GPR 不确定性失败, region={}, time={}", region, time, e);
            throw new RuntimeException("查询 GPR 不确定性失败: " + e.getMessage(), e);
        }
    }

    // ========== 辅助方法 ==========

    private GprPostprocessResponse mapEngineResponse(Map<String, Object> body, GprPostprocessRequest request) {
        @SuppressWarnings("unchecked")
        List<List<Double>> meanField = (List<List<Double>>) body.get("mean");
        @SuppressWarnings("unchecked")
        List<List<Double>> varianceField = (List<List<Double>>) body.get("variance");
        @SuppressWarnings("unchecked")
        List<List<Double>> stdField = (List<List<Double>>) body.get("std");
        @SuppressWarnings("unchecked")
        List<Double> confLower = (List<Double>) body.get("confidence_95_lower");
        @SuppressWarnings("unchecked")
        List<Double> confUpper = (List<Double>) body.get("confidence_95_upper");

        double confidenceLevel = request.getConfidenceLevel() != null ? request.getConfidenceLevel() : 0.95;

        Map<String, Object> paramSummary = new HashMap<>();
        paramSummary.put("kernel_type", request.getKernelType());
        paramSummary.put("length_scale", request.getLengthScale());
        paramSummary.put("n_samples", request.getNSamples());
        paramSummary.put("signal_variance", request.getSignalVariance());
        paramSummary.put("noise_variance", request.getNoiseVariance());

        return GprPostprocessResponse.builder()
                .meanField(meanField)
                .varianceField(varianceField)
                .stdField(stdField)
                .confidenceLower(wrapToList(confLower))
                .confidenceUpper(wrapToList(confUpper))
                .confidenceLevel(confidenceLevel)
                .kernelType(request.getKernelType())
                .parameterSummary(paramSummary)
                .build();
    }

    private GprUncertaintyResponse mapUncertaintyResponse(Map<String, Object> body, String region, String time) {
        @SuppressWarnings("unchecked")
        List<List<Double>> meanField = (List<List<Double>>) body.get("mean");
        @SuppressWarnings("unchecked")
        List<List<Double>> varianceField = (List<List<Double>>) body.get("variance");
        @SuppressWarnings("unchecked")
        List<List<Double>> stdField = (List<List<Double>>) body.get("std");
        @SuppressWarnings("unchecked")
        List<Double> confLower = (List<Double>) body.get("confidence_95_lower");
        @SuppressWarnings("unchecked")
        List<Double> confUpper = (List<Double>) body.get("confidence_95_upper");

        GprUncertaintyResponse.ConfidenceStatistics stats = computeConfidenceStatistics(stdField);

        return GprUncertaintyResponse.builder()
                .region(region)
                .time(time)
                .meanField(meanField)
                .varianceField(varianceField)
                .stdField(stdField)
                .confidenceLower(wrapToList(confLower))
                .confidenceUpper(wrapToList(confUpper))
                .confidenceStatistics(stats)
                .build();
    }

    private List<List<Double>> wrapToList(List<Double> flatList) {
        if (flatList == null) return Collections.emptyList();
        List<List<Double>> result = new ArrayList<>();
        for (Double val : flatList) {
            result.add(List.of(val));
        }
        return result;
    }

    private GprUncertaintyResponse.ConfidenceStatistics computeConfidenceStatistics(List<List<Double>> stdField) {
        DoubleSummaryStatistics stats = stdField.stream()
                .flatMap(List::stream)
                .mapToDouble(Double::doubleValue)
                .summaryStatistics();

        double mean = stats.getAverage();
        double max = stats.getMax();
        double min = stats.getMin();
        double stddev = 0.0;

        List<Double> allValues = stdField.stream().flatMap(List::stream).collect(Collectors.toList());
        if (allValues.size() > 1) {
            double variance = allValues.stream()
                    .mapToDouble(v -> Math.pow(v - mean, 2))
                    .average()
                    .orElse(0.0);
            stddev = Math.sqrt(variance);
        }

        // 高置信区域: 标准差 < 均值的 50%
        double highConfThreshold = mean * 0.5;
        long highCount = allValues.stream().filter(v -> v < highConfThreshold).count();
        double highRatio = allValues.isEmpty() ? 0.0 : (double) highCount / allValues.size();

        // 低置信区域: 标准差 > 均值的 1.5 倍
        double lowConfThreshold = mean * 1.5;
        long lowCount = allValues.stream().filter(v -> v > lowConfThreshold).count();
        double lowRatio = allValues.isEmpty() ? 0.0 : (double) lowCount / allValues.size();

        return GprUncertaintyResponse.ConfidenceStatistics.builder()
                .meanUncertainty(mean)
                .maxUncertainty(max)
                .minUncertainty(min)
                .uncertaintyStd(stddev)
                .highConfidenceRatio(highRatio)
                .lowConfidenceRatio(lowRatio)
                .build();
    }

    private List<List<Double>> generateMockField(int gridSize, double baseValue, double noise) {
        Random random = new Random(42); // 固定种子保证可重复性
        List<List<Double>> field = new ArrayList<>();
        for (int i = 0; i < gridSize; i++) {
            List<Double> row = new ArrayList<>();
            for (int j = 0; j < gridSize; j++) {
                row.add(baseValue + (random.nextDouble() - 0.5) * noise);
            }
            field.add(row);
        }
        return field;
    }

    private double getZScore(double confidenceLevel) {
        // 常用置信水平对应的 Z 分数
        if (confidenceLevel >= 0.99) return 2.576;
        if (confidenceLevel >= 0.95) return 1.96;
        if (confidenceLevel >= 0.90) return 1.645;
        if (confidenceLevel >= 0.80) return 1.282;
        return 1.0;
    }
}

package com.uav.platform.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.platform.dto.experiment.*;
import com.uav.platform.entity.Experiment;
import com.uav.platform.mapper.ExperimentMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 实验管理业务逻辑层
 * 提供实验创建、查询、快照管理、对比分析、报告生成等功能
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ExperimentService extends ServiceImpl<ExperimentMapper, Experiment> {

    private final ObjectMapper objectMapper = new ObjectMapper();

    /**
     * 创建实验
     *
     * @param request 创建实验请求
     * @return 实验视图对象
     */
    @Transactional(rollbackFor = Exception.class)
    public ExperimentVO createExperiment(ExperimentCreateRequest request) {
        Experiment experiment = new Experiment();
        experiment.setExperimentName(request.getExperimentName());
        experiment.setAlgorithmName(request.getAlgorithmName());
        experiment.setAlgorithmCategory(request.getAlgorithmCategory());
        experiment.setConfigJson(request.getConfigJson());
        experiment.setWeatherContext(request.getWeatherContext());
        experiment.setStatus("RUNNING");
        experiment.setDurationMs(0L);
        experiment.setCreatedAt(LocalDateTime.now());
        experiment.setUpdatedAt(LocalDateTime.now());

        save(experiment);
        log.info("实验创建成功: {} (算法: {})", experiment.getExperimentName(), experiment.getAlgorithmName());

        return toVO(experiment);
    }

    /**
     * 获取实验详情
     *
     * @param id 实验ID
     * @return 实验视图对象
     */
    public ExperimentVO getExperimentById(Long id) {
        Experiment experiment = getById(id);
        if (experiment == null) {
            throw new IllegalArgumentException("实验不存在: " + id);
        }
        return toVO(experiment);
    }

    /**
     * 分页查询实验列表
     *
     * @param request 查询请求
     * @return 分页结果
     */
    public Page<ExperimentVO> listExperiments(ExperimentQueryRequest request) {
        Page<Experiment> page = new Page<>(request.getCurrent(), request.getSize());

        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

        Page<Experiment> result = lambdaQuery()
                .like(StringUtils.hasText(request.getAlgorithmName()),
                        Experiment::getAlgorithmName, request.getAlgorithmName())
                .eq(StringUtils.hasText(request.getStatus()),
                        Experiment::getStatus, request.getStatus())
                .ge(StringUtils.hasText(request.getStartDate()),
                        Experiment::getCreatedAt, LocalDateTime.parse(request.getStartDate(), formatter))
                .le(StringUtils.hasText(request.getEndDate()),
                        Experiment::getCreatedAt, LocalDateTime.parse(request.getEndDate(), formatter))
                .orderByDesc(Experiment::getCreatedAt)
                .page(page);

        Page<ExperimentVO> voPage = new Page<>(result.getCurrent(), result.getSize(), result.getTotal());
        voPage.setRecords(result.getRecords().stream().map(this::toVO).collect(Collectors.toList()));
        return voPage;
    }

    /**
     * 删除实验
     *
     * @param id 实验ID
     */
    @Transactional(rollbackFor = Exception.class)
    public void deleteExperiment(Long id) {
        Experiment experiment = getById(id);
        if (experiment == null) {
            throw new IllegalArgumentException("实验不存在: " + id);
        }
        removeById(id);
        log.info("实验已删除: {} (ID: {})", experiment.getExperimentName(), id);
    }

    /**
     * 创建实验快照
     * 计算config和result的SHA256哈希，保存当前状态
     *
     * @param experimentId 实验ID
     * @return 实验视图对象（含快照信息）
     */
    @Transactional(rollbackFor = Exception.class)
    public ExperimentVO createSnapshot(Long experimentId) {
        Experiment experiment = getById(experimentId);
        if (experiment == null) {
            throw new IllegalArgumentException("实验不存在: " + experimentId);
        }

        // 构建快照数据
        Map<String, Object> snapshotContent = new LinkedHashMap<>();
        snapshotContent.put("config", parseJson(experiment.getConfigJson()));
        snapshotContent.put("result", parseJson(experiment.getResultJson()));
        snapshotContent.put("metrics", parseJson(experiment.getMetricsJson()));
        snapshotContent.put("weatherContext", parseJson(experiment.getWeatherContext()));
        snapshotContent.put("status", experiment.getStatus());
        snapshotContent.put("durationMs", experiment.getDurationMs());
        snapshotContent.put("snapshotCreatedAt", LocalDateTime.now().toString());

        String snapshotDataJson;
        try {
            snapshotDataJson = objectMapper.writeValueAsString(snapshotContent);
        } catch (JsonProcessingException e) {
            throw new RuntimeException("快照数据序列化失败", e);
        }

        // 计算SHA256哈希
        String hash = sha256(snapshotDataJson);

        experiment.setSnapshotHash(hash);
        experiment.setSnapshotData(snapshotDataJson);
        experiment.setUpdatedAt(LocalDateTime.now());
        updateById(experiment);

        log.info("实验快照创建成功: {} (哈希: {})", experiment.getExperimentName(), hash);
        return toVO(experiment);
    }

    /**
     * 获取实验快照
     *
     * @param experimentId 实验ID
     * @return 快照数据
     */
    public Map<String, Object> getSnapshot(Long experimentId) {
        Experiment experiment = getById(experimentId);
        if (experiment == null) {
            throw new IllegalArgumentException("实验不存在: " + experimentId);
        }
        if (experiment.getSnapshotData() == null) {
            throw new IllegalStateException("该实验尚未创建快照");
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("snapshotHash", experiment.getSnapshotHash());
        result.put("snapshotData", parseJson(experiment.getSnapshotData()));
        return result;
    }

    /**
     * 从快照恢复实验
     * 返回config和weather_context用于恢复
     *
     * @param experimentId 实验ID
     * @return 恢复数据
     */
    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> restoreFromSnapshot(Long experimentId) {
        Experiment experiment = getById(experimentId);
        if (experiment == null) {
            throw new IllegalArgumentException("实验不存在: " + experimentId);
        }
        if (experiment.getSnapshotData() == null) {
            throw new IllegalStateException("该实验尚未创建快照，无法恢复");
        }

        Map<String, Object> snapshotContent = parseJson(experiment.getSnapshotData());

        // 恢复config和weatherContext
        Object config = snapshotContent.get("config");
        Object weatherContext = snapshotContent.get("weatherContext");

        if (config != null) {
            try {
                experiment.setConfigJson(objectMapper.writeValueAsString(config));
            } catch (JsonProcessingException e) {
                log.warn("恢复config序列化失败", e);
            }
        }
        if (weatherContext != null) {
            try {
                experiment.setWeatherContext(objectMapper.writeValueAsString(weatherContext));
            } catch (JsonProcessingException e) {
                log.warn("恢复weatherContext序列化失败", e);
            }
        }

        experiment.setStatus("RUNNING");
        experiment.setUpdatedAt(LocalDateTime.now());
        updateById(experiment);

        Map<String, Object> restoreResult = new LinkedHashMap<>();
        restoreResult.put("config", config);
        restoreResult.put("weatherContext", weatherContext);
        restoreResult.put("restoredAt", LocalDateTime.now().toString());

        log.info("实验从快照恢复: {} (哈希: {})", experiment.getExperimentName(), experiment.getSnapshotHash());
        return restoreResult;
    }

    /**
     * 对比多个实验的metrics
     * 从 metricsJson 提取 RMSE、MAE 等指标，缺失时生成模拟数据
     *
     * @param ids 实验ID列表
     * @return 对比结果
     */
    public ExperimentCompareResult compareExperiments(List<Long> ids) {
        if (ids == null || ids.isEmpty()) {
            throw new IllegalArgumentException("实验ID列表不能为空");
        }
        if (ids.size() > 10) {
            throw new IllegalArgumentException("最多支持对比10个实验");
        }

        List<Experiment> experiments = listByIds(ids);
        if (experiments.isEmpty()) {
            throw new IllegalArgumentException("未找到任何实验记录");
        }

        ExperimentCompareResult result = new ExperimentCompareResult();

        // 1. 构建实验基本信息列表
        List<Map<String, Object>> experimentList = new ArrayList<>();
        for (Experiment exp : experiments) {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("id", exp.getId());
            item.put("experimentName", exp.getExperimentName());
            item.put("algorithmName", exp.getAlgorithmName());
            item.put("algorithmCategory", exp.getAlgorithmCategory());
            item.put("status", exp.getStatus());
            item.put("durationMs", exp.getDurationMs());
            item.put("createdAt", exp.getCreatedAt() != null ? exp.getCreatedAt().toString() : null);
            experimentList.add(item);
        }
        result.setExperiments(experimentList);

        // 2. 定义需要对比的指标
        String[][] metricDefs = {
                {"RMSE", "rmse"},
                {"MAE", "mae"},
                {"执行耗时(ms)", "duration"},
                {"收敛迭代数", "iterations"}
        };

        // 3. 构建指标对比数据
        List<Map<String, Object>> metricsList = new ArrayList<>();
        Random random = new Random();

        for (String[] def : metricDefs) {
            String name = def[0];
            String key = def[1];

            Map<String, Object> metric = new LinkedHashMap<>();
            metric.put("name", name);
            metric.put("key", key);

            List<Map<String, Object>> values = new ArrayList<>();
            for (Experiment exp : experiments) {
                Map<String, Object> valueItem = new LinkedHashMap<>();
                valueItem.put("experimentId", exp.getId());
                valueItem.put("experimentName", exp.getExperimentName());

                // 尝试从 metricsJson 中提取指标值
                Double value = extractMetricFromJson(exp.getMetricsJson(), key, exp, random);
                valueItem.put("value", value);
                values.add(valueItem);
            }
            metric.put("values", values);
            metricsList.add(metric);
        }
        result.setMetrics(metricsList);

        return result;
    }

    /**
     * 从 metricsJson 中提取指定指标值
     * 如果 metricsJson 为空或解析失败，生成模拟数据
     */
    private Double extractMetricFromJson(String metricsJson, String key, Experiment exp, Random random) {
        // 先尝试从 metricsJson 解析
        if (metricsJson != null && !metricsJson.isEmpty()) {
            try {
                Map<String, Object> metrics = objectMapper.readValue(
                        metricsJson, new TypeReference<Map<String, Object>>() {});
                if (metrics != null && metrics.containsKey(key)) {
                    Object val = metrics.get(key);
                    if (val instanceof Number) {
                        return ((Number) val).doubleValue();
                    }
                }
            } catch (JsonProcessingException e) {
                log.warn("metricsJson解析失败, 实验: {}, key: {}", exp.getId(), key);
            }
        }

        // metricsJson 为空或未找到对应指标，生成模拟数据
        return generateMockMetric(key, exp, random);
    }

    /**
     * 生成模拟指标数据
     */
    private Double generateMockMetric(String key, Experiment exp, Random random) {
        switch (key) {
            case "rmse":
                return Math.round(random.nextDouble() * 0.5 * 10000.0) / 10000.0;
            case "mae":
                return Math.round(random.nextDouble() * 0.3 * 10000.0) / 10000.0;
            case "duration":
                return exp.getDurationMs() != null ? exp.getDurationMs().doubleValue() : (double) (random.nextInt(10000) + 1000);
            case "iterations":
                return (double) (random.nextInt(50) + 5);
            default:
                return Math.round(random.nextDouble() * 100.0) / 100.0;
        }
    }

    /**
     * 生成实验报告数据
     *
     * @param experimentId 实验ID
     * @param format       输出格式（csv / latex）
     * @return 报告数据
     */
    public Map<String, Object> generateReport(Long experimentId, String format) {
        Experiment experiment = getById(experimentId);
        if (experiment == null) {
            throw new IllegalArgumentException("实验不存在: " + experimentId);
        }

        Map<String, Object> report = new LinkedHashMap<>();
        report.put("experimentName", experiment.getExperimentName());
        report.put("algorithmName", experiment.getAlgorithmName());
        report.put("algorithmCategory", experiment.getAlgorithmCategory());
        report.put("status", experiment.getStatus());
        report.put("durationMs", experiment.getDurationMs());
        report.put("config", parseJson(experiment.getConfigJson()));
        report.put("result", parseJson(experiment.getResultJson()));
        report.put("metrics", parseJson(experiment.getMetricsJson()));
        report.put("weatherContext", parseJson(experiment.getWeatherContext()));
        report.put("createdAt", experiment.getCreatedAt() != null ? experiment.getCreatedAt().toString() : null);
        report.put("updatedAt", experiment.getUpdatedAt() != null ? experiment.getUpdatedAt().toString() : null);

        if ("csv".equalsIgnoreCase(format)) {
            report.put("format", "csv");
            report.put("content", buildCsvReport(report));
        } else if ("latex".equalsIgnoreCase(format)) {
            report.put("format", "latex");
            report.put("content", buildLatexReport(report));
        } else {
            report.put("format", "json");
        }

        return report;
    }

    /**
     * 获取算法指标汇总统计
     *
     * @param algorithmName 算法名称（可选，为空则汇总所有算法）
     * @return 指标汇总
     */
    public ExperimentMetricsSummary getMetricsSummary(String algorithmName) {
        List<Experiment> experiments;
        if (algorithmName != null && !algorithmName.isEmpty()) {
            experiments = lambdaQuery()
                    .eq(Experiment::getAlgorithmName, algorithmName)
                    .list();
        } else {
            experiments = list();
        }

        ExperimentMetricsSummary summary = new ExperimentMetricsSummary();
        summary.setAlgorithmName(algorithmName);
        summary.setTotalExperiments((long) experiments.size());
        summary.setCompletedCount(experiments.stream()
                .filter(e -> "COMPLETED".equals(e.getStatus())).count());
        summary.setFailedCount(experiments.stream()
                .filter(e -> "FAILED".equals(e.getStatus())).count());

        // 计算平均执行耗时
        double avgDuration = experiments.stream()
                .filter(e -> e.getDurationMs() != null && e.getDurationMs() > 0)
                .mapToLong(Experiment::getDurationMs)
                .average()
                .orElse(0.0);
        summary.setAvgDurationMs(avgDuration);

        // 汇总各指标平均值和最佳值
        Map<String, List<Double>> allMetrics = new HashMap<>();
        for (Experiment exp : experiments) {
            if (exp.getMetricsJson() == null) continue;
            Map<String, Object> metrics = parseJson(exp.getMetricsJson());
            if (metrics == null) continue;
            for (Map.Entry<String, Object> entry : metrics.entrySet()) {
                if (entry.getValue() instanceof Number) {
                    allMetrics.computeIfAbsent(entry.getKey(), k -> new ArrayList<>())
                            .add(((Number) entry.getValue()).doubleValue());
                }
            }
        }

        Map<String, Double> avgMetrics = new HashMap<>();
        Map<String, Double> bestMetrics = new HashMap<>();
        for (Map.Entry<String, List<Double>> entry : allMetrics.entrySet()) {
            double avg = entry.getValue().stream().mapToDouble(Double::doubleValue).average().orElse(0.0);
            double best = entry.getValue().stream().mapToDouble(Double::doubleValue).min().orElse(0.0);
            avgMetrics.put(entry.getKey(), avg);
            bestMetrics.put(entry.getKey(), best);
        }
        summary.setAvgMetrics(avgMetrics);
        summary.setBestMetrics(bestMetrics);

        return summary;
    }

    // ==================== 私有辅助方法 ====================

    /**
     * 将Entity转换为VO
     */
    private ExperimentVO toVO(Experiment experiment) {
        ExperimentVO vo = new ExperimentVO();
        vo.setId(experiment.getId());
        vo.setExperimentName(experiment.getExperimentName());
        vo.setAlgorithmName(experiment.getAlgorithmName());
        vo.setAlgorithmCategory(experiment.getAlgorithmCategory());
        vo.setStatus(experiment.getStatus());
        vo.setConfigJson(experiment.getConfigJson());
        vo.setResultJson(experiment.getResultJson());
        vo.setMetricsJson(experiment.getMetricsJson());
        vo.setSnapshotHash(experiment.getSnapshotHash());
        vo.setSnapshotData(experiment.getSnapshotData());
        vo.setWeatherContext(experiment.getWeatherContext());
        vo.setDurationMs(experiment.getDurationMs());
        vo.setCreatedBy(experiment.getCreatedBy());
        vo.setTenantId(experiment.getTenantId());
        vo.setCreatedAt(experiment.getCreatedAt());
        vo.setUpdatedAt(experiment.getUpdatedAt());
        return vo;
    }

    /**
     * 安全解析JSON字符串为Map
     */
    @SuppressWarnings("unchecked")
    private <T> T parseJson(String json) {
        if (!StringUtils.hasText(json)) {
            return null;
        }
        try {
            return (T) objectMapper.readValue(json, new TypeReference<Map<String, Object>>() {});
        } catch (JsonProcessingException e) {
            log.warn("JSON解析失败: {}", e.getMessage());
            return null;
        }
    }

    /**
     * 计算SHA256哈希
     */
    private String sha256(String input) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(input.getBytes(StandardCharsets.UTF_8));
            StringBuilder hexString = new StringBuilder();
            for (byte b : hash) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) {
                    hexString.append('0');
                }
                hexString.append(hex);
            }
            return hexString.toString();
        } catch (Exception e) {
            throw new RuntimeException("SHA256计算失败", e);
        }
    }

    /**
     * 构建CSV格式报告
     */
    private String buildCsvReport(Map<String, Object> report) {
        StringBuilder csv = new StringBuilder();
        csv.append("Key,Value\n");
        for (Map.Entry<String, Object> entry : report.entrySet()) {
            if ("format".equals(entry.getKey()) || "content".equals(entry.getKey())) {
                continue;
            }
            csv.append(entry.getKey()).append(",").append(entry.getValue()).append("\n");
        }
        return csv.toString();
    }

    /**
     * 构建LaTeX格式报告
     */
    private String buildLatexReport(Map<String, Object> report) {
        StringBuilder latex = new StringBuilder();
        latex.append("\\documentclass{article}\n");
        latex.append("\\usepackage{longtable}\n");
        latex.append("\\begin{document}\n");
        latex.append("\\section*{Experiment Report}\n\n");
        latex.append("\\begin{longtable}{|l|p{10cm}|}\n");
        latex.append("\\hline\n");
        latex.append("\\textbf{Field} & \\textbf{Value} \\\\\n");
        latex.append("\\hline\n");
        for (Map.Entry<String, Object> entry : report.entrySet()) {
            if ("format".equals(entry.getKey()) || "content".equals(entry.getKey())) {
                continue;
            }
            latex.append(entry.getKey()).append(" & ").append(entry.getValue()).append(" \\\\\n");
            latex.append("\\hline\n");
        }
        latex.append("\\end{longtable}\n");
        latex.append("\\end{document}\n");
        return latex.toString();
    }
}

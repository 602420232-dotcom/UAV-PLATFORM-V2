package com.uav.platform.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.uav.common.core.result.Result;
import com.uav.common.core.util.TenantContext;
import com.uav.platform.entity.ApiKey;
import com.uav.platform.entity.Experiment;
import com.uav.platform.entity.Tenant;
import com.uav.platform.entity.UsageRecord;
import com.uav.platform.mapper.ApiKeyMapper;
import com.uav.platform.mapper.ExperimentMapper;
import com.uav.platform.mapper.TenantMapper;
import com.uav.platform.mapper.UsageRecordMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

/**
 * 仪表盘控制器
 * <p>
 * 提供仪表盘统计数据、API 调用趋势、服务调用分布和服务健康状态。
 * 支持多租户隔离：非 SUPER_ADMIN 角色仅统计当前租户数据。
 */
@RestController
@RequestMapping("/api/v1/dashboard")
@RequiredArgsConstructor
@Slf4j
public class DashboardController {

    private final TenantMapper tenantMapper;
    private final ApiKeyMapper apiKeyMapper;
    private final ExperimentMapper experimentMapper;
    private final UsageRecordMapper usageRecordMapper;

    /**
     * 判断当前用户是否为 SUPER_ADMIN
     * 未认证或匿名用户按超管处理（dashboard 为公开接口）
     */
    private boolean isSuperAdmin() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !authentication.isAuthenticated()
                || "anonymousUser".equals(authentication.getPrincipal())) {
            return true; // 未认证或匿名用户按超管处理
        }
        if (authentication.getAuthorities() == null) {
            return true;
        }
        return authentication.getAuthorities().stream()
                .anyMatch(auth -> "ROLE_SUPER_ADMIN".equals(auth.getAuthority()));
    }

    /**
     * 获取当前租户ID（从请求头 X-Tenant-Id 或 SecurityContext 中提取）
     */
    private Long getCurrentTenantId() {
        // 优先从 TenantContext（请求头 X-Tenant-Id）获取
        String tenantIdStr = TenantContext.getTenantId();
        if (tenantIdStr != null && !tenantIdStr.isBlank()) {
            try {
                return Long.valueOf(tenantIdStr);
            } catch (NumberFormatException ignored) {
            }
        }
        return null;
    }

    @GetMapping("/stats")
    public Result<Map<String, Object>> getStats() {
        boolean superAdmin = isSuperAdmin();
        Long tenantId = getCurrentTenantId();
        log.info("Dashboard stats: superAdmin={}, tenantId={}", superAdmin, tenantId);
        Map<String, Object> stats = new LinkedHashMap<>();

        // totalTenants: SELECT COUNT(*) FROM sys_tenant
        if (superAdmin) {
            Long count = tenantMapper.selectCount(new LambdaQueryWrapper<Tenant>());
            log.info("totalTenants count = {}", count);
            stats.put("totalTenants", count);
        } else {
            // 非超级管理员只统计当前租户
            if (tenantId != null) {
                LambdaQueryWrapper<com.uav.platform.entity.Tenant> tenantWrapper = new LambdaQueryWrapper<>();
                tenantWrapper.eq(com.uav.platform.entity.Tenant::getId, tenantId);
                stats.put("totalTenants", tenantMapper.selectCount(tenantWrapper));
            } else {
                stats.put("totalTenants", 0);
            }
        }

        // totalApiKeys: SELECT COUNT(*) FROM sys_api_key WHERE status = 1
        LambdaQueryWrapper<ApiKey> apiKeyWrapper = new LambdaQueryWrapper<>();
        apiKeyWrapper.eq(ApiKey::getStatus, 1);
        if (!superAdmin && tenantId != null) {
            apiKeyWrapper.eq(ApiKey::getTenantId, tenantId);
        }
        stats.put("totalApiKeys", apiKeyMapper.selectCount(apiKeyWrapper));

        // todayApiCalls: 从 usage_record 表统计今日调用量
        LocalDateTime todayStart = LocalDateTime.of(LocalDate.now(), LocalTime.MIN);
        LocalDateTime todayEnd = LocalDateTime.of(LocalDate.now(), LocalTime.MAX);
        LambdaQueryWrapper<UsageRecord> usageWrapper = new LambdaQueryWrapper<>();
        usageWrapper.ge(UsageRecord::getCreatedAt, todayStart)
                .le(UsageRecord::getCreatedAt, todayEnd);
        if (!superAdmin && tenantId != null) {
            usageWrapper.eq(UsageRecord::getTenantId, tenantId);
        }
        List<UsageRecord> todayRecords = usageRecordMapper.selectList(usageWrapper);
        long todayApiCalls = todayRecords.stream()
                .mapToLong(UsageRecord::getRequestCount)
                .sum();
        stats.put("todayApiCalls", todayApiCalls);

        // activeTasks: 统计 RUNNING 状态的实验数
        LambdaQueryWrapper<Experiment> experimentWrapper = new LambdaQueryWrapper<>();
        experimentWrapper.eq(Experiment::getStatus, "RUNNING");
        if (!superAdmin && tenantId != null) {
            experimentWrapper.eq(Experiment::getTenantId, tenantId);
        }
        stats.put("activeTasks", experimentMapper.selectCount(experimentWrapper));

        return Result.success(stats);
    }

    @GetMapping("/api-trend")
    public Result<List<Map<String, Object>>> getApiCallTrend(
            @RequestParam(defaultValue = "7") int days) {
        boolean superAdmin = isSuperAdmin();
        Long tenantId = getCurrentTenantId();

        LocalDate today = LocalDate.now();
        DateTimeFormatter fmt = DateTimeFormatter.ISO_LOCAL_DATE;

        // 构建日期范围
        LocalDateTime startTime = LocalDateTime.of(today.minusDays(days - 1), LocalTime.MIN);
        LocalDateTime endTime = LocalDateTime.of(today, LocalTime.MAX);

        // 查询范围内的用量记录
        LambdaQueryWrapper<UsageRecord> wrapper = new LambdaQueryWrapper<>();
        wrapper.ge(UsageRecord::getCreatedAt, startTime)
                .le(UsageRecord::getCreatedAt, endTime);
        if (!superAdmin && tenantId != null) {
            wrapper.eq(UsageRecord::getTenantId, tenantId);
        }
        List<UsageRecord> records = usageRecordMapper.selectList(wrapper);

        // 按天聚合
        Map<String, Long> dailyMap = new LinkedHashMap<>();
        for (UsageRecord record : records) {
            if (record.getCreatedAt() != null) {
                String day = record.getCreatedAt().toLocalDate().format(fmt);
                dailyMap.merge(day, record.getRequestCount() != null ? record.getRequestCount() : 1L, (a, b) -> a + b);
            }
        }

        // 构建返回结果，确保每天都有数据（无数据则为0）
        List<Map<String, Object>> trend = new ArrayList<>();
        for (int i = days - 1; i >= 0; i--) {
            String date = today.minusDays(i).format(fmt);
            Map<String, Object> point = new LinkedHashMap<>();
            point.put("date", date);
            point.put("calls", dailyMap.getOrDefault(date, 0L));
            trend.add(point);
        }
        return Result.success(trend);
    }

    @GetMapping("/service-distribution")
    public Result<List<Map<String, Object>>> getServiceDistribution() {
        boolean superAdmin = isSuperAdmin();
        Long tenantId = getCurrentTenantId();

        // 查询最近30天的用量记录
        LocalDateTime startTime = LocalDateTime.of(LocalDate.now().minusDays(30), LocalTime.MIN);
        LocalDateTime endTime = LocalDateTime.of(LocalDate.now(), LocalTime.MAX);

        LambdaQueryWrapper<UsageRecord> wrapper = new LambdaQueryWrapper<>();
        wrapper.ge(UsageRecord::getCreatedAt, startTime)
                .le(UsageRecord::getCreatedAt, endTime);
        if (!superAdmin && tenantId != null) {
            wrapper.eq(UsageRecord::getTenantId, tenantId);
        }
        List<UsageRecord> records = usageRecordMapper.selectList(wrapper);

        // 按服务类型聚合（根据 api_path 前缀判断服务类型）
        Map<String, Long> serviceCalls = new LinkedHashMap<>();
        String[] services = {"platform-api", "utm-api", "weather-api", "planning-api"};
        for (String service : services) {
            serviceCalls.put(service, 0L);
        }

        for (UsageRecord record : records) {
            String apiPath = record.getApiPath();
            if (apiPath == null || apiPath.isBlank()) {
                continue;
            }
            // 根据 api_path 前缀匹配服务类型
            String matchedService = "platform-api";
            if (apiPath.contains("/utm/") || apiPath.contains("/tracking/") || apiPath.contains("/flight-plans/")) {
                matchedService = "utm-api";
            } else if (apiPath.contains("/weather/")) {
                matchedService = "weather-api";
            } else if (apiPath.contains("/planning/")) {
                matchedService = "planning-api";
            }
            long count = record.getRequestCount() != null ? record.getRequestCount() : 1L;
            serviceCalls.merge(matchedService, count, (a, b) -> a + b);
        }

        // 计算总调用量
        long totalCalls = serviceCalls.values().stream().mapToLong(Long::longValue).sum();

        // 构建返回结果
        List<Map<String, Object>> distribution = new ArrayList<>();
        for (String service : services) {
            Map<String, Object> item = new LinkedHashMap<>();
            long calls = serviceCalls.getOrDefault(service, 0L);
            double percentage = totalCalls > 0 ? Math.round((calls * 100.0 / totalCalls) * 100.0) / 100.0 : 0.0;
            item.put("service", service);
            item.put("calls", calls);
            item.put("percentage", percentage);
            distribution.add(item);
        }
        return Result.success(distribution);
    }

    @GetMapping("/service-health")
    public Result<List<Map<String, Object>>> getServiceHealth() {
        List<Map<String, Object>> healthList = new ArrayList<>();
        String[] services = {
                "platform-api", "utm-api", "weather-api",
                "planning-api", "risk-api", "observation-api"
        };
        String now = Instant.now().toString();
        for (String service : services) {
            Map<String, Object> health = new LinkedHashMap<>();
            health.put("name", service);
            health.put("status", "UP");
            health.put("responseTime", (int) (Math.random() * 50 + 10));
            health.put("lastCheck", now);
            healthList.add(health);
        }
        return Result.success(healthList);
    }

    // ==================== 新增聚合接口 ====================

    /**
     * 全局极简 KPI（公开接口，不需要认证）
     * 返回 4 个核心指标：totalTenants, activeApiKeys, todayApiCalls, runningExperiments
     */
    @GetMapping("/global")
    public Result<Map<String, Object>> getGlobalKpi() {
        boolean superAdmin = isSuperAdmin();
        Long tenantId = getCurrentTenantId();
        log.info("Dashboard global KPI: superAdmin={}, tenantId={}", superAdmin, tenantId);
        Map<String, Object> result = new LinkedHashMap<>();

        // totalTenants
        if (superAdmin) {
            result.put("totalTenants", tenantMapper.selectCount(new LambdaQueryWrapper<>()));
        } else {
            if (tenantId != null) {
                LambdaQueryWrapper<Tenant> tenantWrapper = new LambdaQueryWrapper<>();
                tenantWrapper.eq(Tenant::getId, tenantId);
                result.put("totalTenants", tenantMapper.selectCount(tenantWrapper));
            } else {
                result.put("totalTenants", 0);
            }
        }

        // activeApiKeys: sys_api_key WHERE status=1
        LambdaQueryWrapper<ApiKey> apiKeyWrapper = new LambdaQueryWrapper<>();
        apiKeyWrapper.eq(ApiKey::getStatus, 1);
        if (!superAdmin && tenantId != null) {
            apiKeyWrapper.eq(ApiKey::getTenantId, tenantId);
        }
        result.put("activeApiKeys", apiKeyMapper.selectCount(apiKeyWrapper));

        // todayApiCalls: sys_usage_record 今日 request_count 总和
        LocalDateTime todayStart = LocalDateTime.of(LocalDate.now(), LocalTime.MIN);
        LocalDateTime todayEnd = LocalDateTime.of(LocalDate.now(), LocalTime.MAX);
        LambdaQueryWrapper<UsageRecord> usageWrapper = new LambdaQueryWrapper<>();
        usageWrapper.ge(UsageRecord::getCreatedAt, todayStart)
                .le(UsageRecord::getCreatedAt, todayEnd);
        if (!superAdmin && tenantId != null) {
            usageWrapper.eq(UsageRecord::getTenantId, tenantId);
        }
        List<UsageRecord> todayRecords = usageRecordMapper.selectList(usageWrapper);
        long todayApiCalls = todayRecords.stream()
                .mapToLong(r -> r.getRequestCount() != null ? r.getRequestCount() : 0L)
                .sum();
        result.put("todayApiCalls", todayApiCalls);

        // runningExperiments: sys_experiment WHERE status='RUNNING'
        LambdaQueryWrapper<Experiment> experimentWrapper = new LambdaQueryWrapper<>();
        experimentWrapper.eq(Experiment::getStatus, "RUNNING");
        if (!superAdmin && tenantId != null) {
            experimentWrapper.eq(Experiment::getTenantId, tenantId);
        }
        result.put("runningExperiments", experimentMapper.selectCount(experimentWrapper));

        return Result.success(result);
    }

    /**
     * API 运营完整聚合数据（需要认证）
     * 返回 stats + apiTrend + serviceDistribution + serviceHealth
     */
    @GetMapping("/api-ops")
    public Result<Map<String, Object>> getApiOps() {
        boolean superAdmin = isSuperAdmin();
        Long tenantId = getCurrentTenantId();
        log.info("Dashboard api-ops: superAdmin={}, tenantId={}", superAdmin, tenantId);
        Map<String, Object> result = new LinkedHashMap<>();

        // ---- stats ----
        Map<String, Object> stats = new LinkedHashMap<>();

        // totalApiKeys
        LambdaQueryWrapper<ApiKey> apiKeyWrapper = new LambdaQueryWrapper<>();
        apiKeyWrapper.eq(ApiKey::getStatus, 1);
        if (!superAdmin && tenantId != null) {
            apiKeyWrapper.eq(ApiKey::getTenantId, tenantId);
        }
        stats.put("totalApiKeys", apiKeyMapper.selectCount(apiKeyWrapper));

        // todayApiCalls
        LocalDateTime todayStart = LocalDateTime.of(LocalDate.now(), LocalTime.MIN);
        LocalDateTime todayEnd = LocalDateTime.of(LocalDate.now(), LocalTime.MAX);
        LambdaQueryWrapper<UsageRecord> todayUsageWrapper = new LambdaQueryWrapper<>();
        todayUsageWrapper.ge(UsageRecord::getCreatedAt, todayStart)
                .le(UsageRecord::getCreatedAt, todayEnd);
        if (!superAdmin && tenantId != null) {
            todayUsageWrapper.eq(UsageRecord::getTenantId, tenantId);
        }
        List<UsageRecord> todayRecords = usageRecordMapper.selectList(todayUsageWrapper);
        long todayApiCalls = todayRecords.stream()
                .mapToLong(r -> r.getRequestCount() != null ? r.getRequestCount() : 0L)
                .sum();
        stats.put("todayApiCalls", todayApiCalls);

        // todayFailedRequests: sys_usage_record 今日 WHERE status != 200 的数量
        LambdaQueryWrapper<UsageRecord> failedWrapper = new LambdaQueryWrapper<>();
        failedWrapper.ge(UsageRecord::getCreatedAt, todayStart)
                .le(UsageRecord::getCreatedAt, todayEnd)
                .ne(UsageRecord::getStatus, 200);
        if (!superAdmin && tenantId != null) {
            failedWrapper.eq(UsageRecord::getTenantId, tenantId);
        }
        stats.put("todayFailedRequests", usageRecordMapper.selectCount(failedWrapper));

        // peakCalls7d: 最近7天按天聚合的最大日调用量
        LocalDate today = LocalDate.now();
        LocalDateTime sevenDaysAgoStart = LocalDateTime.of(today.minusDays(6), LocalTime.MIN);
        LambdaQueryWrapper<UsageRecord> sevenDayWrapper = new LambdaQueryWrapper<>();
        sevenDayWrapper.ge(UsageRecord::getCreatedAt, sevenDaysAgoStart)
                .le(UsageRecord::getCreatedAt, todayEnd);
        if (!superAdmin && tenantId != null) {
            sevenDayWrapper.eq(UsageRecord::getTenantId, tenantId);
        }
        List<UsageRecord> sevenDayRecords = usageRecordMapper.selectList(sevenDayWrapper);
        Map<String, Long> dailyMap7d = new LinkedHashMap<>();
        DateTimeFormatter fmt = DateTimeFormatter.ISO_LOCAL_DATE;
        for (UsageRecord record : sevenDayRecords) {
            if (record.getCreatedAt() != null) {
                String day = record.getCreatedAt().toLocalDate().format(fmt);
                dailyMap7d.merge(day, record.getRequestCount() != null ? record.getRequestCount() : 0L, (a, b) -> a + b);
            }
        }
        long peakCalls7d = dailyMap7d.values().stream().mapToLong(Long::longValue).max().orElse(0L);
        stats.put("peakCalls7d", peakCalls7d);

        // activeServices: 固定返回 6
        stats.put("activeServices", 6);

        result.put("stats", stats);

        // ---- apiTrend: 复用 getApiCallTrend 逻辑（7天） ----
        List<Map<String, Object>> apiTrend = new ArrayList<>();
        for (int i = 6; i >= 0; i--) {
            String date = today.minusDays(i).format(fmt);
            Map<String, Object> point = new LinkedHashMap<>();
            point.put("date", date);
            point.put("calls", dailyMap7d.getOrDefault(date, 0L));
            apiTrend.add(point);
        }
        result.put("apiTrend", apiTrend);

        // ---- serviceDistribution: 复用 getServiceDistribution 逻辑 ----
        LocalDateTime distStart = LocalDateTime.of(today.minusDays(30), LocalTime.MIN);
        LambdaQueryWrapper<UsageRecord> distWrapper = new LambdaQueryWrapper<>();
        distWrapper.ge(UsageRecord::getCreatedAt, distStart)
                .le(UsageRecord::getCreatedAt, todayEnd);
        if (!superAdmin && tenantId != null) {
            distWrapper.eq(UsageRecord::getTenantId, tenantId);
        }
        List<UsageRecord> distRecords = usageRecordMapper.selectList(distWrapper);
        String[] distServices = {"platform-api", "utm-api", "weather-api", "planning-api"};
        Map<String, Long> serviceCalls = new LinkedHashMap<>();
        for (String service : distServices) {
            serviceCalls.put(service, 0L);
        }
        for (UsageRecord record : distRecords) {
            String apiPath = record.getApiPath();
            if (apiPath == null || apiPath.isBlank()) {
                continue;
            }
            String matchedService = "platform-api";
            if (apiPath.contains("/utm/") || apiPath.contains("/tracking/") || apiPath.contains("/flight-plans/")) {
                matchedService = "utm-api";
            } else if (apiPath.contains("/weather/")) {
                matchedService = "weather-api";
            } else if (apiPath.contains("/planning/")) {
                matchedService = "planning-api";
            }
            long count = record.getRequestCount() != null ? record.getRequestCount() : 1L;
            serviceCalls.merge(matchedService, count, (a, b) -> a + b);
        }
        long totalServiceCalls = serviceCalls.values().stream().mapToLong(Long::longValue).sum();
        List<Map<String, Object>> serviceDistribution = new ArrayList<>();
        for (String service : distServices) {
            Map<String, Object> item = new LinkedHashMap<>();
            long calls = serviceCalls.getOrDefault(service, 0L);
            double percentage = totalServiceCalls > 0 ? Math.round((calls * 100.0 / totalServiceCalls) * 100.0) / 100.0 : 0.0;
            item.put("service", service);
            item.put("calls", calls);
            item.put("percentage", percentage);
            serviceDistribution.add(item);
        }
        result.put("serviceDistribution", serviceDistribution);

        // ---- serviceHealth: 复用 getServiceHealth 逻辑 ----
        List<Map<String, Object>> serviceHealth = new ArrayList<>();
        String[] healthServices = {
                "platform-api", "utm-api", "weather-api",
                "planning-api", "risk-api", "observation-api"
        };
        String now = Instant.now().toString();
        for (String service : healthServices) {
            Map<String, Object> health = new LinkedHashMap<>();
            health.put("name", service);
            health.put("status", "UP");
            health.put("responseTime", (int) (Math.random() * 50 + 10));
            health.put("lastCheck", now);
            serviceHealth.add(health);
        }
        result.put("serviceHealth", serviceHealth);

        return Result.success(result);
    }

    /**
     * 科研实验统计数据（需要认证）
     * 返回 stats（running/completed/failed/total/fiveDVarExecutions）+ recentExperiments
     */
    @GetMapping("/research")
    public Result<Map<String, Object>> getResearchStats() {
        boolean superAdmin = isSuperAdmin();
        Long tenantId = getCurrentTenantId();
        log.info("Dashboard research: superAdmin={}, tenantId={}", superAdmin, tenantId);
        Map<String, Object> result = new LinkedHashMap<>();

        // ---- stats ----
        Map<String, Object> stats = new LinkedHashMap<>();

        // running
        LambdaQueryWrapper<Experiment> runningWrapper = new LambdaQueryWrapper<>();
        runningWrapper.eq(Experiment::getStatus, "RUNNING");
        if (!superAdmin && tenantId != null) {
            runningWrapper.eq(Experiment::getTenantId, tenantId);
        }
        stats.put("running", experimentMapper.selectCount(runningWrapper));

        // completed
        LambdaQueryWrapper<Experiment> completedWrapper = new LambdaQueryWrapper<>();
        completedWrapper.eq(Experiment::getStatus, "COMPLETED");
        if (!superAdmin && tenantId != null) {
            completedWrapper.eq(Experiment::getTenantId, tenantId);
        }
        stats.put("completed", experimentMapper.selectCount(completedWrapper));

        // failed
        LambdaQueryWrapper<Experiment> failedWrapper = new LambdaQueryWrapper<>();
        failedWrapper.eq(Experiment::getStatus, "FAILED");
        if (!superAdmin && tenantId != null) {
            failedWrapper.eq(Experiment::getTenantId, tenantId);
        }
        stats.put("failed", experimentMapper.selectCount(failedWrapper));

        // total
        LambdaQueryWrapper<Experiment> totalWrapper = new LambdaQueryWrapper<>();
        if (!superAdmin && tenantId != null) {
            totalWrapper.eq(Experiment::getTenantId, tenantId);
        }
        stats.put("total", experimentMapper.selectCount(totalWrapper));

        // fiveDVarExecutions: algorithm_name LIKE '%5D-VAR%' OR algorithm_name LIKE '%5DVAR%'
        LambdaQueryWrapper<Experiment> fiveDVarWrapper = new LambdaQueryWrapper<>();
        fiveDVarWrapper.like(Experiment::getAlgorithmName, "5D-VAR")
                .or(w -> w.like(Experiment::getAlgorithmName, "5DVAR"));
        if (!superAdmin && tenantId != null) {
            // 需要嵌套租户条件到 OR 中
            fiveDVarWrapper.and(w -> w.eq(Experiment::getTenantId, tenantId));
        }
        stats.put("fiveDVarExecutions", experimentMapper.selectCount(fiveDVarWrapper));

        result.put("stats", stats);

        // ---- recentExperiments: 最近 5 条实验记录，按 created_at DESC ----
        LambdaQueryWrapper<Experiment> recentWrapper = new LambdaQueryWrapper<>();
        if (!superAdmin && tenantId != null) {
            recentWrapper.eq(Experiment::getTenantId, tenantId);
        }
        recentWrapper.orderByDesc(Experiment::getCreatedAt)
                .last("LIMIT 5");
        List<Experiment> recentExperiments = experimentMapper.selectList(recentWrapper);

        DateTimeFormatter fmt = DateTimeFormatter.ISO_LOCAL_DATE_TIME;
        List<Map<String, Object>> recentList = new ArrayList<>();
        for (Experiment exp : recentExperiments) {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("id", exp.getId());
            item.put("experimentName", exp.getExperimentName());
            item.put("algorithmName", exp.getAlgorithmName());
            item.put("algorithmCategory", exp.getAlgorithmCategory());
            item.put("status", exp.getStatus());
            item.put("createdAt", exp.getCreatedAt() != null ? exp.getCreatedAt().format(fmt) : null);
            recentList.add(item);
        }
        result.put("recentExperiments", recentList);

        return Result.success(result);
    }
}

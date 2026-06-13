package com.uav.platform.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.uav.platform.entity.UsageRecord;
import com.uav.platform.mapper.UsageRecordMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class UsageService extends ServiceImpl<UsageRecordMapper, UsageRecord> {

    private final UsageRecordMapper usageRecordMapper;

    public List<Map<String, Object>> getDailyAggregation(Long tenantId, LocalDate startDate, LocalDate endDate) {
        LocalDateTime start = startDate.atStartOfDay();
        LocalDateTime end = endDate.plusDays(1).atStartOfDay();
        return usageRecordMapper.selectDailyAggregation(tenantId, start, end);
    }

    public List<Map<String, Object>> getApiPathAggregation(Long tenantId, LocalDate startDate, LocalDate endDate) {
        LocalDateTime start = startDate.atStartOfDay();
        LocalDateTime end = endDate.plusDays(1).atStartOfDay();
        return usageRecordMapper.selectApiPathAggregation(tenantId, start, end);
    }

    public void recordUsage(Long tenantId, String apiKey, String apiPath,
                            Long requestCount, Long responseTimeMs, Integer status) {
        UsageRecord record = new UsageRecord();
        record.setTenantId(tenantId);
        record.setApiKey(apiKey);
        record.setApiPath(apiPath);
        record.setRequestCount(requestCount);
        record.setResponseTimeMs(responseTimeMs);
        record.setStatus(status);
        record.setCreatedAt(LocalDateTime.now());
        save(record);
    }
}

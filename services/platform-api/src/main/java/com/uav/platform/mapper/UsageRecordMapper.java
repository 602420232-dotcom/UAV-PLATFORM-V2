package com.uav.platform.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.uav.platform.entity.UsageRecord;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Mapper
public interface UsageRecordMapper extends BaseMapper<UsageRecord> {

    @Select("SELECT DATE(created_at) as day, SUM(request_count) as total_requests, " +
            "AVG(response_time_ms) as avg_response_time " +
            "FROM sys_usage_record " +
            "WHERE tenant_id = #{tenantId} AND created_at >= #{start} AND created_at < #{end} " +
            "GROUP BY DATE(created_at) ORDER BY day")
    List<Map<String, Object>> selectDailyAggregation(@Param("tenantId") Long tenantId,
                                                      @Param("start") LocalDateTime start,
                                                      @Param("end") LocalDateTime end);

    @Select("SELECT api_path, SUM(request_count) as total_requests " +
            "FROM sys_usage_record " +
            "WHERE tenant_id = #{tenantId} AND created_at >= #{start} AND created_at < #{end} " +
            "GROUP BY api_path ORDER BY total_requests DESC")
    List<Map<String, Object>> selectApiPathAggregation(@Param("tenantId") Long tenantId,
                                                        @Param("start") LocalDateTime start,
                                                        @Param("end") LocalDateTime end);
}

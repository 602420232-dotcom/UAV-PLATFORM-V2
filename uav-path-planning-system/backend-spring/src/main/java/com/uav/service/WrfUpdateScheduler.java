package com.uav.service;

import com.uav.config.UavProperties;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

/**
 * WRF 气象数据定时更新服务。
 * <p>
 * 每 5 分钟执行一次气象数据更新，流程：
 * 1. 扫描 WRF 数据目录检查是否有新文件
 * 2. 将最新数据加载到 {@link WrfDataCacheService} 缓存
 * 3. 记录更新统计和状态日志
 * </p>
 */
@Slf4j
@Service
public class WrfUpdateScheduler {

    private final UavProperties uavProperties;
    private final WrfDataCacheService wrfDataCacheService;

    public WrfUpdateScheduler(UavProperties uavProperties, WrfDataCacheService wrfDataCacheService) {
        this.uavProperties = uavProperties;
        this.wrfDataCacheService = wrfDataCacheService;
    }

    /**
     * 定时更新 WRF 气象数据。
     * <p>
     * fixedRate = 300000ms = 5 分钟。
     * 由 Spring 的 {@link Scheduled} 注解驱动。
     * </p>
     */
    @Scheduled(fixedRateString = "${uav.wrf.update-interval:300000}")
    public void updateWrfData() {
        long startTime = System.currentTimeMillis();
        String dataPath = uavProperties.getWrf().getDataPath();

        try {
            log.info("[WRF] 开始气象数据更新 | 路径={} | 时间={}", dataPath, LocalDateTime.now());

            // 1. 刷新文件缓存（扫描目录、加载最新文件）
            wrfDataCacheService.refresh();

            // 2. 检查更新结果
            long elapsed = System.currentTimeMillis() - startTime;
            boolean available = wrfDataCacheService.isDataAvailable();

            if (available) {
                var stats = wrfDataCacheService.getCacheStats();
                log.info("[WRF] 数据更新完成 | 耗时={}ms | 缓存变量={} | 状态=可用",
                        elapsed, stats.get("cachedVariables"));
            } else {
                log.warn("[WRF] 数据更新完成 | 耗时={}ms | 状态=无可用数据 | 路径={}",
                        elapsed, dataPath);
            }

        } catch (Exception e) {
            log.error("[WRF] 数据更新失败 | 路径={} | 错误={}", dataPath, e.getMessage(), e);
        }
    }
}

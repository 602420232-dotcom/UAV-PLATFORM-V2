package com.uav.weather.scheduler;

import com.uav.weather.service.WeatherCollectorService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * 定时天气数据采集调度器
 * 
 * 按固定频率从多个数据源采集气象数据，
 * 支持 WRF 模型、无人机传感器、地面气象站。
 */
@Slf4j
@Component
@EnableScheduling
public class WeatherCollectionScheduler {

    private final WeatherCollectorService collectorService;

    public WeatherCollectionScheduler(WeatherCollectorService collectorService) {
        this.collectorService = collectorService;
    }

    /**
     * WRF 模型数据采集 - 每 30 分钟执行一次
     * WRF 模型通常每 1-6 小时输出一次预报数据，
     * 30 分钟轮询可及时发现新数据。
     */
    @Scheduled(fixedRateString = "${weather.collection.wrf-interval:1800000}")
    public void collectWrfData() {
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME);
        log.info("[Scheduler] Starting WRF data collection at {}", timestamp);
        try {
            collectorService.collectWrfData();
            log.info("[Scheduler] WRF data collection completed");
        } catch (Exception e) {
            log.error("[Scheduler] WRF data collection failed: {}", e.getMessage());
        }
    }

    /**
     * 地面气象站数据采集 - 每 5 分钟执行一次
     * 地面站数据更新频率较高，5 分钟间隔可满足实时性需求。
     */
    @Scheduled(fixedRateString = "${weather.collection.ground-interval:300000}")
    public void collectGroundStationData() {
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME);
        log.info("[Scheduler] Starting ground station data collection at {}", timestamp);
        try {
            collectorService.collectGroundStationData();
            log.info("[Scheduler] Ground station data collection completed");
        } catch (Exception e) {
            log.error("[Scheduler] Ground station data collection failed: {}", e.getMessage());
        }
    }

    /**
     * 多源数据融合 - 每 15 分钟执行一次
     * 将 WRF、地面站、无人机等多源数据融合为统一气象场。
     */
    @Scheduled(fixedRateString = "${weather.collection.fusion-interval:900000}")
    public void fuseMultiSourceData() {
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME);
        log.info("[Scheduler] Starting multi-source data fusion at {}", timestamp);
        try {
            collectorService.fuseMultiSourceData();
            log.info("[Scheduler] Multi-source data fusion completed");
        } catch (Exception e) {
            log.error("[Scheduler] Multi-source data fusion failed: {}", e.getMessage());
        }
    }

    /**
     * 气象风险评估 - 每 10 分钟执行一次
     * 基于最新融合气象数据评估飞行风险。
     */
    @Scheduled(fixedRateString = "${weather.collection.risk-interval:600000}")
    public void assessWeatherRisk() {
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME);
        log.info("[Scheduler] Starting weather risk assessment at {}", timestamp);
        try {
            collectorService.assessWeatherRisk();
            log.info("[Scheduler] Weather risk assessment completed");
        } catch (Exception e) {
            log.error("[Scheduler] Weather risk assessment failed: {}", e.getMessage());
        }
    }
}

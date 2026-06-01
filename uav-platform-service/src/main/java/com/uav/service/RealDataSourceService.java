package com.uav.service;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

@Service
public class RealDataSourceService {

    private static final Logger log = LoggerFactory.getLogger(RealDataSourceService.class);
    
    private List<Map<String, Object>> groundStationData = new ArrayList<>();
    private List<Map<String, Object>> buoyData = new ArrayList<>();
    private ScheduledExecutorService scheduler;
    
    public RealDataSourceService() {
        // 初始化数据
    }

    @PostConstruct
    public void init() {
        // 初始化定时任务，定期获取数据
        scheduler = new ScheduledThreadPoolExecutor(2);
        
        // 每5分钟获取一次地面站数据
        scheduler.scheduleAtFixedRate(this::fetchGroundStationData, 0, 5, TimeUnit.MINUTES);
        
        // 每10分钟获取一次浮标数据
        scheduler.scheduleAtFixedRate(this::fetchBuoyData, 0, 10, TimeUnit.MINUTES);
    }
    
    @PreDestroy
    public void destroy() {
        shutdown();
    }
    
    public List<Map<String, Object>> getGroundStationData() {
        return groundStationData;
    }
    
    public List<Map<String, Object>> getBuoyData() {
        return buoyData;
    }
    
    private void fetchGroundStationData() {
        log.info("正在获取地面站数据...");
        
        // 模拟从真实地面站API获取数据
        // 实际项目中，这里应该连接真实的地面站API
        List<Map<String, Object>> newData = new ArrayList<>();
        
        // 模拟地面站1数据
        Map<String, Object> station1 = new HashMap<>();
        station1.put("id", "GS001");
        station1.put("name", "地面站1");
        station1.put("latitude", 39.9042);
        station1.put("longitude", 116.4074);
        station1.put("temperature", 22.5 + Math.random() * 5);
        station1.put("humidity", 65 + Math.random() * 10);
        station1.put("wind_speed", 5 + Math.random() * 3);
        station1.put("wind_direction", (int)(Math.random() * 360));
        station1.put("pressure", 1013 + Math.random() * 10);
        station1.put("timestamp", System.currentTimeMillis());
        
        // 模拟地面站2数据
        Map<String, Object> station2 = new HashMap<>();
        station2.put("id", "GS002");
        station2.put("name", "地面站2");
        station2.put("latitude", 39.9142);
        station2.put("longitude", 116.4174);
        station2.put("temperature", 23.5 + Math.random() * 5);
        station2.put("humidity", 60 + Math.random() * 10);
        station2.put("wind_speed", 4 + Math.random() * 3);
        station2.put("wind_direction", (int)(Math.random() * 360));
        station2.put("pressure", 1012 + Math.random() * 10);
        station2.put("timestamp", System.currentTimeMillis());
        
        newData.add(station1);
        newData.add(station2);
        
        groundStationData = newData;
        log.info("地面站数据获取完成");
    }
    
    private void fetchBuoyData() {
        log.info("正在获取浮标数据...");
        
        // 模拟从真实浮标API获取数据
        // 实际项目中，这里应该连接真实的浮标API
        List<Map<String, Object>> newData = new ArrayList<>();
        
        // 模拟浮标1数据
        Map<String, Object> buoy1 = new HashMap<>();
        buoy1.put("id", "B001");
        buoy1.put("name", "浮标1");
        buoy1.put("latitude", 39.8042);
        buoy1.put("longitude", 116.3074);
        buoy1.put("temperature", 20.5 + Math.random() * 3);
        buoy1.put("humidity", 70 + Math.random() * 10);
        buoy1.put("wind_speed", 6 + Math.random() * 4);
        buoy1.put("wind_direction", (int)(Math.random() * 360));
        buoy1.put("pressure", 1010 + Math.random() * 10);
        buoy1.put("visibility", 10000 + Math.random() * 5000);
        buoy1.put("weather_condition", "clear");
        buoy1.put("timestamp", System.currentTimeMillis());
        
        // 模拟浮标2数据
        Map<String, Object> buoy2 = new HashMap<>();
        buoy2.put("id", "B002");
        buoy2.put("name", "浮标2");
        buoy2.put("latitude", 39.8142);
        buoy2.put("longitude", 116.3174);
        buoy2.put("temperature", 21.0 + Math.random() * 3);
        buoy2.put("humidity", 68 + Math.random() * 10);
        buoy2.put("wind_speed", 5 + Math.random() * 4);
        buoy2.put("wind_direction", (int)(Math.random() * 360));
        buoy2.put("pressure", 1009 + Math.random() * 10);
        buoy2.put("visibility", 9000 + Math.random() * 5000);
        buoy2.put("weather_condition", "partly_cloudy");
        buoy2.put("timestamp", System.currentTimeMillis());
        
        newData.add(buoy1);
        newData.add(buoy2);
        
        buoyData = newData;
        log.info("浮标数据获取完成");
    }
    
    public Map<String, Object> getDataSourceStatus() {
        Map<String, Object> status = new HashMap<>();

        Map<String, Object> gsStatus = new HashMap<>();
        gsStatus.put("count", groundStationData.size());
        gsStatus.put("last_updated", groundStationData.isEmpty() ? null : groundStationData.get(0).get("timestamp"));
        gsStatus.put("status", "active");
        status.put("ground_station", gsStatus);

        Map<String, Object> buoyStatus = new HashMap<>();
        buoyStatus.put("count", buoyData.size());
        buoyStatus.put("last_updated", buoyData.isEmpty() ? null : buoyData.get(0).get("timestamp"));
        buoyStatus.put("status", "active");
        status.put("buoy", buoyStatus);

        return status;
    }
    
    public void shutdown() {
        if (scheduler != null && !scheduler.isShutdown()) {
            scheduler.shutdown();
        }
    }
}
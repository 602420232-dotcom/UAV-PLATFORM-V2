package com.uav.service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

import org.springframework.stereotype.Service;

@Service
public class DataSourceService {
    
    // 模拟数据源存储
    private List<Map<String, Object>> dataSources = new ArrayList<>();
    private Long nextId = 1L;
    
    public DataSourceService() {
        // 初始化一些默认数据源
        Map<String, Object> defaultSource1 = new HashMap<>();
        defaultSource1.put("id", nextId++);
        defaultSource1.put("name", "地面站数据源");
        defaultSource1.put("type", "ground_station");
        defaultSource1.put("url", "http://ground-station:8080/api");
        defaultSource1.put("status", "active");
        defaultSource1.put("created_at", "2026-04-15T10:00:00");
        
        Map<String, Object> defaultSource2 = new HashMap<>();
        defaultSource2.put("id", nextId++);
        defaultSource2.put("name", "浮标数据源");
        defaultSource2.put("type", "buoy");
        defaultSource2.put("url", "http://buoy-service:8080/api");
        defaultSource2.put("status", "active");
        defaultSource2.put("created_at", "2026-04-15T10:00:00");
        
        Map<String, Object> defaultSource3 = new HashMap<>();
        defaultSource3.put("id", nextId++);
        defaultSource3.put("name", "气象卫星数据源");
        defaultSource3.put("type", "satellite");
        defaultSource3.put("url", "http://satellite-service:8080/api");
        defaultSource3.put("status", "active");
        defaultSource3.put("created_at", "2026-04-15T10:00:00");
        
        dataSources.add(defaultSource1);
        dataSources.add(defaultSource2);
        dataSources.add(defaultSource3);
    }
    
    public List<Map<String, Object>> listDataSources() {
        return dataSources;
    }
    
    public Map<String, Object> getDataSourceById(Long id) {
        for (Map<String, Object> dataSource : dataSources) {
            if (Objects.equals(dataSource.get("id"), id)) {
                return dataSource;
            }
        }
        return null;
    }
    
    public Map<String, Object> createDataSource(Map<String, Object> requestBody) {
        Map<String, Object> newDataSource = new HashMap<>();
        newDataSource.put("id", nextId++);
        newDataSource.put("name", requestBody.get("name"));
        newDataSource.put("type", requestBody.get("type"));
        newDataSource.put("url", requestBody.get("url"));
        newDataSource.put("status", "active");
        newDataSource.put("created_at", java.time.LocalDateTime.now().toString());
        
        dataSources.add(newDataSource);
        return newDataSource;
    }
    
    public Map<String, Object> updateDataSource(Long id, Map<String, Object> requestBody) {
        for (Map<String, Object> dataSource : dataSources) {
            if (Objects.equals(dataSource.get("id"), id)) {
                if (requestBody.containsKey("name")) {
                    dataSource.put("name", requestBody.get("name"));
                }
                if (requestBody.containsKey("type")) {
                    dataSource.put("type", requestBody.get("type"));
                }
                if (requestBody.containsKey("url")) {
                    dataSource.put("url", requestBody.get("url"));
                }
                if (requestBody.containsKey("status")) {
                    dataSource.put("status", requestBody.get("status"));
                }
                dataSource.put("updated_at", java.time.LocalDateTime.now().toString());
                return dataSource;
            }
        }
        return null;
    }
    
    public boolean deleteDataSource(Long id) {
        for (int i = 0; i < dataSources.size(); i++) {
            if (Objects.equals(dataSources.get(i).get("id"), id)) {
                dataSources.remove(i);
                return true;
            }
        }
        return false;
    }
    
    public Map<String, Object> testDataSource(Map<String, Object> requestBody) {
        // 模拟数据源测试
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("message", "数据源测试成功");
        result.put("response_time", 123); // 毫秒
        result.put("status_code", 200);
        
        // 模拟不同类型数据源的测试结果
        String type = (String) requestBody.get("type");
        if (type != null) {
            switch (type) {
                case "ground_station":
                    result.put("details", "地面站数据源连接正常，数据可用");
                    break;
                case "buoy":
                    result.put("details", "浮标数据源连接正常，数据可用");
                    break;
                case "satellite":
                    result.put("details", "卫星数据源连接正常，数据可用");
                    break;
                default:
                    result.put("details", "未知数据源类型，测试成功");
            }
        }
        
        return result;
    }
    
    public List<Map<String, Object>> getDataSourceTypes() {
        List<Map<String, Object>> types = new ArrayList<>();
        
        Map<String, Object> type1 = new HashMap<>();
        type1.put("value", "ground_station");
        type1.put("label", "地面站数据源");
        type1.put("description", "来自地面站的实时数据");
        
        Map<String, Object> type2 = new HashMap<>();
        type2.put("value", "buoy");
        type2.put("label", "浮标数据源");
        type2.put("description", "来自海洋浮标的数据");
        
        Map<String, Object> type3 = new HashMap<>();
        type3.put("value", "satellite");
        type3.put("label", "卫星数据源");
        type3.put("description", "来自气象卫星的遥感数据");
        
        Map<String, Object> type4 = new HashMap<>();
        type4.put("value", "weather_station");
        type4.put("label", "气象站数据源");
        type4.put("description", "来自地面气象站的观测数据");
        
        types.add(type1);
        types.add(type2);
        types.add(type3);
        types.add(type4);
        
        return types;
    }
}
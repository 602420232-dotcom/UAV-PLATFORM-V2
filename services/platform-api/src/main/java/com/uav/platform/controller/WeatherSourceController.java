package com.uav.platform.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.common.core.result.Result;
import com.uav.platform.entity.WeatherSource;
import com.uav.platform.mapper.WeatherSourceMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 气象数据源管理控制器
 * <p>
 * 提供气象数据源的查询、配置更新、连接测试和状态查询功能。
 * 所有接口均为公开接口，不需要认证。
 */
@RestController
@RequestMapping("/api/v1/weather/sources")
@RequiredArgsConstructor
@Slf4j
public class WeatherSourceController {

    private final WeatherSourceMapper weatherSourceMapper;
    private final ObjectMapper objectMapper;

    private static final DateTimeFormatter FMT = DateTimeFormatter.ISO_LOCAL_DATE_TIME;

    /**
     * 获取所有气象数据源配置
     * <p>
     * 查询 sys_weather_source 表全部记录，将 configJson 解析为 Map 返回。
     * 如果表为空，返回内置的默认数据源列表。
     */
    @GetMapping
    public Result<List<Map<String, Object>>> getAllSources() {
        List<WeatherSource> sources = weatherSourceMapper.selectList(null);

        if (sources.isEmpty()) {
            return Result.success(getDefaultSources());
        }

        List<Map<String, Object>> result = new ArrayList<>();
        for (WeatherSource source : sources) {
            result.add(toSourceMap(source));
        }
        return Result.success(result);
    }

    /**
     * 获取指定数据源详情
     */
    @GetMapping("/{sourceType}")
    public Result<Map<String, Object>> getSourceByType(@PathVariable String sourceType) {
        LambdaQueryWrapper<WeatherSource> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(WeatherSource::getSourceType, sourceType);
        WeatherSource source = weatherSourceMapper.selectOne(wrapper);

        if (source == null) {
            return Result.error(404, "数据源不存在: " + sourceType);
        }

        return Result.success(toSourceMap(source));
    }

    /**
     * 更新数据源配置（UPSERT 逻辑）
     * <p>
     * 请求体：{ enabled, priority, config }
     * 存在则更新，不存在则插入。config 对象序列化为 configJson 存储。
     */
    @PostMapping("/{sourceType}/config")
    public Result<Map<String, Object>> updateConfig(
            @PathVariable String sourceType,
            @RequestBody Map<String, Object> body) {

        LambdaQueryWrapper<WeatherSource> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(WeatherSource::getSourceType, sourceType);
        WeatherSource existing = weatherSourceMapper.selectOne(wrapper);

        LocalDateTime now = LocalDateTime.now();

        if (existing != null) {
            // 更新已有记录
            if (body.containsKey("enabled")) {
                existing.setEnabled((Boolean) body.get("enabled"));
            }
            if (body.containsKey("priority")) {
                existing.setPriority(((Number) body.get("priority")).intValue());
            }
            if (body.containsKey("config")) {
                try {
                    String configJson = objectMapper.writeValueAsString(body.get("config"));
                    existing.setConfigJson(configJson);
                } catch (Exception e) {
                    log.error("序列化 config 失败", e);
                    return Result.error(400, "config 格式错误");
                }
            }
            existing.setUpdatedAt(now);
            weatherSourceMapper.updateById(existing);
            return Result.success(toSourceMap(existing));
        } else {
            // 插入新记录
            WeatherSource newSource = new WeatherSource();
            newSource.setSourceType(sourceType);
            newSource.setName(getDefaultName(sourceType));
            newSource.setEnabled(body.containsKey("enabled") ? (Boolean) body.get("enabled") : true);
            newSource.setPriority(body.containsKey("priority") ? ((Number) body.get("priority")).intValue() : 0);
            newSource.setForecastHours(72);
            newSource.setResolution("3km");

            if (body.containsKey("config")) {
                try {
                    String configJson = objectMapper.writeValueAsString(body.get("config"));
                    newSource.setConfigJson(configJson);
                } catch (Exception e) {
                    log.error("序列化 config 失败", e);
                    return Result.error(400, "config 格式错误");
                }
            }

            newSource.setCreatedAt(now);
            newSource.setUpdatedAt(now);
            weatherSourceMapper.insert(newSource);
            return Result.success(toSourceMap(newSource));
        }
    }

    /**
     * 测试数据源连接
     * <p>
     * 模拟测试：返回成功结果。后续可替换为真实 HTTP 调用 Python 引擎。
     */
    @PostMapping("/{sourceType}/test")
    public Result<Map<String, Object>> testConnection(@PathVariable String sourceType) {
        log.info("测试气象数据源连接: {}", sourceType);

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("success", true);
        result.put("message", "连接测试成功（模拟）");
        result.put("sourceType", sourceType);
        result.put("testedAt", LocalDateTime.now().format(FMT));

        return Result.success(result);
    }

    /**
     * 获取数据源状态
     * <p>
     * 返回各数据源的启用状态和最后更新时间。
     */
    @GetMapping("/status")
    public Result<List<Map<String, Object>>> getStatus() {
        List<WeatherSource> sources = weatherSourceMapper.selectList(null);

        List<Map<String, Object>> statusList = new ArrayList<>();
        if (sources.isEmpty()) {
            // 表为空时返回默认数据源状态
            for (Map<String, Object> defaultSource : getDefaultSources()) {
                Map<String, Object> status = new LinkedHashMap<>();
                status.put("sourceType", defaultSource.get("sourceType"));
                status.put("name", defaultSource.get("name"));
                status.put("enabled", defaultSource.get("enabled"));
                status.put("lastUpdated", null);
                statusList.add(status);
            }
        } else {
            for (WeatherSource source : sources) {
                Map<String, Object> status = new LinkedHashMap<>();
                status.put("sourceType", source.getSourceType());
                status.put("name", source.getName());
                status.put("enabled", source.getEnabled());
                status.put("lastUpdated", source.getUpdatedAt() != null
                        ? source.getUpdatedAt().format(FMT) : null);
                statusList.add(status);
            }
        }

        return Result.success(statusList);
    }

    // ==================== 私有辅助方法 ====================

    /**
     * 将 WeatherSource 实体转换为前端所需的 Map 格式
     */
    private Map<String, Object> toSourceMap(WeatherSource source) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("sourceType", source.getSourceType());
        map.put("name", source.getName());
        map.put("enabled", source.getEnabled());
        map.put("priority", source.getPriority());
        map.put("forecastHours", source.getForecastHours());
        map.put("resolution", source.getResolution());

        // 解析 configJson 为 Map
        Map<String, Object> config = new LinkedHashMap<>();
        if (source.getConfigJson() != null && !source.getConfigJson().isBlank()) {
            try {
                config = objectMapper.readValue(source.getConfigJson(),
                        new TypeReference<LinkedHashMap<String, Object>>() {});
            } catch (Exception e) {
                log.warn("解析 configJson 失败, sourceType={}: {}", source.getSourceType(), e.getMessage());
            }
        }
        map.put("config", config);

        return map;
    }

    /**
     * 获取内置默认数据源列表（风雷、天资、风乌）
     */
    private List<Map<String, Object>> getDefaultSources() {
        List<Map<String, Object>> defaults = new ArrayList<>();

        // 风雷气象
        Map<String, Object> fenglei = new LinkedHashMap<>();
        fenglei.put("sourceType", "fenglei");
        fenglei.put("name", "风雷气象");
        fenglei.put("enabled", true);
        fenglei.put("priority", 10);
        fenglei.put("forecastHours", 72);
        fenglei.put("resolution", "3km");
        Map<String, Object> fengleiConfig = new LinkedHashMap<>();
        fengleiConfig.put("apiEndpoint", "https://fenglei.example.com/api");
        fengleiConfig.put("apiKey", "");
        fengleiConfig.put("timeout", 30000);
        fenglei.put("config", fengleiConfig);
        defaults.add(fenglei);

        // 天资气象
        Map<String, Object> tianzi = new LinkedHashMap<>();
        tianzi.put("sourceType", "tianzi");
        tianzi.put("name", "天资气象");
        tianzi.put("enabled", true);
        tianzi.put("priority", 5);
        tianzi.put("forecastHours", 120);
        tianzi.put("resolution", "0.25\u00B0");
        Map<String, Object> tianziConfig = new LinkedHashMap<>();
        tianziConfig.put("apiEndpoint", "https://tianzi.example.com/api");
        tianziConfig.put("apiKey", "");
        tianziConfig.put("timeout", 30000);
        tianzi.put("config", tianziConfig);
        defaults.add(tianzi);

        // 风乌气象
        Map<String, Object> fengwu = new LinkedHashMap<>();
        fengwu.put("sourceType", "fengwu");
        fengwu.put("name", "风乌气象");
        fengwu.put("enabled", false);
        fengwu.put("priority", 1);
        fengwu.put("forecastHours", 48);
        fengwu.put("resolution", "9km");
        Map<String, Object> fengwuConfig = new LinkedHashMap<>();
        fengwuConfig.put("apiEndpoint", "");
        fengwuConfig.put("apiKey", "");
        fengwuConfig.put("timeout", 30000);
        fengwu.put("config", fengwuConfig);
        defaults.add(fengwu);

        return defaults;
    }

    /**
     * 根据 sourceType 获取默认显示名称
     */
    private String getDefaultName(String sourceType) {
        switch (sourceType) {
            case "fenglei": return "风雷气象";
            case "tianzi": return "天资气象";
            case "fengwu": return "风乌气象";
            default: return sourceType;
        }
    }
}

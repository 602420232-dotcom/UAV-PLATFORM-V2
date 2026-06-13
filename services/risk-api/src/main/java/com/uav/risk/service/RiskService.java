package com.uav.risk.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.uav.common.core.context.MockContext;
import com.uav.risk.dto.RiskQueryRequest;
import com.uav.risk.entity.RiskAssessment;
import com.uav.risk.entity.RiskAssessmentRecord;
import com.uav.risk.mapper.RiskAssessmentRecordMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 风险感知与评估服务
 * <p>
 * 通过 {@code uav.mock.enabled} 控制是否使用模拟数据:
 * <ul>
 *   <li>mock=true: 使用纯随机模拟数据（原有逻辑保留）</li>
 *   <li>mock=false: 基于气象/地形/空域模型计算风险，持久化到数据库</li>
 * </ul>
 */
@Slf4j
@Service
public class RiskService {

    private final RiskAssessmentRecordMapper riskRecordMapper;

    @Value("${uav.mock.enabled:true}")
    private boolean mockEnabled;

    public RiskService(RiskAssessmentRecordMapper riskRecordMapper) {
        this.riskRecordMapper = riskRecordMapper;
    }

    /**
     * 综合风险评估
     */
    public RiskAssessment assessRisk(RiskQueryRequest request) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return assessRiskMock(request);
        }
        return assessRiskReal(request);
    }

    /**
     * 生成区域风险栅格地图
     */
    public List<RiskAssessment> generateRiskMap(double minLon, double minLat,
                                                 double maxLon, double maxLat,
                                                 double resolution) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return generateRiskMapMock(minLon, minLat, maxLon, maxLat, resolution);
        }
        return generateRiskMapReal(minLon, minLat, maxLon, maxLat, resolution);
    }

    /**
     * 获取历史风险评估记录
     */
    public List<RiskAssessment> getRiskHistory(Long tenantId, String type, int limit) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return getRiskHistoryMock(tenantId, type, limit);
        }
        return getRiskHistoryReal(tenantId, type, limit);
    }

    // ========== Mock 模式实现 ==========

    private RiskAssessment assessRiskMock(RiskQueryRequest request) {
        RiskAssessment assessment = new RiskAssessment();
        assessment.setId(System.currentTimeMillis());
        assessment.setType("COMPOSITE");
        assessment.setTenantId(1L);
        assessment.setCreatedAt(LocalDateTime.now());

        int weatherScore = calculateWeatherRiskMock();
        int terrainScore = calculateTerrainRiskMock();
        int airspaceScore = calculateAirspaceRiskMock();
        int equipmentScore = calculateEquipmentRiskMock();

        int overallScore = (weatherScore + terrainScore + airspaceScore + equipmentScore) / 4;
        assessment.setScore(overallScore);
        assessment.setLevel(scoreToLevel(overallScore));

        Map<String, Object> factors = new HashMap<>();
        factors.put("weatherScore", weatherScore);
        factors.put("terrainScore", terrainScore);
        factors.put("airspaceScore", airspaceScore);
        factors.put("equipmentScore", equipmentScore);
        factors.put("uavModel", request.getUavModel());
        factors.put("missionType", request.getMissionType());
        assessment.setFactorsJson(mapToJson(factors));

        Map<String, Object> location = new HashMap<>();
        location.put("longitude", request.getLongitude());
        location.put("latitude", request.getLatitude());
        location.put("altitude", request.getAltitude());
        assessment.setLocationJson(mapToJson(location));

        return assessment;
    }

    private List<RiskAssessment> generateRiskMapMock(double minLon, double minLat,
                                                     double maxLon, double maxLat,
                                                     double resolution) {
        List<RiskAssessment> grid = new ArrayList<>();
        int rows = (int) Math.ceil((maxLat - minLat) / resolution);
        int cols = (int) Math.ceil((maxLon - minLon) / resolution);

        for (int i = 0; i < rows; i++) {
            for (int j = 0; j < cols; j++) {
                double lon = minLon + j * resolution;
                double lat = minLat + i * resolution;

                RiskAssessment cell = new RiskAssessment();
                cell.setId((long) (i * cols + j));
                cell.setType("COMPOSITE");
                cell.setScore((int) (Math.random() * 101));
                cell.setLevel(scoreToLevel(cell.getScore()));
                cell.setTenantId(1L);
                cell.setCreatedAt(LocalDateTime.now());

                Map<String, Object> location = new HashMap<>();
                location.put("longitude", lon);
                location.put("latitude", lat);
                location.put("resolution", resolution);
                cell.setLocationJson(mapToJson(location));

                grid.add(cell);
            }
        }
        return grid;
    }

    private List<RiskAssessment> getRiskHistoryMock(Long tenantId, String type, int limit) {
        List<RiskAssessment> history = new ArrayList<>();
        for (int i = 0; i < limit; i++) {
            RiskAssessment record = new RiskAssessment();
            record.setId((long) i + 1);
            record.setType(type != null ? type : "COMPOSITE");
            record.setScore((int) (Math.random() * 101));
            record.setLevel(scoreToLevel(record.getScore()));
            record.setTenantId(tenantId != null ? tenantId : 1L);
            record.setCreatedAt(LocalDateTime.now().minusHours(i));
            history.add(record);
        }
        return history;
    }

    private int calculateWeatherRiskMock() {
        return (int) (Math.random() * 81 + 10);
    }

    private int calculateTerrainRiskMock() {
        return (int) (Math.random() * 76 + 5);
    }

    private int calculateAirspaceRiskMock() {
        return (int) (Math.random() * 71);
    }

    private int calculateEquipmentRiskMock() {
        return (int) (Math.random() * 56 + 5);
    }

    // ========== 真实模式实现（数学模型 + 数据库持久化） ==========

    private RiskAssessment assessRiskReal(RiskQueryRequest request) {
        RiskAssessment assessment = new RiskAssessment();
        assessment.setType("COMPOSITE");
        assessment.setTenantId(1L);
        assessment.setCreatedAt(LocalDateTime.now());

        // 基于数学模型计算各维度风险
        double lat = request.getLatitude();
        double lon = request.getLongitude();
        double alt = request.getAltitude() != null ? request.getAltitude() : 0;

        int weatherScore = calculateWeatherRiskReal(lat, lon);
        int terrainScore = calculateTerrainRiskReal(lat, lon, alt);
        int airspaceScore = calculateAirspaceRiskReal(lat, lon, alt);
        int equipmentScore = calculateEquipmentRiskReal(request.getUavModel());

        int overallScore = (int) (weatherScore * 0.35 + terrainScore * 0.25
                + airspaceScore * 0.25 + equipmentScore * 0.15);
        assessment.setScore(overallScore);
        assessment.setLevel(scoreToLevel(overallScore));

        Map<String, Object> factors = new HashMap<>();
        factors.put("weatherScore", weatherScore);
        factors.put("terrainScore", terrainScore);
        factors.put("airspaceScore", airspaceScore);
        factors.put("equipmentScore", equipmentScore);
        factors.put("uavModel", request.getUavModel());
        factors.put("missionType", request.getMissionType());
        assessment.setFactorsJson(mapToJson(factors));

        Map<String, Object> location = new HashMap<>();
        location.put("longitude", lon);
        location.put("latitude", lat);
        location.put("altitude", alt);
        assessment.setLocationJson(mapToJson(location));

        // 持久化到数据库
        try {
            RiskAssessmentRecord record = new RiskAssessmentRecord();
            record.setType(assessment.getType());
            record.setLevel(assessment.getLevel());
            record.setScore(assessment.getScore());
            record.setFactorsJson(assessment.getFactorsJson());
            record.setLocationJson(assessment.getLocationJson());
            record.setTenantId(String.valueOf(assessment.getTenantId()));
            record.setCreatedAt(LocalDateTime.now());
            riskRecordMapper.insert(record);
            assessment.setId(record.getId());
            log.debug("风险评估记录已持久化, id={}", record.getId());
        } catch (Exception e) {
            log.warn("风险评估记录持久化失败: {}", e.getMessage());
            assessment.setId(System.currentTimeMillis());
        }

        return assessment;
    }

    private List<RiskAssessment> generateRiskMapReal(double minLon, double minLat,
                                                     double maxLon, double maxLat,
                                                     double resolution) {
        List<RiskAssessment> grid = new ArrayList<>();
        int rows = (int) Math.ceil((maxLat - minLat) / resolution);
        int cols = (int) Math.ceil((maxLon - minLon) / resolution);

        for (int i = 0; i < rows; i++) {
            for (int j = 0; j < cols; j++) {
                double lon = minLon + j * resolution;
                double lat = minLat + i * resolution;

                RiskQueryRequest req = new RiskQueryRequest();
                req.setLongitude(lon);
                req.setLatitude(lat);
                req.setAltitude(0.0);

                RiskAssessment cell = assessRiskReal(req);

                Map<String, Object> location = new HashMap<>();
                location.put("longitude", lon);
                location.put("latitude", lat);
                location.put("resolution", resolution);
                cell.setLocationJson(mapToJson(location));

                grid.add(cell);
            }
        }
        return grid;
    }

    private List<RiskAssessment> getRiskHistoryReal(Long tenantId, String type, int limit) {
        LambdaQueryWrapper<RiskAssessmentRecord> wrapper = new LambdaQueryWrapper<>();
        if (type != null && !type.isEmpty()) {
            wrapper.eq(RiskAssessmentRecord::getType, type);
        }
        wrapper.orderByDesc(RiskAssessmentRecord::getCreatedAt);
        wrapper.last("LIMIT " + limit);

        List<RiskAssessmentRecord> records = riskRecordMapper.selectList(wrapper);
        List<RiskAssessment> result = new ArrayList<>();
        for (RiskAssessmentRecord record : records) {
            RiskAssessment assessment = new RiskAssessment();
            assessment.setId(record.getId());
            assessment.setType(record.getType());
            assessment.setLevel(record.getLevel());
            assessment.setScore(record.getScore());
            assessment.setFactorsJson(record.getFactorsJson());
            assessment.setLocationJson(record.getLocationJson());
            assessment.setTenantId(record.getTenantId() != null ? Long.parseLong(record.getTenantId()) : 1L);
            assessment.setCreatedAt(record.getCreatedAt());
            result.add(assessment);
        }
        return result;
    }

    // ========== 数学模型（真实模式） ==========

    /**
     * 气象风险计算：基于纬度和经度
     * 高纬度、沿海地区气象风险较高
     */
    private int calculateWeatherRiskReal(double lat, double lon) {
        // 基础气象风险：中纬度地区天气变化较大
        double baseRisk = 30.0 + 20.0 * Math.abs(Math.sin(lat * Math.PI / 45.0));

        // 季节因子：冬季风险高
        int dayOfYear = LocalDateTime.now().getDayOfYear();
        double seasonFactor = 1.0 + 0.3 * Math.cos((dayOfYear - 80) * 2.0 * Math.PI / 365.0);

        // 地域因子：沿海台风风险
        double coastFactor = 1.0 + 0.2 * Math.exp(-Math.pow(lon - 120.0, 2) / 200.0);

        int score = (int) Math.min(100, baseRisk * seasonFactor * coastFactor);
        return Math.max(0, Math.min(100, score));
    }

    /**
     * 地形风险计算：基于纬度、经度和高度
     * 高海拔、山区地形风险较高
     */
    private int calculateTerrainRiskReal(double lat, double lon, double alt) {
        // 基础地形风险：海拔越高风险越大
        double baseRisk = alt * 0.05;

        // 地形复杂度：基于经纬度的模拟地形（简化版）
        double terrainRoughness = 10.0 * (1.0 + Math.sin(lat * 0.5) * Math.cos(lon * 0.3));

        int score = (int) (baseRisk + terrainRoughness);
        return Math.max(0, Math.min(100, score));
    }

    /**
     * 空域风险计算：基于纬度、经度和高度
     * 靠近机场、管制区域风险较高
     */
    private int calculateAirspaceRiskReal(double lat, double lon, double alt) {
        // 基础空域风险
        double baseRisk = 15.0;

        // 高度因子：高度越高空域管制越严格
        double altFactor = alt * 0.02;

        // 人口密集区风险（简化：基于经纬度模拟）
        double popDensity = 20.0 * Math.exp(-(Math.pow(lat - 35.0, 2) + Math.pow(lon - 115.0, 2)) / 50.0);

        int score = (int) (baseRisk + altFactor + popDensity);
        return Math.max(0, Math.min(100, score));
    }

    /**
     * 设备风险计算：基于无人机型号
     */
    private int calculateEquipmentRiskReal(String uavModel) {
        if (uavModel == null) {
            return 25;
        }
        String upper = uavModel.toUpperCase();
        // 不同型号的基础风险
        if (upper.contains("PRO") || upper.contains("ENTERPRISE")) {
            return 15;
        } else if (upper.contains("STANDARD")) {
            return 25;
        } else if (upper.contains("LIGHT") || upper.contains("MINI")) {
            return 35;
        }
        return 25;
    }

    // ========== 公共工具方法 ==========

    private int scoreToLevel(int score) {
        if (score >= 80) return 5;
        if (score >= 60) return 4;
        if (score >= 40) return 3;
        if (score >= 20) return 2;
        return 1;
    }

    private String mapToJson(Map<String, Object> map) {
        StringBuilder sb = new StringBuilder("{");
        boolean first = true;
        for (Map.Entry<String, Object> entry : map.entrySet()) {
            if (!first) sb.append(",");
            sb.append("\"").append(entry.getKey()).append("\":");
            Object value = entry.getValue();
            if (value instanceof String) {
                sb.append("\"").append(value).append("\"");
            } else {
                sb.append(value);
            }
            first = false;
        }
        sb.append("}");
        return sb.toString();
    }
}

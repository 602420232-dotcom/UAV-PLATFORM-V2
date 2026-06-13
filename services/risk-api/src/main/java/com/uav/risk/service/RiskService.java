package com.uav.risk.service;

import com.uav.risk.dto.RiskQueryRequest;
import com.uav.risk.entity.RiskAssessment;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;

/**
 * 风险感知与评估服务
 */
@Service
public class RiskService {

    /**
     * 综合风险评估（模拟计算各维度风险）
     */
    public RiskAssessment assessRisk(RiskQueryRequest request) {
        RiskAssessment assessment = new RiskAssessment();
        assessment.setId(System.currentTimeMillis());
        assessment.setType("COMPOSITE");
        assessment.setTenantId(1L);
        assessment.setCreatedAt(LocalDateTime.now());

        // 模拟各维度风险计算
        int weatherScore = calculateWeatherRisk(request);
        int terrainScore = calculateTerrainRisk(request);
        int airspaceScore = calculateAirspaceRisk(request);
        int equipmentScore = calculateEquipmentRisk(request);

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

    /**
     * 生成区域风险栅格地图
     */
    public List<RiskAssessment> generateRiskMap(double minLon, double minLat,
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
                cell.setScore(ThreadLocalRandom.current().nextInt(0, 101));
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

    /**
     * 获取历史风险评估记录
     */
    public List<RiskAssessment> getRiskHistory(Long tenantId, String type, int limit) {
        List<RiskAssessment> history = new ArrayList<>();
        for (int i = 0; i < limit; i++) {
            RiskAssessment record = new RiskAssessment();
            record.setId((long) i + 1);
            record.setType(type != null ? type : "COMPOSITE");
            record.setScore(ThreadLocalRandom.current().nextInt(0, 101));
            record.setLevel(scoreToLevel(record.getScore()));
            record.setTenantId(tenantId != null ? tenantId : 1L);
            record.setCreatedAt(LocalDateTime.now().minusHours(i));
            history.add(record);
        }
        return history;
    }

    private int calculateWeatherRisk(RiskQueryRequest request) {
        // MVP: 模拟气象风险计算
        return ThreadLocalRandom.current().nextInt(10, 91);
    }

    private int calculateTerrainRisk(RiskQueryRequest request) {
        // MVP: 模拟地形风险计算
        return ThreadLocalRandom.current().nextInt(5, 81);
    }

    private int calculateAirspaceRisk(RiskQueryRequest request) {
        // MVP: 模拟空域风险计算
        return ThreadLocalRandom.current().nextInt(0, 71);
    }

    private int calculateEquipmentRisk(RiskQueryRequest request) {
        // MVP: 模拟设备风险计算
        return ThreadLocalRandom.current().nextInt(5, 61);
    }

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

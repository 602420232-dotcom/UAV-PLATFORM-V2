package com.uav.risk.service;

import com.uav.common.core.context.MockContext;
import com.uav.risk.dto.AirworthinessRequest;
import com.uav.risk.entity.AirworthinessAssessment;
import com.uav.risk.entity.AirworthinessRecord;
import com.uav.risk.mapper.AirworthinessRecordMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 适航评估服务
 * <p>
 * 通过 {@code uav.mock.enabled} 控制是否使用模拟数据:
 * <ul>
 *   <li>mock=true: 使用纯内存计算（原有逻辑保留）</li>
 *   <li>mock=false: 计算结果持久化到数据库</li>
 * </ul>
 */
@Slf4j
@Service
public class AirworthinessService {

    private final AirworthinessRecordMapper airworthinessRecordMapper;

    @Value("${uav.mock.enabled:true}")
    private boolean mockEnabled;

    public AirworthinessService(AirworthinessRecordMapper airworthinessRecordMapper) {
        this.airworthinessRecordMapper = airworthinessRecordMapper;
    }

    /**
     * 全维度适航评估
     */
    public AirworthinessAssessment assessAirworthiness(AirworthinessRequest request) {
        if (mockEnabled) {
            MockContext.setMockMode();
        }
        AirworthinessAssessment assessment = new AirworthinessAssessment();
        assessment.setUavModel(request.getUavModel());
        assessment.setTenantId(1L);
        assessment.setCreatedAt(LocalDateTime.now());

        // 全维度评分计算
        int weatherScore = assessWeatherDimension(request);
        int structureScore = assessStructureDimension(request);
        int powerScore = assessPowerDimension(request);
        int communicationScore = assessCommunicationDimension(request);
        int missionScore = assessMissionDimension(request);

        int overallScore = (weatherScore + structureScore + powerScore + communicationScore + missionScore) / 5;
        assessment.setOverallScore(overallScore);
        assessment.setStatus(determineStatus(overallScore));

        Map<String, Integer> dimensionScores = new HashMap<>();
        dimensionScores.put("weather", weatherScore);
        dimensionScores.put("structure", structureScore);
        dimensionScores.put("power", powerScore);
        dimensionScores.put("communication", communicationScore);
        dimensionScores.put("mission", missionScore);
        assessment.setDimensionScoresJson(mapToJson(dimensionScores));

        List<String> recommendations = generateRecommendations(weatherScore, structureScore,
                powerScore, communicationScore, missionScore, request);
        assessment.setRecommendationsJson(listToJson(recommendations));

        // 真实模式：持久化到数据库
        if (!mockEnabled) {
            try {
                AirworthinessRecord record = new AirworthinessRecord();
                record.setUavModel(assessment.getUavModel());
                record.setOverallScore((double) assessment.getOverallScore());
                record.setDimensionScoresJson(assessment.getDimensionScoresJson());
                record.setStatus(assessment.getStatus());
                record.setRecommendationsJson(assessment.getRecommendationsJson());
                record.setTenantId("1");
                record.setCreatedAt(LocalDateTime.now());
                airworthinessRecordMapper.insert(record);
                assessment.setId(record.getId());
                log.debug("适航评估记录已持久化, id={}", record.getId());
            } catch (Exception e) {
                log.warn("适航评估记录持久化失败: {}", e.getMessage());
                assessment.setId(System.currentTimeMillis());
            }
        } else {
            assessment.setId(System.currentTimeMillis());
        }

        return assessment;
    }

    /**
     * 获取适航标准信息
     */
    public Map<String, Object> getAirworthinessStandard(String uavModel) {
        Map<String, Object> standard = new HashMap<>();
        standard.put("uavModel", uavModel);
        standard.put("category", determineCategory(uavModel));
        standard.put("maxTakeoffWeight", 25.0);
        standard.put("maxAltitude", 120);
        standard.put("maxSpeed", 25.0);
        standard.put("weatherLimit", Map.of(
                "maxWindSpeed", 10.8,
                "minVisibility", 5.0,
                "maxPrecipitation", 0.0,
                "temperatureRange", List.of(-10, 40)
        ));
        standard.put("structureRequirements", List.of(
                "机身无裂纹",
                "螺旋桨完好",
                "起落架正常"
        ));
        standard.put("powerRequirements", List.of(
                "电池电量 >= 30%",
                "电机运转正常",
                "续航时间满足任务需求"
        ));
        standard.put("communicationRequirements", List.of(
                "遥控信号强度 >= -90dBm",
                "图传信号稳定",
                "GPS 卫星数 >= 8"
        ));
        standard.put("updatedAt", LocalDateTime.now().toString());
        return standard;
    }

    // ========== 各维度评估方法 ==========

    private int assessWeatherDimension(AirworthinessRequest request) {
        Map<String, Object> weather = request.getWeatherConditions();
        if (weather == null) {
            return 85;
        }
        int score = 100;
        Object windSpeed = weather.get("windSpeed");
        if (windSpeed instanceof Number && ((Number) windSpeed).doubleValue() > 10.8) {
            score -= 30;
        }
        Object visibility = weather.get("visibility");
        if (visibility instanceof Number && ((Number) visibility).doubleValue() < 5.0) {
            score -= 25;
        }
        Object precipitation = weather.get("precipitation");
        if (precipitation instanceof Number && ((Number) precipitation).doubleValue() > 0.0) {
            score -= 35;
        }
        return Math.max(0, score);
    }

    private int assessStructureDimension(AirworthinessRequest request) {
        int score = 90;
        if (request.getWeight() != null && request.getWeight() > 25.0) {
            score -= 20;
        }
        if (request.getWingspan() != null && request.getWingspan() > 3.0) {
            score -= 10;
        }
        return Math.max(0, score);
    }

    private int assessPowerDimension(AirworthinessRequest request) {
        int score = 85;
        if (request.getBatteryCapacity() != null) {
            if (request.getBatteryCapacity() < 3000) {
                score -= 25;
            } else if (request.getBatteryCapacity() < 5000) {
                score -= 10;
            }
        }
        return Math.max(0, score);
    }

    private int assessCommunicationDimension(AirworthinessRequest request) {
        // MVP: 模拟通信适航评估
        return 88;
    }

    private int assessMissionDimension(AirworthinessRequest request) {
        int score = 90;
        String missionType = request.getMissionType();
        if (missionType != null) {
            switch (missionType.toUpperCase()) {
                case "SURVEILLANCE":
                case "INSPECTION":
                    score -= 5;
                    break;
                case "DELIVERY":
                    score -= 15;
                    break;
                case "EMERGENCY":
                    score -= 20;
                    break;
                default:
                    break;
            }
        }
        return Math.max(0, score);
    }

    private String determineStatus(int overallScore) {
        if (overallScore >= 80) return "PASS";
        if (overallScore >= 60) return "WARNING";
        return "FAIL";
    }

    private String determineCategory(String uavModel) {
        if (uavModel == null) return "UNKNOWN";
        String upper = uavModel.toUpperCase();
        if (upper.contains("MULTIROTOR") || upper.contains("QUAD") || upper.contains("HEXA")) {
            return "MULTIROTOR";
        }
        if (upper.contains("FIXED") || upper.contains("WING")) {
            return "FIXED_WING";
        }
        if (upper.contains("VTOL")) {
            return "VTOL";
        }
        return "GENERAL";
    }

    private List<String> generateRecommendations(int weatherScore, int structureScore,
                                                  int powerScore, int communicationScore,
                                                  int missionScore, AirworthinessRequest request) {
        List<String> recommendations = new ArrayList<>();
        if (weatherScore < 60) {
            recommendations.add("气象条件不满足适航要求，建议等待天气好转或更换作业区域");
        }
        if (structureScore < 60) {
            recommendations.add("结构适航评分较低，建议进行机体检查并确认重量/尺寸在限制范围内");
        }
        if (powerScore < 60) {
            recommendations.add("动力适航评分较低，建议更换高容量电池或缩短任务航线");
        }
        if (communicationScore < 60) {
            recommendations.add("通信适航评分较低，建议检查天线、确认作业区域信号覆盖");
        }
        if (missionScore < 60) {
            recommendations.add("任务适航评分较低，建议评估任务复杂度并调整飞行计划");
        }
        if (recommendations.isEmpty()) {
            recommendations.add("当前条件下适航评估通过，可按计划执行任务");
        }
        return recommendations;
    }

    private String mapToJson(Map<String, ?> map) {
        StringBuilder sb = new StringBuilder("{");
        boolean first = true;
        for (Map.Entry<String, ?> entry : map.entrySet()) {
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

    private String listToJson(List<String> list) {
        StringBuilder sb = new StringBuilder("[");
        for (int i = 0; i < list.size(); i++) {
            if (i > 0) sb.append(",");
            sb.append("\"").append(list.get(i)).append("\"");
        }
        sb.append("]");
        return sb.toString();
    }
}

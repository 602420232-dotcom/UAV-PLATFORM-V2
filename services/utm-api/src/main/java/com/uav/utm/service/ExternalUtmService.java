package com.uav.utm.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.uav.common.resilience.annotation.WithCircuitBreaker;
import com.uav.utm.entity.FlightPlan;
import com.uav.utm.entity.UavPosition;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.*;

/**
 * 外部 UTM 对接服务
 * <p>
 * 负责与外部 UTM 系统的双向通信，包括：
 * <ul>
 *   <li>飞行计划提交</li>
 *   <li>位置上报</li>
 *   <li>告警接收（模拟轮询）</li>
 *   <li>空域限制查询</li>
 * </ul>
 * <p>
 * 通过 {@code uav.utm.external.enabled} 控制是否启用外部对接。
 * 未启用时所有方法返回模拟数据。
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ExternalUtmService {

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    @Value("${uav.utm.external.enabled:false}")
    private boolean externalEnabled;

    @Value("${uav.utm.external.base-url:http://external-utm-api:8080}")
    private String externalBaseUrl;

    @Value("${uav.utm.external.api-key:}")
    private String externalApiKey;

    @Value("${uav.utm.external.alert-poll-interval-ms:5000}")
    private long alertPollIntervalMs;

    // ===== 飞行计划提交 =====

    /**
     * 向外部 UTM 提交飞行计划
     *
     * @param flightPlan 飞行计划
     * @return 外部 UTM 返回的审批结果
     */
    @WithCircuitBreaker(name = "externalUtm", failureRateThreshold = 60,
            slowCallDurationThreshold = 3000, waitDurationInOpenState = 30000)
    public Map<String, Object> submitFlightPlanToUtm(FlightPlan flightPlan) {
        if (!externalEnabled) {
            log.info("[MOCK] 跳过外部UTM飞行计划提交, planId={}", flightPlan.getPlanId());
            return mockSubmitResponse(flightPlan);
        }

        String url = externalBaseUrl + "/api/v1/flight-plans";
        try {
            Map<String, Object> body = buildFlightPlanBody(flightPlan);
            HttpHeaders headers = buildHeaders();
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);

            ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.POST, request, String.class);
            JsonNode jsonNode = objectMapper.readTree(response.getBody());

            Map<String, Object> result = new HashMap<>();
            result.put("externalPlanId", jsonNode.path("planId").asText());
            result.put("status", jsonNode.path("status").asText());
            result.put("approvalCode", jsonNode.path("approvalCode").asText());
            log.info("飞行计划已提交到外部UTM, planId={}, externalStatus={}",
                    flightPlan.getPlanId(), result.get("status"));
            return result;
        } catch (Exception e) {
            log.error("提交飞行计划到外部UTM失败, planId={}", flightPlan.getPlanId(), e);
            return Map.of("status", "SUBMIT_FAILED", "error", e.getMessage());
        }
    }

    // ===== 位置上报 =====

    /**
     * 向外部 UTM 上报无人机位置
     *
     * @param uavPosition 无人机位置
     * @return 上报结果
     */
    @WithCircuitBreaker(name = "externalUtm", failureRateThreshold = 60,
            slowCallDurationThreshold = 2000, waitDurationInOpenState = 15000)
    public Map<String, Object> reportPositionToUtm(UavPosition uavPosition) {
        if (!externalEnabled) {
            log.debug("[MOCK] 跳过外部UTM位置上报, uavId={}", uavPosition.getUavId());
            return Map.of("status", "REPORTED");
        }

        String url = externalBaseUrl + "/api/v1/positions/report";
        try {
            Map<String, Object> body = Map.of(
                    "uavId", uavPosition.getUavId(),
                    "longitude", uavPosition.getLongitude(),
                    "latitude", uavPosition.getLatitude(),
                    "altitude", uavPosition.getAltitude(),
                    "speed", uavPosition.getSpeed() != null ? uavPosition.getSpeed() : 0.0,
                    "heading", uavPosition.getHeading() != null ? uavPosition.getHeading() : 0.0,
                    "timestamp", uavPosition.getRecordedAt() != null
                            ? uavPosition.getRecordedAt().toString() : LocalDateTime.now().toString()
            );
            HttpHeaders headers = buildHeaders();
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);

            restTemplate.exchange(url, HttpMethod.POST, request, String.class);
            log.debug("位置已上报到外部UTM, uavId={}", uavPosition.getUavId());
            return Map.of("status", "REPORTED");
        } catch (Exception e) {
            log.error("上报位置到外部UTM失败, uavId={}", uavPosition.getUavId(), e);
            return Map.of("status", "REPORT_FAILED", "error", e.getMessage());
        }
    }

    // ===== 告警接收（模拟轮询） =====

    /**
     * 接收外部 UTM 告警（模拟轮询）
     * <p>
     * 在实际对接中，应替换为 WebSocket 推送或回调机制。
     *
     * @return 告警列表
     */
    @WithCircuitBreaker(name = "externalUtm", failureRateThreshold = 70,
            slowCallDurationThreshold = 5000, waitDurationInOpenState = 30000)
    public List<Map<String, Object>> receiveUtmAlerts() {
        if (!externalEnabled) {
            log.debug("[MOCK] 跳过外部UTM告警轮询");
            return List.of();
        }

        String url = externalBaseUrl + "/api/v1/alerts";
        try {
            HttpHeaders headers = buildHeaders();
            HttpEntity<Void> request = new HttpEntity<>(headers);

            ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.GET, request, String.class);
            JsonNode jsonNode = objectMapper.readTree(response.getBody());

            List<Map<String, Object>> alerts = new ArrayList<>();
            if (jsonNode.isArray()) {
                for (JsonNode node : jsonNode) {
                    Map<String, Object> alert = new HashMap<>();
                    alert.put("alertId", node.path("alertId").asText());
                    alert.put("type", node.path("type").asText());
                    alert.put("severity", node.path("severity").asText());
                    alert.put("message", node.path("message").asText());
                    alert.put("timestamp", node.path("timestamp").asText());
                    alerts.add(alert);
                }
            }
            log.debug("从外部UTM接收到 {} 条告警", alerts.size());
            return alerts;
        } catch (Exception e) {
            log.error("接收外部UTM告警失败", e);
            return List.of();
        }
    }

    // ===== 空域限制查询 =====

    /**
     * 查询外部 UTM 空域限制
     *
     * @param bounds     空域边界 {minLon, minLat, maxLon, maxLat}
     * @param timeWindow 时间窗口 {start, end}
     * @return 空域限制列表
     */
    @WithCircuitBreaker(name = "externalUtm", failureRateThreshold = 60,
            slowCallDurationThreshold = 3000, waitDurationInOpenState = 20000)
    public List<Map<String, Object>> checkAirspaceWithUtm(Map<String, Double> bounds,
                                                          Map<String, String> timeWindow) {
        if (!externalEnabled) {
            log.debug("[MOCK] 跳过外部UTM空域查询, bounds={}", bounds);
            return List.of();
        }

        String url = externalBaseUrl + "/api/v1/airspace/check";
        try {
            Map<String, Object> body = new HashMap<>();
            body.put("bounds", bounds);
            body.put("timeWindow", timeWindow);

            HttpHeaders headers = buildHeaders();
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);

            ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.POST, request, String.class);
            JsonNode jsonNode = objectMapper.readTree(response.getBody());

            List<Map<String, Object>> restrictions = new ArrayList<>();
            if (jsonNode.isArray()) {
                for (JsonNode node : jsonNode) {
                    Map<String, Object> restriction = new HashMap<>();
                    restriction.put("restrictionId", node.path("restrictionId").asText());
                    restriction.put("type", node.path("type").asText());
                    restriction.put("altitudeMin", node.path("altitudeMin").asDouble());
                    restriction.put("altitudeMax", node.path("altitudeMax").asDouble());
                    restriction.put("reason", node.path("reason").asText());
                    restrictions.add(restriction);
                }
            }
            log.debug("从外部UTM查询到 {} 条空域限制", restrictions.size());
            return restrictions;
        } catch (Exception e) {
            log.error("查询外部UTM空域限制失败", e);
            return List.of();
        }
    }

    // ===== 辅助方法 =====

    private Map<String, Object> buildFlightPlanBody(FlightPlan flightPlan) {
        Map<String, Object> body = new HashMap<>();
        body.put("planId", flightPlan.getPlanId());
        body.put("uavId", flightPlan.getUavId());
        body.put("operatorId", flightPlan.getOperatorId());
        body.put("waypoints", flightPlan.getWaypointsJson());
        body.put("plannedStartTime", flightPlan.getPlannedStartTime().toString());
        body.put("plannedEndTime", flightPlan.getPlannedEndTime().toString());
        body.put("emergencyFlag", flightPlan.getEmergencyFlag() != null ? flightPlan.getEmergencyFlag() : false);
        body.put("tenantId", flightPlan.getTenantId());
        return body;
    }

    private HttpHeaders buildHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        if (externalApiKey != null && !externalApiKey.isEmpty()) {
            headers.set("X-API-Key", externalApiKey);
        }
        return headers;
    }

    private Map<String, Object> mockSubmitResponse(FlightPlan flightPlan) {
        Map<String, Object> result = new HashMap<>();
        result.put("externalPlanId", "EXT-" + flightPlan.getPlanId());
        result.put("status", "SUBMITTED");
        result.put("approvalCode", "");
        return result;
    }

    /**
     * 判断外部 UTM 对接是否启用
     */
    public boolean isEnabled() {
        return externalEnabled;
    }
}

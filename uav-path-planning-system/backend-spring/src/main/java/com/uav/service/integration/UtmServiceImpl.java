package com.uav.service.integration;

import com.uav.common.integration.UtmService;
import com.uav.common.integration.dto.AirspaceStatus;
import com.uav.common.integration.dto.DroneInfo;
import com.uav.common.integration.dto.EmergencyResponse;
import com.uav.common.integration.dto.FlightApproval;
import com.uav.common.integration.dto.FlightPlan;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import jakarta.annotation.PostConstruct;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * UTM系统服务实现
 *
 * 默认使用模拟模式运行，可通过配置 utm.enabled=true 切换为真实UTM提供商的调用。
 * 所有操作均记录日志，便于监控和调试。
 */
@Service
public class UtmServiceImpl implements UtmService {

    private static final Logger log = LoggerFactory.getLogger(UtmServiceImpl.class);

    @Value("${utm.enabled:false}")
    private boolean utmEnabled;

    @Value("${utm.provider:simulation}")
    private String utmProvider;

    @Value("${utm.api.base-url:https://api.utm-platform.com/v1}")
    private String apiBaseUrl;

    @Value("${utm.api.timeout:30000}")
    private int apiTimeout;

    private RestTemplate restTemplate;

    @PostConstruct
    public void init() {
        restTemplate = new RestTemplate();
        restTemplate.getInterceptors().add((request, body, execution) -> {
            log.debug("UTM API Request: {} {}", request.getMethod(), request.getURI());
            return execution.execute(request, body);
        });
        log.info("UTM Service initialized | enabled={} | provider={} | baseUrl={}",
                utmEnabled, utmProvider, apiBaseUrl);
    }

    @Override
    public String registerDrone(DroneInfo droneInfo) {
        log.info("Registering drone with UTM: droneId={}, model={}, operator={}",
                droneInfo.getDroneId(), droneInfo.getModel(), droneInfo.getOperatorName());

        if (utmEnabled) {
            try {
                String endpoint = apiBaseUrl + "/drones";
                @SuppressWarnings("unchecked")
                Map<String, Object> response = restTemplate.postForObject(endpoint, droneInfo, Map.class);
                if (response != null && response.containsKey("registrationId")) {
                    String registrationId = response.get("registrationId").toString();
                    log.info("Drone registered via UTM API: registrationId={}", registrationId);
                    return registrationId;
                }
            } catch (RestClientException e) {
                log.error("Failed to register drone with UTM provider: {}", e.getMessage(), e);
            }
        }

        String registrationId = "UTM-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase();
        log.info("Drone registered (simulated): registrationId={}", registrationId);
        return registrationId;
    }

    @Override
    public boolean submitFlightPlan(FlightPlan plan) {
        log.info("Submitting flight plan to UTM: planId={}, droneId={}, missionType={}",
                plan.getPlanId(), plan.getDroneId(), plan.getMissionType());

        if (utmEnabled) {
            try {
                String endpoint = apiBaseUrl + "/flight-plans";
                @SuppressWarnings("unchecked")
                Map<String, Object> response = restTemplate.postForObject(endpoint, plan, Map.class);
                if (response != null && response.containsKey("approved")) {
                    boolean approved = (Boolean) response.get("approved");
                    log.info("Flight plan submitted via UTM API: planId={}, approved={}", plan.getPlanId(), approved);
                    return approved;
                }
            } catch (RestClientException e) {
                log.error("Failed to submit flight plan to UTM provider: {}", e.getMessage(), e);
            }
        }

        log.info("Flight plan submitted and approved (simulated): planId={}", plan.getPlanId());
        return true;
    }

    @Override
    public FlightApproval getFlightApproval(String planId) {
        log.info("Querying flight approval status: planId={}", planId);

        if (utmEnabled) {
            try {
                String endpoint = apiBaseUrl + "/flight-plans/" + planId;
                @SuppressWarnings("unchecked")
                Map<String, Object> response = restTemplate.getForObject(endpoint, Map.class);
                if (response != null) {
                    FlightApproval approval = mapToFlightApproval(response);
                    log.info("Flight approval retrieved via UTM API: planId={}, approved={}", planId, approval.isApproved());
                    return approval;
                }
            } catch (RestClientException e) {
                log.error("Failed to get flight approval from UTM provider: {}", e.getMessage(), e);
            }
        }

        FlightApproval approval = new FlightApproval();
        approval.setPlanId(planId);
        approval.setApproved(true);
        approval.setApprovedAt(LocalDateTime.now());
        approval.setExpirationTime(LocalDateTime.now().plusHours(4));
        approval.setRestrictions("Max altitude: 120m; No-fly zones: military area");
        log.info("Flight approval retrieved (simulated): planId={}", planId);
        return approval;
    }

    @Override
    public AirspaceStatus queryAirspace(double lat, double lon, double radius) {
        log.info("Querying airspace status: lat={}, lon={}, radius={}m", lat, lon, radius);

        if (utmEnabled) {
            try {
                String endpoint = String.format("%s/airspace?lat=%f&lon=%f&radius=%f", apiBaseUrl, lat, lon, radius);
                @SuppressWarnings("unchecked")
                Map<String, Object> response = restTemplate.getForObject(endpoint, Map.class);
                if (response != null) {
                    AirspaceStatus status = mapToAirspaceStatus(response);
                    log.info("Airspace status retrieved via UTM API: zoneId={}, status={}", 
                            status.getZoneId(), status.getStatus());
                    return status;
                }
            } catch (RestClientException e) {
                log.error("Failed to query airspace from UTM provider: {}", e.getMessage(), e);
            }
        }

        AirspaceStatus status = new AirspaceStatus();
        status.setZoneId("ZONE-" + UUID.randomUUID().toString().substring(0, 4).toUpperCase());
        status.setStatus(AirspaceStatus.Status.ACTIVE);
        status.setRestrictions("None");
        status.setWeatherAlert("Clear");
        status.setDroneCount(3);
        status.setMaxDronesAllowed(10);
        log.info("Airspace status retrieved (simulated): zoneId={}", status.getZoneId());
        return status;
    }

    @Override
    public EmergencyResponse sendEmergencyAlert(String droneId, EmergencyType type) {
        log.warn("Sending emergency alert: droneId={}, type={}", droneId, type);

        if (utmEnabled) {
            try {
                String endpoint = apiBaseUrl + "/emergency";
                Map<String, Object> requestBody = new HashMap<>();
                requestBody.put("droneId", droneId);
                requestBody.put("type", type.name());
                requestBody.put("timestamp", LocalDateTime.now().toString());

                @SuppressWarnings("unchecked")
                Map<String, Object> response = restTemplate.postForObject(endpoint, requestBody, Map.class);
                if (response != null) {
                    EmergencyResponse emergencyResponse = mapToEmergencyResponse(response);
                    log.info("Emergency alert sent via UTM API: alertId={}, severity={}", 
                            emergencyResponse.getAlertId(), emergencyResponse.getSeverity());
                    return emergencyResponse;
                }
            } catch (RestClientException e) {
                log.error("Failed to send emergency alert to UTM provider: {}", e.getMessage(), e);
            }
        }

        EmergencyResponse response = new EmergencyResponse();
        response.setAlertId("ALERT-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase());
        response.setDroneId(droneId);
        response.setType(type.name());
        response.setSeverity(determineSeverity(type));
        response.setTimestamp(LocalDateTime.now());
        response.setInstructions(buildInstructions(type));
        log.warn("Emergency alert sent (simulated): alertId={}", response.getAlertId());
        return response;
    }

    private FlightApproval mapToFlightApproval(Map<String, Object> response) {
        FlightApproval approval = new FlightApproval();
        approval.setPlanId(response.get("planId").toString());
        approval.setApproved((Boolean) response.get("approved"));
        if (response.containsKey("approvedAt")) {
            approval.setApprovedAt(LocalDateTime.parse(response.get("approvedAt").toString()));
        }
        if (response.containsKey("expirationTime")) {
            approval.setExpirationTime(LocalDateTime.parse(response.get("expirationTime").toString()));
        }
        if (response.containsKey("restrictions")) {
            approval.setRestrictions(response.get("restrictions").toString());
        }
        return approval;
    }

    private AirspaceStatus mapToAirspaceStatus(Map<String, Object> response) {
        AirspaceStatus status = new AirspaceStatus();
        status.setZoneId(response.get("zoneId").toString());
        status.setStatus(AirspaceStatus.Status.valueOf(response.get("status").toString()));
        if (response.containsKey("restrictions")) {
            status.setRestrictions(response.get("restrictions").toString());
        }
        if (response.containsKey("weatherAlert")) {
            status.setWeatherAlert(response.get("weatherAlert").toString());
        }
        if (response.containsKey("droneCount")) {
            status.setDroneCount(((Number) response.get("droneCount")).intValue());
        }
        if (response.containsKey("maxDronesAllowed")) {
            status.setMaxDronesAllowed(((Number) response.get("maxDronesAllowed")).intValue());
        }
        return status;
    }

    private EmergencyResponse mapToEmergencyResponse(Map<String, Object> response) {
        EmergencyResponse emergencyResponse = new EmergencyResponse();
        emergencyResponse.setAlertId(response.get("alertId").toString());
        if (response.containsKey("droneId")) {
            emergencyResponse.setDroneId(response.get("droneId").toString());
        }
        if (response.containsKey("type")) {
            emergencyResponse.setType(response.get("type").toString());
        }
        if (response.containsKey("severity")) {
            emergencyResponse.setSeverity(response.get("severity").toString());
        }
        if (response.containsKey("timestamp")) {
            emergencyResponse.setTimestamp(LocalDateTime.parse(response.get("timestamp").toString()));
        }
        if (response.containsKey("instructions")) {
            emergencyResponse.setInstructions(response.get("instructions").toString());
        }
        return emergencyResponse;
    }

    private String determineSeverity(EmergencyType type) {
        switch (type) {
            case COLLISION_RISK:
            case MECHANICAL_FAILURE:
                return "CRITICAL";
            case BATTERY_LOW:
            case SIGNAL_LOST:
                return "HIGH";
            case GEOFENCE_VIOLATION:
                return "MEDIUM";
            case WEATHER_EMERGENCY:
                return "HIGH";
            case OTHER:
            default:
                return "LOW";
        }
    }

    private String buildInstructions(EmergencyType type) {
        switch (type) {
            case BATTERY_LOW:
                return "Immediately return to home point or execute emergency landing";
            case SIGNAL_LOST:
                return "Activate return-to-home (RTH) protocol";
            case GEOFENCE_VIOLATION:
                return "Adjust course immediately to return to authorized airspace";
            case MECHANICAL_FAILURE:
                return "Execute emergency landing in nearest safe zone";
            case WEATHER_EMERGENCY:
                return "Divert to safe area or land immediately";
            case COLLISION_RISK:
                return "Change altitude or course to avoid collision";
            case OTHER:
            default:
                return "Follow standard emergency procedures";
        }
    }
}

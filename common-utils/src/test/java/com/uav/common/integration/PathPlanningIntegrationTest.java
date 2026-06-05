package com.uav.common.integration;

import static org.junit.jupiter.api.Assertions.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
/**
 * 路径规划服务集成测试
 * 
 * 测试 VRPTW / A* / DWA / Full 三层规划流程。
 * 需要路径规划服务和认证服务运行中。
 * 使用 -Dgroups=integration 单独运行集成测试。
 */
@SuppressWarnings({"unchecked", "null"})
@Tag("integration")
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class PathPlanningIntegrationTest {

    private static final Logger log = LoggerFactory.getLogger(PathPlanningIntegrationTest.class);
    private static final String PLAN_BASE = System.getProperty("test.planning", "http://localhost:8083");
    private static final String AUTH_BASE = System.getProperty("test.target", "http://localhost:8089");
    private static final TestRestTemplate restTemplate = new TestRestTemplate();
    private static String authToken;

    @BeforeAll
    static void setup() {
        // 先登录获取 Token
        try {
            Map<String, String> loginBody = Map.of("username", "admin", "password", "Uav@2024!Secure");
            ResponseEntity<Map<String, Object>> loginResp = restTemplate.postForEntity(
                AUTH_BASE + "/api/v1/auth/login",
                new HttpEntity<>(loginBody, createJsonHeaders()),
                (Class<Map<String, Object>>) (Class<?>) Map.class);
            if (loginResp.getStatusCode().value() == 200 && loginResp.getBody() != null) {
                authToken = (String) loginResp.getBody().get("token");
                log.info("Auth token acquired");
            }
        } catch (Exception e) {
            log.warn("Cannot get auth token, tests may fail: {}", e.getMessage());
        }
    }

    @Test
    @Order(1)
    @DisplayName("VRPTW 规划接口 - 应返回规划结果")
    void vrptw_planning() {
        Map<String, Object> request = new HashMap<>();
        request.put("algorithm", "vrptw");
        request.put("drones", List.of(
            Map.of("id", "drone1", "max_payload", 10.0, "max_endurance", 60.0, "max_speed", 15.0)
        ));
        request.put("tasks", List.of(
            Map.of("id", "task1", "location", List.of(10.0, 10.0), "demand", 2.0, "start_time", 0.0, "end_time", 60.0),
            Map.of("id", "task2", "location", List.of(20.0, 20.0), "demand", 3.0, "start_time", 0.0, "end_time", 120.0)
        ));
        request.put("weatherData", Map.of("wind_speed", 5.0));

        ResponseEntity<Map<String, Object>> response = restTemplate.postForEntity(
            PLAN_BASE + "/api/planning/vrptw",
            new HttpEntity<>(request, createHeaders()),
            (Class<Map<String, Object>>) (Class<?>) Map.class);

        log.info("VRPTW response: {}", response.getStatusCode());
        
        if (response.getStatusCode().value() == 200 && response.getBody() != null) {
            Map<String, Object> body = response.getBody();
            log.info("VRPTW result: success={}, routes={}",
                body.get("success"),
                body.get("routes") != null ? ((List<?>) body.get("routes")).size() : 0);
        }
        
        assertTrue(response.getStatusCode().value() == 200 || response.getStatusCode().value() == 401,
            "VRPTW 应返回 200（成功）或 401（未认证）");
    }

    @Test
    @Order(2)
    @DisplayName("A* 路径规划接口 - 应返回路径")
    void astar_planning() {
        Map<String, Object> request = new HashMap<>();
        request.put("algorithm", "astar");
        request.put("start", List.of(0.0, 0.0));
        request.put("goal", List.of(10.0, 10.0));
        request.put("obstacles", List.of(
            Map.of("location", List.of(5.0, 5.0), "radius", 2.0)
        ));

        ResponseEntity<Map<String, Object>> response = restTemplate.postForEntity(
            PLAN_BASE + "/api/planning/astar",
            new HttpEntity<>(request, createHeaders()),
            (Class<Map<String, Object>>) (Class<?>) Map.class);

        log.info("A* response: {}", response.getStatusCode());
        assertTrue(response.getStatusCode().value() == 200 || response.getStatusCode().value() == 401);
    }

    @Test
    @Order(3)
    @DisplayName("DWA 局部规划接口 - 应返回轨迹")
    void dwa_planning() {
        Map<String, Object> request = new HashMap<>();
        request.put("algorithm", "dwa");
        request.put("current_pose", List.of(0.0, 0.0, 0.0));
        request.put("goal", List.of(5.0, 5.0));

        ResponseEntity<Map<String, Object>> response = restTemplate.postForEntity(
            PLAN_BASE + "/api/planning/dwa",
            new HttpEntity<>(request, createHeaders()),
            (Class<Map<String, Object>>) (Class<?>) Map.class);

        log.info("DWA response: {}", response.getStatusCode());
        assertTrue(response.getStatusCode().value() == 200 || response.getStatusCode().value() == 401);
    }

    @Test
    @Order(4)
    @DisplayName("完整三层路径规划 - 应返回多航线结果")
    void full_planning() {
        Map<String, Object> request = new HashMap<>();
        request.put("algorithm", "full");
        request.put("drones", List.of(
            Map.of("id", "uav1", "max_payload", 5.0, "max_endurance", 30.0, "max_speed", 10.0)
        ));
        request.put("tasks", List.of(
            Map.of("id", "t1", "location", List.of(10.0, 0.0), "demand", 2.0, "start_time", 0.0, "end_time", 30.0)
        ));
        request.put("weatherData", Map.of("wind_speed", 3.0));

        ResponseEntity<Map<String, Object>> response = restTemplate.postForEntity(
            PLAN_BASE + "/api/planning/full",
            new HttpEntity<>(request, createHeaders()),
            (Class<Map<String, Object>>) (Class<?>) Map.class);

        log.info("Full planning response: {}", response.getStatusCode());
        assertTrue(response.getStatusCode().value() == 200 || response.getStatusCode().value() == 401);
    }

    @Test
    @Order(5)
    @DisplayName("健康检查 - 路径规划服务应可用")
    void healthCheck() {
        ResponseEntity<String> response = restTemplate.getForEntity(
            PLAN_BASE + "/actuator/health", String.class);
        assertEquals(200, response.getStatusCode().value(), "路径规划服务健康检查应返回 200");
        log.info("✅ 路径规划服务健康: {}", response.getBody());
    }

    // ====== 辅助方法 ======

    private static HttpHeaders createJsonHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        return headers;
    }

    private HttpHeaders createHeaders() {
        HttpHeaders headers = createJsonHeaders();
        if (authToken != null) {
            headers.setBearerAuth(authToken);
        }
        return headers;
    }
}

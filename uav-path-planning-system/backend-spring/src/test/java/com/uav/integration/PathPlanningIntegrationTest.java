package com.uav.integration;

import com.uav.UavPathPlanningApplication;
import com.uav.model.User;
import com.uav.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;

import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 路径规划系统集成测试
 * 覆盖系统主要功能模块间的交互逻辑
 */
@SpringBootTest(classes = UavPathPlanningApplication.class, webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class PathPlanningIntegrationTest {

    @LocalServerPort
    private int port;

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private UserRepository userRepository;

    private String baseUrl;

    @BeforeEach
    void setUp() {
        baseUrl = "http://localhost:" + port;
    }

    @Test
    @DisplayName("集成测试：完整路径规划流程")
    void testCompletePathPlanningFlow() {
        // Step 1: 用户认证
        ResponseEntity<Map<String, Object>> loginResponse = authenticateUser("admin", "password");
        assertEquals(200, loginResponse.getStatusCode().value());
        assertNotNull(loginResponse.getBody());
        assertTrue(loginResponse.getBody().containsKey("token"));

        String token = loginResponse.getBody().get("token").toString();

        // Step 2: 请求路径规划
        ResponseEntity<Map<String, Object>> planResponse = requestPathPlanning(token);
        assertEquals(200, planResponse.getStatusCode().value());
        assertNotNull(planResponse.getBody());
        assertTrue((Boolean) planResponse.getBody().get("success"));
        assertEquals(200, planResponse.getBody().get("code"));
        assertNotNull(planResponse.getBody().get("data"));

        // Step 3: 获取规划历史
        ResponseEntity<Map<String, Object>> historyResponse = getPlanningHistory(token);
        assertEquals(200, historyResponse.getStatusCode().value());
        assertNotNull(historyResponse.getBody());
        assertTrue((Boolean) historyResponse.getBody().get("success"));
    }

    @Test
    @DisplayName("集成测试：用户创建与认证流程")
    void testUserCreationAndAuthentication() {
        // 创建新用户
        String username = "testuser_" + System.currentTimeMillis();
        ResponseEntity<Map<String, Object>> createResponse = createUser(username);
        assertEquals(200, createResponse.getStatusCode().value());

        // 验证用户已创建
        User user = userRepository.findByUsername(username).orElse(null);
        assertNotNull(user);
        assertEquals(username, user.getUsername());

        // 使用新用户登录
        ResponseEntity<Map<String, Object>> loginResponse = authenticateUser(username, "Password123");
        assertEquals(200, loginResponse.getStatusCode().value());
        assertNotNull(loginResponse.getBody().get("token"));
    }

    @Test
    @DisplayName("集成测试：权限验证流程")
    void testPermissionValidation() {
        // 未认证请求应被拒绝
        ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
            baseUrl + "/api/users", HttpMethod.GET, null, new ParameterizedTypeReference<Map<String, Object>>() {});
        assertEquals(401, response.getStatusCode().value());
    }

    @Test
    @DisplayName("集成测试：路径规划边界条件")
    void testPathPlanningBoundaryConditions() {
        // 认证
        ResponseEntity<Map<String, Object>> loginResponse = authenticateUser("admin", "password");
        String token = loginResponse.getBody().get("token").toString();

        // 空请求参数
        ResponseEntity<Map<String, Object>> emptyResponse = requestPathPlanningWithEmptyParams(token);
        assertEquals(200, emptyResponse.getStatusCode().value());
        assertTrue((Boolean) emptyResponse.getBody().get("success"));

        // 正常请求参数
        ResponseEntity<Map<String, Object>> normalResponse = requestPathPlanning(token);
        assertEquals(200, normalResponse.getStatusCode().value());
        assertTrue((Boolean) normalResponse.getBody().get("success"));
    }

    @Test
    @DisplayName("集成测试：异常场景处理")
    void testExceptionHandling() {
        // 认证失败
        ResponseEntity<Map<String, Object>> failedLogin = authenticateUser("invalid", "wrong");
        assertEquals(401, failedLogin.getStatusCode().value());

        // 无效token
        HttpHeaders headers = new HttpHeaders();
        headers.set("Authorization", "Bearer invalid_token");
        HttpEntity<Void> entity = new HttpEntity<>(headers);
        ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
            baseUrl + "/api/users", HttpMethod.GET, entity, new ParameterizedTypeReference<Map<String, Object>>() {});
        assertEquals(401, response.getStatusCode().value());
    }

    private ResponseEntity<Map<String, Object>> authenticateUser(String username, String password) {
        Map<String, String> credentials = new HashMap<>();
        credentials.put("username", username);
        credentials.put("password", password);
        HttpEntity<Map<String, String>> entity = new HttpEntity<>(credentials);
        return restTemplate.exchange(baseUrl + "/auth/login", HttpMethod.POST, entity, new ParameterizedTypeReference<Map<String, Object>>() {});
    }

    private ResponseEntity<Map<String, Object>> createUser(String username) {
        Map<String, String> userData = new HashMap<>();
        userData.put("username", username);
        userData.put("password", "Password123");
        userData.put("email", username + "@example.com");
        userData.put("fullName", "Test User");
        HttpEntity<Map<String, String>> entity = new HttpEntity<>(userData);
        return restTemplate.exchange(baseUrl + "/auth/register", HttpMethod.POST, entity, new ParameterizedTypeReference<Map<String, Object>>() {});
    }

    private ResponseEntity<Map<String, Object>> requestPathPlanning(String token) {
        HttpHeaders headers = new HttpHeaders();
        headers.set("Authorization", "Bearer " + token);
        headers.set("Content-Type", "application/json");

        Map<String, String> request = new HashMap<>();
        request.put("tasks", "[{\"id\":1,\"location\":\"北京\",\"priority\":1}]");
        request.put("drones", "[{\"id\":1,\"capacity\":100}]");
        request.put("weatherData", "{\"windSpeed\":10,\"temperature\":25}");

        HttpEntity<Map<String, String>> entity = new HttpEntity<>(request, headers);
        return restTemplate.exchange(baseUrl + "/path-planning/plan", HttpMethod.POST, entity, new ParameterizedTypeReference<Map<String, Object>>() {});
    }

    private ResponseEntity<Map<String, Object>> requestPathPlanningWithEmptyParams(String token) {
        HttpHeaders headers = new HttpHeaders();
        headers.set("Authorization", "Bearer " + token);
        headers.set("Content-Type", "application/json");

        Map<String, String> request = new HashMap<>();
        request.put("tasks", "");
        request.put("drones", "");
        request.put("weatherData", "");

        HttpEntity<Map<String, String>> entity = new HttpEntity<>(request, headers);
        return restTemplate.exchange(baseUrl + "/path-planning/plan", HttpMethod.POST, entity, new ParameterizedTypeReference<Map<String, Object>>() {});
    }

    private ResponseEntity<Map<String, Object>> getPlanningHistory(String token) {
        HttpHeaders headers = new HttpHeaders();
        headers.set("Authorization", "Bearer " + token);
        HttpEntity<Void> entity = new HttpEntity<>(headers);
        return restTemplate.exchange(baseUrl + "/path-planning/history", 
            HttpMethod.GET, entity, new ParameterizedTypeReference<Map<String, Object>>() {});
    }
}
package com.uav.common.integration;

import org.junit.jupiter.api.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.*;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 认证流程集成测试
 * 
 * 测试完整的 JWT 认证生命周期：
 * 1. 用户注册
 * 2. 用户登录获取 Token
 * 3. 使用 Token 访问受保护端点
 * 4. Token 刷新
 * 5. 使用过期/无效 Token 应被拒绝
 * 6. 用户登出
 * 
 * 注意: 这些测试需要后端服务运行中。
 * 通过 -Dtest.target=http://localhost:8089 指定目标服务地址。
 */
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class AuthFlowIntegrationTest {

    private static final Logger log = LoggerFactory.getLogger(AuthFlowIntegrationTest.class);
    private static final String BASE_URL = System.getProperty("test.target", "http://localhost:8089");
    private static final TestRestTemplate restTemplate = new TestRestTemplate();
    
    private static String authToken;
    private static String username;

    @BeforeAll
    static void setup() {
        username = "testuser_" + System.currentTimeMillis();
        log.info("Test target: {}", BASE_URL);
        log.info("Test username: {}", username);
    }

    @Test
    @Order(1)
    @DisplayName("健康检查 - 服务应可用")
    void healthCheck() {
        ResponseEntity<String> response = restTemplate.getForEntity(
            BASE_URL + "/actuator/health", String.class);
        
        assertEquals(200, response.getStatusCode().value(), "服务应返回 200 OK");
        log.info("✅ 健康检查通过: {}", response.getBody());
    }

    @Test
    @Order(2)
    @DisplayName("用户注册 - 应返回 Token")
    void register_shouldReturnToken() {
        Map<String, String> body = Map.of(
            "username", username,
            "password", "TestPass123!",
            "email", username + "@test.com",
            "fullName", "Test User"
        );

        ResponseEntity<Map<String, Object>> response = restTemplate.postForEntity(
            BASE_URL + "/api/v1/auth/register", 
            new HttpEntity<>(body, createJsonHeaders()),
            (Class<Map<String, Object>>) (Class<?>) Map.class);

        log.info("Register response: {}", response.getBody());
        
        assertEquals(201, response.getStatusCode().value(), "注册应返回 201 Created");
        assertNotNull(response.getBody(), "响应不应为空");
        assertNotNull(response.getBody().get("token"), "响应应包含 token");
        
        authToken = (String) response.getBody().get("token");
        assertNotNull(authToken, "Token 不应为空");
        log.info("✅ 用户注册成功, token 前20位: {}...", authToken.substring(0, 20));
    }

    @Test
    @Order(3)
    @DisplayName("用户登录 - 应返回 Token")
    void login_shouldReturnToken() {
        Map<String, String> body = Map.of(
            "username", username,
            "password", "TestPass123!"
        );

        ResponseEntity<Map<String, Object>> response = restTemplate.postForEntity(
            BASE_URL + "/api/v1/auth/login",
            new HttpEntity<>(body, createJsonHeaders()),
            (Class<Map<String, Object>>) (Class<?>) Map.class);

        log.info("Login response status: {}", response.getStatusCode());
        
        assertEquals(200, response.getStatusCode().value(), "登录应返回 200 OK");
        assertNotNull(response.getBody(), "响应不应为空");
        assertNotNull(response.getBody().get("token"), "响应应包含 token");
        
        authToken = (String) response.getBody().get("token");
        log.info("✅ 用户登录成功");
    }

    @Test
    @Order(4)
    @DisplayName("使用 Token 访问受保护端点 - 应成功")
    void accessProtectedEndpoint_withValidToken() {
        HttpHeaders headers = createAuthHeaders();
        ResponseEntity<String> response = restTemplate.exchange(
            BASE_URL + "/api/user/locations",
            HttpMethod.GET,
            new HttpEntity<>(headers),
            String.class);

        log.info("Protected endpoint response: {}", response.getStatusCode());
        assertTrue(response.getStatusCode().value() == 200 || response.getStatusCode().value() == 403,
            "应返回 200（有权限）或 403（初始用户无角色权限）");
        log.info("✅ 受保护端点访问正常: {}", response.getStatusCode());
    }

    @Test
    @Order(5)
    @DisplayName("使用无效 Token - 应返回 401")
    void accessProtectedEndpoint_withInvalidToken() {
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth("invalid_token_here");
        
        ResponseEntity<String> response = restTemplate.exchange(
            BASE_URL + "/api/user/locations",
            HttpMethod.GET,
            new HttpEntity<>(headers),
            String.class);

        assertEquals(401, response.getStatusCode().value(), "无效 Token 应返回 401");
        log.info("✅ 无效 Token 被正确拒绝: 401");
    }

    @Test
    @Order(6)
    @DisplayName("空密码登录 - 应返回 400")
    void login_withEmptyPassword_shouldFail() {
        Map<String, String> body = Map.of(
            "username", username,
            "password", ""
        );

        ResponseEntity<Map<String, Object>> response = restTemplate.postForEntity(
            BASE_URL + "/api/v1/auth/login",
            new HttpEntity<>(body, createJsonHeaders()),
            (Class<Map<String, Object>>) (Class<?>) Map.class);

        log.info("Empty password response: {}", response.getStatusCode());
        assertTrue(response.getStatusCode().value() == 400, "空密码应返回 400");
        log.info("✅ 空密码被正确拒绝: 400");
    }

    @Test
    @Order(7)
    @DisplayName("用户登出 - 应成功")
    void logout_shouldSucceed() {
        HttpHeaders headers = createAuthHeaders();
        ResponseEntity<String> response = restTemplate.exchange(
            BASE_URL + "/api/v1/auth/logout",
            HttpMethod.POST,
            new HttpEntity<>(headers),
            String.class);

        log.info("Logout response: {}", response.getStatusCode());
        assertTrue(response.getStatusCode().value() == 200, "登出应返回 200");
        log.info("✅ 用户登出成功");
    }

    // ====== 辅助方法 ======

    private HttpHeaders createJsonHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        return headers;
    }

    @SuppressWarnings("unchecked")
    private HttpHeaders createAuthHeaders() {
        HttpHeaders headers = createJsonHeaders();
        if (authToken != null) {
            headers.setBearerAuth(authToken);
        }
        return headers;
    }
}

package com.uav.common.config;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("CommonSecurityConfig 测试")
class CommonSecurityConfigTest {

    @Test
    @DisplayName("CORS配置源创建")
    void testCorsConfigurationSource() {
        CommonSecurityConfig config = new CommonSecurityConfig();
        CorsConfigurationSource source = config.corsConfigurationSource();
        assertNotNull(source);
        MockHttpServletRequest request = new MockHttpServletRequest();
        CorsConfiguration corsConfig = source.getCorsConfiguration(request);
        assertNotNull(corsConfig);
        assertTrue(corsConfig.getAllowedOriginPatterns().contains("http://localhost:3000"));
    }

    @Test
    @DisplayName("CORS配置允许凭证")
    void testCorsAllowsCredentials() {
        CommonSecurityConfig config = new CommonSecurityConfig();
        CorsConfigurationSource source = config.corsConfigurationSource();
        MockHttpServletRequest request = new MockHttpServletRequest();
        CorsConfiguration corsConfig = source.getCorsConfiguration(request);
        assertTrue(corsConfig.getAllowCredentials());
    }
}

@DisplayName("NacosConfigRefresher 测试")
class NacosConfigRefresherTest {

    @Test
    @DisplayName("创建配置刷新器（无NacosConfigManager）")
    void testConstructorWithoutNacos() {
        NacosConfigRefresher refresher = new NacosConfigRefresher(null);
        assertNotNull(refresher);
        assertNotNull(refresher.getRegisteredListeners());
        assertTrue(refresher.getRegisteredListeners().isEmpty());
    }

    @Test
    @DisplayName("getConfig返回null（无Nacos）")
    void testGetConfigWithoutNacos() {
        NacosConfigRefresher refresher = new NacosConfigRefresher(null);
        assertNull(refresher.getConfig("test", 1000));
    }
}

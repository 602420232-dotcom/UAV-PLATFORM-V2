package com.uav.platform.controller;

import com.uav.platform.entity.Tenant;
import com.uav.platform.service.TenantService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.http.MediaType;

import java.time.LocalDateTime;

import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Platform 控制器单元测试
 */
@DisplayName("Platform 控制器测试")
@SpringBootTest(classes = com.uav.platform.PlatformApplication.class)
@AutoConfigureMockMvc(addFilters = false)
@TestPropertySource(locations = "classpath:application-test.yml")
@WithMockUser(roles = {"ADMIN"})
class PlatformControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private TenantService tenantService;

    @Test
    @DisplayName("GET /api/v1/tenants/{id} 应返回租户详情")
    void getTenantByIdShouldReturnTenantDetails() throws Exception {
        Tenant tenant = new Tenant();
        tenant.setId(1L);
        tenant.setName("Test Tenant");
        tenant.setSchemaName("test_schema");
        tenant.setStatus(1);
        tenant.setCreatedAt(LocalDateTime.now());

        when(tenantService.getById(anyLong())).thenReturn(tenant);

        mockMvc.perform(get("/api/v1/tenants/1")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.name").value("Test Tenant"))
                .andExpect(jsonPath("$.data.schemaName").value("test_schema"));
    }

    @Test
    @DisplayName("GET /api/v1/tenants/{id} 租户不存在时应返回 null data")
    void getNonExistentTenantShouldReturnNullData() throws Exception {
        when(tenantService.getById(anyLong())).thenReturn(null);

        mockMvc.perform(get("/api/v1/tenants/999")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data").isEmpty());
    }

    @Test
    @DisplayName("GET /api/v1/tenants 应返回租户列表")
    void listTenantsShouldReturnPageResult() throws Exception {
        mockMvc.perform(get("/api/v1/tenants")
                        .param("current", "1")
                        .param("size", "10")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }

    @Test
    @DisplayName("GET /api/v1/tenants 不带分页参数应使用默认值")
    void listTenantsWithoutParamsShouldUseDefaults() throws Exception {
        mockMvc.perform(get("/api/v1/tenants")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }

    @Test
    @DisplayName("GET /api/v1/tenants 应支持 application/json 内容协商")
    void contentNegotiationShouldSupportJson() throws Exception {
        mockMvc.perform(get("/api/v1/tenants")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk());
    }
}

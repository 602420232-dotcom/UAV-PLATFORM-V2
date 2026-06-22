package com.uav.platform.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.uav.platform.entity.Tenant;
import com.uav.platform.service.TenantService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

/**
 * Tenant 控制器单元测试
 * 使用纯 Mockito 测试，不依赖 Spring 上下文
 */
@DisplayName("Tenant 控制器测试")
@ExtendWith(MockitoExtension.class)
class PlatformControllerTest {

    @Mock
    private TenantService tenantService;

    @InjectMocks
    private TenantController tenantController;

    private Tenant testTenant;

    @BeforeEach
    void setUp() {
        testTenant = new Tenant();
        testTenant.setId(1L);
        testTenant.setName("Test Tenant");
        testTenant.setSchemaName("test_schema");
        testTenant.setStatus(1);
        testTenant.setCreatedAt(LocalDateTime.now());
    }

    @Test
    @DisplayName("getById 应返回租户详情")
    void getTenantByIdShouldReturnTenantDetails() {
        when(tenantService.getById(1L)).thenReturn(testTenant);

        var result = tenantController.getById(1L);

        assertNotNull(result);
        assertEquals(200, result.getCode());
        assertNotNull(result.getData());
        assertEquals("Test Tenant", result.getData().getName());
    }

    @Test
    @DisplayName("getById 租户不存在时应返回 null data")
    void getNonExistentTenantShouldReturnNullData() {
        when(tenantService.getById(999L)).thenReturn(null);

        var result = tenantController.getById(999L);

        assertNotNull(result);
        assertEquals(200, result.getCode());
        assertNull(result.getData());
    }

    @Test
    @DisplayName("list 应返回分页结果")
    void listTenantsShouldReturnPageResult() {
        Page<Tenant> mockPage = new Page<>(1, 10);
        mockPage.setRecords(java.util.List.of(testTenant));
        when(tenantService.page(any())).thenReturn(mockPage);

        var result = tenantController.list(1, 10);

        assertNotNull(result);
        assertEquals(200, result.getCode());
        assertNotNull(result.getData());
        assertEquals(1, result.getData().getRecords().size());
    }
}

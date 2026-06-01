package com.uav.service;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("RealDataSourceService 单元测试")
class RealDataSourceServiceTest {

    private RealDataSourceService service;

    @BeforeEach
    void setUp() {
        service = new RealDataSourceService();
    }

    @AfterEach
    void tearDown() {
        if (service != null) {
            service.shutdown();
        }
    }

    @Test
    @DisplayName("初始化后地面站数据不为null且为空")
    void shouldHaveNonNullEmptyGroundStationDataInitially() {
        List<Map<String, Object>> data = service.getGroundStationData();
        assertNotNull(data);
        assertTrue(data.isEmpty());
    }

    @Test
    @DisplayName("初始化后浮标数据不为null且为空")
    void shouldHaveNonNullEmptyBuoyDataInitially() {
        List<Map<String, Object>> data = service.getBuoyData();
        assertNotNull(data);
        assertTrue(data.isEmpty());
    }

    @Test
    @DisplayName("getDataSourceStatus 不抛异常")
    void shouldReturnStatusWithoutException() {
        Map<String, Object> status = service.getDataSourceStatus();
        assertNotNull(status);
    }

    @Test
    @DisplayName("状态包含地面站信息")
    void shouldContainGroundStationStatus() {
        Map<String, Object> status = service.getDataSourceStatus();
        assertNotNull(status.get("ground_station"));
        Map<String, Object> gs = (Map<String, Object>) status.get("ground_station");
        assertNotNull(gs);
    }

    @Test
    @DisplayName("状态包含浮标信息")
    void shouldContainBuoyStatus() {
        Map<String, Object> status = service.getDataSourceStatus();
        assertNotNull(status.get("buoy"));
        Map<String, Object> buoy = (Map<String, Object>) status.get("buoy");
        assertNotNull(buoy);
    }

    @Test
    @DisplayName("数据源status标记为active")
    void shouldBeActive() {
        Map<String, Object> status = service.getDataSourceStatus();
        Map<String, Object> gs = (Map<String, Object>) status.get("ground_station");
        assertNotNull(gs);
        assertEquals("active", gs.get("status"));
    }

    @Test
    @DisplayName("地面站初始count为0")
    void shouldHaveZeroGroundStationCountInitially() {
        Map<String, Object> status = service.getDataSourceStatus();
        Map<String, Object> gs = (Map<String, Object>) status.get("ground_station");
        assertNotNull(gs);
        assertEquals(0, (int) gs.get("count"));
    }

    @Test
    @DisplayName("init不抛异常")
    void shouldNotThrowOnInit() {
        assertDoesNotThrow(() -> service.init());
    }

    @Test
    @DisplayName("重复shutdown不抛异常")
    void shouldNotThrowOnDoubleShutdown() {
        service.shutdown();
        assertDoesNotThrow(() -> service.shutdown());
    }
}

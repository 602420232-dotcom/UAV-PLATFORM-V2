package com.uav.wrf.processor.service;

import com.uav.wrf.processor.entity.WrfDataFile;
import com.uav.wrf.processor.repository.WrfDataFileRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("WrfDataService 单元测试")
@SuppressWarnings("null")
class WrfDataServiceTest {

    @Mock
    private WrfDataFileRepository repository;

    private WrfDataService service;

    @BeforeEach
    void setUp() {
        service = new WrfDataService(repository);
    }

    private WrfDataFile createTestFile() {
        return WrfDataFile.builder()
            .id(1L).fileId("wrf_test").fileName("test.nc")
            .filePath("./data/test.nc").fileSize(1024L).height(100)
            .timeSteps(24).variables("temperature,humidity,wind_speed")
            .status("UPLOADED").createdAt(LocalDateTime.now())
            .updatedAt(LocalDateTime.now()).build();
    }

    @Test
    @DisplayName("通过fileId查找文件")
    void testFindByFileId() {
        when(repository.findByFileId("wrf_test")).thenReturn(Optional.of(createTestFile()));
        Optional<WrfDataFile> result = service.findByFileId("wrf_test");
        assertTrue(result.isPresent());
        assertEquals("test.nc", result.get().getFileName());
    }

    @Test
    @DisplayName("通过ID查找文件")
    void testFindById() {
        when(repository.findById(1L)).thenReturn(Optional.of(createTestFile()));
        Optional<WrfDataFile> result = service.findById(1L);
        assertTrue(result.isPresent());
        assertEquals("wrf_test", result.get().getFileId());
    }

    @Test
    @DisplayName("获取所有文件")
    void testFindAll() {
        Page<WrfDataFile> page = new PageImpl<>(List.of(createTestFile()));
        when(repository.findAllByOrderByCreatedAtDesc(any(PageRequest.class))).thenReturn(page);
        Page<WrfDataFile> result = service.findAll(0, 10);
        assertEquals(1, result.getTotalElements());
    }

    @Test
    @DisplayName("创建WRF数据文件")
    void testCreateWrfDataFile() {
        when(repository.save(any(WrfDataFile.class))).thenReturn(createTestFile());
        WrfDataFile result = service.createWrfDataFile("test.nc", "./data/test.nc", 1024L);
        assertNotNull(result);
        assertEquals("test.nc", result.getFileName());
    }

    @Test
    @DisplayName("获取湍流数据")
    @SuppressWarnings("unchecked")
    void testGetTurbulence() {
        when(repository.findByFileId("wrf_test")).thenReturn(Optional.of(createTestFile()));
        Map<String, Object> result = service.getTurbulence("wrf_test");
        assertTrue((Boolean) result.get("success"));
        assertNotNull(result.get("data"));
        assertEquals("MODERATE", ((Map<String, Object>) result.get("data")).get("turbulence_intensity"));
    }

    @Test
    @DisplayName("获取能见度数据")
    @SuppressWarnings("unchecked")
    void testGetVisibility() {
        when(repository.findByFileId("wrf_test")).thenReturn(Optional.of(createTestFile()));
        Map<String, Object> result = service.getVisibility("wrf_test");
        assertTrue((Boolean) result.get("success"));
        assertNotNull(result.get("data"));
        assertEquals("GOOD", ((Map<String, Object>) result.get("data")).get("visibility_category"));
    }

    @Test
    @DisplayName("获取闪电风险评估")
    @SuppressWarnings("unchecked")
    void testGetLightningRisk() {
        when(repository.findByFileId("wrf_test")).thenReturn(Optional.of(createTestFile()));
        Map<String, Object> result = service.getLightningRisk("wrf_test");
        assertTrue((Boolean) result.get("success"));
        assertNotNull(result.get("data"));
        assertEquals("LOW", ((Map<String, Object>) result.get("data")).get("risk_level"));
    }

    @Test
    @DisplayName("获取高度分层数据")
    @SuppressWarnings("unchecked")
    void testGetHeightLayers() {
        when(repository.findByFileId("wrf_test")).thenReturn(Optional.of(createTestFile()));
        Map<String, Object> result = service.getHeightLayers("wrf_test", List.of(0, 100, 1000));
        assertTrue((Boolean) result.get("success"));
        Map<String, Object> data = (Map<String, Object>) result.get("data");
        assertEquals(3, data.get("layer_count"));
    }

    @Test
    @DisplayName("文件不存在时返回错误")
    void testFileNotFound() {
        when(repository.findByFileId("not_exist")).thenReturn(Optional.empty());
        Map<String, Object> result = service.getWeatherData("not_exist");
        assertFalse((Boolean) result.get("success"));
    }

    @Test
    @DisplayName("获取详情")
    void testGetDetail() {
        when(repository.findById(1L)).thenReturn(Optional.of(createTestFile()));
        Map<String, Object> result = service.getDetail(1L);
        assertTrue((Boolean) result.get("success"));
    }
}

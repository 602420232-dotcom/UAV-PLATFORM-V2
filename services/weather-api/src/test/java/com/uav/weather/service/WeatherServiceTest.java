package com.uav.weather.service;

import com.uav.weather.dto.WeatherQueryRequest;
import com.uav.weather.dto.WindProfileQueryRequest;
import com.uav.weather.entity.WeatherGrid;
import com.uav.weather.entity.WeatherRecord;
import com.uav.weather.entity.WindProfile;
import com.uav.weather.mapper.WeatherRecordMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.ValueOperations;
import org.springframework.test.util.ReflectionTestUtils;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * WeatherService 单元测试
 * 测试气象数据获取（点查询/区域查询）、风廓线计算
 */
@ExtendWith(MockitoExtension.class)
class WeatherServiceTest {

    @Mock
    private RedisTemplate<String, Object> redisTemplate;

    @Mock
    private WeatherRecordMapper weatherRecordMapper;

    @Mock
    private ValueOperations<String, Object> valueOperations;

    @InjectMocks
    private WeatherService weatherService;

    private WeatherQueryRequest pointRequest;
    private WindProfileQueryRequest windProfileRequest;

    @BeforeEach
    void setUp() {
        // 启用 mock 模式
        ReflectionTestUtils.setField(weatherService, "mockEnabled", true);

        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.get(anyString())).thenReturn(null);

        pointRequest = new WeatherQueryRequest();
        pointRequest.setLongitude(116.4);
        pointRequest.setLatitude(39.9);
        pointRequest.setAltitude(100.0);
        pointRequest.setSource("FUSION");
        pointRequest.setForecastTime(LocalDateTime.of(2025, 6, 15, 12, 0));

        windProfileRequest = new WindProfileQueryRequest();
        windProfileRequest.setLongitude(116.4);
        windProfileRequest.setLatitude(39.9);
        windProfileRequest.setMinAltitude(0.0);
        windProfileRequest.setMaxAltitude(500.0);
        windProfileRequest.setInterval(100.0);
        windProfileRequest.setSource("FUSION");
        windProfileRequest.setForecastTime(LocalDateTime.of(2025, 6, 15, 12, 0));
    }

    @Test
    void testQueryPoint_ReturnsWeatherGrid() {
        WeatherGrid result = weatherService.queryPoint(pointRequest);

        assertNotNull(result);
        assertEquals(116.4, result.getLongitude());
        assertEquals(39.9, result.getLatitude());
        assertEquals(100.0, result.getAltitude());
        assertNotNull(result.getTemperature());
        assertNotNull(result.getHumidity());
        assertNotNull(result.getWindSpeed());
        assertNotNull(result.getWindDirection());
        assertNotNull(result.getPressure());
        assertNotNull(result.getVisibility());
        assertNotNull(result.getCloudCover());

        // 验证缓存写入
        verify(valueOperations).set(anyString(), any(WeatherGrid.class), eq(Duration.ofMinutes(10)));
    }

    @Test
    void testQueryPoint_CacheHit() {
        WeatherGrid cachedGrid = new WeatherGrid();
        cachedGrid.setLongitude(116.4);
        cachedGrid.setLatitude(39.9);
        cachedGrid.setTemperature(25.0);
        when(valueOperations.get(anyString())).thenReturn(cachedGrid);

        WeatherGrid result = weatherService.queryPoint(pointRequest);

        assertNotNull(result);
        assertEquals(25.0, result.getTemperature());
        // 缓存命中时不应再写入缓存
        verify(valueOperations, never()).set(anyString(), any(), any(Duration.class));
    }

    @Test
    void testQueryRegion_ReturnsMultipleGrids() {
        // 使用小范围查询以避免过多格点
        List<WeatherGrid> result = weatherService.queryRegion(
                116.39, 39.89, 116.41, 39.91,
                100.0, "FUSION", LocalDateTime.of(2025, 6, 15, 12, 0)
        );

        assertNotNull(result);
        assertFalse(result.isEmpty());
        // 验证每个格点都有基本数据
        for (WeatherGrid grid : result) {
            assertNotNull(grid.getTemperature());
            assertNotNull(grid.getWindSpeed());
            assertNotNull(grid.getPressure());
        }
    }

    @Test
    void testQueryWindProfile_ReturnsProfileWithLayers() {
        WindProfile result = weatherService.queryWindProfile(windProfileRequest);

        assertNotNull(result);
        assertEquals(116.4, result.getLongitude());
        assertEquals(39.9, result.getLatitude());
        assertNotNull(result.getLayers());
        assertFalse(result.getLayers().isEmpty());

        // 验证各高度层
        for (WindProfile.WindLayer layer : result.getLayers()) {
            assertNotNull(layer.getAltitude());
            assertNotNull(layer.getWindSpeed());
            assertNotNull(layer.getWindDirection());
            assertNotNull(layer.getVerticalWindSpeed());
            assertNotNull(layer.getTurbulence());
        }
    }

    @Test
    void testQueryWindProfile_DefaultParameters() {
        WindProfileQueryRequest request = new WindProfileQueryRequest();
        request.setLongitude(116.4);
        request.setLatitude(39.9);

        WindProfile result = weatherService.queryWindProfile(request);

        assertNotNull(result);
        assertEquals("FUSION", result.getSource());
        assertNotNull(result.getForecastTime());
        assertNotNull(result.getLayers());
        assertFalse(result.getLayers().isEmpty());
    }

    @Test
    void testQueryFusion_SetsSourceToNull() {
        WeatherQueryRequest fusionRequest = new WeatherQueryRequest();
        fusionRequest.setLongitude(116.4);
        fusionRequest.setLatitude(39.9);
        fusionRequest.setSource("WRF");

        WeatherGrid result = weatherService.queryFusion(fusionRequest);

        assertNotNull(result);
        assertEquals(116.4, result.getLongitude());
        assertEquals(39.9, result.getLatitude());
    }

    @Test
    void testQueryPoint_WithNullAltitude() {
        WeatherQueryRequest request = new WeatherQueryRequest();
        request.setLongitude(116.4);
        request.setLatitude(39.9);
        request.setAltitude(null);

        WeatherGrid result = weatherService.queryPoint(request);

        assertNotNull(result);
        assertNotNull(result.getTemperature());
        assertNotNull(result.getPressure());
    }

    @Test
    void testQueryPoint_RealMode_PersistsToDatabase() {
        // 切换到真实模式
        ReflectionTestUtils.setField(weatherService, "mockEnabled", false);
        when(weatherRecordMapper.insert(any(WeatherRecord.class))).thenReturn(1);

        WeatherGrid result = weatherService.queryPoint(pointRequest);

        assertNotNull(result);
        assertNotNull(result.getTemperature());
        // 验证数据已持久化
        verify(weatherRecordMapper).insert(any(WeatherRecord.class));
    }
}

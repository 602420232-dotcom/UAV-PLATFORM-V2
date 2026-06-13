package com.uav.weather.service;

import com.uav.weather.dto.WeatherQueryRequest;
import com.uav.weather.dto.WindProfileQueryRequest;
import com.uav.weather.entity.WeatherGrid;
import com.uav.weather.entity.WeatherRecord;
import com.uav.weather.entity.WindProfile;
import com.uav.common.core.context.MockContext;
import com.uav.weather.mapper.WeatherRecordMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;

/**
 * 气象数据服务
 * <p>
 * 通过 {@code uav.mock.enabled} 控制是否使用模拟数据:
 * <ul>
 *   <li>mock=true: 使用纯随机模拟数据（原有逻辑保留）</li>
 *   <li>mock=false: 使用数学模型生成逼真气象数据，持久化到数据库，缓存到 Redis</li>
 * </ul>
 */
@Slf4j
@Service
public class WeatherService {

    private final RedisTemplate<String, Object> redisTemplate;
    private final WeatherRecordMapper weatherRecordMapper;

    @Value("${uav.mock.enabled:true}")
    private boolean mockEnabled;

    public WeatherService(RedisTemplate<String, Object> redisTemplate,
                          WeatherRecordMapper weatherRecordMapper) {
        this.redisTemplate = redisTemplate;
        this.weatherRecordMapper = weatherRecordMapper;
    }

    /**
     * 查询单点气象数据（支持多源融合）
     */
    public WeatherGrid queryPoint(WeatherQueryRequest request) {
        String cacheKey = buildCacheKey(request);

        WeatherGrid cached = (WeatherGrid) redisTemplate.opsForValue().get(cacheKey);
        if (cached != null) {
            log.debug("Weather cache hit: {}", cacheKey);
            return cached;
        }

        WeatherGrid grid;
        if (mockEnabled) {
            MockContext.setMockMode();
            grid = fetchFromSourceMock(request);
        } else {
            grid = fetchFromSourceReal(request);
        }

        redisTemplate.opsForValue().set(cacheKey, grid, Duration.ofMinutes(10));
        return grid;
    }

    /**
     * 查询区域气象格点
     */
    public List<WeatherGrid> queryRegion(double minLon, double minLat, double maxLon, double maxLat,
                                          Double altitude, String source, LocalDateTime forecastTime) {
        List<WeatherGrid> grids = new ArrayList<>();
        double step = 0.01; // ~1km

        for (double lon = minLon; lon <= maxLon; lon += step) {
            for (double lat = minLat; lat <= maxLat; lat += step) {
                WeatherQueryRequest req = new WeatherQueryRequest();
                req.setLongitude(lon);
                req.setLatitude(lat);
                req.setAltitude(altitude);
                req.setSource(source);
                req.setForecastTime(forecastTime);
                grids.add(queryPoint(req));
            }
        }
        return grids;
    }

    /**
     * 查询风场剖面
     */
    public WindProfile queryWindProfile(WindProfileQueryRequest request) {
        WindProfile profile = new WindProfile();
        profile.setLongitude(request.getLongitude());
        profile.setLatitude(request.getLatitude());
        profile.setSource(request.getSource() != null ? request.getSource() : "FUSION");
        profile.setForecastTime(request.getForecastTime() != null ? request.getForecastTime() : LocalDateTime.now());
        profile.setCreatedAt(LocalDateTime.now());

        List<WindProfile.WindLayer> layers = new ArrayList<>();
        for (double alt = request.getMinAltitude(); alt <= request.getMaxAltitude(); alt += request.getInterval()) {
            WindProfile.WindLayer layer = new WindProfile.WindLayer();
            layer.setAltitude(alt);
            if (mockEnabled) {
                MockContext.setMockMode();
                layer.setWindSpeed(generateWindSpeedMock(alt));
                layer.setWindDirection(generateWindDirectionMock(alt));
                layer.setVerticalWindSpeed(generateVerticalWindMock(alt));
                layer.setTurbulence(generateTurbulenceMock(alt));
            } else {
                layer.setWindSpeed(calculateWindSpeed(request.getLatitude(), request.getLongitude(), alt, request.getForecastTime()));
                layer.setWindDirection(calculateWindDirection(request.getLatitude(), request.getLongitude(), alt, request.getForecastTime()));
                layer.setVerticalWindSpeed(calculateVerticalWind(alt, request.getForecastTime()));
                layer.setTurbulence(calculateTurbulence(alt));
            }
            layers.add(layer);
        }
        profile.setLayers(layers);
        return profile;
    }

    /**
     * 多源融合查询
     */
    public WeatherGrid queryFusion(WeatherQueryRequest request) {
        request.setSource(null);
        return queryPoint(request);
    }

    private String buildCacheKey(WeatherQueryRequest request) {
        return String.format("weather:%.4f:%.4f:%s:%s:%s",
                request.getLongitude(),
                request.getLatitude(),
                request.getAltitude() != null ? request.getAltitude() : "g",
                request.getSource() != null ? request.getSource() : "fusion",
                request.getForecastTime() != null ? request.getForecastTime() : "latest");
    }

    // ========== Mock 模式实现（纯随机数据） ==========

    private WeatherGrid fetchFromSourceMock(WeatherQueryRequest request) {
        WeatherGrid grid = new WeatherGrid();
        grid.setLongitude(request.getLongitude());
        grid.setLatitude(request.getLatitude());
        grid.setAltitude(request.getAltitude());
        grid.setSource(request.getSource() != null ? request.getSource() : "FUSION");
        grid.setForecastTime(request.getForecastTime() != null ? request.getForecastTime() : LocalDateTime.now());
        grid.setCreatedAt(LocalDateTime.now());

        grid.setTemperature(generateTemperatureMock(request.getLatitude()));
        grid.setHumidity(generateHumidityMock());
        grid.setWindSpeed(generateWindSpeedMock(request.getAltitude() != null ? request.getAltitude() : 10));
        grid.setWindDirection(generateWindDirectionMock(0));
        grid.setPressure(generatePressure(request.getAltitude()));
        grid.setPrecipitation(generatePrecipitationMock());
        grid.setVisibility(generateVisibilityMock());
        grid.setCloudCover(generateCloudCoverMock());

        return grid;
    }

    // ========== 真实模式实现（数学模型 + 数据库持久化） ==========

    private WeatherGrid fetchFromSourceReal(WeatherQueryRequest request) {
        LocalDateTime observationTime = request.getForecastTime() != null
                ? request.getForecastTime() : LocalDateTime.now();
        double lat = request.getLatitude();
        double lon = request.getLongitude();
        double alt = request.getAltitude() != null ? request.getAltitude() : 0;

        // 使用数学模型计算逼真气象数据
        double temperature = calculateTemperature(lat, lon, alt, observationTime);
        double humidity = calculateHumidity(lat, lon, observationTime);
        double windSpeed = calculateWindSpeed(lat, lon, alt, observationTime);
        double windDirection = calculateWindDirection(lat, lon, alt, observationTime);
        double pressure = calculatePressure(alt);
        double precipitation = calculatePrecipitation(lat, lon, observationTime);
        double visibility = calculateVisibility(humidity, precipitation);
        double cloudCover = calculateCloudCover(humidity, precipitation);

        // 构建返回对象
        WeatherGrid grid = new WeatherGrid();
        grid.setLongitude(lon);
        grid.setLatitude(lat);
        grid.setAltitude(alt);
        grid.setSource(request.getSource() != null ? request.getSource() : "FUSION");
        grid.setForecastTime(observationTime);
        grid.setCreatedAt(LocalDateTime.now());
        grid.setTemperature(temperature);
        grid.setHumidity(humidity);
        grid.setWindSpeed(windSpeed);
        grid.setWindDirection(windDirection);
        grid.setPressure(pressure);
        grid.setPrecipitation(precipitation);
        grid.setVisibility(visibility);
        grid.setCloudCover(cloudCover);

        // 持久化到数据库
        try {
            WeatherRecord record = new WeatherRecord();
            record.setLat(lat);
            record.setLon(lon);
            record.setAltitude(alt);
            record.setTemperature(temperature);
            record.setHumidity(humidity);
            record.setWindSpeed(windSpeed);
            record.setWindDirection(windDirection);
            record.setPressure(pressure);
            record.setVisibility(visibility);
            record.setDataSource(grid.getSource());
            record.setObservationTime(observationTime);
            record.setTenantId(1L);
            record.setCreatedAt(LocalDateTime.now());
            weatherRecordMapper.insert(record);
            log.debug("气象数据已持久化, id={}", record.getId());
        } catch (Exception e) {
            log.warn("气象数据持久化失败, lat={}, lon={}: {}", lat, lon, e.getMessage());
        }

        return grid;
    }

    // ========== 数学模型（真实模式） ==========

    /**
     * 基于纬度、经度、高度和时间的温度计算模型
     * 使用纬度递减率 + 日变化正弦波 + 季节变化
     */
    private double calculateTemperature(double lat, double lon, double alt, LocalDateTime time) {
        // 基础温度：赤道约30°C，极地约-15°C
        double baseTemp = 30.0 - Math.abs(lat) * 0.6;

        // 高度递减率：每升高1000m降低6.5°C
        baseTemp -= alt * 0.0065;

        // 日变化：午后14时最高，凌晨4时最低，振幅约5°C
        double hourOfDay = time.getHour() + time.getMinute() / 60.0;
        double dailyCycle = 5.0 * Math.sin((hourOfDay - 4.0) * Math.PI / 12.0);

        // 季节变化：北半球7月最热，1月最冷
        int dayOfYear = time.getDayOfYear();
        double seasonalCycle = 8.0 * Math.sin((dayOfYear - 80) * 2.0 * Math.PI / 365.0);

        // 经度微调（大陆性气候效应）
        double continentEffect = 2.0 * Math.cos((lon - 110.0) * Math.PI / 30.0);

        return Math.round((baseTemp + dailyCycle + seasonalCycle + continentEffect) * 10.0) / 10.0;
    }

    /**
     * 基于纬度、经度和时间的湿度计算模型
     * 沿海湿度高，内陆低；清晨高，午后低
     */
    private double calculateHumidity(double lat, double lon, LocalDateTime time) {
        // 基础湿度：沿海高，内陆低
        double baseHumidity = 70.0 - Math.abs(lon - 120.0) * 0.3;

        // 日变化：清晨湿度高，午后低
        double hourOfDay = time.getHour() + time.getMinute() / 60.0;
        double dailyCycle = 15.0 * Math.cos((hourOfDay - 5.0) * Math.PI / 12.0);

        // 季节变化：夏季湿度高
        int dayOfYear = time.getDayOfYear();
        double seasonalCycle = 10.0 * Math.sin((dayOfYear - 80) * 2.0 * Math.PI / 365.0);

        double humidity = baseHumidity + dailyCycle + seasonalCycle;
        return Math.max(20.0, Math.min(98.0, Math.round(humidity * 10.0) / 10.0));
    }

    /**
     * 基于纬度、经度、高度和时间的风速计算模型
     * 地面摩擦层风速小，高空风速大（对数风廓线）
     */
    private double calculateWindSpeed(double lat, double lon, double alt, LocalDateTime time) {
        // 地面基准风速（约3-5 m/s）
        double surfaceWind = 3.5 + 1.5 * Math.sin((lon + lat) * 0.1);

        // 对数风廓线：风速随高度对数增长
        double roughnessLength = 0.1; // 地表粗糙度(m)
        double refHeight = 10.0; // 参考高度(m)
        double windSpeed;
        if (alt > refHeight) {
            windSpeed = surfaceWind * Math.log(alt / roughnessLength) / Math.log(refHeight / roughnessLength);
        } else {
            windSpeed = surfaceWind * Math.max(0.1, alt / refHeight);
        }

        // 日变化：午后风速略大
        double hourOfDay = time.getHour() + time.getMinute() / 60.0;
        double dailyFactor = 1.0 + 0.15 * Math.sin((hourOfDay - 6.0) * Math.PI / 12.0);

        windSpeed *= dailyFactor;

        return Math.max(0.0, Math.round(windSpeed * 10.0) / 10.0);
    }

    /**
     * 基于纬度、经度、高度和时间的主导风向计算模型
     * 中国东部中纬度地区盛行西风带
     */
    private double calculateWindDirection(double lat, double lon, double alt, LocalDateTime time) {
        // 基础风向：中纬度盛行偏西风（约270°）
        double baseDirection = 270.0;

        // 纬度修正：低纬度偏东风
        double latEffect = -30.0 * Math.sin(lat * Math.PI / 90.0);

        // 季节修正：冬季西北风，夏季东南风
        int dayOfYear = time.getDayOfYear();
        double seasonalEffect = 45.0 * Math.sin((dayOfYear - 80) * 2.0 * Math.PI / 365.0);

        // 日变化：海陆风效应
        double hourOfDay = time.getHour() + time.getMinute() / 60.0;
        double dailyEffect = 20.0 * Math.sin((hourOfDay - 6.0) * Math.PI / 12.0);

        double direction = baseDirection + latEffect + seasonalEffect + dailyEffect;

        // 归一化到 0-360
        direction = ((direction % 360) + 360) % 360;
        return Math.round(direction * 10.0) / 10.0;
    }

    /**
     * 基于高度的气压计算模型（气压高度公式）
     */
    private double calculatePressure(double alt) {
        // 标准大气压 1013.25 hPa，标高 8500m
        return Math.round(1013.25 * Math.exp(-alt / 8500.0) * 100.0) / 100.0;
    }

    /**
     * 基于纬度、经度和时间的降水概率计算模型
     */
    private double calculatePrecipitation(double lat, double lon, LocalDateTime time) {
        // 降水概率与湿度相关（简化模型）
        double humidity = calculateHumidity(lat, lon, time);
        if (humidity < 60) {
            return 0.0;
        }

        // 季节性降水概率
        int dayOfYear = time.getDayOfYear();
        double seasonalFactor = 0.3 + 0.4 * Math.sin((dayOfYear - 60) * 2.0 * Math.PI / 365.0);

        // 地域降水概率
        double regionFactor = 0.5 + 0.3 * Math.cos((lon - 110.0) * Math.PI / 40.0);

        double precipProbability = (humidity - 60.0) / 40.0 * seasonalFactor * regionFactor;

        if (precipProbability < 0.3) {
            return 0.0;
        }

        // 降水量：0-15mm
        double precipitation = precipProbability * 15.0;
        return Math.round(precipitation * 10.0) / 10.0;
    }

    /**
     * 基于湿度和降水量的能见度计算模型
     */
    private double calculateVisibility(double humidity, double precipitation) {
        // 基础能见度
        double visibility = 20.0;

        // 湿度影响：湿度高能见度低
        if (humidity > 80) {
            visibility -= (humidity - 80) * 0.5;
        }

        // 降水影响：降水越大能见度越低
        if (precipitation > 0) {
            visibility -= precipitation * 1.5;
        }

        return Math.max(0.5, Math.round(visibility * 10.0) / 10.0);
    }

    /**
     * 基于湿度和降水量的云量计算模型
     */
    private double calculateCloudCover(double humidity, double precipitation) {
        double cloudCover = 20.0 + (humidity - 30.0) * 0.8;

        if (precipitation > 0) {
            cloudCover += precipitation * 3.0;
        }

        return Math.max(0.0, Math.min(100.0, Math.round(cloudCover * 10.0) / 10.0));
    }

    /**
     * 基于高度和时间计算垂直风速
     */
    private double calculateVerticalWind(double alt, LocalDateTime time) {
        double hourOfDay = time.getHour() + time.getMinute() / 60.0;
        // 对流在午后最强
        double convectionFactor = Math.sin((hourOfDay - 6.0) * Math.PI / 12.0);
        double verticalWind = 0.3 * convectionFactor * Math.min(1.0, alt / 500.0);
        return Math.round(verticalWind * 100.0) / 100.0;
    }

    /**
     * 基于高度计算湍流强度
     * 地面湍流强，高空减弱
     */
    private double calculateTurbulence(double alt) {
        double turbulence = 0.25 * Math.exp(-alt / 2000.0);
        return Math.round(turbulence * 100.0) / 100.0;
    }

    // ========== Mock 随机数据生成（原有逻辑） ==========

    private double generateTemperatureMock(double latitude) {
        double base = 25.0 - Math.abs(latitude - 30.0) * 0.5;
        return base + (Math.random() * 6 - 3);
    }

    private double generateHumidityMock() {
        return 40 + Math.random() * 50;
    }

    private double generateWindSpeedMock(double altitude) {
        double base = 3.0 + altitude * 0.005;
        return Math.max(0, base + (Math.random() * 4 - 2));
    }

    private double generateWindDirectionMock(double altitude) {
        return Math.random() * 360;
    }

    private double generateVerticalWindMock(double altitude) {
        return Math.random() - 0.5;
    }

    private double generateTurbulenceMock(double altitude) {
        return Math.random() * 0.3;
    }

    private double generatePressure(Double altitude) {
        double alt = altitude != null ? altitude : 0;
        return 1013.25 * Math.exp(-alt / 8500.0);
    }

    private double generatePrecipitationMock() {
        return Math.random() < 0.3 ? Math.random() * 5 : 0;
    }

    private double generateVisibilityMock() {
        return 5 + Math.random() * 15;
    }

    private double generateCloudCoverMock() {
        return Math.random() * 100;
    }
}

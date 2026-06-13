package com.uav.weather.service;

import com.uav.weather.dto.WeatherQueryRequest;
import com.uav.weather.dto.WindProfileQueryRequest;
import com.uav.weather.entity.WeatherGrid;
import com.uav.weather.entity.WindProfile;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

/**
 * 气象数据服务
 * <p>
 * MVP 阶段使用模拟数据，后续对接 Python 算法服务获取真实 WRF 数据。
 */
@Slf4j
@Service
public class WeatherService {

    private final RedisTemplate<String, Object> redisTemplate;

    public WeatherService(RedisTemplate<String, Object> redisTemplate) {
        this.redisTemplate = redisTemplate;
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

        WeatherGrid grid = fetchFromSource(request);
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
            layer.setWindSpeed(generateWindSpeed(alt));
            layer.setWindDirection(generateWindDirection(alt));
            layer.setVerticalWindSpeed(generateVerticalWind(alt));
            layer.setTurbulence(generateTurbulence(alt));
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

    private WeatherGrid fetchFromSource(WeatherQueryRequest request) {
        WeatherGrid grid = new WeatherGrid();
        grid.setLongitude(request.getLongitude());
        grid.setLatitude(request.getLatitude());
        grid.setAltitude(request.getAltitude());
        grid.setSource(request.getSource() != null ? request.getSource() : "FUSION");
        grid.setForecastTime(request.getForecastTime() != null ? request.getForecastTime() : LocalDateTime.now());
        grid.setCreatedAt(LocalDateTime.now());

        // MVP: 模拟数据，后续对接 Python 算法服务
        grid.setTemperature(generateTemperature(request.getLatitude()));
        grid.setHumidity(generateHumidity());
        grid.setWindSpeed(generateWindSpeed(request.getAltitude() != null ? request.getAltitude() : 10));
        grid.setWindDirection(generateWindDirection(0));
        grid.setPressure(generatePressure(request.getAltitude()));
        grid.setPrecipitation(generatePrecipitation());
        grid.setVisibility(generateVisibility());
        grid.setCloudCover(generateCloudCover());

        return grid;
    }

    private String buildCacheKey(WeatherQueryRequest request) {
        return String.format("weather:%.4f:%.4f:%s:%s:%s",
                request.getLongitude(),
                request.getLatitude(),
                request.getAltitude() != null ? request.getAltitude() : "g",
                request.getSource() != null ? request.getSource() : "fusion",
                request.getForecastTime() != null ? request.getForecastTime() : "latest");
    }

    // ===== 模拟数据生成 =====

    private double generateTemperature(double latitude) {
        double base = 25.0 - Math.abs(latitude - 30.0) * 0.5;
        return base + ThreadLocalRandom.current().nextDouble(-3, 3);
    }

    private double generateHumidity() {
        return ThreadLocalRandom.current().nextDouble(40, 90);
    }

    private double generateWindSpeed(double altitude) {
        double base = 3.0 + altitude * 0.005;
        return Math.max(0, base + ThreadLocalRandom.current().nextDouble(-2, 2));
    }

    private double generateWindDirection(double altitude) {
        return ThreadLocalRandom.current().nextDouble(0, 360);
    }

    private double generateVerticalWind(double altitude) {
        return ThreadLocalRandom.current().nextDouble(-0.5, 0.5);
    }

    private double generateTurbulence(double altitude) {
        return ThreadLocalRandom.current().nextDouble(0, 0.3);
    }

    private double generatePressure(Double altitude) {
        double alt = altitude != null ? altitude : 0;
        return 1013.25 * Math.exp(-alt / 8500.0);
    }

    private double generatePrecipitation() {
        return ThreadLocalRandom.current().nextDouble() < 0.3
                ? ThreadLocalRandom.current().nextDouble(0, 5)
                : 0;
    }

    private double generateVisibility() {
        return ThreadLocalRandom.current().nextDouble(5, 20);
    }

    private double generateCloudCover() {
        return ThreadLocalRandom.current().nextDouble(0, 100);
    }
}

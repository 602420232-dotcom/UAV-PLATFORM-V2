package com.uav.utm.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.uav.common.core.context.MockContext;
import com.uav.utm.entity.Airspace;
import com.uav.utm.mapper.AirspaceMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 空域管理服务
 * <p>
 * 通过 {@code uav.mock.enabled} 开关控制：
 * <ul>
 *   <li>true（默认）: 返回空数据（现有逻辑保留）</li>
 *   <li>false: 使用数据库 CRUD</li>
 * </ul>
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AirspaceService {

    private final AirspaceMapper airspaceMapper;

    @Value("${uav.mock.enabled:true}")
    private boolean mockEnabled;

    public List<Airspace> getAirspaces() {
        if (mockEnabled) {
            MockContext.setMockMode();
            return List.of();
        }
        LambdaQueryWrapper<Airspace> wrapper = new LambdaQueryWrapper<>();
        wrapper.orderByDesc(Airspace::getCreatedAt);
        return airspaceMapper.selectList(wrapper);
    }

    public boolean checkAirspaceRestriction(Double lon, Double lat, Double altitude) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return false;
        }
        LambdaQueryWrapper<Airspace> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Airspace::getStatus, Airspace.AirspaceStatus.ACTIVE)
                .le(Airspace::getAltitudeMin, altitude)
                .ge(Airspace::getAltitudeMax, altitude);
        Long count = airspaceMapper.selectCount(wrapper);
        return count != null && count > 0;
    }

    public Airspace createDynamicAirspace(Airspace airspace) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return airspace;
        }
        airspace.setStatus(Airspace.AirspaceStatus.ACTIVE);
        airspace.setCreatedAt(LocalDateTime.now());
        airspace.setUpdatedAt(LocalDateTime.now());
        airspaceMapper.insert(airspace);
        log.info("动态空域已创建, id={}", airspace.getId());
        return airspace;
    }
}

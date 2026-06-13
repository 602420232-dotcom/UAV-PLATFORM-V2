package com.uav.utm.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.uav.utm.dto.UavPositionReport;
import com.uav.utm.entity.ConflictAlert;
import com.uav.utm.entity.UavPosition;
import com.uav.utm.mapper.ConflictAlertMapper;
import com.uav.utm.mapper.UavPositionMapper;
import com.uav.utm.ws.UtmWebSocketHandler;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * 无人机追踪服务
 * <p>
 * 通过 {@code uav.mock.enabled} 开关控制：
 * <ul>
 *   <li>true（默认）: 返回空数据（现有逻辑保留）</li>
 *   <li>false: 使用数据库持久化</li>
 * </ul>
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class UavTrackingService {

    private final UavPositionMapper uavPositionMapper;
    private final ConflictAlertMapper conflictAlertMapper;
    private final UtmWebSocketHandler utmWebSocketHandler;

    @Value("${uav.mock.enabled:true}")
    private boolean mockEnabled;

    public UavPosition reportPosition(UavPositionReport report) {
        UavPosition position;
        if (mockEnabled) {
            MockContext.setMockMode();
            position = new UavPosition();
            position.setUavId(report.getUavId());
            position.setLongitude(report.getLon());
            position.setLatitude(report.getLat());
            position.setAltitude(report.getAlt());
            position.setSpeed(report.getSpeed());
            position.setHeading(report.getHeading());
            position.setRecordedAt(report.getTimestamp());
        } else {
            position = new UavPosition();
            position.setUavId(report.getUavId());
            position.setLongitude(report.getLon());
            position.setLatitude(report.getLat());
            position.setAltitude(report.getAlt());
            position.setSpeed(report.getSpeed());
            position.setHeading(report.getHeading());
            position.setRecordedAt(LocalDateTime.now());
            uavPositionMapper.insert(position);
            log.debug("无人机位置已记录, uavId={}, id={}", report.getUavId(), position.getId());
        }

        // 通过 WebSocket 广播位置更新到订阅了该 UAV 的客户端
        broadcastPositionUpdate(position);

        return position;
    }

    public Optional<UavPosition> getCurrentPosition(String uavId) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return Optional.empty();
        }
        LambdaQueryWrapper<UavPosition> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(UavPosition::getUavId, uavId)
                .orderByDesc(UavPosition::getRecordedAt)
                .last("LIMIT 1");
        return Optional.ofNullable(uavPositionMapper.selectOne(wrapper));
    }

    public List<UavPosition> getTrackHistory(String uavId) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return List.of();
        }
        LambdaQueryWrapper<UavPosition> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(UavPosition::getUavId, uavId)
                .orderByDesc(UavPosition::getRecordedAt)
                .last("LIMIT 100");
        return uavPositionMapper.selectList(wrapper);
    }

    public List<ConflictAlert> checkConflicts(String uavId) {
        List<ConflictAlert> alerts;
        if (mockEnabled) {
            MockContext.setMockMode();
            alerts = List.of();
        } else {
            LambdaQueryWrapper<ConflictAlert> wrapper = new LambdaQueryWrapper<>();
            wrapper.eq(ConflictAlert::getStatus, ConflictAlert.AlertStatus.ACTIVE)
                    .like(ConflictAlert::getInvolvedEntitiesJson, uavId)
                    .orderByDesc(ConflictAlert::getCreatedAt);
            alerts = conflictAlertMapper.selectList(wrapper);
        }

        // 发现冲突后广播到 "alerts" 频道
        for (ConflictAlert alert : alerts) {
            broadcastConflictAlert(alert);
        }

        return alerts;
    }

    // ===== WebSocket 广播 =====

    /**
     * 广播位置更新到订阅了该 UAV 的 WebSocket 客户端
     */
    private void broadcastPositionUpdate(UavPosition position) {
        try {
            Map<String, Object> positionData = new HashMap<>();
            positionData.put("type", "POSITION_UPDATE");
            positionData.put("uavId", position.getUavId());
            positionData.put("longitude", position.getLongitude());
            positionData.put("latitude", position.getLatitude());
            positionData.put("altitude", position.getAltitude());
            positionData.put("speed", position.getSpeed());
            positionData.put("heading", position.getHeading());
            positionData.put("timestamp", position.getRecordedAt() != null
                    ? position.getRecordedAt().toString() : LocalDateTime.now().toString());

            utmWebSocketHandler.broadcastUavPosition(position.getUavId(), positionData);
            log.debug("位置更新已通过 WebSocket 广播, uavId={}", position.getUavId());
        } catch (Exception e) {
            log.error("广播位置更新失败, uavId={}", position.getUavId(), e);
        }
    }

    /**
     * 广播冲突告警到 "alerts" 频道
     */
    private void broadcastConflictAlert(ConflictAlert alert) {
        try {
            Map<String, Object> alertData = new HashMap<>();
            alertData.put("type", "CONFLICT_ALERT");
            alertData.put("alertId", alert.getId());
            alertData.put("conflictType", alert.getType().name());
            alertData.put("severity", alert.getSeverity().name());
            alertData.put("involvedEntities", alert.getInvolvedEntitiesJson());
            alertData.put("status", alert.getStatus().name());
            alertData.put("createdAt", alert.getCreatedAt() != null
                    ? alert.getCreatedAt().toString() : "");

            utmWebSocketHandler.broadcastAlert(alertData);
            log.debug("冲突告警已通过 WebSocket 广播, alertId={}", alert.getId());
        } catch (Exception e) {
            log.error("广播冲突告警失败, alertId={}", alert.getId(), e);
        }
    }
}

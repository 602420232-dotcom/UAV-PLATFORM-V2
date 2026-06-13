package com.uav.utm.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.uav.common.core.context.MockContext;
import com.uav.common.core.util.IdUtil;
import com.uav.utm.entity.FlightPlan;
import com.uav.utm.mapper.FlightPlanMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * 飞行计划服务
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
public class FlightPlanService {

    private final FlightPlanMapper flightPlanMapper;

    @Value("${uav.mock.enabled:true}")
    private boolean mockEnabled;

    public FlightPlan submitPlan(FlightPlan plan) {
        if (mockEnabled) {
            MockContext.setMockMode();
            plan.setStatus(FlightPlan.FlightPlanStatus.SUBMITTED);
            return plan;
        }
        plan.setPlanId(IdUtil.fastUuid());
        plan.setStatus(FlightPlan.FlightPlanStatus.SUBMITTED);
        plan.setCreatedAt(LocalDateTime.now());
        if (plan.getEmergencyFlag() == null) {
            plan.setEmergencyFlag(false);
        }
        flightPlanMapper.insert(plan);
        log.info("飞行计划已提交, planId={}", plan.getPlanId());
        return plan;
    }

    public FlightPlan approvePlan(Long planId) {
        if (mockEnabled) {
            MockContext.setMockMode();
            FlightPlan plan = new FlightPlan();
            plan.setId(planId);
            plan.setStatus(FlightPlan.FlightPlanStatus.APPROVED);
            return plan;
        }
        FlightPlan plan = flightPlanMapper.selectById(planId);
        if (plan == null) {
            return null;
        }
        plan.setStatus(FlightPlan.FlightPlanStatus.APPROVED);
        plan.setApprovalCode("APR-" + IdUtil.fastUuid().substring(0, 8));
        flightPlanMapper.updateById(plan);
        log.info("飞行计划已审批, planId={}", planId);
        return plan;
    }

    public FlightPlan rejectPlan(Long planId) {
        if (mockEnabled) {
            MockContext.setMockMode();
            FlightPlan plan = new FlightPlan();
            plan.setId(planId);
            plan.setStatus(FlightPlan.FlightPlanStatus.REJECTED);
            return plan;
        }
        FlightPlan plan = flightPlanMapper.selectById(planId);
        if (plan == null) {
            return null;
        }
        plan.setStatus(FlightPlan.FlightPlanStatus.REJECTED);
        flightPlanMapper.updateById(plan);
        log.info("飞行计划已拒绝, planId={}", planId);
        return plan;
    }

    public FlightPlan startFlight(Long planId) {
        if (mockEnabled) {
            MockContext.setMockMode();
            FlightPlan plan = new FlightPlan();
            plan.setId(planId);
            plan.setStatus(FlightPlan.FlightPlanStatus.ACTIVE);
            return plan;
        }
        FlightPlan plan = flightPlanMapper.selectById(planId);
        if (plan == null) {
            return null;
        }
        plan.setStatus(FlightPlan.FlightPlanStatus.ACTIVE);
        plan.setActualStartTime(LocalDateTime.now());
        flightPlanMapper.updateById(plan);
        log.info("飞行已开始, planId={}", planId);
        return plan;
    }

    public FlightPlan completeFlight(Long planId) {
        if (mockEnabled) {
            MockContext.setMockMode();
            FlightPlan plan = new FlightPlan();
            plan.setId(planId);
            plan.setStatus(FlightPlan.FlightPlanStatus.COMPLETED);
            return plan;
        }
        FlightPlan plan = flightPlanMapper.selectById(planId);
        if (plan == null) {
            return null;
        }
        plan.setStatus(FlightPlan.FlightPlanStatus.COMPLETED);
        plan.setActualEndTime(LocalDateTime.now());
        flightPlanMapper.updateById(plan);
        log.info("飞行已完成, planId={}", planId);
        return plan;
    }

    public FlightPlan cancelPlan(Long planId) {
        if (mockEnabled) {
            MockContext.setMockMode();
            FlightPlan plan = new FlightPlan();
            plan.setId(planId);
            plan.setStatus(FlightPlan.FlightPlanStatus.CANCELLED);
            return plan;
        }
        FlightPlan plan = flightPlanMapper.selectById(planId);
        if (plan == null) {
            return null;
        }
        plan.setStatus(FlightPlan.FlightPlanStatus.CANCELLED);
        flightPlanMapper.updateById(plan);
        log.info("飞行计划已取消, planId={}", planId);
        return plan;
    }

    public Optional<FlightPlan> getPlan(Long planId) {
        if (mockEnabled) {
            MockContext.setMockMode();
            return Optional.empty();
        }
        return Optional.ofNullable(flightPlanMapper.selectById(planId));
    }

    public List<FlightPlan> listPlans() {
        if (mockEnabled) {
            MockContext.setMockMode();
            return List.of();
        }
        LambdaQueryWrapper<FlightPlan> wrapper = new LambdaQueryWrapper<>();
        wrapper.orderByDesc(FlightPlan::getCreatedAt);
        return flightPlanMapper.selectList(wrapper);
    }
}

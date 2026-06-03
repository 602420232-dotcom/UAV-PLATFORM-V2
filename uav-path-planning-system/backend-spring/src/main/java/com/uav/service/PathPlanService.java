package com.uav.service;

import com.uav.model.PathPlan;
import com.uav.repository.PathPlanRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class PathPlanService {

    private final PathPlanRepository pathPlanRepository;

    public PathPlanService(PathPlanRepository pathPlanRepository) {
        this.pathPlanRepository = pathPlanRepository;
    }

    public List<PathPlan> findAll() {
        return pathPlanRepository.findAll();
    }

    public PathPlan findById(Long id) {
        return pathPlanRepository.findById(id).orElse(null);
    }

    public PathPlan create(PathPlan plan) {
        return pathPlanRepository.save(plan);
    }

    public PathPlan update(Long id, PathPlan plan) {
        PathPlan existing = pathPlanRepository.findById(id).orElse(null);
        if (existing == null) {
            return null;
        }
        existing.setName(plan.getName());
        existing.setDescription(plan.getDescription());
        existing.setDroneCount(plan.getDroneCount());
        existing.setTaskCount(plan.getTaskCount());
        existing.setTotalDistance(plan.getTotalDistance());
        existing.setTotalTime(plan.getTotalTime());
        existing.setTotalRisk(plan.getTotalRisk());
        existing.setRoutesJson(plan.getRoutesJson());
        existing.setStatus(plan.getStatus());
        existing.setWeatherDataId(plan.getWeatherDataId());
        existing.setRiskThreshold(plan.getRiskThreshold());
        return pathPlanRepository.save(existing);
    }

    public void delete(Long id) {
        pathPlanRepository.deleteById(id);
    }

    public List<PathPlan> findByStatus(String status) {
        return pathPlanRepository.findByStatus(status);
    }
}

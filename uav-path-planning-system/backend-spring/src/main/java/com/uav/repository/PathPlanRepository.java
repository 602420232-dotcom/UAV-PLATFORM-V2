package com.uav.repository;

import com.uav.model.PathPlan;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PathPlanRepository extends JpaRepository<PathPlan, Long> {

    List<PathPlan> findByStatus(String status);

    List<PathPlan> findByNameContaining(String name);
}

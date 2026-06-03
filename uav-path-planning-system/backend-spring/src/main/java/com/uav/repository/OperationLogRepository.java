package com.uav.repository;

import com.uav.model.OperationLog;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface OperationLogRepository extends JpaRepository<OperationLog, Long> {

    List<OperationLog> findByUsername(String username);

    List<OperationLog> findByOperation(String operation);

    List<OperationLog> findByStatus(String status);

    List<OperationLog> findAllByOrderByCreatedAtDesc();
}

package com.uav.repository;

import com.uav.entity.DemoSession;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface DemoSessionRepository extends JpaRepository<DemoSession, Long> {

    Optional<DemoSession> findBySessionId(String sessionId);

    Optional<DemoSession> findByDemoUserId(String demoUserId);

    Optional<DemoSession> findByUserId(Long userId);

    List<DemoSession> findByIsActiveTrue();

    List<DemoSession> findByExpiresAtBefore(LocalDateTime now);

    List<DemoSession> findByIsActiveTrueAndExpiresAtAfter(LocalDateTime now);

    long countByIsActiveTrue();

    void deleteByExpiresAtBefore(LocalDateTime now);
}

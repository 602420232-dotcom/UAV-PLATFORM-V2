package com.uav.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "demo_sessions")
public class DemoSession {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "demo_user_id", unique = true, nullable = false)
    private String demoUserId;

    @Column(name = "user_id")
    private Long userId;

    @Column(name = "tenant_id")
    private String tenantId;

    @Column(name = "session_id", unique = true, nullable = false)
    private String sessionId;

    @Column(name = "ip_address")
    private String ipAddress;

    @Column(name = "purpose")
    private String purpose;

    @Column(name = "api_calls", nullable = false)
    private Integer apiCalls;

    @Column(name = "started_at", nullable = false)
    private LocalDateTime startedAt;

    @Column(name = "expires_at", nullable = false)
    private LocalDateTime expiresAt;

    @Column(name = "is_active", nullable = false)
    private Boolean isActive;
}

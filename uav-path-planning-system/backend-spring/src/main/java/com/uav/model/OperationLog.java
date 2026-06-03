package com.uav.model;
import lombok.Data;
import java.time.LocalDateTime;
import jakarta.persistence.*;

@Data
@Entity
@Table(name = "operation_logs")
public class OperationLog {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String username;
    private String operation; // LOGIN, CREATE_TASK, UPDATE_DRONE, DELETE_PATH
    private String details;
    private String ipAddress;
    private String status; // SUCCESS, FAILED
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}

package com.uav.model;
import lombok.Data;
import java.time.LocalDateTime;
import jakarta.persistence.*;

@Data
@Entity
@Table(name = "tasks")
public class Task {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    private String name;
    private String description;
    
    // 任务点坐标
    private Double latitude;
    private Double longitude;
    private Double altitude;
    
    // 任务需求
    private Double demand;
    
    // 时间窗
    private LocalDateTime startTime;
    private LocalDateTime endTime;
    private Integer serviceTime; // 服务时间（分钟）
    
    // 优先级
    private Integer priority;
    
    // 任务状态
    private String status; // PENDING, IN_PROGRESS, COMPLETED, FAILED
    
    // 创建和更新时间
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    
    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }
    
    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
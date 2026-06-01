package com.uav.model;
import lombok.Data;
import java.time.LocalDateTime;
import jakarta.persistence.*;

@Data
@Entity
@Table(name = "path_plans")
public class PathPlan {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    private String name;
    private String description;
    
    // 规划参数
    private Integer droneCount;
    private Integer taskCount;
    private Double totalDistance;
    private Double totalTime;
    private Double totalRisk;
    
    // 规划结果
    private String routesJson; // JSON格式的路径信息
    private String status; // PENDING, COMPLETED, FAILED
    
    // 气象数据关联
    private String weatherDataId;
    private Double riskThreshold;
    
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
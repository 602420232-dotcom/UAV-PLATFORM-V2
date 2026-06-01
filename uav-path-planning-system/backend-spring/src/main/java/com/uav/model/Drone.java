package com.uav.model;
import lombok.Data;
import java.time.LocalDateTime;
import jakarta.persistence.*;

@Data
@Entity
@Table(name = "drones")
public class Drone {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    private String name;
    private String model;
    private String serialNumber;
    
    // 无人机参数
    private Double maxSpeed; // 最大速度（m/s）
    private Double maxCapacity; // 最大载重（kg）
    private Double maxBattery; // 最大续航时间（分钟）
    private Double cruiseSpeed; // 巡航速度（m/s）
    private Double windResistance; // 抗风等级（m/s）
    
    // 状态
    private String status; // IDLE, BUSY, MAINTENANCE, FAILED
    
    // 位置信息
    private Double currentLatitude;
    private Double currentLongitude;
    private Double currentAltitude;
    
    // 电池电量
    private Integer batteryLevel; // 百分比
    
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
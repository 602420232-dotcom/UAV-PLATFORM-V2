package com.uav.model;
import lombok.Data;
import java.time.LocalDateTime;
import jakarta.persistence.*;

@Data
@Entity
@Table(name = "weather_data")
public class WeatherData {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    // 数据时间
    private LocalDateTime forecastTime;
    private LocalDateTime updateTime;
    
    // 空间范围
    private Double minLatitude;
    private Double maxLatitude;
    private Double minLongitude;
    private Double maxLongitude;
    private Integer height;
    
    // 气象要素
    private String windSpeedData; // JSON格式
    private String windDirData; // JSON格式
    private String temperatureData; // JSON格式
    private String humidityData; // JSON格式
    private String turbulenceData; // JSON格式
    private String visibilityData; // JSON格式
    private String thunderRiskData; // JSON格式
    
    // 同化结果
    private String uncertaintyData; // 不确定性方差场
    private String varianceField; // 综合方差场
    
    // 数据来源
    private String source; // WRF, ASSIMILATED, OBSERVATION
    private String status; // AVAILABLE, PROCESSING, EXPIRED
    
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
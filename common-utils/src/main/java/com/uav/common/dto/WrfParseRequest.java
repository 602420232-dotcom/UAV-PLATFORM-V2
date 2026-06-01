package com.uav.common.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

/**
 * WRF数据解析请求 - 用于参数化WRF解析
 * 替代直接上传NetCDF文件的方式，接受JSON格式的气象数据
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class WrfParseRequest {

    /**
     * 高度值（米）
     */
    private Integer height;

    /**
     * 区域范围
     */
    private Map<String, Double> bounds;

    /**
     * 气象数据（可以是已经解析好的数据）
     */
    private Map<String, Object> data;

    /**
     * 文件路径（可选，如果是从已有的文件加载）
     */
    private String filePath;

    /**
     * 时间戳
     */
    private Long timestamp;

    /**
     * 获取高度值，如果未设置则使用默认值
     */
    public int getSafeHeight() {
        return height != null ? height : 100;
    }
}

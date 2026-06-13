package com.uav.assimilation.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 数据同化结果实体
 */
@Data
@TableName("assimilation_result")
public class AssimilationResult {

    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    /**
     * 关联任务ID
     */
    private Long taskId;

    /**
     * 分析场数据 JSON
     */
    private String analysisFieldJson;

    /**
     * 不确定性估计 JSON
     */
    private String uncertaintyJson;

    /**
     * 收敛信息
     */
    private String convergenceInfo;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;
}

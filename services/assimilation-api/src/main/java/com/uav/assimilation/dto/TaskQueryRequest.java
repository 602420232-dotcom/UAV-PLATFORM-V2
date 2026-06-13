package com.uav.assimilation.dto;

import lombok.Data;

/**
 * 任务查询请求
 */
@Data
public class TaskQueryRequest {

    private Long taskId;

    private String status;

    private Integer page = 1;

    private Integer size = 10;
}

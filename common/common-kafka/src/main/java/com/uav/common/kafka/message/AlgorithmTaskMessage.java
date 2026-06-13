package com.uav.common.kafka.message;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.util.Map;

/**
 * Java -> Python 算法任务消息
 * <p>
 * 发送到 topic: {@code uav.algorithm.tasks}
 * <p>
 * Python 端接收格式（snake_case）:
 * <pre>
 * {
 *   "task_id": "uuid",
 *   "algorithm_id": "string",
 *   "params": {...},
 *   "timestamp": "ISO-8601",
 *   "priority": 0
 * }
 * </pre>
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AlgorithmTaskMessage implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 任务唯一标识 */
    private String taskId;

    /** 算法标识 */
    private String algorithmId;

    /** 算法参数 */
    private Map<String, Object> params;

    /** 发送时间（ISO-8601） */
    private String timestamp;

    /** 优先级（数值越小优先级越高） */
    private int priority;

    /** 结果回调 topic（可选，默认使用 uav.algorithm.results） */
    private String callbackTopic;

    /** 租户ID（多租户隔离） */
    private String tenantId;
}

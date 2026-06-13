package com.uav.common.kafka.message;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.util.Map;

/**
 * Python -> Java 算法结果消息
 * <p>
 * 从 topic: {@code uav.algorithm.results} 消费
 * <p>
 * Python 端发送格式（snake_case）:
 * <pre>
 * {
 *   "task_id": "uuid",
 *   "algorithm_id": "string",
 *   "status": "success|failed",
 *   "result": {...},
 *   "error": "string|null",
 *   "completed_at": "ISO-8601"
 * }
 * </pre>
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AlgorithmResultMessage implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 任务唯一标识（与 AlgorithmTaskMessage.taskId 对应） */
    private String taskId;

    /** 算法标识 */
    private String algorithmId;

    /** 执行状态: SUCCESS / FAILED / CANCELLED */
    private String status;

    /** 算法执行结果数据 */
    private Map<String, Object> result;

    /** 错误信息（status=FAILED 时有值） */
    private String error;

    /** 完成时间（ISO-8601） */
    private String completedAt;

    /** 执行进度 0-100 */
    private int progress;
}

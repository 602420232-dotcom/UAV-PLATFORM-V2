package com.uav.common.core.constant;

import lombok.Getter;

/**
 * 异步任务统一状态枚举
 * 全平台对齐，与ResultCode中的任务状态码对应
 */
@Getter
public enum TaskStatus {

    QUEUED("QUEUED", "排队中", 100),
    RUNNING("RUNNING", "运行中", 200),
    SUCCESS("SUCCESS", "成功", 300),
    FAILED("FAILED", "失败", 400),
    TIMEOUT("TIMEOUT", "超时", 500),
    CANCELLED("CANCELLED", "已取消", 600);

    private final String name;
    private final String displayName;
    private final int code;

    TaskStatus(String name, String displayName, int code) {
        this.name = name;
        this.displayName = displayName;
        this.code = code;
    }

    public boolean isTerminal() {
        return this == SUCCESS || this == FAILED || this == TIMEOUT || this == CANCELLED;
    }

    public boolean isRunning() {
        return this == RUNNING;
    }

    public static TaskStatus fromCode(int code) {
        for (TaskStatus status : values()) {
            if (status.code == code) {
                return status;
            }
        }
        return null;
    }

    public static TaskStatus fromName(String name) {
        for (TaskStatus status : values()) {
            if (status.name.equalsIgnoreCase(name)) {
                return status;
            }
        }
        return null;
    }
}

package com.uav.sdk.model;

/**
 * 异步任务结果
 */
public class TaskResult {

    private Long id;
    private String taskId;
    private String status;
    private Integer progress;
    private String algorithmType;
    private String errorMsg;
    private String resultJson;
    private String createdAt;
    private String startedAt;
    private String completedAt;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getTaskId() { return taskId; }
    public void setTaskId(String taskId) { this.taskId = taskId; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public Integer getProgress() { return progress; }
    public void setProgress(Integer progress) { this.progress = progress; }
    public String getAlgorithmType() { return algorithmType; }
    public void setAlgorithmType(String algorithmType) { this.algorithmType = algorithmType; }
    public String getErrorMsg() { return errorMsg; }
    public void setErrorMsg(String errorMsg) { this.errorMsg = errorMsg; }
    public String getResultJson() { return resultJson; }
    public void setResultJson(String resultJson) { this.resultJson = resultJson; }
    public String getCreatedAt() { return createdAt; }
    public void setCreatedAt(String createdAt) { this.createdAt = createdAt; }
    public String getStartedAt() { return startedAt; }
    public void setStartedAt(String startedAt) { this.startedAt = startedAt; }
    public String getCompletedAt() { return completedAt; }
    public void setCompletedAt(String completedAt) { this.completedAt = completedAt; }

    /**
     * 判断任务是否已完成（终态）
     */
    public boolean isTerminal() {
        return "SUCCESS".equals(status) || "FAILED".equals(status)
                || "TIMEOUT".equals(status) || "CANCELLED".equals(status);
    }

    /**
     * 判断任务是否成功
     */
    public boolean isSuccess() {
        return "SUCCESS".equals(status);
    }
}

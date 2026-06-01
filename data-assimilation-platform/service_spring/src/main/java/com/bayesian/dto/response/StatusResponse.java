package com.bayesian.dto.response;

public class StatusResponse {
    private String status;
    private String version;
    private boolean gpuAvailable;
    private int activeJobs;

    public StatusResponse() {}

    public StatusResponse(String status, String version) {
        this.status = status;
        this.version = version;
    }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getVersion() { return version; }
    public void setVersion(String version) { this.version = version; }
    public boolean isGpuAvailable() { return gpuAvailable; }
    public void setGpuAvailable(boolean gpuAvailable) { this.gpuAvailable = gpuAvailable; }
    public int getActiveJobs() { return activeJobs; }
    public void setActiveJobs(int activeJobs) { this.activeJobs = activeJobs; }
}

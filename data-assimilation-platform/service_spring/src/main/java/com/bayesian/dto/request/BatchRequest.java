package com.bayesian.dto.request;

import java.util.List;

public class BatchRequest {
    private List<AssimilationRequest> jobs;
    private String option;

    public List<AssimilationRequest> getJobs() { return jobs; }
    public void setJobs(List<AssimilationRequest> jobs) { this.jobs = jobs; }
    public String getOption() { return option; }
    public void setOption(String option) { this.option = option; }
}

package com.uav.common.integration.dto;

import java.time.LocalDateTime;

/**
 * 飞行审批结果 - UTM系统返回
 */
public class FlightApproval {

    private String planId;
    private boolean approved;
    private LocalDateTime approvedAt;
    private LocalDateTime expirationTime;
    private String restrictions;
    private String rejectionReason;

    public FlightApproval() {}

    public FlightApproval(String planId, boolean approved, LocalDateTime approvedAt,
                          LocalDateTime expirationTime, String restrictions,
                          String rejectionReason) {
        this.planId = planId;
        this.approved = approved;
        this.approvedAt = approvedAt;
        this.expirationTime = expirationTime;
        this.restrictions = restrictions;
        this.rejectionReason = rejectionReason;
    }

    public String getPlanId() {
        return planId;
    }

    public void setPlanId(String planId) {
        this.planId = planId;
    }

    public boolean isApproved() {
        return approved;
    }

    public void setApproved(boolean approved) {
        this.approved = approved;
    }

    public LocalDateTime getApprovedAt() {
        return approvedAt;
    }

    public void setApprovedAt(LocalDateTime approvedAt) {
        this.approvedAt = approvedAt;
    }

    public LocalDateTime getExpirationTime() {
        return expirationTime;
    }

    public void setExpirationTime(LocalDateTime expirationTime) {
        this.expirationTime = expirationTime;
    }

    public String getRestrictions() {
        return restrictions;
    }

    public void setRestrictions(String restrictions) {
        this.restrictions = restrictions;
    }

    public String getRejectionReason() {
        return rejectionReason;
    }

    public void setRejectionReason(String rejectionReason) {
        this.rejectionReason = rejectionReason;
    }
}

package com.uav.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DemoLoginResponse {

    private Integer code;
    private String message;
    private DemoLoginData data;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class DemoLoginData {
        private String accessToken;
        private String refreshToken;
        private Long expiresIn;
        private String tokenType;
        private UserInfo user;
        private Boolean isDemo;
        private String demoInfo;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class UserInfo {
        private Long id;
        private String username;
        private String email;
        private String fullName;
    }
}

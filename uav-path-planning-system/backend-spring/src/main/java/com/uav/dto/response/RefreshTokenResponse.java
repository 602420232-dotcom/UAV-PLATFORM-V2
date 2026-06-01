package com.uav.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RefreshTokenResponse {

    private Integer code;
    private String message;
    private RefreshTokenData data;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RefreshTokenData {
        private String accessToken;
        private String refreshToken;
        private Long expiresIn;
    }
}

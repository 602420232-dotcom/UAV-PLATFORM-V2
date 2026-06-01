package com.uav.controller;

import com.uav.common.exception.BusinessException;
import com.uav.config.JwtProperties;
import com.uav.config.JwtUtil;
import com.uav.config.SecurityAuditConfig;
import com.uav.config.TokenType;
import com.uav.dto.request.LoginRequest;
import com.uav.dto.request.RefreshTokenRequest;
import com.uav.dto.response.DemoLoginResponse;
import com.uav.dto.response.LoginResponse;
import com.uav.dto.response.RefreshTokenResponse;
import com.uav.model.User;
import com.uav.repository.UserRepository;
import com.uav.service.CustomUserDetailsService;
import com.uav.service.TokenBlacklistService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.security.SecurityRequirements;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.DisabledException;
import org.springframework.security.authentication.LockedException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
@Tag(name = "Authentication", description = "用户认证管理 API，包括登录、登出、Token 刷新等")
public class AuthController {

    private final AuthenticationManager authenticationManager;
    private final CustomUserDetailsService userDetailsService;
    private final JwtUtil jwtUtil;
    private final SecurityAuditConfig securityAuditConfig;
    private final UserRepository userRepository;
    private final TokenBlacklistService tokenBlacklistService;
    private final JwtProperties jwtProperties;

    @Operation(
        summary = "用户登录",
        description = "使用用户名和密码进行身份认证，成功后返回 Access Token 和 Refresh Token。"
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "登录成功", content = @Content(schema = @Schema(implementation = LoginResponse.class))),
        @ApiResponse(responseCode = "401", description = "用户名或密码错误"),
        @ApiResponse(responseCode = "403", description = "账号已被禁用或锁定")
    })
    @SecurityRequirements
    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(
            @Valid @RequestBody LoginRequest request,
            HttpServletRequest httpRequest) {
        
        String clientIp = getClientIp(httpRequest);
        String username = request.getUsername();
        
        try {
            authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(username, request.getPassword())
            );

            User user = userRepository.findByUsername(username)
                    .orElseThrow(() -> new UsernameNotFoundException("用户不存在"));
            UserDetails userDetails = userDetailsService.loadUserByUsername(username);
            
            String accessToken = jwtUtil.generateAccessToken(userDetails, user.getId(), "default-tenant");
            String refreshToken = jwtUtil.generateRefreshToken(userDetails, user.getId());
            
            tokenBlacklistService.storeRefreshToken(refreshToken, httpRequest.getHeader("User-Agent"), clientIp);
            
            securityAuditConfig.logAuthenticationSuccess(username, httpRequest);
            
            LoginResponse.UserInfo userInfo = LoginResponse.UserInfo.builder()
                    .id(user.getId())
                    .username(user.getUsername())
                    .email(user.getEmail())
                    .fullName(user.getFullName())
                    .build();
            
            LoginResponse.LoginData loginData = LoginResponse.LoginData.builder()
                    .accessToken(accessToken)
                    .refreshToken(refreshToken)
                    .expiresIn(jwtProperties.getAccessExpiration())
                    .tokenType("Bearer")
                    .user(userInfo)
                    .build();
            
            LoginResponse response = LoginResponse.builder()
                    .code(200)
                    .message("登录成功")
                    .data(loginData)
                    .build();
            
            return ResponseEntity.ok(response);
            
        } catch (BadCredentialsException e) {
            securityAuditConfig.logAuthenticationFailure(username, "凭证错误", httpRequest);
            LoginResponse response = LoginResponse.builder()
                    .code(401)
                    .message("用户名或密码错误")
                    .build();
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(response);
        } catch (DisabledException e) {
            securityAuditConfig.logAuthenticationFailure(username, "账户已禁用", httpRequest);
            LoginResponse response = LoginResponse.builder()
                    .code(403)
                    .message("账户已被禁用")
                    .build();
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(response);
        } catch (LockedException e) {
            securityAuditConfig.logAuthenticationFailure(username, "账户已锁定", httpRequest);
            LoginResponse response = LoginResponse.builder()
                    .code(403)
                    .message("账户已被锁定")
                    .build();
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(response);
        } catch (AuthenticationException e) {
            securityAuditConfig.logAuthenticationFailure(username, "认证失败", httpRequest);
            throw new BusinessException("AUTH_ERROR", "登录失败，请稍后重试");
        }
    }

    @Operation(
        summary = "演示登录",
        description = "使用预置的演示账户快速登录，无需密码。演示账户功能受限，不可用于生产环境。"
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "演示登录成功"),
        @ApiResponse(responseCode = "500", description = "演示登录失败")
    })
    @SecurityRequirements
    @PostMapping("/demo-login")
    public ResponseEntity<DemoLoginResponse> demoLogin(
            HttpServletRequest httpRequest) {
        
        String clientIp = getClientIp(httpRequest);
        String demoUsername = "demo_user";
        
        try {
            User user = userRepository.findByUsername(demoUsername)
                    .orElseGet(() -> {
                        User demoUser = new User();
                        demoUser.setUsername(demoUsername);
                        demoUser.setEmail("demo@example.com");
                        demoUser.setFullName("演示用户");
                        demoUser.setPassword("");
                        demoUser.setEnabled(true);
                        demoUser.setAccountNonExpired(true);
                        demoUser.setAccountNonLocked(true);
                        demoUser.setCredentialsNonExpired(true);
                        return userRepository.save(demoUser);
                    });
            
            UserDetails userDetails = userDetailsService.loadUserByUsername(demoUsername);
            String accessToken = jwtUtil.generateAccessToken(userDetails, user.getId(), "default-tenant");
            String refreshToken = jwtUtil.generateRefreshToken(userDetails, user.getId());
            
            tokenBlacklistService.storeRefreshToken(refreshToken, httpRequest.getHeader("User-Agent"), clientIp);
            
            log.info("Demo login successful for user: {}, IP: {}", demoUsername, clientIp);
            
            DemoLoginResponse.UserInfo userInfo = DemoLoginResponse.UserInfo.builder()
                    .id(user.getId())
                    .username(user.getUsername())
                    .email(user.getEmail())
                    .fullName(user.getFullName())
                    .build();
            
            DemoLoginResponse.DemoLoginData demoLoginData = DemoLoginResponse.DemoLoginData.builder()
                    .accessToken(accessToken)
                    .refreshToken(refreshToken)
                    .expiresIn(jwtProperties.getAccessExpiration())
                    .tokenType("Bearer")
                    .user(userInfo)
                    .isDemo(true)
                    .demoInfo("这是演示账户，功能有限")
                    .build();
            
            DemoLoginResponse response = DemoLoginResponse.builder()
                    .code(200)
                    .message("演示登录成功")
                    .data(demoLoginData)
                    .build();
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            log.error("Demo login failed", e);
            DemoLoginResponse response = DemoLoginResponse.builder()
                    .code(500)
                    .message("演示登录失败")
                    .build();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }

    @Operation(
        summary = "刷新 Token",
        description = "使用 Refresh Token 获取新的 Access Token。Refresh Token 使用一次后即失效。"
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "Token 刷新成功", content = @Content(schema = @Schema(implementation = RefreshTokenResponse.class))),
        @ApiResponse(responseCode = "401", description = "Refresh Token 无效或已过期")
    })
    @SecurityRequirements
    @PostMapping("/refresh")
    public ResponseEntity<RefreshTokenResponse> refresh(
            @Valid @RequestBody RefreshTokenRequest request,
            HttpServletRequest httpRequest) {
        
        String refreshToken = request.getRefreshToken();
        
        try {
            String username = jwtUtil.extractUsername(refreshToken, TokenType.REFRESH);
            User user = userRepository.findByUsername(username)
                    .orElseThrow(() -> new UsernameNotFoundException("用户不存在"));
            UserDetails userDetails = userDetailsService.loadUserByUsername(username);
            
            if (!jwtUtil.validateRefreshToken(refreshToken, userDetails)) {
                RefreshTokenResponse response = RefreshTokenResponse.builder()
                        .code(401)
                        .message("令牌无效或已过期")
                        .build();
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(response);
            }
            
            if (!tokenBlacklistService.isRefreshTokenValid(refreshToken)) {
                RefreshTokenResponse response = RefreshTokenResponse.builder()
                        .code(401)
                        .message("令牌已失效")
                        .build();
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(response);
            }
            
            tokenBlacklistService.markRefreshTokenAsUsed(refreshToken);
            
            String newAccessToken = jwtUtil.generateAccessToken(userDetails, user.getId(), "default-tenant");
            String newRefreshToken = jwtUtil.generateRefreshToken(userDetails, user.getId());
            
            tokenBlacklistService.storeRefreshToken(
                    newRefreshToken, 
                    httpRequest.getHeader("User-Agent"), 
                    getClientIp(httpRequest)
            );
            
            RefreshTokenResponse.RefreshTokenData refreshTokenData = RefreshTokenResponse.RefreshTokenData.builder()
                    .accessToken(newAccessToken)
                    .refreshToken(newRefreshToken)
                    .expiresIn(jwtProperties.getAccessExpiration())
                    .build();
            
            RefreshTokenResponse response = RefreshTokenResponse.builder()
                    .code(200)
                    .message("令牌刷新成功")
                    .data(refreshTokenData)
                    .build();
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            log.warn("Token refresh failed: {}", e.getMessage());
            RefreshTokenResponse response = RefreshTokenResponse.builder()
                    .code(401)
                    .message("令牌无效")
                    .build();
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(response);
        }
    }

    @Operation(
        summary = "用户登出",
        description = "将当前 Token 加入黑名单，使其立即失效。"
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "登出成功"),
        @ApiResponse(responseCode = "401", description = "未提供有效的 Token")
    })
    @PostMapping("/logout")
    public ResponseEntity<Map<String, Object>> logout(
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String authHeader,
            HttpServletRequest httpRequest) {

        String username = securityAuditConfig.getCurrentUsername();

        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String accessToken = authHeader.substring(7);
            try {
                tokenBlacklistService.addToBlacklist(accessToken, TokenType.ACCESS, "用户登出");
            } catch (Exception e) {
                log.warn("Failed to blacklist access token during logout", e);
            }
        }
        
        securityAuditConfig.logUserActivity(username, "登出", "用户主动登出");
        
        return ResponseEntity.ok(Map.of(
                "code", 200,
                "message", "登出成功"
        ));
    }

    @Operation(
        summary = "撤销 Token",
        description = "主动撤销指定的 Refresh Token，使其无法继续刷新。用于安全场景（如密码修改、设备移除）。"
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "Token 已撤销"),
        @ApiResponse(responseCode = "400", description = "请求参数无效"),
        @ApiResponse(responseCode = "401", description = "未授权")
    })
    @PostMapping("/revoke")
    public ResponseEntity<Map<String, Object>> revoke(
            @RequestHeader(HttpHeaders.AUTHORIZATION) String authHeader,
            @RequestBody Map<String, String> request,
            HttpServletRequest httpRequest) {
        
        String username = securityAuditConfig.getCurrentUsername();
        String tokenToRevoke = request.get("token");
        
        if (tokenToRevoke == null || tokenToRevoke.isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of(
                    "code", 400,
                    "message", "需要提供要撤销的令牌"
            ));
        }
        
        try {
            tokenBlacklistService.addToBlacklist(tokenToRevoke, TokenType.ACCESS, "用户主动撤销");
            log.info("Token revoked by user: {}", username);
            
            return ResponseEntity.ok(Map.of(
                    "code", 200,
                    "message", "令牌已撤销"
            ));
            
        } catch (Exception e) {
            log.error("Failed to revoke token", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of(
                    "code", 500,
                    "message", "撤销令牌失败"
            ));
        }
    }

    @Operation(
        summary = "获取当前用户信息",
        description = "获取当前登录用户的详细信息，包括角色、权限等。需要有效的 Access Token。"
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "成功获取用户信息"),
        @ApiResponse(responseCode = "401", description = "未提供有效的 Token")
    })
    @GetMapping("/me")
    public ResponseEntity<Map<String, Object>> getCurrentUser(
            @AuthenticationPrincipal UserDetails userDetails) {
        
        if (userDetails == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(Map.of(
                    "code", 401,
                    "message", "未认证"
            ));
        }
        
        User user = userRepository.findByUsername(userDetails.getUsername())
                .orElseThrow(() -> new UsernameNotFoundException("用户不存在"));
        
        Map<String, Object> userData = Map.of(
                "id", user.getId(),
                "username", user.getUsername(),
                "email", user.getEmail(),
                "fullName", user.getFullName(),
                "enabled", user.isEnabled()
        );
        
        return ResponseEntity.ok(Map.of(
                "code", 200,
                "message", "获取成功",
                "data", userData
        ));
    }

    private String getClientIp(HttpServletRequest request) {
        String ip = request.getHeader("X-Forwarded-For");
        if (ip == null || ip.isEmpty() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getHeader("X-Real-IP");
        }
        if (ip == null || ip.isEmpty() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getRemoteAddr();
        }
        if (ip != null && ip.contains(",")) {
            ip = ip.split(",")[0].trim();
        }
        return ip;
    }
}

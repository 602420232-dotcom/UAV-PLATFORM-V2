package com.uav.controller;

import com.uav.common.exception.BusinessException;
import com.uav.config.JwtUtil;
import com.uav.config.SecurityAuditConfig;
import com.uav.model.Role;
import com.uav.model.User;
import com.uav.repository.RoleRepository;
import com.uav.repository.UserRepository;
import com.uav.service.CustomUserDetailsService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.DisabledException;
import org.springframework.security.authentication.LockedException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import jakarta.servlet.http.HttpServletRequest;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    private final AuthenticationManager authenticationManager;
    private final CustomUserDetailsService userDetailsService;
    private final JwtUtil jwtUtil;
    private final PasswordEncoder passwordEncoder;
    private final UserRepository userRepository;
    private final RoleRepository roleRepository;

    public AuthController(AuthenticationManager authenticationManager,
                          CustomUserDetailsService userDetailsService,
                          JwtUtil jwtUtil,
                          PasswordEncoder passwordEncoder,
                          UserRepository userRepository,
                          RoleRepository roleRepository) {
        this.authenticationManager = authenticationManager;
        this.userDetailsService = userDetailsService;
        this.jwtUtil = jwtUtil;
        this.passwordEncoder = passwordEncoder;
        this.userRepository = userRepository;
        this.roleRepository = roleRepository;
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody Map<String, String> request, HttpServletRequest httpRequest) {
        String username = request.get("username");
        String password = request.get("password");

        if (username == null || username.trim().isEmpty()) {
            throw new BusinessException("VALIDATION_ERROR", "用户名不能为空");
        }
        if (password == null || password.trim().isEmpty()) {
            throw new BusinessException("VALIDATION_ERROR", "密码不能为空");
        }

        try {
            authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(username, password)
            );

            UserDetails userDetails = userDetailsService.loadUserByUsername(username);
            String token = jwtUtil.generateToken(userDetails);

            SecurityAuditConfig.logAuthenticationSuccess(username, httpRequest);

            Map<String, Object> response = new HashMap<>();
            response.put("token", token);
            response.put("user", userDetails);

            return ResponseEntity.ok(response);
        } catch (BadCredentialsException e) {
            SecurityAuditConfig.logAuthenticationFailure(username, "凭证错误", httpRequest);
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body("用户名或密码错误");
        } catch (DisabledException e) {
            SecurityAuditConfig.logAuthenticationFailure(username, "账户已禁用", httpRequest);
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body("账户已被禁用");
        } catch (LockedException e) {
            SecurityAuditConfig.logAuthenticationFailure(username, "账户已锁定", httpRequest);
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body("账户已被锁定");
        } catch (UsernameNotFoundException e) {
            SecurityAuditConfig.logAuthenticationFailure(username, "凭证错误", httpRequest);
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body("用户名或密码错误");
        } catch (AuthenticationException e) {
            SecurityAuditConfig.logAuthenticationFailure(username, "认证失败", httpRequest);
            throw new BusinessException("AUTH_ERROR", "登录失败，请稍后重试");
        }
    }

    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody Map<String, String> request, HttpServletRequest httpRequest) {
        String username = request.get("username");
        String password = request.get("password");
        String email = request.get("email");
        String fullName = request.get("fullName");

        if (username == null || username.trim().isEmpty()) {
            throw new BusinessException("VALIDATION_ERROR", "用户名不能为空");
        }
        if (password == null || password.length() < 6) {
            throw new BusinessException("VALIDATION_ERROR", "密码长度不能少于6位");
        }

        if (userRepository.existsByUsername(username)) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("用户名已存在");
        }

        try {
            User user = new User();
            user.setUsername(username);
            user.setPassword(passwordEncoder.encode(password));
            user.setEmail(email);
            user.setFullName(fullName);
            user.setEnabled(true);
            user.setAccountNonExpired(true);
            user.setAccountNonLocked(true);
            user.setCredentialsNonExpired(true);

            Role userRole = roleRepository.findByName("USER")
                .orElseThrow(() -> new BusinessException("ROLE_NOT_FOUND", "默认角色不存在"));
            user.setRoles(Set.of(userRole));

            userRepository.save(user);

            UserDetails userDetails = userDetailsService.loadUserByUsername(username);
            String token = jwtUtil.generateToken(userDetails);

            SecurityAuditConfig.logAuthenticationSuccess(username, httpRequest);

            Map<String, Object> response = new HashMap<>();
            response.put("token", token);

            Map<String, Object> userMap = new HashMap<>();
            userMap.put("id", user.getId());
            userMap.put("username", user.getUsername());
            userMap.put("email", user.getEmail());
            userMap.put("fullName", user.getFullName());
            response.put("user", userMap);

            return ResponseEntity.status(HttpStatus.CREATED).body(response);
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            throw new BusinessException("REGISTRATION_ERROR", "注册失败，请稍后重试");
        }
    }

    @PostMapping("/refresh")
    public ResponseEntity<?> refreshToken(@RequestBody Map<String, String> request, HttpServletRequest httpRequest) {
        String refreshToken = request.get("refreshToken");

        if (refreshToken == null || refreshToken.trim().isEmpty()) {
            throw new BusinessException("VALIDATION_ERROR", "刷新令牌不能为空");
        }

        try {
            String username = jwtUtil.extractUsername(refreshToken);
            UserDetails userDetails = userDetailsService.loadUserByUsername(username);

            if (!jwtUtil.validateToken(refreshToken, userDetails)) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body("令牌无效或已过期");
            }

            String newToken = jwtUtil.generateToken(userDetails);

            Map<String, Object> response = new HashMap<>();
            response.put("token", newToken);

            return ResponseEntity.ok(response);
        } catch (UsernameNotFoundException e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body("令牌无效或已过期");
        } catch (Exception e) {
            throw new BusinessException("TOKEN_REFRESH_ERROR", "刷新令牌失败");
        }
    }

    @PostMapping("/logout")
    public ResponseEntity<?> logout(HttpServletRequest httpRequest) {
        String username = SecurityAuditConfig.getCurrentUsername();

        SecurityAuditConfig.logUserActivity(username, "登出", "用户主动登出");

        return ResponseEntity.ok("登出成功");
    }
}

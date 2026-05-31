package com.uav.common.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.lang.NonNull;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.filter.OncePerRequestFilter;

import jakarta.annotation.PostConstruct;
import javax.crypto.SecretKey;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    @Value("${jwt.secret}")
    private String jwtSecret;

    @Value("${jwt.enabled:true}")
    private boolean jwtEnabled;

    @PostConstruct
    public void validateConfig() {
        String profile = getActiveProfile();
        boolean isProduction = "prod".equals(profile) || "production".equals(profile);

        if (!jwtEnabled && isProduction) {
            throw new IllegalStateException(
                "JWT 认证在生产环境不可禁用。请设置 jwt.enabled=true 并配置 jwt.secret");
        }

        if (jwtEnabled) {
            if (jwtSecret == null || jwtSecret.isEmpty()) {
                throw new IllegalStateException(
                    "JWT secret is NOT configured. Set JWT_SECRET environment variable or jwt.secret in application.yml");
            }
            if (jwtSecret.length() < 32) {
                throw new IllegalStateException(
                    "JWT secret is too short (minimum 32 chars required, got " + jwtSecret.length() + ")");
            }
        }
    }

    private String getActiveProfile() {
        return System.getenv("SPRING_PROFILES_ACTIVE");
    }

    @Override
    protected void doFilterInternal(@NonNull HttpServletRequest request,
                                    @NonNull HttpServletResponse response,
                                    @NonNull FilterChain filterChain) throws ServletException, IOException {
        if (!jwtEnabled || isPublicPath(request.getRequestURI())) {
            filterChain.doFilter(request, response);
            return;
        }

        String header = request.getHeader("Authorization");
        if (header == null || !header.startsWith("Bearer ")) {
            response.setStatus(401);
            response.getWriter().write("{\"code\":401,\"message\":\"Missing or invalid Authorization header\"}");
            return;
        }

        try {
            SecretKey key = Keys.hmacShaKeyFor(jwtSecret.getBytes(StandardCharsets.UTF_8));
            Claims claims = Jwts.parser().verifyWith(key).build()
                    .parseSignedClaims(header.substring(7)).getPayload();

            String username = claims.getSubject();
            List<?> rawRoles = claims.get("roles", List.class);
            List<String> roles = rawRoles.stream()
                    .filter(String.class::isInstance)
                    .map(String.class::cast)
                    .collect(Collectors.toList());
            List<SimpleGrantedAuthority> authorities = roles.stream()
                    .map(SimpleGrantedAuthority::new).collect(Collectors.toList());

            UsernamePasswordAuthenticationToken auth =
                    new UsernamePasswordAuthenticationToken(username, null, authorities);
            SecurityContextHolder.getContext().setAuthentication(auth);
        } catch (Exception e) {
            log.warn("JWT verification failed: {}", e.getMessage());
            response.setStatus(401);
            response.getWriter().write("{\"code\":401,\"message\":\"Invalid token\"}");
            return;
        }
        filterChain.doFilter(request, response);
    }

    private boolean isPublicPath(String uri) {
        return uri.equals("/actuator/health") || uri.equals("/actuator/info")
                || uri.startsWith("/api/public/") || uri.startsWith("/api/auth/")
                || uri.startsWith("/api/v1/auth/");
    }
}

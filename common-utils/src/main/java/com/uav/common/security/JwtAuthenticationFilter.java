package com.uav.common.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import jakarta.annotation.PostConstruct;
import javax.crypto.SecretKey;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.stream.Collectors;

@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private static final Logger log = LoggerFactory.getLogger(JwtAuthenticationFilter.class);

    @Value("${uav.jwt.secret}")
    private String jwtSecret;

    @Value("${uav.jwt.enabled:true}")
    private boolean jwtEnabled;

    @PostConstruct
    public void validateConfig() {
        if (jwtEnabled) {
            if (jwtSecret == null || jwtSecret.isEmpty()) {
                // 生产环境必须抛出异常
                String message = "JWT secret is NOT configured. Set uav.jwt.secret in application.yml";
                if (isProductionEnvironment()) {
                    throw new IllegalStateException(message);
                } else {
                    log.error(message);
                }
            } else if (jwtSecret.length() < 32) {
                String message = "JWT secret is too short (minimum 32 chars required)";
                if (isProductionEnvironment()) {
                    throw new IllegalStateException(message);
                } else {
                    log.warn(message);
                }
            }
        }
    }
    
    private boolean isProductionEnvironment() {
        String profile = System.getenv("SPRING_PROFILES_ACTIVE");
        return "prod".equals(profile) || "production".equals(profile);
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        if (!jwtEnabled || isPublicPath(request.getRequestURI())) {
            filterChain.doFilter(request, response);
            return;
        }

        String header = request.getHeader("Authorization");
        if (header == null || !header.startsWith("Bearer ")) {
            response.setStatus(401);
            response.getWriter().write("{\"success\":false,\"error\":\"Missing or invalid Authorization header\"}");
            return;
        }

        try {
            SecretKey key = Keys.hmacShaKeyFor(jwtSecret.getBytes(StandardCharsets.UTF_8));
            Claims claims = Jwts.parserBuilder().setSigningKey(key).build()
                    .parseClaimsJws(header.substring(7)).getBody();

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
            response.getWriter().write("{\"success\":false,\"error\":\"Invalid token\"}");
            return;
        }
        filterChain.doFilter(request, response);
    }

    private boolean isPublicPath(String uri) {
        return uri.equals("/actuator/health") || uri.equals("/actuator/info")
                || uri.startsWith("/api/public/") || uri.startsWith("/api/auth/");
    }
}

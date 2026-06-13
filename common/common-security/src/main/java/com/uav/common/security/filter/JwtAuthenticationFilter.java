package com.uav.common.security.filter;

import com.uav.common.security.service.JwtService;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpHeaders;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Collections;
import java.util.List;

/**
 * JWT 认证过滤器
 * <p>
 * 从请求头中提取 Bearer Token，解析并验证 JWT，将认证信息写入 Spring Security 上下文。
 * <p>
 * 过滤器顺序：在 TenantContextFilter、HmacAuthenticationFilter 之后执行
 */
@Slf4j
@Component
@Order(200)
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    public static final String BEARER_PREFIX = "Bearer ";

    private final JwtService jwtService;

    public JwtAuthenticationFilter(JwtService jwtService) {
        this.jwtService = jwtService;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {

        final String authHeader = request.getHeader(HttpHeaders.AUTHORIZATION);

        // 无 Authorization 头或不是 Bearer 类型，直接放行
        if (authHeader == null || !authHeader.startsWith(BEARER_PREFIX)) {
            filterChain.doFilter(request, response);
            return;
        }

        final String jwt = authHeader.substring(BEARER_PREFIX.length());

        try {
            if (!jwtService.validateToken(jwt)) {
                log.warn("JWT 验证失败 - uri: {}", request.getRequestURI());
                filterChain.doFilter(request, response);
                return;
            }

            String username = jwtService.extractUsername(jwt);
            if (username == null || username.isBlank()) {
                filterChain.doFilter(request, response);
                return;
            }

            // 如果当前上下文未认证，则设置认证信息
            if (SecurityContextHolder.getContext().getAuthentication() == null) {
                List<SimpleGrantedAuthority> authorities = Collections.singletonList(
                        new SimpleGrantedAuthority("ROLE_USER")
                );

                UserDetails userDetails = User.builder()
                        .username(username)
                        .password("")
                        .authorities(authorities)
                        .build();

                UsernamePasswordAuthenticationToken authToken =
                        new UsernamePasswordAuthenticationToken(
                                userDetails,
                                null,
                                userDetails.getAuthorities()
                        );
                authToken.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                SecurityContextHolder.getContext().setAuthentication(authToken);

                log.debug("JWT 认证成功 - user: {}, uri: {}", username, request.getRequestURI());
            }
        } catch (Exception e) {
            log.error("JWT 认证过程中发生异常", e);
            SecurityContextHolder.clearContext();
        }

        filterChain.doFilter(request, response);
    }
}

package com.uav.common.security;

import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.security.web.csrf.CsrfToken;
import org.springframework.security.web.csrf.CsrfTokenRepository;
import org.springframework.security.web.csrf.DefaultCsrfToken;
import org.springframework.util.StringUtils;
import org.springframework.web.util.WebUtils;

import java.util.UUID;

public class CookieCsrfTokenRepository implements CsrfTokenRepository {

    private static final Logger log = LoggerFactory.getLogger(CookieCsrfTokenRepository.class);

    static final String DEFAULT_CSRF_COOKIE_NAME = "XSRF-TOKEN";
    static final String DEFAULT_CSRF_HEADER_NAME = "X-XSRF-TOKEN";
    static final String DEFAULT_CSRF_PARAMETER_NAME = "_csrf";

    private String cookieName = DEFAULT_CSRF_COOKIE_NAME;
    private String headerName = DEFAULT_CSRF_HEADER_NAME;
    private String parameterName = DEFAULT_CSRF_PARAMETER_NAME;
    private boolean cookieHttpOnly = false;
    private String cookiePath = "/";
    private String cookieDomain;
    private Boolean secure;
    private int cookieMaxAge = -1;

    public void setCookieName(String cookieName) {
        this.cookieName = cookieName;
    }

    public void setHeaderName(String headerName) {
        this.headerName = headerName;
    }

    public void setParameterName(String parameterName) {
        this.parameterName = parameterName;
    }

    public void setCookieHttpOnly(boolean cookieHttpOnly) {
        this.cookieHttpOnly = cookieHttpOnly;
    }

    public void setCookiePath(String cookiePath) {
        this.cookiePath = cookiePath;
    }

    public void setCookieDomain(String cookieDomain) {
        this.cookieDomain = cookieDomain;
    }

    public void setSecure(Boolean secure) {
        this.secure = secure;
    }

    public void setCookieMaxAge(int cookieMaxAge) {
        this.cookieMaxAge = cookieMaxAge;
    }

    @Override
    public CsrfToken generateToken(HttpServletRequest request) {
        return new DefaultCsrfToken(this.headerName, this.parameterName, createNewToken());
    }

    @Override
    public void saveToken(CsrfToken token, HttpServletRequest request, HttpServletResponse response) {
        String tokenValue = token != null ? token.getToken() : "";
        Cookie cookie = new Cookie(this.cookieName, tokenValue);
        cookie.setSecure(this.secure != null ? this.secure : request.isSecure());
        cookie.setPath(StringUtils.hasLength(this.cookiePath) ? this.cookiePath : "/");
        cookie.setHttpOnly(this.cookieHttpOnly);
        if (this.cookieDomain != null) {
            cookie.setDomain(this.cookieDomain);
        }
        cookie.setMaxAge(token != null ? this.cookieMaxAge : 0);
        cookie.setAttribute("SameSite", "Lax");
        response.addCookie(cookie);

        if (token != null) {
            response.setHeader(this.headerName, token.getToken());
        }
    }

    @Override
    public CsrfToken loadToken(HttpServletRequest request) {
        Cookie cookie = WebUtils.getCookie(request, this.cookieName);
        if (cookie == null) {
            return null;
        }
        String token = cookie.getValue();
        if (!StringUtils.hasLength(token)) {
            return null;
        }
        return new DefaultCsrfToken(this.headerName, this.parameterName, token);
    }

    private String createNewToken() {
        return UUID.randomUUID().toString();
    }

    public static CookieCsrfTokenRepository withDefaults() {
        return new CookieCsrfTokenRepository();
    }

    public static CookieCsrfTokenRepository withHttpOnly(boolean httpOnly) {
        CookieCsrfTokenRepository repository = new CookieCsrfTokenRepository();
        repository.setCookieHttpOnly(httpOnly);
        return repository;
    }

    public static class CsrfOriginValidator {

        private final String allowedOrigin;

        public CsrfOriginValidator(String allowedOrigin) {
            this.allowedOrigin = allowedOrigin;
        }

        public boolean isValid(HttpServletRequest request) {
            String origin = request.getHeader(HttpHeaders.ORIGIN);
            if (origin == null) {
                String referer = request.getHeader(HttpHeaders.REFERER);
                if (referer == null) {
                    return request.getMethod().equals("GET") || request.getMethod().equals("HEAD");
                }
                return referer.startsWith(allowedOrigin);
            }
            boolean valid = origin.equals(allowedOrigin);
            if (!valid) {
                log.warn("CSRF Origin验证失败: expected={}, actual={}", allowedOrigin, origin);
            }
            return valid;
        }
    }
}

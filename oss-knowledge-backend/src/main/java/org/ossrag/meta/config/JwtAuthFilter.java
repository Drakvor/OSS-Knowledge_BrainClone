package org.ossrag.meta.config;

import java.io.IOException;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.ossrag.meta.service.JwtService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.util.ArrayList;

/** JWT 인증 필터 */
@Component
public class JwtAuthFilter extends OncePerRequestFilter {

    private static final Logger logger = LoggerFactory.getLogger(JwtAuthFilter.class);
    private final JwtService jwtService;

    public JwtAuthFilter(JwtService jwtService) {
        this.jwtService = jwtService;
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String uri = request.getRequestURI();
        // Allow health checks, auth endpoints, docs, and internal chat session endpoints
        if ("/healthz".equals(uri) || "/health".equals(uri) || uri.startsWith("/auth/") || uri.startsWith("/api-docs")
                || uri.startsWith("/swagger-ui") || "/documents/add-after-embedding".equals(uri)) {
            return true;
        }
        // Allow all /chat/sessions endpoints for internal service calls (including /chat/sessions itself)
        if (uri.startsWith("/chat/sessions")) {
            return true;
        }
        return false;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        String auth = request.getHeader("Authorization");
        
        if (auth == null || !auth.startsWith("Bearer ")) {
            logger.warn("JWT authentication failed: Missing or invalid Authorization header for URI: {}", request.getRequestURI());
            writeUnauthorized(response, "UNAUTHORIZED", "Missing or invalid Authorization header");
            return;
        }
        
        String token = auth.substring(7);
        if (!jwtService.validate(token)) {
            logger.warn("JWT authentication failed: Invalid or expired token for URI: {}", request.getRequestURI());
            writeUnauthorized(response, "UNAUTHORIZED", "Invalid or expired token");
            return;
        }
        
        // 토큰에서 사용자 정보 추출하여 SecurityContext 설정
        String username = jwtService.extractSubject(token).orElse(null);
        if (username != null) {
            UserDetails userDetails = User.builder()
                    .username(username)
                    .password("")
                    .authorities(new ArrayList<>())
                    .build();
            
            UsernamePasswordAuthenticationToken authentication = 
                    new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities());
            
            SecurityContextHolder.getContext().setAuthentication(authentication);
            logger.debug("JWT authentication successful for user: {} accessing URI: {}", username, request.getRequestURI());
        }
        
        chain.doFilter(request, response);
    }

    private void writeUnauthorized(HttpServletResponse response, String code, String message) throws IOException {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType("application/json;charset=UTF-8");
        String traceId = org.slf4j.MDC.get("requestId");
        String json = String.format("{\"code\":\"%s\",\"message\":\"%s\",\"traceId\":%s}",
                escape(code), escape(message), traceId == null ? "null" : ("\"" + escape(traceId) + "\""));
        response.getWriter().write(json);
    }

    private String escape(String s) {
        return s.replace("\\", "\\\\").replace("\"", "\\\"");
    }
}

package org.ossrag.meta.config;

import java.io.IOException;
import java.util.UUID;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.MDC;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/** 요청/세션 ID 로깅 */
@Component
public class RequestContextFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        try {
            String requestId = request.getHeader("X-Request-Id");
            if (requestId == null || requestId.isBlank()) {
                requestId = UUID.randomUUID().toString();
            }
            MDC.put("requestId", requestId);
            var session = request.getSession(false);
            if (session != null) {
                MDC.put("sessionId", session.getId());
            }
            chain.doFilter(request, response);
        } finally {
            MDC.remove("requestId");
            MDC.remove("sessionId");
        }
    }
}

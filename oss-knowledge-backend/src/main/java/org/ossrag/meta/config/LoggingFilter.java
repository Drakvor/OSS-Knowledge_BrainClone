package org.ossrag.meta.config;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * 요청/응답 요약 로그 필터.
 * - Health 체크는 성공 시 TRACE, 실패 시 WARN/ERROR
 * - 일반 요청은 성공 시 DEBUG, 실패 시 WARN/ERROR
 * - 불필요한 본문 로깅/중복 MDC 설정 제거
 */
@Component
public class LoggingFilter extends OncePerRequestFilter {
    private static final Logger log = LoggerFactory.getLogger(LoggingFilter.class);

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        long start = System.currentTimeMillis();
        try {
            filterChain.doFilter(request, response);
        } finally {
            long took = System.currentTimeMillis() - start;
            writeSummaryLog(request, response, took);
        }
    }

    private void writeSummaryLog(HttpServletRequest req, HttpServletResponse res, long tookMs) {
        String method = req.getMethod();
        String uri = req.getRequestURI();
        int status = res.getStatus();
        boolean isHealth = "/healthz".equals(uri) || "/health".equals(uri);
        String msg = String.format("%s %s -> %d (%dms)", method, uri, status, tookMs);

        if (status >= 500) {
            // 서버 오류는 항상 에러
            log.error(msg);
        } else if (status >= 400) {
            // 클라이언트 오류는 경고
            log.warn(msg);
        } else {
            // 정상 요청
            if (isHealth) {
                // 평소에는 보이지 않도록 TRACE로 하향
                log.trace(msg);
            } else {
                // 일반 요청은 디버그로 하향
                log.debug(msg);
            }
        }
    }
}

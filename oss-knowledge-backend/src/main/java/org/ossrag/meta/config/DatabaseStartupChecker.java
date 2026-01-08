package org.ossrag.meta.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;

/**
 * 애플리케이션 기동 시 DB 연결 확인 및 로그 출력.
 */
@Component
public class DatabaseStartupChecker implements ApplicationRunner {
    private static final Logger log = LoggerFactory.getLogger(DatabaseStartupChecker.class);
    private final DataSource dataSource;

    public DatabaseStartupChecker(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    @Override
    public void run(ApplicationArguments args) {
        try (Connection conn = dataSource.getConnection();
             Statement st = conn.createStatement();
             ResultSet rs = st.executeQuery("SELECT 1")) {
            if (rs.next()) {
                String url = safe(conn.getMetaData().getURL());
                String user = safe(conn.getMetaData().getUserName());
                log.info("Database connection OK (url={}, user={})", url, user);
            } else {
                log.warn("Database connection verified but validation query returned no rows");
            }
        } catch (Exception e) {
            log.error("Database connection FAILED", e);
        }
    }

    private String safe(String s) {
        return s == null ? "" : s;
    }
}


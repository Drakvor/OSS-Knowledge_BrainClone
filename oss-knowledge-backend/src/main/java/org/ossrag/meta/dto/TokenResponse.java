package org.ossrag.meta.dto;

import java.time.Instant;

/** 토큰 응답 */
public class TokenResponse {
    private String accessToken;
    private String refreshToken;
    private Instant expiresAt;
    private Instant refreshExpiresAt;

    public TokenResponse(String accessToken, String refreshToken, Instant expiresAt, Instant refreshExpiresAt) {
        this.accessToken = accessToken;
        this.refreshToken = refreshToken;
        this.expiresAt = expiresAt;
        this.refreshExpiresAt = refreshExpiresAt;
    }

    public String getAccessToken() {
        return accessToken;
    }

    public String getRefreshToken() {
        return refreshToken;
    }

    public Instant getExpiresAt() {
        return expiresAt;
    }

    public Instant getRefreshExpiresAt() {
        return refreshExpiresAt;
    }
}

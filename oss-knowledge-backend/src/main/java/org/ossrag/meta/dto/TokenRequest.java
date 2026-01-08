package org.ossrag.meta.dto;

import jakarta.validation.constraints.NotBlank;

/** 토큰 발급 요청 */
public class TokenRequest {
    @NotBlank
    private String userId;

    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }
}

package org.ossrag.meta.dto;

import jakarta.validation.constraints.NotBlank;

/**
 * 대화 생성/수정 요청.
 */
public class ConversationRequest {
    @NotBlank
    private String sessionId;
    @NotBlank
    private String title;

    public String getSessionId() {
        return sessionId;
    }

    public void setSessionId(String sessionId) {
        this.sessionId = sessionId;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }
}


package org.ossrag.meta.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;
import java.util.Map;

/**
 * 채팅 세션 응답 DTO
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class ChatSessionResponse {
    private String id;
    private Long userId;
    private String title;
    private String llmModel;
    private String status;
    private Map<String, Object> metadata;
    
    // 메시지 카운트
    private Integer assistantMessageCount;
    private Integer totalMessageCount;
    
    // 토큰 관리
    private Long totalTokensUsed;
    
    // 대화 요약
    private String contextSummary;
    private Instant summaryUpdatedAt;
    private Integer summaryVersion;
    
    private Instant createdAt;
    private Instant updatedAt;
}

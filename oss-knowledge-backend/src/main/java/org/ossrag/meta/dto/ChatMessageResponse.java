package org.ossrag.meta.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;
import java.util.Map;

/**
 * 채팅 메시지 응답 DTO
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class ChatMessageResponse {
    private String id;
    private String sessionId;
    private Integer turnIndex; // 세션 내 메시지 순서 번호
    private String messageType; // 'user', 'assistant', 'system'
    private String content;
    private Integer tokenCount; // 토큰 수
    private Long departmentId; // 메시지별 부서 컨텍스트
    private Map<String, Object> metadata;
    private String parentMessageId;
    private String status; // 'pending', 'completed', 'failed'
    private Instant createdAt;
    private Instant updatedAt;
}

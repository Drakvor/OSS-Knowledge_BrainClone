package org.ossrag.meta.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Map;

/**
 * 채팅 메시지 요청 DTO
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class ChatMessageRequest {
    private String sessionId;
    private String messageType; // 'user', 'assistant', 'system'
    private String content;
    private Integer tokenCount; // 토큰 수 (다른 백엔드에서 계산해서 전달)
    private Long departmentId; // 메시지별 부서 컨텍스트
    private Map<String, Object> metadata;
    private String parentMessageId;
    private String status; // 'pending', 'completed', 'failed'
}

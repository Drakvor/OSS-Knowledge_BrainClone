package org.ossrag.meta.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Map;

/**
 * 채팅 메시지 피드백 요청 DTO
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class ChatMessageFeedbackRequest {
    private String userMessageId; // 사용자 질문 메시지 ID
    private Long userId;
    private Integer rating; // 1-5점 별점
    private String comment;
    private String feedbackType; // 'general', 'accuracy', 'helpfulness', 'clarity'
    private Boolean isAnonymous;
    private Map<String, Object> metadata;
}

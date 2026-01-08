package org.ossrag.meta.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Map;

/**
 * 채팅 세션 요청 DTO
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class ChatSessionRequest {
    private Long userId;
    private String title;
    private Long departmentId;
    private String llmModel;
    private String status;
    private Map<String, Object> metadata;
}

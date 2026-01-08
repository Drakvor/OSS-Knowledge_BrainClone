package org.ossrag.meta.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 채팅 제목 생성 요청 DTO
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class ChatTitleRequest {
    @NotBlank(message = "메시지 내용은 필수입니다")
    private String message;
    
    private String language = "ko"; // 기본값: 한국어
}

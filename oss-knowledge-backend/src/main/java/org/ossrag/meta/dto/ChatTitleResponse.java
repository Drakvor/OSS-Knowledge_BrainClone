package org.ossrag.meta.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 채팅 제목 생성 응답 DTO
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class ChatTitleResponse {
    private String title;
    private boolean success;
    private String errorMessage;
    
    public static ChatTitleResponse success(String title) {
        return new ChatTitleResponse(title, true, null);
    }
    
    public static ChatTitleResponse failure(String errorMessage) {
        return new ChatTitleResponse(null, false, errorMessage);
    }
}

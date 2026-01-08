package org.ossrag.meta.service;

import org.ossrag.meta.dto.ChatTitleRequest;
import org.ossrag.meta.dto.ChatTitleResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

/**
 * 채팅 제목 생성 서비스
 */
@Service
public class ChatTitleService {
    
    @Value("${search.server.url:http://localhost:8002}")
    private String searchServerUrl;
    
    private final RestTemplate restTemplate = new RestTemplate();
    
    /**
     * LLM을 사용하여 채팅 제목을 생성합니다.
     */
    public ChatTitleResponse generateTitle(ChatTitleRequest request) {
        try {
            System.out.println("🔍 [ChatTitleService] Starting title generation for: " + request.getMessage().substring(0, Math.min(50, request.getMessage().length())) + "...");
            
            // 검색 서버의 LLM API 호출
            String url = searchServerUrl + "/search/generate-title";
            System.out.println("🔍 [ChatTitleService] Calling search server: " + url);
            
            Map<String, Object> payload = new HashMap<>();
            payload.put("message", request.getMessage());
            payload.put("language", request.getLanguage());
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(payload, headers);
            
            ResponseEntity<Map> response = restTemplate.exchange(
                url, 
                HttpMethod.POST, 
                entity, 
                Map.class
            );
            
            System.out.println("🔍 [ChatTitleService] Search server response status: " + response.getStatusCode());
            System.out.println("🔍 [ChatTitleService] Search server response body: " + response.getBody());
            
            if (response.getStatusCode() == HttpStatus.OK && response.getBody() != null) {
                Map<String, Object> responseBody = response.getBody();
                String title = (String) responseBody.get("title");
                
                if (title != null && !title.trim().isEmpty()) {
                    // 제목 길이 제한 (최대 12자) - 단어 경계에서 자르기
                    if (title.length() > 12) {
                        // 12자 이내에서 마지막 공백 찾기
                        int lastSpaceIndex = title.lastIndexOf(' ', 11);
                        if (lastSpaceIndex > 0) {
                            title = title.substring(0, lastSpaceIndex);
                        } else {
                            // 공백이 없으면 12자로 자르기
                            title = title.substring(0, 12);
                        }
                    }
                    System.out.println("✅ [ChatTitleService] Title generated successfully: " + title);
                    return ChatTitleResponse.success(title);
                }
            }
            
            System.out.println("⚠️ [ChatTitleService] Title generation failed, using fallback");
            return ChatTitleResponse.failure("제목 생성에 실패했습니다.");
            
        } catch (Exception e) {
            System.err.println("❌ [ChatTitleService] Chat title generation error: " + e.getMessage());
            e.printStackTrace();
            
            // 폴백: 기존 20자 자르기 방식
            return generateFallbackTitle(request.getMessage());
        }
    }
    
    /**
     * LLM 호출 실패 시 사용할 폴백 제목 생성
     */
    private ChatTitleResponse generateFallbackTitle(String message) {
        String cleanContent = message.trim();
        
        // 20자 이하면 그대로 사용
        if (cleanContent.length() <= 20) {
            return ChatTitleResponse.success(cleanContent);
        }
        
        // 문장 끝에서 자르기 (마침표, 물음표, 느낌표 기준)
        int sentenceEnd = cleanContent.indexOf('.');
        if (sentenceEnd == -1) sentenceEnd = cleanContent.indexOf('?');
        if (sentenceEnd == -1) sentenceEnd = cleanContent.indexOf('!');
        
        if (sentenceEnd > 0 && sentenceEnd <= 20) {
            return ChatTitleResponse.success(cleanContent.substring(0, sentenceEnd));
        }
        
        // 단어 경계에서 자르기 (공백 기준)
        String[] words = cleanContent.substring(0, 20).split(" ");
        if (words.length > 1) {
            StringBuilder result = new StringBuilder();
            for (int i = 0; i < words.length - 1; i++) {
                if (i > 0) result.append(" ");
                result.append(words[i]);
            }
            String title = result.toString();
            return ChatTitleResponse.success(title.length() > 0 ? title + "..." : cleanContent.substring(0, 17) + "...");
        }
        
        // 단어 경계가 없으면 17자 + ...
        return ChatTitleResponse.success(cleanContent.substring(0, 17) + "...");
    }
}

package org.ossrag.meta.service;

import com.knuddels.jtokkit.Encodings;
import com.knuddels.jtokkit.api.Encoding;
import com.knuddels.jtokkit.api.EncodingRegistry;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class TokenCountService {
    
    private final EncodingRegistry registry = Encodings.newDefaultEncodingRegistry();
    private final Map<String, Encoding> encodingCache = new ConcurrentHashMap<>();
    
    // 모델별 인코딩 매핑
    private static final Map<String, String> MODEL_ENCODINGS = Map.of(
        "gpt-4", "cl100k_base",
        "gpt-4.0", "cl100k_base",
        "gpt-4-32k", "cl100k_base", 
        "gpt-4-turbo", "cl100k_base",
        "gpt-4o", "o200k_base",
        "gpt-4.1-mini", "o200k_base",
        "gpt-3.5-turbo", "cl100k_base",
        "gpt-3.5-turbo-16k", "cl100k_base"
    );
    
    /**
     * 텍스트의 토큰 수를 계산합니다.
     * 
     * @param text 토큰 수를 계산할 텍스트
     * @param model 사용할 모델명 (기본값: "gpt-4.1-mini")
     * @return 토큰 수
     */
    public int countTokens(String text, String model) {
        if (text == null || text.trim().isEmpty()) {
            return 0;
        }
        
        try {
            Encoding encoding = getEncoding(model);
            return encoding.countTokens(text);
        } catch (Exception e) {
            System.err.println("토큰 계산 오류: " + e.getMessage());
            // 오류 발생 시 대략적인 추정값 반환
            return estimateTokenCount(text);
        }
    }
    
    /**
     * 기본 모델(gpt-4.1-mini)로 토큰 수를 계산합니다.
     */
    public int countTokens(String text) {
        return countTokens(text, "gpt-4.1-mini");
    }
    
    /**
     * 모델명에 해당하는 인코딩을 반환합니다.
     */
    private Encoding getEncoding(String model) {
        return encodingCache.computeIfAbsent(model, modelName -> {
            String encodingName = MODEL_ENCODINGS.getOrDefault(modelName, "cl100k_base");
            try {
                return registry.getEncoding(encodingName).orElseThrow(() -> 
                    new RuntimeException("인코딩을 찾을 수 없습니다: " + encodingName));
            } catch (Exception e) {
                System.err.println("인코딩을 찾을 수 없습니다: " + encodingName + ", 기본값 사용");
                return registry.getEncoding("cl100k_base").orElseThrow(() -> 
                    new RuntimeException("기본 인코딩도 찾을 수 없습니다"));
            }
        });
    }
    
    /**
     * 토큰 계산 실패 시 대략적인 추정값을 반환합니다.
     */
    private int estimateTokenCount(String text) {
        // 한국어 기준 대략적 추정: 1토큰 ≈ 2-3글자
        // 영어 기준: 1토큰 ≈ 4글자
        int koreanChars = text.replaceAll("[^가-힣]", "").length();
        int englishChars = text.replaceAll("[^a-zA-Z]", "").length();
        int otherChars = text.length() - koreanChars - englishChars;
        
        int estimatedTokens = (koreanChars / 2) + (englishChars / 4) + (otherChars / 3);
        
        // 최소 1토큰 보장
        return Math.max(1, estimatedTokens);
    }
    
    /**
     * 토큰 수를 기반으로 대략적인 비용을 추정합니다.
     */
    public double estimateCost(int tokens, String model) {
        Map<String, Double> pricing = Map.of(
            "gpt-4", 0.03,
            "gpt-4.0", 0.03,
            "gpt-4-32k", 0.06,
            "gpt-4-turbo", 0.01,
            "gpt-4o", 0.005,
            "gpt-4.1-mini", 0.00015,
            "gpt-3.5-turbo", 0.0015,
            "gpt-3.5-turbo-16k", 0.003
        );
        
        double pricePer1k = pricing.getOrDefault(model, 0.00015); // 기본값: GPT-4.1-mini 가격
        return (tokens / 1000.0) * pricePer1k;
    }
}

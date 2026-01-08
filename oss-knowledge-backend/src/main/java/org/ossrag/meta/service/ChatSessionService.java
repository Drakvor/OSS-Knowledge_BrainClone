package org.ossrag.meta.service;

import org.ossrag.meta.domain.ChatSession;
import org.ossrag.meta.dto.PageResponse;
import org.ossrag.meta.repository.ChatSessionRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.UUID;

@Service
public class ChatSessionService {
    private final ChatSessionRepository repository;

    public ChatSessionService(ChatSessionRepository repository) {
        this.repository = repository;
    }

    // 기본 CRUD 메서드들
    public PageResponse<ChatSession> list(int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        Page<ChatSession> sessionPage = repository.findActiveSessions(pageable);
        
        return new PageResponse<>(sessionPage.getTotalElements(), page, size, sessionPage.getContent());
    }

    public List<ChatSession> listRecent(int limit) {
        Pageable pageable = PageRequest.of(0, limit);
        return repository.findActiveSessions(pageable).getContent();
    }

    public List<ChatSession> listRecentByUserId(Long userId, int limit) {
        Pageable pageable = PageRequest.of(0, limit);
        return repository.findActiveByUserId(userId, pageable).getContent();
    }

    public ChatSession get(UUID id) {
        return repository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Chat session not found"));
    }

    public ChatSession create(ChatSession chatSession) {
        // 기본값 설정
        if (chatSession.getLlmModel() == null) {
            chatSession.setLlmModel("gpt-4.1-mini");
        }
        if (chatSession.getStatus() == null) {
            chatSession.setStatus("active");
        }
        if (chatSession.getTitle() == null) {
            chatSession.setTitle("새 대화");
        }
        if (chatSession.getMetadata() == null) {
            chatSession.setMetadata(new HashMap<>());
        }

        return repository.save(chatSession);
    }

    public ChatSession update(ChatSession chatSession) {
        ChatSession existing = get(chatSession.getId());
        
        // 업데이트 가능한 필드들만 설정
        if (chatSession.getTitle() != null) {
            existing.setTitle(chatSession.getTitle());
        }
        if (chatSession.getLlmModel() != null) {
            existing.setLlmModel(chatSession.getLlmModel());
        }
        if (chatSession.getStatus() != null) {
            existing.setStatus(chatSession.getStatus());
        }
        if (chatSession.getMetadata() != null) {
            existing.setMetadata(chatSession.getMetadata());
        }

        return repository.save(existing);
    }

    public boolean delete(UUID id) {
        if (repository.existsById(id)) {
            repository.deleteById(id);
            return true;
        }
        return false;
    }

    // 특별한 메서드들
    public List<ChatSession> findByUserId(Long userId, int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        return repository.findByUserId(userId, pageable).getContent();
    }

    public List<ChatSession> findByStatus(String status, int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        return repository.findByUserIdAndStatus(null, status, pageable).getContent();
    }

    public boolean updateStatus(UUID id, String status) {
        ChatSession session = get(id);
        session.setStatus(status);
        repository.save(session);
        return true;
    }

    public boolean archive(UUID id) {
        return updateStatus(id, "archived");
    }

    public boolean activate(UUID id) {
        return updateStatus(id, "active");
    }

    /**
     * 채팅방의 메시지 카운트와 토큰 수를 업데이트
     * 메시지가 생성될 때마다 호출되어 채팅방이 최상단으로 올라가도록 함
     */
    public void updateMessageCount(UUID sessionId, String messageType, Integer tokenCount) {
        // 채팅방이 존재하는지 확인하고 업데이트
        if (repository.existsById(sessionId)) {
            ChatSession session = repository.findById(sessionId).orElse(null);
            if (session != null) {
                // 전체 메시지 카운트 증가
                session.setTotalMessageCount(session.getTotalMessageCount() + 1);
                
                // Assistant 메시지인 경우 카운트 증가
                if ("assistant".equals(messageType)) {
                    session.setAssistantMessageCount(session.getAssistantMessageCount() + 1);
                }
                
                // 토큰 수 증가
                if (tokenCount != null && tokenCount > 0) {
                    session.setTotalTokensUsed(session.getTotalTokensUsed() + tokenCount);
                }
                
                // updated_at은 DB 트리거에 의해 자동으로 현재 시간으로 설정됨
                repository.save(session);
            }
        }
    }

    /**
     * 대화 요약 업데이트
     */
    public void updateContextSummary(UUID sessionId, String summary) {
        ChatSession session = get(sessionId);
        session.setContextSummary(summary);
        session.setSummaryUpdatedAt(Instant.now());
        session.setSummaryVersion(session.getSummaryVersion() + 1);
        repository.save(session);
    }

    /**
     * 대화 요약 조회
     */
    public String getContextSummary(UUID sessionId) {
        ChatSession session = get(sessionId);
        return session.getContextSummary();
    }
}

package org.ossrag.meta.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.ossrag.meta.domain.ChatMessage;
import org.ossrag.meta.domain.ChatMessageFeedback;
import org.ossrag.meta.domain.ChatSession;
import org.ossrag.meta.domain.RAGDepartment;
import org.ossrag.meta.dto.*;
import org.ossrag.meta.service.ChatMessageFeedbackService;
import org.ossrag.meta.service.UserService;
import org.ossrag.meta.service.ChatMessageService;
import org.ossrag.meta.service.ChatSessionService;
import org.ossrag.meta.service.ChatTitleService;
import org.ossrag.meta.service.RAGDepartmentService;
import org.ossrag.meta.service.TokenCountService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.stream.Collectors;

@RestController
@Tag(name = "Chat", description = "채팅 관련 API")
@SecurityRequirement(name = "BearerAuth")
public class ChatController {
    private final RestTemplate restTemplate = new RestTemplate();
    
    @Value("${search.server.url:http://localhost:8002}")
    private String searchServerUrl;
    
    @Value("${intent.classifier.url:http://localhost:8001}")
    private String intentClassifierUrl;
    
    @Value("${orchestrator.url:http://localhost:8000}")
    private String orchestratorUrl;
    
    private final ChatSessionService chatSessionService;
    private final ChatMessageService chatMessageService;
    private final ChatMessageFeedbackService chatMessageFeedbackService;
    private final ChatTitleService chatTitleService;
    private final TokenCountService tokenCountService;
    private final RAGDepartmentService ragDepartmentService;
    private final UserService userService;

    public ChatController(ChatSessionService chatSessionService, 
                         ChatMessageService chatMessageService,
                         ChatMessageFeedbackService chatMessageFeedbackService,
                         ChatTitleService chatTitleService,
                         TokenCountService tokenCountService,
                         RAGDepartmentService ragDepartmentService,
                         UserService userService) {
        this.chatSessionService = chatSessionService;
        this.chatMessageService = chatMessageService;
        this.chatMessageFeedbackService = chatMessageFeedbackService;
        this.chatTitleService = chatTitleService;
        this.tokenCountService = tokenCountService;
        this.ragDepartmentService = ragDepartmentService;
        this.userService = userService;
    }

    // ============================================
    // 기존 채팅 API (검색 서버 연동)
    // ============================================

    @PostMapping(value = "/chat", consumes = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "채팅 메시지 전송 (프록시)", description = "Orchestrator 서비스로 요청을 프록시합니다.")
    public ResponseEntity<Map<String, Object>> chat(@RequestBody Map<String, Object> payload) {
        try {
            // Forward request to Orchestrator
            String url = orchestratorUrl + "/chat";
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<Map<String, Object>> requestEntity = new HttpEntity<>(payload, headers);
            
            @SuppressWarnings({"unchecked", "rawtypes"})
            ResponseEntity<Map<String, Object>> response = (ResponseEntity) restTemplate.postForEntity(
                url,
                requestEntity,
                Map.class
            );
            
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                return ResponseEntity.ok(response.getBody());
            } else {
                Map<String, Object> error = new HashMap<>();
                error.put("error", "Failed to get response from orchestrator");
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
            }
        } catch (Exception e) {
            Map<String, Object> error = new HashMap<>();
            error.put("error", "Proxy error: " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }
    
    @PostMapping(value = "/chat/orchestrate", consumes = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "채팅 오케스트레이션 (프록시)", description = "Orchestrator 서비스의 /chat 엔드포인트로 요청을 프록시합니다.")
    public ResponseEntity<Map<String, Object>> orchestrate(@RequestBody Map<String, Object> payload) {
        return chat(payload);
    }

    @PostMapping(value = "/chat/generate-title", consumes = MediaType.APPLICATION_JSON_VALUE, produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "채팅 제목 생성(프록시)", description = "Search-Back의 /search/generate-title 엔드포인트로 요청을 프록시합니다.")
    public ResponseEntity<Map<String, Object>> generateChatTitle(@RequestBody Map<String, Object> payload) {
        try {
            // 요청 바디 정규화
            String message = payload.get("message") != null ? payload.get("message").toString() : null;
            String language = payload.getOrDefault("language", "ko").toString();

            if (message == null || message.trim().isEmpty()) {
                Map<String, Object> error = new HashMap<>();
                error.put("title", "새 대화");
                error.put("success", false);
                error.put("error_message", "message is required");
                return ResponseEntity.badRequest().body(error);
            }

            // Search-Back 요청 엔드포인트
            String url = searchServerUrl + "/search/generate-title";

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            Map<String, Object> forwardBody = new HashMap<>();
            forwardBody.put("message", message);
            forwardBody.put("language", language);

            HttpEntity<Map<String, Object>> requestEntity = new HttpEntity<>(forwardBody, headers);

            @SuppressWarnings({"unchecked", "rawtypes"})
            ResponseEntity<Map<String, Object>> resp = (ResponseEntity) restTemplate.postForEntity(
                url,
                requestEntity,
                Map.class
            );

            if (resp.getStatusCode().is2xxSuccessful() && resp.getBody() != null) {
                return ResponseEntity.ok(resp.getBody());
            } else {
                Map<String, Object> error = new HashMap<>();
                error.put("title", "새 대화");
                error.put("success", false);
                error.put("error_message", "Failed to generate title");
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
            }
        } catch (Exception e) {
            Map<String, Object> error = new HashMap<>();
            error.put("title", "새 대화");
            error.put("success", false);
            error.put("error_message", "Proxy error: " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }

    @PostMapping(value = "/chat/search-engine", consumes = MediaType.APPLICATION_JSON_VALUE, produces = {MediaType.APPLICATION_JSON_VALUE, MediaType.TEXT_EVENT_STREAM_VALUE})
    public Object searchEngineChat(
            @RequestBody Map<String, Object> payload,
            @RequestParam(value = "stream", defaultValue = "false") boolean stream,
            Authentication authentication) {
        String message = (String) payload.get("message");
        String conversationId = (String) payload.get("conversationId");
        String selectedModel = (String) payload.get("selectedModel");
        ChatMessage savedUserMessage = null; // 변수를 try 블록 밖으로 이동
        
        // Extract authenticated user ID
        Long userId = getCurrentUserId(authentication);
        
        System.out.println("DEBUG: message=" + message);
        System.out.println("DEBUG: conversationId=" + conversationId);
        System.out.println("DEBUG: selectedModel=" + selectedModel);
        System.out.println("DEBUG: userId=" + userId);
        
        if (message == null || message.trim().isEmpty()) {
            Map<String, Object> error = new HashMap<>();
            error.put("code", "INVALID_INPUT");
            error.put("message", "메시지가 비어 있습니다. 내용을 입력해 주세요.");
            return ResponseEntity.badRequest().body(error);
        }

        // Validate conversationId: required, valid UUID, and must exist
        if (conversationId == null || conversationId.trim().isEmpty()) {
            Map<String, Object> error = new HashMap<>();
            error.put("code", "SESSION_REQUIRED");
            error.put("message", "세션 ID가 필요합니다. 먼저 세션을 생성한 후 요청해 주세요.");
            return ResponseEntity.badRequest().body(error);
        }
        UUID sessionUuid;
        try {
            sessionUuid = UUID.fromString(conversationId);
        } catch (IllegalArgumentException e) {
            Map<String, Object> error = new HashMap<>();
            error.put("code", "INVALID_SESSION_ID");
            error.put("message", "세션 ID 형식이 올바르지 않습니다. 올바른 UUID를 사용해 주세요.");
            return ResponseEntity.badRequest().body(error);
        }
        try {
            ChatSession existing = chatSessionService.get(sessionUuid);
            if (existing == null) {
                Map<String, Object> error = new HashMap<>();
                error.put("code", "SESSION_NOT_FOUND");
                error.put("message", "해당 세션이 존재하지 않습니다. 새 세션을 생성해 주세요.");
                return ResponseEntity.badRequest().body(error);
            }
        } catch (Exception ex) {
            Map<String, Object> error = new HashMap<>();
            error.put("code", "SESSION_NOT_FOUND");
            error.put("message", "해당 세션이 존재하지 않습니다. 새 세션을 생성해 주세요.");
            return ResponseEntity.badRequest().body(error);
        }

        try {
            System.out.println("DEBUG: === ENTERING TRY BLOCK ===");
            System.out.println("DEBUG: payload: " + payload);
            
            // conversationId는 위에서 검증됨
            
            // Extract mentioned departments and determine collection
            String collection = null; // No default collection - let it be null if no department mentioned
            final Object mentionedDepartmentsObj = payload.get("mentionedDepartments");
            System.out.println("DEBUG: mentionedDepartmentsObj RAW: " + mentionedDepartmentsObj);
            
            if (mentionedDepartmentsObj instanceof java.util.List) {
                java.util.List<?> mentionedDepartments = (java.util.List<?>) mentionedDepartmentsObj;
                if (!mentionedDepartments.isEmpty()) {
                    // Use the first mentioned department as the collection
                    Object firstDept = mentionedDepartments.get(0);
                    if (firstDept instanceof String) {
                        collection = (String) firstDept;
                    } else if (firstDept instanceof java.util.Map) {
                        java.util.Map<?, ?> deptMap = (java.util.Map<?, ?>) firstDept;
                        Object deptName = deptMap.get("name");
                        if (deptName instanceof String) {
                            collection = (String) deptName;
                        }
                    }
                }
            }
            

            // Prepare intent classifier request (채팅방 ID 포함)
            Map<String, Object> intentRequest = new HashMap<>();
            intentRequest.put("message", message);
            intentRequest.put("user_id", userId.toString());
            intentRequest.put("session_id", conversationId); // 채팅방 ID 전달
            
            // Retrieve chat context (sliding window: 3 turns = 6 messages) and merge with attachments
            Map<String, Object> chatContext = getChatContext(conversationId);
            
            // 첨부된 텍스트/코드 파일 스니펫으로 채팅 컨텍스트 보강
            try {
                Object filesObjForCtx = payload.get("files");
                if (filesObjForCtx instanceof java.util.List) {
                    @SuppressWarnings("unchecked")
                    java.util.List<Object> filesList = (java.util.List<Object>) filesObjForCtx;
                    java.util.List<Map<String, String>> attachmentsText = extractAttachmentSnippets(filesList);
                    if (!attachmentsText.isEmpty()) {
                        if (chatContext == null) chatContext = new HashMap<>();
                        chatContext.put("attachments_text", attachmentsText);
                        System.out.println("INFO: Added " + attachmentsText.size() + " attachment snippets to chat context");
                    }
                }
            } catch (Exception e) {
                // best-effort; log failures but don't fail the request
                System.out.println("WARN: Failed to extract attachment snippets: " + e.getMessage());
            }

            if (chatContext != null) {
                intentRequest.put("chat_context", chatContext);
            }

            // 1. 사용자 메시지 저장 (즉시, 상태: pending)
            ChatMessage userMessage = new ChatMessage();
            userMessage.setSessionId(UUID.fromString(conversationId));
            userMessage.setMessageType("user");
            userMessage.setContent(message);
            userMessage.setStatus("pending");
            
            // 사용자 메시지 토큰 수를 즉시 계산
            int userTokenCount = tokenCountService.countTokens(message);
            userMessage.setTokenCount(userTokenCount);
            System.out.println("DEBUG: Calculated user message token count: " + userTokenCount);
            
            // departmentId 설정 (mentionedDepartments에서 추출)
            final Long departmentId = extractDepartmentId(mentionedDepartmentsObj);
            userMessage.setDepartmentId(departmentId);
            
            // 사용자 메시지 metadata에 입력 정보 저장
            Map<String, Object> userMetadata = new HashMap<>();
            // Clean mentioned departments before storing
            System.out.println("DEBUG: mentionedDepartmentsObj BEFORE clean: " + mentionedDepartmentsObj);
            if (mentionedDepartmentsObj != null) {
                Object cleaned = cleanNullNameFields(mentionedDepartmentsObj);
                System.out.println("DEBUG: mentionedDepartmentsObj AFTER clean: " + cleaned);
                userMetadata.put("mentioned_departments", cleaned);
            }
            // 첨부 파일 정보 저장 (프론트에서 업로드 완료 후 전달되는 파일 메타데이터)
            Object filesObj = payload.get("files");
            if (filesObj != null) {
                try {
                    userMetadata.put("files", filesObj);
                } catch (Exception ignore) {
                    // ignore malformed files field gracefully
                }
            }
            if (selectedModel != null) {
                userMetadata.put("selected_model", selectedModel);
            }
            System.out.println("DEBUG: userMetadata: " + userMetadata);
            userMessage.setMetadata(userMetadata);
            
            System.out.println("DEBUG: About to create user message: " + userMessage);
            try {
                savedUserMessage = chatMessageService.create(userMessage);
            } catch (Exception dbEx) {
                System.err.println("DEBUG: Database error: " + dbEx.getMessage());
                dbEx.printStackTrace();
                throw dbEx;
            }
            System.out.println("DEBUG: User message created successfully: " + savedUserMessage.getId());

            final String userMessageId = savedUserMessage.getId().toString();

            // Check if department is selected
            String effectiveCollection = collection;
            boolean hasDepartment = (collection != null && !collection.isEmpty() && departmentId != null);
            
            if (!hasDepartment) {
                // No department selected - skip intent classifier, go directly to Search Server for conversational chat
                System.out.println("DEBUG: No department selected, calling Search Server directly for conversational chat");
                if (stream) {
                    return handleDirectChatStreaming(message, conversationId, departmentId, selectedModel, userMessageId, chatContext, userId);
                } else {
                    return handleDirectChatNonStreaming(message, conversationId, departmentId, selectedModel, userMessageId, savedUserMessage, chatContext, userId);
                }
            }
            
            // Department is selected - call intent classifier for RAG-based response
            intentRequest.put("collection", effectiveCollection);
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> requestEntity = new HttpEntity<>(intentRequest, headers);
            
            try {
                if (stream) {
                    // Handle streaming response through intent classifier
                    return handleStreamingResponse(intentClassifierUrl + "/chat", requestEntity, userMessageId, conversationId, departmentId);
                } else {
                    // Handle non-streaming response through intent classifier
                    @SuppressWarnings({"unchecked", "rawtypes"})
                    ResponseEntity<Map<String, Object>> intentResponse = (ResponseEntity) restTemplate.postForEntity(
                        intentClassifierUrl + "/chat",
                        requestEntity,
                        Map.class
                    );

                if (intentResponse.getStatusCode() == HttpStatus.OK && intentResponse.getBody() != null) {
                    Map<String, Object> intentResult = intentResponse.getBody();
                    System.out.println("DEBUG: Intent result: " + intentResult);
                    
                    // 2. AI 응답 저장 (완료 후)
                    ChatMessage assistantMessage = new ChatMessage();
                    assistantMessage.setSessionId(UUID.fromString(conversationId));
                    assistantMessage.setMessageType("assistant");
                    String responseContent = (String) intentResult.get("response");
                    assistantMessage.setContent(responseContent != null ? responseContent : "응답을 받을 수 없습니다.");
                    assistantMessage.setParentMessageId(savedUserMessage.getId());
                    assistantMessage.setStatus("completed");
                    
                    // 메타데이터 설정
                    Map<String, Object> metadata = new HashMap<>();
                    
                    // intent 정보 저장
                    Object intent = intentResult.get("intent");
                    if (intent != null) {
                        metadata.put("intent", intent);
                    }
                    
                    // timestamp 정보 저장
                    Object timestamp = intentResult.get("timestamp");
                    if (timestamp != null) {
                        metadata.put("timestamp", timestamp);
                    }
                    
                    // sources 정보 저장 (if available)
                    Object sources = intentResult.get("sources");
                    if (sources != null) {
                        metadata.put("sources", sources);
                    }
                    
                    // 사용자 입력에서 받은 정보 추가
                    metadata.put("mentioned_departments", mentionedDepartmentsObj);
                    if (collection != null) {
                        metadata.put("selected_collection", collection);
                    }
                    metadata.put("selected_model", selectedModel);
                    
                    assistantMessage.setMetadata(metadata);
                    
                    chatMessageService.create(assistantMessage);
                    
                    // 3. 사용자 메시지 상태를 completed로 업데이트
                    savedUserMessage.setStatus("completed");
                    chatMessageService.update(savedUserMessage);
                    
                    // 4. 대화 요약 체크 (하이브리드 조건: 8K 토큰 또는 10턴)
                    checkAndGenerateSummary(conversationId);
                    
                    // Return non-streaming response
                    Map<String, Object> response = new HashMap<>();
                    response.put("id", String.valueOf(Instant.now().toEpochMilli()));
                    response.put("message", "ok");
                    response.put("content", intentResult.get("response"));
                    response.put("intent", intentResult.get("intent"));
                    response.put("timestamp", intentResult.get("timestamp"));
                    // Include sources in response if available
                    if (sources != null) {
                        response.put("sources", sources);
                    }
                    return ResponseEntity.ok(response);
                } else {
                    // AI 응답 실패 시 사용자 메시지 상태를 failed로 업데이트
                    savedUserMessage.setStatus("failed");
                    chatMessageService.update(savedUserMessage);
                    throw new RuntimeException("Intent Classifier returned error: " + intentResponse.getStatusCode());
                }
                }
            } catch (Exception intentException) {
                System.err.println("Intent Classifier request failed: " + intentException.getMessage());
                intentException.printStackTrace();
                
                // 예외 발생 시 사용자 메시지 상태를 failed로 업데이트
                try {
                    if (savedUserMessage != null) {
                        savedUserMessage.setStatus("failed");
                        chatMessageService.update(savedUserMessage);
                    }
                } catch (Exception updateError) {
                    System.err.println("Failed to update user message status: " + updateError.getMessage());
                }
                
                Map<String, Object> error = new HashMap<>();
                error.put("error", "Intent Classifier failed: " + intentException.getMessage());
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
            }
        } catch (Exception e) {
            System.err.println("Intent Classifier request failed: " + e.getMessage());
            
            // 예외 발생 시 사용자 메시지 상태를 failed로 업데이트
            try {
                if (savedUserMessage != null) {
                    savedUserMessage.setStatus("failed");
                    chatMessageService.update(savedUserMessage);
                }
            } catch (Exception updateError) {
                System.err.println("Failed to update user message status: " + updateError.getMessage());
            }
            
            Map<String, Object> error = new HashMap<>();
            error.put("error", "Search failed: " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }

    /**
     * Handle streaming response from search server
     */
    private SseEmitter handleStreamingResponse(String url, HttpEntity<Map<String, Object>> requestEntity, String userMessageId, String conversationId, Long departmentId) {
        SseEmitter emitter = new SseEmitter(60000L); // 60초 타임아웃
        
        // 즉시 연결 확인 메시지 전송 (JSON 형식으로 변경)
        try {
            Map<String, Object> pingData = new HashMap<>();
            pingData.put("type", "ping");
            pingData.put("data", Map.of("message", "connected"));
            emitter.send(SseEmitter.event()
                .name("ping")
                .data(pingData));
        } catch (Exception e) {
            System.err.println("Failed to send SSE ping: " + e.getMessage());
        }
        
        // 비동기로 스트리밍 처리
        new Thread(() -> {
            StringBuilder fullResponse = new StringBuilder();
            Map<String, Object> searchResults = null;
            Map<String, Object> modelInfo = null;
            Long processingTime = null;
            Map<String, Object> searchResult = null;
                // departmentId는 이미 계산되어 있음
            
            try {
                // Call search server for streaming response
                @SuppressWarnings({"unchecked", "rawtypes"})
                ResponseEntity<Map<String, Object>> searchResponse = (ResponseEntity) restTemplate.postForEntity(
                    url, 
                    requestEntity, 
                    Map.class
                );
                
                if (searchResponse.getStatusCode() == HttpStatus.OK && searchResponse.getBody() != null) {
                    searchResult = searchResponse.getBody();
                    
                    // Extract sources from response
                    Object sources = searchResult.get("sources");
                    
                    // Send metadata with real user message ID
                    sendSseEvent(emitter, "metadata", Map.of(
                        "timestamp", System.currentTimeMillis(),
                        "userMessageId", userMessageId
                    ));
                    
                    // Send content
                    String responseContent = (String) searchResult.get("response");
                    if (responseContent != null && !responseContent.isEmpty()) {
                        // Simulate streaming by sending content in chunks
                        String[] words = responseContent.split(" ");
                        for (int i = 0; i < words.length; i++) {
                            String chunk = words[i] + (i < words.length - 1 ? " " : "");
                            if (!sendSseEvent(emitter, "content", Map.of("content", chunk))) {
                                break;
                            }
                            fullResponse.append(chunk);
                            
                            // Small delay to simulate streaming
                            try {
                                Thread.sleep(50);
                            } catch (InterruptedException e) {
                                Thread.currentThread().interrupt();
                                break;
                            }
                        }
                    }
                    
                    // Store metadata for later use (before saving message)
                    searchResults = extractSearchResults(searchResult);
                    modelInfo = extractModelInfo(searchResult);
                    processingTime = extractProcessingTime(searchResult);
                    
                    // Save message BEFORE sending 'done' event to ensure IDs are available
                    ChatMessage savedAssistantMessage = null;
                    UUID savedUserMessageId = null;
                    try {
                        ChatMessage assistantMessage = new ChatMessage();
                        assistantMessage.setSessionId(UUID.fromString(conversationId));
                        assistantMessage.setMessageType("assistant");
                        assistantMessage.setContent(fullResponse.toString());
                        assistantMessage.setParentMessageId(UUID.fromString(userMessageId));
                        assistantMessage.setStatus("completed");
                        
                        // 토큰 수 설정 (Java에서 직접 계산)
                        int responseTokens = tokenCountService.countTokens(fullResponse.toString());
                        assistantMessage.setTokenCount(responseTokens);
                        
                        // departmentId 설정 (사용자 메시지와 동일하게)
                        assistantMessage.setDepartmentId(departmentId);
                        
                        // 메타데이터 설정
                        Map<String, Object> metadata = new HashMap<>();
                        if (searchResults != null) {
                            metadata.put("search_results", cleanNullNameFields(searchResults));
                        }
                        if (processingTime != null) {
                            metadata.put("processing_time_ms", processingTime);
                        }
                        if (modelInfo != null) {
                            metadata.put("model_info", cleanNullNameFields(modelInfo));
                        }
                        
                        // Include sources in metadata if available
                        if (sources != null) {
                            metadata.put("sources", sources);
                        }
                        
                        // 사용자 입력에서 받은 정보 추가
                        Map<String, Object> requestBody = requestEntity.getBody();
                        if (requestBody != null) {
                            Object mentionedDepts = requestBody.get("mentionedDepartments");
                            if (mentionedDepts != null) {
                                metadata.put("mentioned_departments", mentionedDepts);
                            }
                            Object collection = requestBody.get("collection");
                            if (collection != null) {
                                metadata.put("selected_collection", collection);
                            }
                            Object selectedModel = requestBody.get("selectedModel");
                            if (selectedModel != null) {
                                metadata.put("selected_model", selectedModel);
                            }
                        }
                        
                        assistantMessage.setMetadata(metadata);
                        savedAssistantMessage = chatMessageService.create(assistantMessage);
                        
                        // 사용자 메시지 상태를 completed로 업데이트
                        ChatMessage userMessage = chatMessageService.get(userMessageId);
                        userMessage.setStatus("completed");
                        chatMessageService.update(userMessage);
                        savedUserMessageId = userMessage.getId();
                        
                        // 대화 요약 체크
                        checkAndGenerateSummary(conversationId);
                    } catch (Exception saveError) {
                        System.err.println("Failed to save assistant message: " + saveError.getMessage());
                        updateUserMessageStatus(userMessageId, "failed");
                    }
                    
                    // Send done event WITH message IDs (if available)
                    // This ensures IDs are sent even if message_saved event fails
                    Map<String, Object> doneData = new HashMap<>();
                    doneData.put("final_response", responseContent);
                    if (savedAssistantMessage != null) {
                        doneData.put("assistantMessageId", savedAssistantMessage.getId().toString());
                    }
                    if (savedUserMessageId != null) {
                        doneData.put("userMessageId", savedUserMessageId.toString());
                    }
                    // Include sources in done event if available
                    if (sources != null) {
                        doneData.put("sources", sources);
                    }
                    sendSseEvent(emitter, "done", doneData);
                    
                    // message_saved event removed; 'done' includes IDs
                    
                    emitter.complete();
                } else {
                    // Fallback response
                    String fallbackResponse = "검색 서버에서 응답을 받을 수 없습니다.";
                    sendFallbackResponse(emitter, fallbackResponse);
                    fullResponse.append(fallbackResponse);
                }
                
                // 스트리밍 완료 후 AI 응답 저장
                try {
                    ChatMessage assistantMessage = new ChatMessage();
                    assistantMessage.setSessionId(UUID.fromString(conversationId));
                    assistantMessage.setMessageType("assistant");
                    assistantMessage.setContent(fullResponse.toString());
                    assistantMessage.setParentMessageId(UUID.fromString(userMessageId));
                    assistantMessage.setStatus("completed");
                    
                    // 토큰 수 설정 (Java에서 직접 계산)
                    System.out.println("=== STREAMING TOKEN COUNT SETTING DEBUG ===");
                    System.out.println("Search result for token extraction: " + searchResult);
                    
                    // Java에서 직접 토큰 수 계산
                    int responseTokens = tokenCountService.countTokens(fullResponse.toString());
                    System.out.println("Calculated response tokens: " + responseTokens);
                    assistantMessage.setTokenCount(responseTokens);
                    System.out.println("Set assistant message token count to: " + assistantMessage.getTokenCount());
                    
                    // departmentId 설정 (사용자 메시지와 동일하게)
                    assistantMessage.setDepartmentId(departmentId);
                    
                    System.out.println("=== STREAMING TOKEN COUNT SETTING DEBUG END ===");
                    
                    // 메타데이터 설정
                    Map<String, Object> metadata = new HashMap<>();
                    if (searchResults != null) {
                        metadata.put("search_results", cleanNullNameFields(searchResults));
                    }
                    if (processingTime != null) {
                        metadata.put("processing_time_ms", processingTime);
                    }
                    if (modelInfo != null) {
                        metadata.put("model_info", cleanNullNameFields(modelInfo));
                    }
                    
                    // 사용자 입력에서 받은 정보 추가 (스트리밍의 경우 requestEntity에서 추출)
                    Map<String, Object> requestBody = requestEntity.getBody();
                    if (requestBody != null) {
                        Object mentionedDepts = requestBody.get("mentionedDepartments");
                        if (mentionedDepts != null) {
                            metadata.put("mentioned_departments", mentionedDepts);
                        }
                        Object collection = requestBody.get("collection");
                        if (collection != null) {
                            metadata.put("selected_collection", collection);
                        }
                        Object selectedModel = requestBody.get("selectedModel");
                        if (selectedModel != null) {
                            metadata.put("selected_model", selectedModel);
                        }
                    }
                    
                    assistantMessage.setMetadata(metadata);
                    
                    ChatMessage savedAssistantMessage = chatMessageService.create(assistantMessage);
                    
                    // 사용자 메시지 상태를 completed로 업데이트
                    ChatMessage userMessage = chatMessageService.get(userMessageId);
                    userMessage.setStatus("completed");
                    chatMessageService.update(userMessage);
                    
                    // 대화 요약 체크 (하이브리드 조건: 8K 토큰 또는 10턴)
                    checkAndGenerateSummary(conversationId);
                    
                    // message_saved event removed; IDs persisted and 'done' already sent
                } catch (Exception saveError) {
                    System.err.println("Failed to save assistant message: " + saveError.getMessage());
                    
                    // 저장 실패 시 사용자 메시지 상태를 failed로 업데이트
                    updateUserMessageStatus(userMessageId, "failed");
                }
                
                emitter.complete();
                
            } catch (Exception e) {
                System.err.println("Streaming error: " + e.getMessage());
                e.printStackTrace();
                sendSseEvent(emitter, "error", Map.of("error", e.getMessage()));
                updateUserMessageStatus(userMessageId, "failed");
                // Avoid propagating error after SSE response is committed
                emitter.complete();
            }
        }).start();
        
        return emitter;
    }
    
    /**
     * Handle direct Search-Back streaming for general chat (when collection is null)
     */
    private SseEmitter handleSearchBackStreaming(String message, String conversationId, Long departmentId, String selectedModel, String userMessageId) {
        SseEmitter emitter = new SseEmitter(60000L);
        
        // 즉시 연결 확인
        try {
            Map<String, Object> pingData = new HashMap<>();
            pingData.put("type", "ping");
            pingData.put("data", Map.of("message", "connected"));
            emitter.send(SseEmitter.event().name("ping").data(pingData));
        } catch (Exception e) {
            System.err.println("Failed to send SSE ping: " + e.getMessage());
        }
        
        // 비동기로 Search-Back 호출 및 스트리밍 처리
        new Thread(() -> {
            StringBuilder fullResponse = new StringBuilder();
            
            try {
                // Prepare Search-Back request
                Map<String, Object> searchRequest = new HashMap<>();
                searchRequest.put("query", message);
                searchRequest.put("collection", "");
                searchRequest.put("limit", 1);
                searchRequest.put("threshold", 1.0);
                searchRequest.put("max_tokens", 1000);
                searchRequest.put("temperature", 0.7);
                if (conversationId != null) {
                    searchRequest.put("session_id", conversationId);
                }
                
                HttpHeaders headers = new HttpHeaders();
                headers.setContentType(MediaType.APPLICATION_JSON);
                HttpEntity<Map<String, Object>> searchRequestEntity = new HttpEntity<>(searchRequest, headers);
                
                // Call Search-Back (non-streaming endpoint)
                @SuppressWarnings({"unchecked", "rawtypes"})
                ResponseEntity<Map<String, Object>> searchResponse = (ResponseEntity) restTemplate.postForEntity(
                    searchServerUrl + "/search/response",
                    searchRequestEntity,
                    Map.class
                );
                
                if (searchResponse.getStatusCode() == HttpStatus.OK && searchResponse.getBody() != null) {
                    Map<String, Object> searchResult = searchResponse.getBody();
                    String responseText = (String) searchResult.get("response");
                    Object sources = searchResult.get("sources");
                    
                    // Send metadata
                    sendSseEvent(emitter, "metadata", Map.of(
                        "timestamp", System.currentTimeMillis(),
                        "userMessageId", userMessageId
                    ));
                    
                    // Simulate streaming by sending content in chunks
                    if (responseText != null && !responseText.isEmpty()) {
                        String[] words = responseText.split(" ");
                        for (int i = 0; i < words.length; i++) {
                            String chunk = words[i] + (i < words.length - 1 ? " " : "");
                            if (!sendSseEvent(emitter, "content", Map.of("content", chunk))) {
                                break;
                            }
                            fullResponse.append(chunk);
                            
                            try {
                                Thread.sleep(50);
                            } catch (InterruptedException e) {
                                Thread.currentThread().interrupt();
                                break;
                            }
                        }
                    }
                    
                    // Save assistant message BEFORE sending 'done' event
                    ChatMessage savedAssistant = null;
                    UUID savedUserMessageId = null;
                    try {
                        ChatMessage assistantMessage = new ChatMessage();
                        assistantMessage.setSessionId(UUID.fromString(conversationId));
                        assistantMessage.setMessageType("assistant");
                        assistantMessage.setContent(responseText);
                        assistantMessage.setParentMessageId(UUID.fromString(userMessageId));
                        assistantMessage.setStatus("completed");
                        assistantMessage.setTokenCount(tokenCountService.countTokens(responseText));
                        assistantMessage.setDepartmentId(departmentId);
                        
                        Map<String, Object> metadata = new HashMap<>();
                        metadata.put("selected_model", selectedModel);
                        metadata.put("direct_chat", true);
                        // Include sources in metadata if available
                        if (sources != null) {
                            metadata.put("sources", sources);
                        }
                        assistantMessage.setMetadata(metadata);
                        
                        savedAssistant = chatMessageService.create(assistantMessage);
                        
                        // 사용자 메시지 상태를 completed로 업데이트
                        ChatMessage userMessage = chatMessageService.get(userMessageId);
                        userMessage.setStatus("completed");
                        chatMessageService.update(userMessage);
                        savedUserMessageId = userMessage.getId();
                        
                        checkAndGenerateSummary(conversationId);
                    } catch (Exception saveError) {
                        System.err.println("Failed to save assistant message: " + saveError.getMessage());
                        updateUserMessageStatus(userMessageId, "failed");
                    }
                    
                    // Send done event WITH message IDs (if available)
                    Map<String, Object> doneData = new HashMap<>();
                    doneData.put("final_response", responseText);
                    if (savedAssistant != null) {
                        doneData.put("assistantMessageId", savedAssistant.getId().toString());
                    }
                    if (savedUserMessageId != null) {
                        doneData.put("userMessageId", savedUserMessageId.toString());
                    }
                    // Include sources in done event if available
                    if (sources != null) {
                        doneData.put("sources", sources);
                    }
                    sendSseEvent(emitter, "done", doneData);
                    
                    // message_saved event removed; 'done' includes IDs
                } else {
                    String fallbackResponse = "응답을 받을 수 없습니다.";
                    sendFallbackResponse(emitter, fallbackResponse);
                }
                
                emitter.complete();
                
            } catch (Exception e) {
                System.err.println("Search-Back streaming error: " + e.getMessage());
                e.printStackTrace();
                sendSseEvent(emitter, "error", Map.of("error", e.getMessage()));
                updateUserMessageStatus(userMessageId, "failed");
                // Avoid propagating error after SSE response is committed
                emitter.complete();
            }
        }).start();
        
        return emitter;
    }
    
    /**
     * Handle direct chat for non-streaming mode (bypass Intent Classifier)
     */
    private ResponseEntity<Map<String, Object>> handleDirectChatNonStreaming(
        String message, 
        String conversationId, 
        Long departmentId, 
        String selectedModel, 
        String userMessageId,
        ChatMessage savedUserMessage,
        Map<String, Object> chatContext,
        Long userId
    ) {
        try {
            // Ensure chatContext includes chat_history (sliding window: 3 turns)
            if (chatContext == null) {
                chatContext = getChatContext(conversationId);
            } else if (!chatContext.containsKey("chat_history")) {
                // Merge with retrieved chat context to ensure chat_history is included
                Map<String, Object> retrievedContext = getChatContext(conversationId);
                if (retrievedContext != null) {
                    chatContext.put("chat_history", retrievedContext.get("chat_history"));
                    chatContext.put("context_summary", retrievedContext.get("context_summary"));
                    chatContext.put("session_id", retrievedContext.get("session_id"));
                    if (retrievedContext.containsKey("current_department")) {
                        chatContext.put("current_department", retrievedContext.get("current_department"));
                    }
                    if (retrievedContext.containsKey("current_department_id")) {
                        chatContext.put("current_department_id", retrievedContext.get("current_department_id"));
                    }
                }
            }
            
            // Search Server로 직접 대화 요청 준비
            Map<String, Object> searchRequest = new HashMap<>();
            searchRequest.put("query", message);
            searchRequest.put("collection", ""); // 빈 컬렉션으로 직접 대화
            searchRequest.put("limit", 1); // 최소 제한 (컬렉션이 비어있어 사용되지 않음)
            searchRequest.put("threshold", 1.0); // 검색을 건너뛰기 위한 높은 임계값
            searchRequest.put("include_metadata", false);
            searchRequest.put("include_content", false);
            searchRequest.put("max_tokens", 1000);
            searchRequest.put("temperature", 0.7);
            
            // 채팅 컨텍스트를 파라미터로 추가 (chat_history 및 attachments_text 포함)
            if (chatContext != null) {
                searchRequest.put("chat_context", chatContext);
            }
            
            // Add user ID and session ID for memory management
            if (userId != null) {
                searchRequest.put("user_id", userId.intValue());
            }
            if (conversationId != null) {
                searchRequest.put("session_id", conversationId);
            }
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> requestEntity = new HttpEntity<>(searchRequest, headers);
            
            // Search Server 직접 호출
            @SuppressWarnings({"unchecked", "rawtypes"})
            ResponseEntity<Map<String, Object>> searchResponse = (ResponseEntity) restTemplate.postForEntity(
                searchServerUrl + "/search/response",
                requestEntity,
                Map.class
            );
            
            if (searchResponse.getStatusCode() == HttpStatus.OK && searchResponse.getBody() != null) {
                Map<String, Object> searchResult = searchResponse.getBody();
                String responseContent = (String) searchResult.get("response");
                Object sources = searchResult.get("sources");
                
                // Save assistant message
                ChatMessage assistantMessage = new ChatMessage();
                assistantMessage.setSessionId(UUID.fromString(conversationId));
                assistantMessage.setMessageType("assistant");
                assistantMessage.setContent(responseContent);
                assistantMessage.setParentMessageId(UUID.fromString(userMessageId));
                assistantMessage.setStatus("completed");
                assistantMessage.setTokenCount(tokenCountService.countTokens(responseContent));
                assistantMessage.setDepartmentId(departmentId);
                
                Map<String, Object> metadata = new HashMap<>();
                metadata.put("selected_model", selectedModel);
                metadata.put("direct_chat", true);
                metadata.put("intent", "CONVERSATIONAL");
                // Include sources in metadata if available
                if (sources != null) {
                    metadata.put("sources", sources);
                }
                assistantMessage.setMetadata(metadata);
                
                chatMessageService.create(assistantMessage);
                
                // Update user message status
                savedUserMessage.setStatus("completed");
                chatMessageService.update(savedUserMessage);
                
                // Check for summary generation
                checkAndGenerateSummary(conversationId);
                
                // Return response
                Map<String, Object> response = new HashMap<>();
                response.put("id", String.valueOf(Instant.now().toEpochMilli()));
                response.put("message", "ok");
                response.put("content", responseContent);
                response.put("intent", "CONVERSATIONAL");
                response.put("timestamp", Instant.now().toString());
                // Include sources in response if available
                if (sources != null) {
                    response.put("sources", sources);
                }
                return ResponseEntity.ok(response);
            } else {
                throw new RuntimeException("Direct chat failed: " + searchResponse.getStatusCode());
            }
        } catch (Exception e) {
            System.err.println("Direct chat error: " + e.getMessage());
            e.printStackTrace();
            savedUserMessage.setStatus("failed");
            chatMessageService.update(savedUserMessage);
            
            Map<String, Object> error = new HashMap<>();
            error.put("error", "Direct chat failed: " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }
    
    /**
     * Handle direct chat for streaming mode (bypass Intent Classifier)
     */
    private SseEmitter handleDirectChatStreaming(
        String message, 
        String conversationId, 
        Long departmentId, 
        String selectedModel, 
        String userMessageId,
        Map<String, Object> chatContext,
        Long userId
    ) {
        SseEmitter emitter = new SseEmitter(60000L);
        
        // Send immediate connection confirmation
        try {
            Map<String, Object> pingData = new HashMap<>();
            pingData.put("type", "ping");
            pingData.put("data", Map.of("message", "connected"));
            emitter.send(SseEmitter.event().name("ping").data(pingData));
        } catch (Exception e) {
            System.err.println("Failed to send SSE ping: " + e.getMessage());
        }
        
        // 직접 대화 스트리밍을 비동기로 처리
        // chatContext는 이미 attachments_text를 포함하여 전달받음
        final Map<String, Object> finalChatContext = chatContext; // final로 캡처하여 스레드에서 사용
        final Long finalUserId = userId; // final로 캡처하여 스레드에서 사용
        new Thread(() -> {
            StringBuilder fullResponse = new StringBuilder();
            
            try {
                // Ensure chatContext includes chat_history (sliding window: 3 turns)
                Map<String, Object> chatContextToUse = finalChatContext;
                if (chatContextToUse == null) {
                    chatContextToUse = getChatContext(conversationId);
                } else if (!chatContextToUse.containsKey("chat_history")) {
                    // Merge with retrieved chat context to ensure chat_history is included
                    Map<String, Object> retrievedContext = getChatContext(conversationId);
                    if (retrievedContext != null) {
                        chatContextToUse.put("chat_history", retrievedContext.get("chat_history"));
                        chatContextToUse.put("context_summary", retrievedContext.get("context_summary"));
                        chatContextToUse.put("session_id", retrievedContext.get("session_id"));
                        if (retrievedContext.containsKey("current_department")) {
                            chatContextToUse.put("current_department", retrievedContext.get("current_department"));
                        }
                        if (retrievedContext.containsKey("current_department_id")) {
                            chatContextToUse.put("current_department_id", retrievedContext.get("current_department_id"));
                        }
                    }
                }
                
                // Search Server로 직접 대화 요청 준비
                Map<String, Object> searchRequest = new HashMap<>();
                searchRequest.put("query", message);
                searchRequest.put("collection", "");
                searchRequest.put("limit", 1); // 최소 제한 (컬렉션이 비어있어 사용되지 않음)
                searchRequest.put("threshold", 1.0);
                searchRequest.put("include_metadata", false);
                searchRequest.put("include_content", false);
                searchRequest.put("max_tokens", 1000);
                searchRequest.put("temperature", 0.7);
                
                // 채팅 컨텍스트를 파라미터로 추가 (chat_history 및 attachments_text 포함)
                if (chatContextToUse != null) {
                    searchRequest.put("chat_context", chatContextToUse);
                }
                
                // Add user ID and session ID for memory management
                if (finalUserId != null) {
                    searchRequest.put("user_id", finalUserId.intValue());
                }
                if (conversationId != null) {
                    searchRequest.put("session_id", conversationId);
                }
                
                HttpHeaders headers = new HttpHeaders();
                headers.setContentType(MediaType.APPLICATION_JSON);
                HttpEntity<Map<String, Object>> searchRequestEntity = new HttpEntity<>(searchRequest, headers);
                
                // Search Server 직접 호출
                @SuppressWarnings({"unchecked", "rawtypes"})
                ResponseEntity<Map<String, Object>> searchResponse = (ResponseEntity) restTemplate.postForEntity(
                    searchServerUrl + "/search/response",
                    searchRequestEntity,
                    Map.class
                );
                
                if (searchResponse.getStatusCode() == HttpStatus.OK && searchResponse.getBody() != null) {
                    Map<String, Object> searchResult = searchResponse.getBody();
                    String responseText = (String) searchResult.get("response");
                    Object sources = searchResult.get("sources");
                    
                    // Send metadata
                    sendSseEvent(emitter, "metadata", Map.of(
                        "timestamp", System.currentTimeMillis(),
                        "userMessageId", userMessageId
                    ));
                    
                    // Simulate streaming by sending content in chunks
                    if (responseText != null && !responseText.isEmpty()) {
                        String[] words = responseText.split(" ");
                        for (int i = 0; i < words.length; i++) {
                            String chunk = words[i] + (i < words.length - 1 ? " " : "");
                            if (!sendSseEvent(emitter, "content", Map.of("content", chunk))) {
                                break;
                            }
                            fullResponse.append(chunk);
                            
                            try {
                                Thread.sleep(50);
                            } catch (InterruptedException e) {
                                Thread.currentThread().interrupt();
                                break;
                            }
                        }
                    }
                    
                    // Save assistant message BEFORE sending 'done' event
                    ChatMessage savedAssistant = null;
                    UUID savedUserMessageId = null;
                    try {
                        ChatMessage assistantMessage = new ChatMessage();
                        assistantMessage.setSessionId(UUID.fromString(conversationId));
                        assistantMessage.setMessageType("assistant");
                        assistantMessage.setContent(responseText);
                        assistantMessage.setParentMessageId(UUID.fromString(userMessageId));
                        assistantMessage.setStatus("completed");
                        assistantMessage.setTokenCount(tokenCountService.countTokens(responseText));
                        assistantMessage.setDepartmentId(departmentId);
                        
                        Map<String, Object> metadata = new HashMap<>();
                        metadata.put("selected_model", selectedModel);
                        metadata.put("direct_chat", true);
                        metadata.put("intent", "CONVERSATIONAL");
                        // Include sources in metadata if available
                        if (sources != null) {
                            metadata.put("sources", sources);
                        }
                        assistantMessage.setMetadata(metadata);
                        
                        savedAssistant = chatMessageService.create(assistantMessage);
                        
                        // 사용자 메시지 상태를 completed로 업데이트
                        ChatMessage userMessage = chatMessageService.get(userMessageId);
                        userMessage.setStatus("completed");
                        chatMessageService.update(userMessage);
                        savedUserMessageId = userMessage.getId();
                        
                        checkAndGenerateSummary(conversationId);
                    } catch (Exception saveError) {
                        System.err.println("Failed to save assistant message: " + saveError.getMessage());
                        updateUserMessageStatus(userMessageId, "failed");
                    }
                    
                    // Send done event WITH message IDs (if available)
                    Map<String, Object> doneData = new HashMap<>();
                    doneData.put("final_response", responseText);
                    if (savedAssistant != null) {
                        doneData.put("assistantMessageId", savedAssistant.getId().toString());
                    }
                    if (savedUserMessageId != null) {
                        doneData.put("userMessageId", savedUserMessageId.toString());
                    }
                    // Include sources in done event if available
                    if (sources != null) {
                        doneData.put("sources", sources);
                    }
                    sendSseEvent(emitter, "done", doneData);
                    
                    // message_saved event removed; 'done' includes IDs
                } else {
                    String fallbackResponse = "응답을 받을 수 없습니다.";
                    sendFallbackResponse(emitter, fallbackResponse);
                }
                
                emitter.complete();
                
            } catch (Exception e) {
                System.err.println("Direct chat streaming error: " + e.getMessage());
                e.printStackTrace();
                sendSseEvent(emitter, "error", Map.of("error", e.getMessage()));
                updateUserMessageStatus(userMessageId, "failed");
                // Avoid propagating error after SSE response is committed
                emitter.complete();
            }
        }).start();
        
        return emitter;
    }
    
    /**
     * Retrieve chat context from database for a given conversation ID
     */
    private Map<String, Object> getChatContext(String conversationId) {
        if (conversationId == null) {
            return null;
        }
        
        try {
            // Get recent messages for this conversation (last 6 messages = 3 turns)
            List<ChatMessage> recentMessages = chatMessageService.getLastNMessages(conversationId, 6);
            
            // Convert to chat history format (limit content length)
            List<Map<String, Object>> chatHistory = new ArrayList<>();
            Long currentDepartmentId = null;
            
            for (ChatMessage msg : recentMessages) {
                Map<String, Object> historyEntry = new HashMap<>();
                historyEntry.put("role", msg.getMessageType()); // "user" or "assistant"
                
                // Include departmentId if present
                if (msg.getDepartmentId() != null) {
                    historyEntry.put("department_id", msg.getDepartmentId());
                    // Track most recent department
                    if (currentDepartmentId == null) {
                        currentDepartmentId = msg.getDepartmentId();
                    }
                }
                
                // Limit content length to preserve context while managing token usage
                // 3000 chars ≈ 750 tokens per message, 6 messages ≈ 4500 tokens total, well within 128K context window
                String content = msg.getContent();
                if (content != null && content.length() > 3000) {
                    content = content.substring(0, 3000) + "...";
                }
                historyEntry.put("content", content);
                chatHistory.add(historyEntry);
            }
            
            // Reverse to get chronological order (oldest first)
            java.util.Collections.reverse(chatHistory);
            
            // Get session summary if available
            ChatSession session = chatSessionService.get(UUID.fromString(conversationId));
            String contextSummary = session != null ? session.getContextSummary() : null;
            
            // Build chat context (keep it concise)
            Map<String, Object> chatContext = new HashMap<>();
            chatContext.put("session_id", conversationId);
            chatContext.put("chat_history", chatHistory);
            chatContext.put("context_summary", contextSummary);
            chatContext.put("total_tokens_used", session != null ? session.getTotalTokensUsed() : 0);
            
            // Add current department (most recent with department_id)
            if (currentDepartmentId != null) {
                chatContext.put("current_department_id", currentDepartmentId);
                try {
                    // Get department name for easier reference
                    RAGDepartmentResponse dept = ragDepartmentService.getDepartmentById(currentDepartmentId);
                    chatContext.put("current_department", dept.getName());
                } catch (Exception e) {
                    // If department lookup fails, just use the ID
                    System.out.println("DEBUG: Could not lookup department name for ID: " + currentDepartmentId);
                }
            }
            
            System.out.println("DEBUG: Retrieved chat context - history_count: " + chatHistory.size() + 
                             ", has_summary: " + (contextSummary != null));
            
            return chatContext;
            
        } catch (Exception e) {
            System.err.println("Failed to retrieve chat context: " + e.getMessage());
            e.printStackTrace();
            return null;
        }
    }

    // ============================================
    // 새로운 채팅 세션 관리 API
    // ============================================

    @GetMapping("/chat/sessions")
    @Operation(summary = "채팅 세션 목록 조회", description = "페이지네이션을 지원하는 채팅 세션 목록을 조회합니다.")
    public ResponseEntity<PageResponse<ChatSessionResponse>> getSessions(
            @Parameter(description = "페이지 번호 (0부터 시작)") @RequestParam(defaultValue = "0") int page,
            @Parameter(description = "페이지 크기") @RequestParam(defaultValue = "20") int size,
            Authentication authentication) {
        
        // 사용자 소유 세션만 반환
        Long userId = getCurrentUserId(authentication);
        List<ChatSession> sessionItems = chatSessionService.findByUserId(userId, page, size);
        PageResponse<ChatSession> sessions = new PageResponse<>(sessionItems.size(), page, size, sessionItems);
        List<ChatSessionResponse> responses = sessions.getItems().stream()
                .map(this::convertToSessionResponse)
                .collect(Collectors.toList());
        
        PageResponse<ChatSessionResponse> response = new PageResponse<>(
                sessions.getTotal(), sessions.getPage(), sessions.getSize(), responses);
        
        return ResponseEntity.ok(response);
    }

    @GetMapping("/chat/sessions/recent")
    @Operation(summary = "최근 채팅 세션 조회", description = "최근 생성된 채팅 세션 목록을 조회합니다.")
    public ResponseEntity<List<ChatSessionResponse>> getRecentSessions(
            @Parameter(description = "조회할 개수") @RequestParam(defaultValue = "10") int limit,
            Authentication authentication) {
        
        // 인증 실패 시에도 기본 사용자로 대체하지 않음: 빈 목록 반환
        try {
            Long userId = getCurrentUserId(authentication);
            List<ChatSession> sessions = chatSessionService.listRecentByUserId(userId, limit);
            List<ChatSessionResponse> responses = sessions.stream()
                    .map(this::convertToSessionResponse)
                    .collect(Collectors.toList());
            return ResponseEntity.ok(responses);
        } catch (Exception e) {
            return ResponseEntity.ok(new ArrayList<>());
        }
    }

    @GetMapping("/chat/sessions/{id}")
    @Operation(summary = "채팅 세션 상세 조회", description = "특정 채팅 세션의 상세 정보를 조회합니다.")
    public ResponseEntity<ChatSessionResponse> getSession(
            @Parameter(description = "세션 ID") @PathVariable String id) {
        
        ChatSession session = chatSessionService.get(UUID.fromString(id));
        return ResponseEntity.ok(convertToSessionResponse(session));
    }

    @PostMapping("/chat/sessions")
    @Operation(summary = "채팅 세션 생성", description = "새로운 채팅 세션을 생성합니다.")
    public ResponseEntity<ChatSessionResponse> createSession(
            @RequestBody ChatSessionRequest request,
            Authentication authentication) {
        
        ChatSession session = convertToSession(request);
        
        // 사용자 ID 설정: 인증된 사용자 > request의 userId > 기본값
        Long userId = null;
        try {
            if (authentication != null) {
                userId = getCurrentUserId(authentication);
            }
        } catch (Exception e) {
            // 인증 실패 시 request의 userId 사용
        }
        
        if (userId == null) {
            // Request에서 userId 가져오기 (테스트용 또는 인증 없는 경우)
            userId = request.getUserId();
        }
        
        if (userId == null) {
            userId = 1L; // 기본 사용자 ID
        }
        
        session.setUserId(userId);
        ChatSession created = chatSessionService.create(session);
        return ResponseEntity.status(HttpStatus.CREATED).body(convertToSessionResponse(created));
    }

    @PutMapping("/chat/sessions/{id}")
    @Operation(summary = "채팅 세션 수정", description = "기존 채팅 세션을 수정합니다.")
    public ResponseEntity<ChatSessionResponse> updateSession(
            @Parameter(description = "세션 ID") @PathVariable String id,
            @RequestBody ChatSessionRequest request) {
        
        ChatSession session = convertToSession(request);
        session.setId(UUID.fromString(id));
        ChatSession updated = chatSessionService.update(session);
        return ResponseEntity.ok(convertToSessionResponse(updated));
    }

    @DeleteMapping("/chat/sessions/{id}")
    @Operation(summary = "채팅 세션 삭제", description = "채팅 세션을 삭제합니다.")
    public ResponseEntity<Void> deleteSession(
            @Parameter(description = "세션 ID") @PathVariable String id) {
        
        boolean deleted = chatSessionService.delete(UUID.fromString(id));
        return deleted ? ResponseEntity.noContent().build() : ResponseEntity.notFound().build();
    }

    // ============================================
    // 새로운 채팅 메시지 관리 API
    // ============================================

    @GetMapping("/chat/sessions/{sessionId}/messages")
    @Operation(summary = "채팅 메시지 목록 조회", description = "특정 세션의 채팅 메시지 목록을 조회합니다.")
    public ResponseEntity<List<ChatMessageResponse>> getMessages(
            @Parameter(description = "세션 ID") @PathVariable String sessionId,
            @Parameter(description = "페이지 번호") @RequestParam(defaultValue = "0") int page,
            @Parameter(description = "페이지 크기") @RequestParam(defaultValue = "50") int size) {
        
        List<ChatMessage> messages = chatMessageService.findBySessionId(sessionId, page, size);
        List<ChatMessageResponse> responses = messages.stream()
                .map(this::convertToMessageResponse)
                .collect(Collectors.toList());
        
        return ResponseEntity.ok(responses);
    }

    @GetMapping("/chat/sessions/{sessionId}/messages/ordered")
    @Operation(summary = "채팅 메시지 시간순 조회", description = "특정 세션의 채팅 메시지를 시간순으로 조회합니다.")
    public ResponseEntity<List<ChatMessageResponse>> getMessagesOrdered(
            @Parameter(description = "세션 ID") @PathVariable String sessionId) {
        
        List<ChatMessage> messages = chatMessageService.findBySessionIdOrderByCreatedAt(sessionId);
        List<ChatMessageResponse> responses = messages.stream()
                .map(this::convertToMessageResponse)
                .collect(Collectors.toList());
        
        return ResponseEntity.ok(responses);
    }

    @PostMapping("/chat/sessions/{sessionId}/messages")
    @Operation(summary = "채팅 메시지 생성", description = "새로운 채팅 메시지를 생성합니다.")
    public ResponseEntity<?> createMessage(
            @Parameter(description = "세션 ID") @PathVariable String sessionId,
            @RequestBody ChatMessageRequest request) {
        try {
            ChatMessage message = convertToMessage(request);
            message.setSessionId(UUID.fromString(sessionId));
            
            // Clean metadata to prevent null name errors
            if (message.getMetadata() != null) {
                message.setMetadata((java.util.Map<String, Object>) cleanNullNameFields(message.getMetadata()));
            }
            
            ChatMessage created = chatMessageService.create(message);
            return ResponseEntity.status(HttpStatus.CREATED).body(convertToMessageResponse(created));
        } catch (Exception e) {
            System.err.println("Error creating message: " + e.getMessage());
            e.printStackTrace();
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("code", "INTERNAL_ERROR");
            errorResponse.put("message", "Failed to create message: " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    // ============================================
    // 새로운 채팅 메시지 피드백 관리 API
    // ============================================

    @PostMapping("/chat/messages/{userMessageId}/feedback")
    @Operation(summary = "메시지 피드백 생성", description = "사용자 질문에 대한 답변 피드백을 생성합니다.")
    public ResponseEntity<ChatMessageFeedbackResponse> createFeedback(
            @Parameter(description = "사용자 질문 메시지 ID") @PathVariable String userMessageId,
            @RequestBody ChatMessageFeedbackRequest request) {
        
        ChatMessageFeedback feedback = convertToFeedback(request, userMessageId);
        ChatMessageFeedback created = chatMessageFeedbackService.create(feedback);
        return ResponseEntity.status(HttpStatus.CREATED).body(convertToFeedbackResponse(created));
    }

    @GetMapping("/chat/messages/{userMessageId}/feedback")
    @Operation(summary = "메시지 피드백 조회", description = "특정 사용자 질문에 대한 피드백 목록을 조회합니다.")
    public ResponseEntity<List<ChatMessageFeedbackResponse>> getFeedbacks(
            @Parameter(description = "사용자 질문 메시지 ID") @PathVariable String userMessageId) {
        
        List<ChatMessageFeedback> feedbacks = chatMessageFeedbackService.findByUserMessageId(userMessageId);
        List<ChatMessageFeedbackResponse> responses = feedbacks.stream()
                .map(this::convertToFeedbackResponse)
                .collect(Collectors.toList());
        
        return ResponseEntity.ok(responses);
    }

    @GetMapping("/chat/messages/{userMessageId}/feedback/stats")
    @Operation(summary = "메시지 피드백 통계", description = "특정 사용자 질문에 대한 피드백 통계를 조회합니다.")
    public ResponseEntity<FeedbackStatsResponse> getFeedbackStats(
            @Parameter(description = "사용자 질문 메시지 ID") @PathVariable String userMessageId) {
        
        double averageRating = chatMessageFeedbackService.getAverageRatingByUserMessageId(userMessageId);
        long totalCount = chatMessageFeedbackService.countByUserMessageId(userMessageId);
        
        FeedbackStatsResponse stats = new FeedbackStatsResponse(userMessageId, averageRating, totalCount);
        return ResponseEntity.ok(stats);
    }

    // ============================================
    // Helper Methods
    // ============================================

    private ChatSessionResponse convertToSessionResponse(ChatSession session) {
        return new ChatSessionResponse(
                session.getId().toString(),
                session.getUserId(),
                session.getTitle(),
                session.getLlmModel(),
                session.getStatus(),
                session.getMetadata(),
                session.getAssistantMessageCount(),
                session.getTotalMessageCount(),
                session.getTotalTokensUsed(),
                session.getContextSummary(),
                session.getSummaryUpdatedAt(),
                session.getSummaryVersion(),
                session.getCreatedAt(),
                session.getUpdatedAt()
        );
    }

    private ChatSession convertToSession(ChatSessionRequest request) {
        ChatSession session = new ChatSession();
        session.setUserId(request.getUserId());
        session.setTitle(request.getTitle());
        session.setLlmModel(request.getLlmModel());
        session.setStatus(request.getStatus());
        session.setMetadata(request.getMetadata());
        return session;
    }

    private ChatMessageResponse convertToMessageResponse(ChatMessage message) {
        return new ChatMessageResponse(
                message.getId().toString(),
                message.getSessionId().toString(),
                message.getTurnIndex(),
                message.getMessageType(),
                message.getContent(),
                message.getTokenCount(),
                message.getDepartmentId(),
                message.getMetadata(),
                message.getParentMessageId() != null ? message.getParentMessageId().toString() : null,
                message.getStatus(),
                message.getCreatedAt(),
                message.getUpdatedAt()
        );
    }

    private ChatMessage convertToMessage(ChatMessageRequest request) {
        ChatMessage message = new ChatMessage();
        // sessionId is set from path variable in the endpoint, not from request
        // Only set it here if it's provided in the request (for backward compatibility)
        if (request.getSessionId() != null && !request.getSessionId().trim().isEmpty()) {
            message.setSessionId(UUID.fromString(request.getSessionId()));
        }
        message.setMessageType(request.getMessageType());
        message.setContent(request.getContent());
        message.setTokenCount(request.getTokenCount());
        message.setDepartmentId(request.getDepartmentId());
        
        // Clean metadata to prevent null name errors
        if (request.getMetadata() != null) {
            try {
                message.setMetadata((java.util.Map<String, Object>) cleanNullNameFields(request.getMetadata()));
            } catch (Exception e) {
                System.err.println("Error cleaning metadata: " + e.getMessage());
                // Set empty metadata if cleaning fails
                message.setMetadata(new HashMap<>());
            }
        } else {
            // Ensure metadata is never null
            message.setMetadata(new HashMap<>());
        }
        
        message.setParentMessageId(request.getParentMessageId() != null ? UUID.fromString(request.getParentMessageId()) : null);
        message.setStatus(request.getStatus() != null ? request.getStatus() : "pending");
        return message;
    }

    private ChatMessageFeedbackResponse convertToFeedbackResponse(ChatMessageFeedback feedback) {
        return new ChatMessageFeedbackResponse(
                feedback.getId().toString(),
                feedback.getUserMessageId().toString(),
                feedback.getUserId(),
                feedback.getRating(),
                feedback.getComment(),
                feedback.getFeedbackType(),
                feedback.getIsAnonymous(),
                feedback.getMetadata(),
                feedback.getCreatedAt(),
                feedback.getUpdatedAt()
        );
    }

    private ChatMessageFeedback convertToFeedback(ChatMessageFeedbackRequest request, String userMessageId) {
        ChatMessageFeedback feedback = new ChatMessageFeedback();
        // PathVariable에서 받은 userMessageId 사용 (사용자 질문 ID)
        feedback.setUserMessageId(java.util.UUID.fromString(userMessageId));
        feedback.setUserId(request.getUserId());
        feedback.setRating(request.getRating());
        feedback.setComment(request.getComment());
        feedback.setFeedbackType(request.getFeedbackType());
        feedback.setIsAnonymous(request.getIsAnonymous());
        feedback.setMetadata(request.getMetadata());
        return feedback;
    }

    // ============================================
    // Helper Methods
    // ============================================
    
    /**
     * null name 필드를 안전하게 처리하는 헬퍼 메서드
     */
    private Object cleanNullNameFields(Object data) {
        if (data == null) {
            return null;
        }
        
        if (data instanceof java.util.List) {
            java.util.List<?> list = (java.util.List<?>) data;
            java.util.List<Object> cleanedList = new ArrayList<>();
            for (Object item : list) {
                try {
                    cleanedList.add(cleanNullNameFields(item));
                } catch (Exception e) {
                    System.err.println("Error processing list item: " + e.getMessage());
                    cleanedList.add(item);
                }
            }
            return cleanedList;
        }
        
        if (data instanceof java.util.Map) {
            java.util.Map<?, ?> map = (java.util.Map<?, ?>) data;
            java.util.Map<String, Object> cleanedMap = new HashMap<>();
            for (java.util.Map.Entry<?, ?> entry : map.entrySet()) {
                try {
                    Object keyObj = entry.getKey();
                    Object value = entry.getValue();
                    
                    // null key 처리
                    if (keyObj == null) {
                        continue;
                    }
                    
                    String key = keyObj.toString();
                    
                    if ("name".equals(key) && value == null) {
                        // null name 필드를 빈 문자열로 대체
                        cleanedMap.put(key, "");
                    } else if ("name".equals(key) && value instanceof String) {
                        // name 필드가 String이면 그대로 사용
                        cleanedMap.put(key, value);
                    } else {
                        // 재귀적으로 중첩된 객체들도 처리
                        cleanedMap.put(key, cleanNullNameFields(value));
                    }
                } catch (Exception e) {
                    System.err.println("Error processing map entry: " + e.getMessage());
                    // Skip problematic entries
                }
            }
            return cleanedMap;
        }
        
        return data;
    }

    /**
     * 첨부된 파일 메타데이터에서 작은 텍스트 스니펫을 추출하여 채팅 컨텍스트를 보강합니다.
     * 파일 메타데이터에는 'url', 'path', 'name', 'contentType' 등의 키가 포함될 수 있습니다.
     * 확장자 허용 목록을 기반으로 텍스트/코드 파일만 고려합니다.
     */
    private java.util.List<Map<String, String>> extractAttachmentSnippets(java.util.List<Object> filesList) {
        final java.util.Set<String> allowedExt = new java.util.HashSet<>(java.util.Arrays.asList(
            "txt","md","py","js","ts","json","yaml","yml","sh","bash","java"
        ));

        java.util.List<Map<String, String>> results = new java.util.ArrayList<>();

        for (Object f : filesList) {
            if (!(f instanceof java.util.Map)) continue;
            @SuppressWarnings("unchecked")
            java.util.Map<String, Object> fm = (java.util.Map<String, Object>) f;
            Object nameObj = fm.getOrDefault("name", "attachment");
            String name = (nameObj != null) ? nameObj.toString() : "attachment";

            // 확장자 확인
            String ext = "";
            if (name != null && name.length() > 0) {
                int dot = name.lastIndexOf('.');
                if (dot >= 0 && dot < name.length() - 1) {
                    ext = name.substring(dot + 1).toLowerCase();
                }
            }
            if (!allowedExt.contains(ext)) {
                continue; // 텍스트/코드가 아닌 파일 건너뛰기
            }

            // content 필드가 있으면 직접 사용, 없으면 URL/path에서 가져오기
            String snippet = null;
            Object contentObj = fm.get("content");
            if (contentObj != null) {
                // content 필드가 있으면 직접 사용 (이미 10KB로 제한됨)
                snippet = contentObj.toString();
            } else {
                // content 필드가 없으면 URL/path에서 가져오기 (기존 동작)
                String url = fm.getOrDefault("url", fm.getOrDefault("path", "")).toString();
                snippet = fetchTextSnippet(url, 10 * 1024); // 파일당 10KB
            }

            if (snippet == null || snippet.isEmpty()) continue;

            Map<String, String> entry = new HashMap<>();
            entry.put("name", name);
            entry.put("snippet", snippet);
            results.add(entry);

            if (results.size() >= 5) break; // 파일 수 제한
        }

        return results;
    }

    /**
     * 가능한 경우 RestTemplate을 사용하여 URL/경로에서 최대 maxBytes까지의 텍스트를 가져옵니다.
     * 가져올 수 없는 경우 빈 문자열로 대체됩니다.
     */
    private String fetchTextSnippet(String urlOrPath, int maxBytes) {
        try {
            if (urlOrPath == null || urlOrPath.isEmpty()) return null;

            // 기본 휴리스틱: http로 시작하면 URL로 처리
            if (urlOrPath.startsWith("http://") || urlOrPath.startsWith("https://")) {
                ResponseEntity<byte[]> resp = restTemplate.getForEntity(urlOrPath, byte[].class);
                if (!resp.getStatusCode().is2xxSuccessful() || resp.getBody() == null) return null;
                byte[] body = resp.getBody();
                int len = Math.min(body.length, Math.max(0, maxBytes));
                String text = new String(body, 0, len, java.nio.charset.StandardCharsets.UTF_8);
                return text;
            } else {
                // Local/relative path (best-effort): read from filesystem if accessible
                java.nio.file.Path p = java.nio.file.Paths.get(urlOrPath);
                if (java.nio.file.Files.exists(p)) {
                    byte[] body = java.nio.file.Files.readAllBytes(p);
                    int len = Math.min(body.length, Math.max(0, maxBytes));
                    return new String(body, 0, len, java.nio.charset.StandardCharsets.UTF_8);
                }
            }
        } catch (Exception ignore) {
        }
        return null;
    }

    // (Deletion endpoint removed as per requirements: keep user message; assistant may be blank)
    
    private Long getCurrentUserId(Authentication authentication) {
        if (authentication == null || authentication.getPrincipal() == null) {
            throw new RuntimeException("User not authenticated");
        }
        
        // Authentication의 username(subject)로 사용자 조회 후 ID 반환
        try {
            String username = authentication.getName();
            if (username == null || username.isEmpty()) {
                throw new RuntimeException("Missing username in authentication");
            }
            return userService.findByUsername(username).getId();
        } catch (Exception e) {
            throw new RuntimeException("Failed to resolve user ID from authentication", e);
        }
    }

    // ============================================
    // SSE Helper Methods
    // ============================================
    
    private void sendFallbackResponse(SseEmitter emitter, String fallbackResponse) {
        try {
            Map<String, Object> contentEvent = createSseEvent("content", Map.of("content", fallbackResponse));
            Map<String, Object> doneEvent = createSseEvent("done", Map.of("final_response", fallbackResponse));
            
            emitter.send(SseEmitter.event().name("content").data(contentEvent));
            emitter.send(SseEmitter.event().name("done").data(doneEvent));
        } catch (Exception e) {
            System.err.println("Failed to send fallback response: " + e.getMessage());
        }
    }
    
    private Map<String, Object> createSseEvent(String type, Map<String, Object> data) {
		Map<String, Object> event = new HashMap<>();
		event.put("type", type);
		// For 'done' events, flatten payload at the top level (no nested 'data')
		if ("done".equals(type)) {
			if (data != null) {
				event.putAll(data);
			}
			return event;
		}
		// Default behavior: wrap payload under 'data'
		event.put("data", data);
		return event;
    }
    
    private boolean sendSseEvent(SseEmitter emitter, String eventName, Map<String, Object> data) {
        try {
            Map<String, Object> event = createSseEvent(eventName, data);
            emitter.send(SseEmitter.event().name(eventName).data(event));
            return true;
        } catch (Exception e) {
            System.err.println("Failed to send " + eventName + " event: " + e.getMessage());
            return false;
        }
    }
    
    @SuppressWarnings("unchecked")
    private Map<String, Object> extractSearchResults(Map<String, Object> searchResult) {
        Object searchResultsObj = searchResult.get("search_results");
        if (searchResultsObj instanceof java.util.List) {
            Map<String, Object> results = new HashMap<>();
            results.put("results", searchResultsObj);
            return results;
        } else if (searchResultsObj instanceof java.util.Map) {
            return (Map<String, Object>) searchResultsObj;
        }
        return null;
    }
    
    @SuppressWarnings("unchecked")
    private Map<String, Object> extractModelInfo(Map<String, Object> searchResult) {
        Object modelInfoObj = searchResult.get("model_info");
        return (modelInfoObj instanceof java.util.Map) ? (Map<String, Object>) modelInfoObj : null;
    }
    
    private Long extractProcessingTime(Map<String, Object> searchResult) {
        Object processingTimeObj = searchResult.get("total_processing_time_ms");
        return (processingTimeObj instanceof Number) ? ((Number) processingTimeObj).longValue() : null;
    }
    
    
    
    
    private Long extractDepartmentId(Object mentionedDepartmentsObj) {
        if (mentionedDepartmentsObj instanceof java.util.List) {
            java.util.List<?> mentionedDepartments = (java.util.List<?>) mentionedDepartmentsObj;
            if (!mentionedDepartments.isEmpty()) {
                Object firstDept = mentionedDepartments.get(0);
                
                // Handle department object with ID
                if (firstDept instanceof java.util.Map) {
                    java.util.Map<?, ?> deptMap = (java.util.Map<?, ?>) firstDept;
                    Object deptId = deptMap.get("id");
                    if (deptId instanceof Number) {
                        return ((Number) deptId).longValue();
                    }
                }
                
                // Handle department name/keyword string - look up in database
                if (firstDept instanceof String) {
                    String deptKeyword = (String) firstDept;
                    System.out.println("DEBUG: Looking up department by keyword: " + deptKeyword);
                    
                    try {
                        // First try exact name match
                        try {
                            RAGDepartmentResponse dept = ragDepartmentService.getDepartmentByName(deptKeyword);
                            System.out.println("DEBUG: Found department by exact name: " + dept.getId() + " for keyword: " + deptKeyword);
                            return dept.getId();
                        } catch (RuntimeException e) {
                            // Not found by exact name, try keyword search
                            System.out.println("DEBUG: No exact name match, searching by keywords...");
                        }
                        
                        // Search by keywords in all departments
                        List<RAGDepartmentResponse> allDepts = ragDepartmentService.getAllDepartments();
                        for (RAGDepartmentResponse dept : allDepts) {
                            if (dept.getKeywords() != null && dept.getKeywords().contains(deptKeyword)) {
                                System.out.println("DEBUG: Found department by keyword: " + dept.getId() + " for keyword: " + deptKeyword);
                                return dept.getId();
                            }
                        }
                        
                        System.out.println("DEBUG: No department found for keyword: " + deptKeyword);
                    } catch (Exception e) {
                        System.err.println("DEBUG: Error looking up department: " + e.getMessage());
                    }
                }
            }
        }
        return null; // 기본값: 부서 없음
    }
    
    private void updateUserMessageStatus(String userMessageId, String status) {
        try {
            ChatMessage userMessage = chatMessageService.get(userMessageId);
            userMessage.setStatus(status);
            chatMessageService.update(userMessage);
        } catch (Exception updateError) {
            System.err.println("Failed to update user message status: " + updateError.getMessage());
        }
    }

    /**
     * 하이브리드 조건으로 대화 요약 생성 체크
     * 조건 1: 10턴마다 (assistant_message_count % 10 == 0)
     * 조건 2: 토큰 8K 초과
     */
    private void checkAndGenerateSummary(String sessionId) {
        try {
            ChatSession session = chatSessionService.get(UUID.fromString(sessionId));
            
            // 조건 1: 10턴마다 (assistant_message_count % 10 == 0)
            boolean turnBased = session.getAssistantMessageCount() % 10 == 0 && 
                               session.getAssistantMessageCount() > 0;
            
            // 조건 2: 토큰 8K 초과
            boolean tokenBased = session.getTotalTokensUsed() > 8000;
            
            if (turnBased || tokenBased) {
                System.out.println("DEBUG: Summary generation triggered - Turn: " + 
                                 session.getAssistantMessageCount() + 
                                 ", Tokens: " + session.getTotalTokensUsed() + 
                                 ", TurnBased: " + turnBased + 
                                 ", TokenBased: " + tokenBased);
                
                // 비동기로 요약 생성 (성능 고려)
                CompletableFuture.runAsync(() -> {
                    try {
                        generateConversationSummary(sessionId);
                    } catch (Exception e) {
                        System.err.println("Summary generation failed: " + e.getMessage());
                        e.printStackTrace();
                    }
                });
            }
        } catch (Exception e) {
            System.err.println("Failed to check summary conditions: " + e.getMessage());
        }
    }
    
    /**
     * 대화 요약 생성
     */
    private void generateConversationSummary(String sessionId) {
        try {
            ChatSession session = chatSessionService.get(UUID.fromString(sessionId));
            
            // 요약할 메시지 범위 결정 (최대 20개)
            int messageLimit = Math.min(20, session.getTotalMessageCount());
            List<ChatMessage> messagesToSummarize = chatMessageService.getLastNMessages(sessionId, messageLimit);
            
            if (messagesToSummarize.isEmpty()) {
                System.out.println("DEBUG: No messages to summarize for session: " + sessionId);
                return;
            }
            
            // 요약 프롬프트 구성
            String summaryPrompt = buildSummaryPrompt(messagesToSummarize);
            
            // LLM으로 요약 생성 (임시로 간단한 요약 생성)
            String summary = generateSimpleSummary(messagesToSummarize);
            
            // 요약 토큰 수 계산
            int summaryTokenCount = tokenCountService.countTokens(summary);
            
            // 세션 업데이트
            session.setContextSummary(summary);
            session.setSummaryUpdatedAt(Instant.now());
            session.setSummaryVersion(session.getSummaryVersion() + 1);
            
            // 요약 토큰 수를 메타데이터에 저장
            Map<String, Object> metadata = session.getMetadata();
            if (metadata == null) {
                metadata = new HashMap<>();
            }
            metadata.put("summary_token_count", summaryTokenCount);
            metadata.put("summary_generated_at", Instant.now().toString());
            metadata.put("summary_prompt_tokens", tokenCountService.countTokens(summaryPrompt));
            session.setMetadata(metadata);
            
            chatSessionService.update(session);
            
            System.out.println("DEBUG: Summary generated successfully for session: " + sessionId + 
                             ", Turn: " + session.getAssistantMessageCount() + 
                             ", Tokens: " + session.getTotalTokensUsed() + 
                             ", Summary length: " + summary.length() +
                             ", Summary tokens: " + summaryTokenCount);
            
        } catch (Exception e) {
            System.err.println("Failed to generate conversation summary for session: " + sessionId + 
                             ", Error: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    /**
     * 요약 프롬프트 구성
     */
    private String buildSummaryPrompt(List<ChatMessage> messages) {
        StringBuilder prompt = new StringBuilder();
        prompt.append("다음 대화를 3-4문장으로 요약해주세요:\n\n");
        
        for (ChatMessage msg : messages) {
            String role = msg.getMessageType().equals("user") ? "사용자" : "어시스턴트";
            prompt.append(role).append(": ").append(msg.getContent()).append("\n");
        }
        
        prompt.append("\n요약 요구사항:\n");
        prompt.append("- 핵심 주제와 주요 질문들 포함\n");
        prompt.append("- 사용자 관심사나 문제점 강조\n");
        prompt.append("- 해결된/미해결 문제 구분\n");
        prompt.append("- 다음 대화 참고용 맥락 제공\n");
        prompt.append("- 3-4문장, 500토큰 이내로 작성");
        
        return prompt.toString();
    }
    
    /**
     * 간단한 요약 생성 (임시 구현)
     */
    private String generateSimpleSummary(List<ChatMessage> messages) {
        try {
            // 사용자 메시지들에서 키워드 추출
            List<String> userMessages = messages.stream()
                .filter(msg -> "user".equals(msg.getMessageType()))
                .map(ChatMessage::getContent)
                .collect(Collectors.toList());
            
            if (userMessages.isEmpty()) {
                return "대화 요약을 생성할 수 없습니다.";
            }
            
            // 첫 번째와 마지막 사용자 메시지 기반으로 간단한 요약 생성
            String firstMessage = userMessages.get(0);
            String lastMessage = userMessages.get(userMessages.size() - 1);
            
            StringBuilder summary = new StringBuilder();
            summary.append("사용자가 ").append(firstMessage.length() > 50 ? 
                firstMessage.substring(0, 50) + "..." : firstMessage).append("에 대해 질문했습니다. ");
            
            if (userMessages.size() > 1) {
                summary.append("총 ").append(userMessages.size()).append("개의 질문이 있었으며, ");
                summary.append("최근에는 ").append(lastMessage.length() > 30 ? 
                    lastMessage.substring(0, 30) + "..." : lastMessage).append("에 대해 논의했습니다.");
            } else {
                summary.append("이 주제에 대한 대화가 진행되었습니다.");
            }
            
            return summary.toString();
            
        } catch (Exception e) {
            System.err.println("Failed to generate simple summary: " + e.getMessage());
            return "대화 요약 생성 중 오류가 발생했습니다.";
        }
    }

    // ============================================
    // 채팅 제목 생성 API
    // ============================================
    
    @PostMapping("/chat/generate-title")
    @Operation(summary = "채팅 제목 생성", description = "LLM을 사용하여 채팅 제목을 자동 생성합니다.")
    public ResponseEntity<ChatTitleResponse> generateChatTitle(@RequestBody ChatTitleRequest request) {
        try {
            ChatTitleResponse response = chatTitleService.generateTitle(request);
            
            if (response.isSuccess()) {
                return ResponseEntity.ok(response);
            } else {
                return ResponseEntity.badRequest().body(response);
            }
        } catch (Exception e) {
            System.err.println("Chat title generation error: " + e.getMessage());
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ChatTitleResponse.failure("제목 생성 중 오류가 발생했습니다."));
        }
    }

    // ============================================
    // Inner Classes
    // ============================================

    public static class FeedbackStatsResponse {
        private String messageId;
        private double averageRating;
        private long totalCount;

        public FeedbackStatsResponse(String messageId, double averageRating, long totalCount) {
            this.messageId = messageId;
            this.averageRating = averageRating;
            this.totalCount = totalCount;
        }

        // Getters
        public String getMessageId() { return messageId; }
        public double getAverageRating() { return averageRating; }
        public long getTotalCount() { return totalCount; }
    }
}
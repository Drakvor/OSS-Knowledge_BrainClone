import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { 
    getRecentChatSessionsAPI, 
    createChatSessionAPI, 
    deleteChatSessionAPI,
    updateChatSessionAPI,
    getChatMessagesOrderedAPI,
    createChatMessageAPI,
    generateChatTitleAPI
} from "@/services/metaApi";
import { useUIStore } from "./ui";

export const useConversationStore = defineStore("conversation", () => {
    const uiStore = useUIStore();
    
    // 대화 목록 (서버에서 로드)
    const conversations = ref([]);
    
    // 현재 선택된 대화 ID
    const currentConversationId = ref(null);
    
    // 검색어
    const searchQuery = ref("");
    
    // 로딩 상태
    const isLoading = ref(false);

    // 현재 대화 가져오기
    const currentConversation = computed(() => {
        return conversations.value.find(
            (c) => c.id === currentConversationId.value
        );
    });

    // 필터링된 대화 목록
    const filteredConversations = computed(() => {
        if (!searchQuery.value) {
            return conversations.value;
        }

        return conversations.value.filter(
            (conv) =>
                conv.title
                    .toLowerCase()
                    .includes(searchQuery.value.toLowerCase()) ||
                conv.messages.some((msg) =>
                    msg.content
                        .toLowerCase()
                        .includes(searchQuery.value.toLowerCase())
                )
        );
    });

    // 새 대화 생성
    const createNewConversation = async () => {
        try {
            isLoading.value = true;
            
            const sessionData = {
                title: "새 채팅",
                status: "active"
            };
            
            const newSession = await createChatSessionAPI(sessionData);
            
            // 로컬 상태에 추가
            const newConv = {
                id: newSession.id,
                title: newSession.title,
                llmModel: newSession.llmModel,
                totalTokensUsed: newSession.totalTokensUsed || 0,
                messages: [],
                createdAt: newSession.createdAt,
                updatedAt: newSession.updatedAt,
            };
            
            conversations.value.unshift(newConv);
            currentConversationId.value = newConv.id;
            
            // 채팅 화면으로 이동
            try {
                const router = await import('@/router')
                router.default.push('/')
            } catch (error) {
                console.error('Failed to navigate to chat:', error)
            }
            
            return newConv;
        } catch (error) {
            console.error("Failed to create new conversation:", error);
            uiStore.setError("새 대화 생성에 실패했습니다.");
            throw error;
        } finally {
            isLoading.value = false;
        }
    };

    // 대화 선택
    const selectConversation = async (id) => {
        currentConversationId.value = id;
        
        // 선택된 대화의 메시지 로드
        try {
            await loadMessages(id);
        } catch (error) {
            console.error('Failed to load messages for conversation:', id, error);
            uiStore.setError("메시지 로드에 실패했습니다.");
        }
        
        // 채팅 페이지로 이동 (현재 페이지가 채팅 페이지가 아닌 경우)
        try {
            const router = await import('@/router')
            const currentRoute = router.default.currentRoute.value
            
            // 현재 경로가 채팅 관련이 아닌 경우에만 네비게이션
            if (currentRoute.path !== '/' && currentRoute.path !== '/chat') {
                await router.default.push('/')
            }
        } catch (error) {
            console.error('Failed to navigate to chat:', error)
        }
    };

    // 대화 삭제
    const deleteConversation = async (id) => {
        try {
            isLoading.value = true;
            
            await deleteChatSessionAPI(id);
            
            const index = conversations.value.findIndex((c) => c.id === id);
            if (index > -1) {
                conversations.value.splice(index, 1);

                // 현재 대화가 삭제된 경우 새 대화 생성
                if (currentConversationId.value === id) {
                    if (conversations.value.length > 0) {
                        currentConversationId.value = conversations.value[0].id;
                    } else {
                        await createNewConversation();
                    }
                }
                
                uiStore.setSuccess("대화가 삭제되었습니다.");
            }
        } catch (error) {
            console.error("Failed to delete conversation:", error);
            uiStore.setError(`대화 삭제에 실패했습니다: ${error.message}`);
            throw error;
        } finally {
            isLoading.value = false;
        }
    };

    // 대화 제목 변경
    const updateConversationTitle = async (id, newTitle) => {
        try {
            const sessionData = { title: newTitle };
            await updateChatSessionAPI(id, sessionData);
            
            const conv = conversations.value.find((c) => c.id === id);
            if (conv) {
                conv.title = newTitle;
                conv.updatedAt = new Date().toISOString();
            }
        } catch (error) {
            console.error("Failed to update conversation title:", error);
            uiStore.setError("대화 제목 변경에 실패했습니다.");
            throw error;
        }
    };

    // LLM을 사용한 채팅 제목 생성 함수
    const generateChatTitle = async (content) => {
        try {
            console.log('🤖 Calling LLM API for title generation...');
            // LLM API 호출
            const response = await generateChatTitleAPI(content);
            console.log('🤖 LLM API response:', response);
            
            if (response.success && response.title) {
                console.log('✅ LLM title generation successful:', response.title);
                return response.title;
            } else {
                console.warn('⚠️ LLM title generation failed, using fallback. Response:', response);
                return generateFallbackTitle(content);
            }
        } catch (error) {
            console.error('❌ Error generating chat title with LLM:', error);
            return generateFallbackTitle(content);
        }
    };

    // 폴백용 제목 생성 함수 (12자 자르기 로직)
    const generateFallbackTitle = (content) => {
        const cleanContent = content.trim();
        
        // 12자 이하면 그대로 사용
        if (cleanContent.length <= 12) {
            return cleanContent;
        }
        
        // 문장 끝에서 자르기 (마침표, 물음표, 느낌표 기준)
        const sentenceEnd = cleanContent.search(/[.!?]/);
        if (sentenceEnd > 0 && sentenceEnd <= 12) {
            return cleanContent.slice(0, sentenceEnd);
        }
        
        // 12자 이내에서 마지막 공백 찾기
        const lastSpaceIndex = cleanContent.lastIndexOf(' ', 11);
        if (lastSpaceIndex > 0) {
            return cleanContent.slice(0, lastSpaceIndex);
        }
        
        // 공백이 없으면 12자로 자르기
        return cleanContent.slice(0, 12);
    };

    // 메시지 추가 (로컬 상태만 업데이트)
    const addMessage = async (conversationId, message) => {
        const conv = conversations.value.find((c) => c.id === conversationId);
        if (conv) {
            // 중복 메시지 방지: 같은 ID가 이미 있는지 확인
            const messageId = message.id || `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
            const existingMessage = conv.messages.find(m => m.id === messageId);
            
            if (existingMessage) {
                return messageId;
            }
            
            const messageWithId = {
                ...message,
                id: messageId,
                timestamp: message.timestamp || new Date().toISOString(),
                // 스트리밍 관련 속성 명시적으로 보존
                isStreaming: message.isStreaming,
                isThinking: message.isThinking,
            };
            
            // 스트리밍 메시지만 로그
            if (message.isStreaming) {
                console.log('🔧 [STREAM] Assistant message added:', {
                    isStreaming: messageWithId.isStreaming,
                    isThinking: messageWithId.isThinking
                });
            }
            
            conv.messages.push(messageWithId);
            conv.updatedAt = new Date().toISOString();

            // 사용자 메시지인 경우 제목 자동 생성
            if (message.role === "user") {
                console.log("User message added, checking title generation...", {
                    messageContent: message.content.substring(0, 50) + "...",
                    currentTitle: conv.title,
                    messageCount: conv.messages.length
                });
                
                // 제목이 아직 생성되지 않은 경우에만 생성
                const needsTitleGeneration = !conv.title || 
                    conv.title === "새 대화" || 
                    conv.title === "새 채팅방" || 
                    conv.title.startsWith("새 ") ||
                    conv.title === "Brain Clone" ||
                    conv.title.includes("죄송합니다");
                
                if (needsTitleGeneration) {
                    console.log("Generating title for message:", message.content.substring(0, 50) + "...");
                    try {
                        const newTitle = await generateChatTitle(message.content);
                        console.log("Generated title:", newTitle);
                        conv.title = newTitle;
                        
                        // 데모 대화방이 아닌 경우에만 서버에 제목 업데이트
                        if (!conversationId.startsWith("demo-conversation-")) {
                            try {
                                await updateChatSessionAPI(conversationId, { title: newTitle });
                                console.log("Title updated on server successfully");
                            } catch (error) {
                                console.error("Failed to update title on server:", error);
                            }
                        } else {
                            console.log("Demo conversation - title updated locally only");
                        }
                    } catch (error) {
                        console.error("Failed to generate chat title:", error);
                        // 폴백으로 기본 제목 사용
                        conv.title = "새 대화";
                    }
                } else {
                    console.log("Title already exists, skipping generation:", conv.title);
                }
            }

            // 대화 목록 최상단으로 이동 (제목 업데이트 후)
            const index = conversations.value.findIndex(
                (c) => c.id === conversationId
            );
            if (index > 0) {
                conversations.value.unshift(
                    conversations.value.splice(index, 1)[0]
                );
            }

            // 메시지 추가 후 채팅방 정보를 서버에서 다시 가져와서 시간 업데이트 반영
            try {
                await refreshConversationInfo(conversationId);
            } catch (error) {
                console.error("Failed to refresh conversation info:", error);
            }
            
            return messageWithId.id; // 메시지 ID 반환
        }
        return null;
    };

    // 메시지 업데이트 (스트리밍용)
    const updateMessage = (conversationId, messageId, updatedData) => {
        const conv = conversations.value.find((c) => c.id === conversationId);
        if (conv) {
            const messageIndex = conv.messages.findIndex((m) => m.id === messageId);
            if (messageIndex !== -1) {
                conv.messages.splice(messageIndex, 1, {
                    ...conv.messages[messageIndex],
                    ...updatedData,
                });
                conv.updatedAt = new Date().toISOString();
            }
        }
    };

    // 메시지 제거 (로컬)
    const removeMessage = (conversationId, messageId) => {
        const conv = conversations.value.find((c) => c.id === conversationId);
        if (conv) {
            const idx = conv.messages.findIndex((m) => m.id === messageId);
            if (idx !== -1) {
                conv.messages.splice(idx, 1);
                conv.updatedAt = new Date().toISOString();
            }
        }
    };

    // 메시지를 서버에 저장
    const saveMessage = async (conversationId, message) => {
        try {
            const messageData = {
                messageType: message.role,
                content: message.content,
                metadata: {
                    files: message.files,
                    mentionedDepartments: message.mentionedDepartments
                }
            };
            
            const savedMessage = await createChatMessageAPI(conversationId, messageData);
            
            // 로컬 상태 업데이트
            await addMessage(conversationId, {
                ...message,
                id: savedMessage.id,
                timestamp: savedMessage.createdAt
            });
            
            return savedMessage;
        } catch (error) {
            console.error("Failed to save message:", error);
            uiStore.setError("메시지 저장에 실패했습니다.");
            throw error;
        }
    };

    // 특정 채팅방 정보만 서버에서 새로고침
    const refreshConversationInfo = async (conversationId) => {
        try {
            console.log("🔄 Refreshing conversation info for:", conversationId);
            
            // 서버에서 최신 채팅방 목록을 가져와서 해당 채팅방만 업데이트
            const sessions = await getRecentChatSessionsAPI(50);
            
            // 해당 채팅방 찾기
            const updatedSession = sessions.find(session => session.id === conversationId);
            if (updatedSession) {
                // 로컬 채팅방 정보 업데이트 (시간, 토큰 사용량, 모델 정보)
                const localConv = conversations.value.find(c => c.id === conversationId);
                if (localConv) {
                    localConv.updatedAt = updatedSession.updatedAt;
                    localConv.totalTokensUsed = updatedSession.totalTokensUsed || 0;
                    localConv.llmModel = updatedSession.llmModel;
                    console.log("✅ Conversation info updated:", {
                        updatedAt: updatedSession.updatedAt,
                        totalTokensUsed: updatedSession.totalTokensUsed,
                        llmModel: updatedSession.llmModel
                    });
                }
            }
        } catch (error) {
            console.error("Failed to refresh conversation info:", error);
        }
    };

    // 서버에서 대화 목록 로드
    const loadConversations = async () => {
        try {
            isLoading.value = true;
            
            const sessions = await getRecentChatSessionsAPI(50);
            
            // 서버 데이터를 로컬 형식으로 변환
            conversations.value = sessions.map(session => ({
                id: session.id,
                title: session.title,
                llmModel: session.llmModel,
                totalTokensUsed: session.totalTokensUsed,
                messages: [], // 메시지는 별도로 로드
                createdAt: session.createdAt,
                updatedAt: session.updatedAt,
            })).sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)); // 최신순 정렬
            
            // 새로고침/로그인 시에는 자동으로 대화를 선택하지 않음
            // 사용자가 명시적으로 대화를 선택하거나 새 메시지를 입력할 때만 대화 선택
            
        } catch (error) {
            console.error("Failed to load conversations:", error);
            uiStore.setError("대화 목록 로드에 실패했습니다.");
            throw error;
        } finally {
            isLoading.value = false;
        }
    };

    // 특정 대화의 메시지 로드
    const loadMessages = async (conversationId) => {
        try {
            const conv = conversations.value.find((c) => c.id === conversationId);
            if (!conv) {
                console.warn("Conversation not found:", conversationId);
                return;
            }
            
            // 이미 메시지가 로드되어 있고, 메시지가 있는 경우 스킵
            if (conv.messages && conv.messages.length > 0) {
                return;
            }
            
            const messages = await getChatMessagesOrderedAPI(conversationId);
            
            conv.messages = messages.map(msg => ({
                id: msg.id,
                role: msg.messageType,
                content: msg.content,
                timestamp: msg.createdAt,
                files: msg.metadata?.files,
                mentionedDepartments: msg.metadata?.mentioned_departments || msg.metadata?.mentionedDepartments,
                sources: msg.metadata?.sources || null  // Include sources from metadata
            }));
            
        } catch (error) {
            console.error("Failed to load messages:", error);
            uiStore.setError("메시지 로드에 실패했습니다.");
            throw error;
        }
    };

    // 로컬 스토리지에서 불러오기 (제거됨 - 서버 기반으로 변경)
    // const loadFromLocalStorage = () => { ... };

    return {
        conversations,
        currentConversationId,
        searchQuery,
        isLoading,
        currentConversation,
        filteredConversations,
        createNewConversation,
        selectConversation,
        deleteConversation,
        updateConversationTitle,
        addMessage,
        updateMessage,
        removeMessage,
        saveMessage,
        loadConversations,
        loadMessages,
        refreshConversationInfo,
        generateChatTitle,
        // loadFromLocalStorage, // 제거됨
    };
});

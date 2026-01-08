import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { useConversationStore } from "./conversation";
// 사용자 메시지는 유지 (중단 시 삭제하지 않음)
import { useUIStore } from "./ui";
import { sendMessageAPI, sendStreamingMessageAPI } from "@/services/searchApi";
import { uploadFileAPI } from "@/services/metaApi";

export const useChatStore = defineStore("chat", () => {
    const conversationStore = useConversationStore();
    const uiStore = useUIStore();

    // 채팅 상태
    const uploadedFiles = ref([]);
    const isLoading = ref(false);
    const isThinking = ref(false);
    const isStreaming = ref(false);
    const streamingContent = ref("");

    // 스트리밍 상태 관리 (DOM 업데이트 없음)
    let currentAssistantMessageId = null;
    let currentAbortController = null;
    let currentUserMessageLocalId = null; // 서버가 실제 ID를 할당하기 전에 로컬에서 생성한 ID
    let currentUserMessageRealId = null; // 메타데이터에서 받은 서버 측 ID (삭제 시 사용 안 함)

    // 메시지 전송 (기본적으로 스트리밍 사용)
    const sendMessage = async (messageData) => {
        // 기본적으로 스트리밍 메시지 전송 사용
        return await sendStreamingMessage(messageData);
    };

    // 스트리밍 메시지 전송
    const sendStreamingMessage = async (messageData) => {
        const {
            content,
            mentionedDepartments = [],
            files = [],
            selectedModel = "gpt-4.1-mini",
        } = messageData;

        // content가 undefined이거나 빈 문자열인 경우 처리
        if ((!content || !content.trim()) && files.length === 0) return;

        // mentionedDepartments를 깊은 복사하여 과거 메시지가 현재 선택 변화에 영향받지 않도록 함
        const finalMentionedDepartments = JSON.parse(
            JSON.stringify(mentionedDepartments)
        );

        // 현재 대화가 없으면 새 대화 생성
        let currentConvId = conversationStore.currentConversationId;
        if (!currentConvId) {
            const newConv = await conversationStore.createNewConversation();
            currentConvId = newConv.id;
        }

        try {
            isLoading.value = true;
            isThinking.value = true;
            isStreaming.value = true;
            streamingContent.value = "";
            // AbortController를 미리 생성하여 stopStreaming이 즉시 중단할 수 있도록 함
            currentAbortController = new AbortController();

            // 파일 업로드 처리
            const uploadedFileData = [];
            if (files.length > 0) {
                for (const file of files) {
                    try {
                        const uploadResult = await uploadFileAPI(file);
                        uploadedFileData.push(uploadResult.data);
                    } catch (error) {
                        uiStore.setError(`파일 업로드 실패: ${file.name}`);
                        console.error("File upload error:", error);
                    }
                }
            }

            // 사용자 메시지 추가 - 고유 ID 생성
            const userMessage = {
                id: `user-${Date.now()}-${Math.random()
                    .toString(36)
                    .substr(2, 9)}`,
                role: "user",
                content,
                files:
                    uploadedFileData.length > 0 ? uploadedFileData : undefined,
                mentionedDepartments: finalMentionedDepartments,
            };

            currentUserMessageLocalId = await conversationStore.addMessage(
                currentConvId,
                userMessage
            );

            // 중단 상태 확인 - 중단된 경우 assistant 메시지를 생성하지 않음
            if (
                currentAbortController &&
                currentAbortController.signal.aborted
            ) {
                // 이미 중단되었으므로 메시지 생성 및 API 호출 스킵
                return;
            }

            // AI 응답 메시지 생성 (스트리밍용) - 고유 ID 생성
            const assistantMessage = {
                id: `assistant-${Date.now()}-${Math.random()
                    .toString(36)
                    .substr(2, 9)}`,
                role: "assistant",
                content: "응답을 생성중입니다...",
                isStreaming: true,
                isThinking: true,
            };

            console.log(
                "🔧 [DEBUG] Creating assistant message:",
                assistantMessage
            );
            const assistantMessageId = await conversationStore.addMessage(
                currentConvId,
                assistantMessage
            );

            // 현재 어시스턴트 메시지 ID 저장
            currentAssistantMessageId = assistantMessageId;

            // assistant 메시지 생성 후 다시 한번 중단 상태 확인
            if (
                currentAbortController &&
                currentAbortController.signal.aborted
            ) {
                // 중단되었으므로 방금 생성한 메시지 제거
                conversationStore.removeMessage(
                    currentConvId,
                    assistantMessageId
                );
                currentAssistantMessageId = null;
                return;
            }

            // API 요청 페이로드
            const payload = {
                conversationId: currentConvId,
                message: content,
                files: uploadedFileData,
                mentionedDepartments: finalMentionedDepartments,
                selectedModel: selectedModel,
            };

            // 스트리밍 API 호출 (fetch + AbortController)
            // Controller는 이미 미리 생성되었으므로 그대로 전달
            await sendStreamingMessageAPI(
                payload,
                (data) => {
                    // 스트리밍 데이터 처리
                    if (data.type === "metadata") {
                        // 메타데이터에서 진짜 사용자 메시지 ID 받기
                        const metaUserId = (data.data && data.data.userMessageId) || data.userMessageId;
                        if (metaUserId) {
                            // 사용자 메시지의 가상 UUID를 진짜 UUID로 교체
                            conversationStore.updateMessage(
                                currentConvId,
                                userMessage.id,
                                {
                                    ...userMessage,
                                    id: metaUserId,
                                    realId: metaUserId,
                                }
                            );
                            currentUserMessageRealId = data.data.userMessageId;
                        }
                    } else if (data.type === "content") {
                        // 첫 번째 콘텐츠가 오면 thinking 상태 종료
                        if (isThinking.value) {
                            isThinking.value = false;
                            // 해당 메시지의 isThinking도 false로 업데이트
                            conversationStore.updateMessage(
                                currentConvId,
                                currentAssistantMessageId,
                                {
                                    isThinking: false,
                                }
                            );
                        }
                        // 스트리밍 콘텐츠 업데이트 (평탄화/래핑 모두 지원)
                        const chunk = (data.data && data.data.content) || data.content || "";
                        streamingContent.value += chunk;
                    } else if (data.type === "done") {
                        console.log("✅ [STREAM] 완료");
                        // 스트리밍 완료 - 최종 내용을 즉시 업데이트
                        isThinking.value = false;
                        const finalContent =
                            (data.data && data.data.final_response) || data.final_response || streamingContent.value;

                        // done 이벤트에 ID가 포함되어 있으면 즉시 교체 (더 안전함)
                        const updateData = {
                            role: "assistant",
                            content: finalContent,
                            isStreaming: false,
                            isThinking: false,
                        };
                        
                        // Include sources if available
                        const sources = (data.data && data.data.sources) || data.sources;
                        if (sources && sources.length > 0) {
                            updateData.sources = sources;
                        }
                        
                        // done 이벤트에 ID가 포함되어 있으면 사용
                        const doneAssistantId = (data.data && data.data.assistantMessageId) || data.assistantMessageId;
                        if (doneAssistantId && currentAssistantMessageId) {
                            updateData.id = doneAssistantId;
                            updateData.realId = doneAssistantId;
                            console.log(`🔄 [STREAM] ID 교체 (done 이벤트에서): ${currentAssistantMessageId} → ${doneAssistantId}`);
                        }
                        
                        conversationStore.updateMessage(
                            currentConvId,
                            assistantMessageId,
                            updateData
                        );

                        // 스트리밍 콘텐츠 초기화
                        streamingContent.value = "";
                        currentAssistantMessageId = null;
                    } else if (data.type === "message_saved") {
                        // 가짜 ID → 진짜 ID 교체 (백워드 호환성)
                        // done 이벤트에 이미 ID가 포함되어 있으면 이건 무시해도 됨
                        const msgSavedAssistantId = (data.data && data.data.assistantMessageId) || data.assistantMessageId;
                        if (msgSavedAssistantId && currentAssistantMessageId) {
                            // 이미 done에서 ID를 교체했는지 확인
                            const conv = conversationStore.conversations.find(
                                (c) => c.id === currentConvId
                            );
                            const message = conv?.messages.find(
                                (m) => m.id === currentAssistantMessageId || m.id === msgSavedAssistantId
                            );
                            
                            // 아직 ID가 교체되지 않았으면 교체
                            if (message && !message.realId) {
                                conversationStore.updateMessage(
                                    currentConvId,
                                    currentAssistantMessageId,
                                    {
                                        id: msgSavedAssistantId,
                                        realId: msgSavedAssistantId,
                                    }
                                );
                                console.log(`🔄 [STREAM] ID 교체 (message_saved 이벤트에서): ${currentAssistantMessageId} → ${msgSavedAssistantId}`);
                            }
                        }
                    }
                },
                (error) => {
                    console.error("Streaming error:", error);
                    uiStore.setError("스트리밍 메시지 전송에 실패했습니다.");

                    // 에러 발생 시 생성된 assistant 메시지 제거
                    if (currentAssistantMessageId) {
                        const conv = conversationStore.conversations.find(
                            (c) => c.id === currentConvId
                        );
                        if (conv) {
                            const messageIndex = conv.messages.findIndex(
                                (m) => m.id === currentAssistantMessageId
                            );
                            if (messageIndex !== -1) {
                                conv.messages.splice(messageIndex, 1);
                            }
                        }
                        currentAssistantMessageId = null;
                    }
                },
                () => {
                    // 완료 처리
                    isStreaming.value = false;
                    streamingContent.value = "";
                    currentAssistantMessageId = null;

                    // 스트리밍 완료 후 토큰 사용량 업데이트
                    try {
                        conversationStore.refreshConversationInfo(
                            currentConvId
                        );
                    } catch (error) {
                        console.error(
                            "Failed to refresh conversation info after streaming:",
                            error
                        );
                    }
                },
                currentAbortController
            );

            // API 호출이 중단되어 아무 내용도 스트리밍되지 않은 경우 assistant 메시지 제거
            if (
                currentAbortController &&
                currentAbortController.signal.aborted
            ) {
                const noContentStreamed =
                    !streamingContent.value ||
                    streamingContent.value.length === 0;
                if (
                    noContentStreamed &&
                    currentAssistantMessageId &&
                    currentConvId
                ) {
                    conversationStore.removeMessage(
                        currentConvId,
                        currentAssistantMessageId
                    );
                    currentAssistantMessageId = null;
                }
            }

            // 업로드된 파일 초기화
            uploadedFiles.value = [];
        } catch (error) {
            console.error("Send streaming message error:", error);
            uiStore.setError("스트리밍 메시지 전송에 실패했습니다.");

            // 에러 발생 시 생성된 assistant 메시지 제거
            if (currentAssistantMessageId) {
                const conv = conversationStore.conversations.find(
                    (c) => c.id === currentConvId
                );
                if (conv) {
                    const messageIndex = conv.messages.findIndex(
                        (m) => m.id === currentAssistantMessageId
                    );
                    if (messageIndex !== -1) {
                        conv.messages.splice(messageIndex, 1);
                    }
                }
                currentAssistantMessageId = null;
            }
        } finally {
            isLoading.value = false;
            isThinking.value = false;
            isStreaming.value = false;
            streamingContent.value = "";
            currentAssistantMessageId = null;
            if (currentAbortController) {
                try {
                    currentAbortController.abort();
                } catch (e) {}
                currentAbortController = null;
            }
            currentUserMessageLocalId = null;
            currentUserMessageRealId = null;
        }
    };

    // 스트리밍 중지
    const stopStreaming = () => {
        try {
            if (currentAbortController) {
                currentAbortController.abort();
                // controller 참조를 유지하여 signal.aborted 상태가 전달되도록 함
                // null로 설정하면 sendStreamingMessageAPI에서 새로운 controller를 생성하여 abort 상태가 손실됨
            }
        } catch (e) {
            console.warn("Failed to abort streaming", e);
        }
        // If no content has streamed yet, remove the just-sent user message
        const noContentStreamedYet =
            !streamingContent.value || streamingContent.value.length === 0;
        const currentConvId = conversationStore.currentConversationId;
        if (noContentStreamedYet && currentConvId) {
            // Remove only the assistant placeholder; keep user message
            if (currentAssistantMessageId) {
                conversationStore.removeMessage(
                    currentConvId,
                    currentAssistantMessageId
                );
            }
            // Keep user message intact both locally and on server
        } else {
            // Update the in-progress assistant message to a final, non-thinking state
            if (currentConvId && currentAssistantMessageId) {
                const finalContent =
                    streamingContent.value || "생성이 중지되었습니다.";
                try {
                    conversationStore.updateMessage(
                        currentConvId,
                        currentAssistantMessageId,
                        {
                            role: "assistant",
                            content: finalContent,
                            isStreaming: false,
                            isThinking: false,
                        }
                    );
                } catch (e) {
                    console.warn(
                        "Failed to update assistant message after stop",
                        e
                    );
                }
            }
        }
        isStreaming.value = false;
        isThinking.value = false;
        streamingContent.value = "";
        currentAssistantMessageId = null;
        currentUserMessageLocalId = null;
        currentUserMessageRealId = null;
    };

    // 파일 추가
    const addFile = (file) => {
        // 파일 유효성 검사 (minimal changes with extension fallback)
        const allowedTypes = [
            "text/plain",
            "application/json",
            "text/markdown",
            "application/x-yaml",
        ];
        const allowedExtensions = [
            ".txt",
            ".md",
            ".py",
            ".js",
            ".ts",
            ".json",
            ".yaml",
            ".yml",
            ".sh",
            ".bash",
            ".java",
        ];
        const maxSize = 10 * 1024 * 1024; // 10MB

        const ext = `.${(file.name.split(".").pop() || "").toLowerCase()}`;
        const mimeOk = file.type ? allowedTypes.includes(file.type) : false;
        const extOk = allowedExtensions.includes(ext);

        if (!(mimeOk || extOk)) {
            uiStore.setError(
                "지원하지 않는 파일 형식입니다. (허용: txt, md, py, js, ts, json, yaml, yml, sh, bash, java)"
            );
            return false;
        }

        if (file.size > maxSize) {
            uiStore.setError("파일 크기는 10MB 이하여야 합니다.");
            return false;
        }

        // 중복 파일 체크
        const isDuplicate = uploadedFiles.value.some(
            (f) => f.name === file.name && f.size === file.size
        );

        if (isDuplicate) {
            uiStore.setError("이미 추가된 파일입니다.");
            return false;
        }

        uploadedFiles.value.push(file);
        return true;
    };

    // 파일 제거
    const removeFile = (index) => {
        uploadedFiles.value.splice(index, 1);
    };

    return {
        isLoading,
        isThinking,
        isStreaming,
        streamingContent,
        uploadedFiles,
        sendMessage,
        sendStreamingMessage,
        stopStreaming,
        addFile,
        removeFile,
    };
});

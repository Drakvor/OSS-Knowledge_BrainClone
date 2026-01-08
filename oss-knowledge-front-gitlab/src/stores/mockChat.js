import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { useConversationStore } from "./conversation";
import { useUIStore } from "./ui";
import { connectOrchestratorStream } from "@/services/orchestratorApi";

export const useMockChatStore = defineStore("mockChat", () => {
    const conversationStore = useConversationStore();
    const uiStore = useUIStore();

    // 채팅 상태
    const isLoading = ref(false);
    const isThinking = ref(false);
    const isStreaming = ref(false);
    const streamingContent = ref("");

    // 시뮬레이션 상태
    const simulationPhase = ref("");
    const currentPhase = ref(0);

    // Todo list state management
    const currentTodoList = ref([]);

    const updateTodoItem = (itemId, completed) => {
        const item = currentTodoList.value.find((t) => t.id === itemId);
        if (item) {
            item.completed = completed;
        }
    };

    // SSE stream controller for cleanup
    let streamController = null;

    // Orchestrator SSE 연결 시작
    const startSimulation = async (messageData) => {
        console.log("Starting orchestrator stream with:", messageData);
        const { content } = messageData;
        if (!content.trim()) {
            console.log("No content provided, skipping");
            return;
        }

        // 현재 대화가 없으면 새 대화 생성 (데모용 가상 대화방)
        let currentConvId = conversationStore.currentConversationId;
        if (!currentConvId) {
            console.log("No current conversation, creating demo one...");
            const newConv = await conversationStore.createNewConversation();
            if (!newConv || !newConv.id) {
                throw new Error("Failed to create demo conversation");
            }
            currentConvId = newConv.id;
            console.log("Demo conversation created:", currentConvId);
        }

        // 이전 스트림이 있으면 중단
        if (streamController) {
            streamController.abort();
        }

        try {
            console.log("Connecting to orchestrator stream...");
            isLoading.value = true;
            isStreaming.value = true;
            currentPhase.value = 0;

            // 사용자 메시지 추가
            const userMessage = {
                id: `user-${Date.now()}-${Math.random()
                    .toString(36)
                    .substr(2, 9)}`,
                role: "user",
                content,
            };

            await conversationStore.addMessage(currentConvId, userMessage);

            // AI 응답 메시지 생성 (컴포넌트 구조로)
            // These variables are used in callbacks, so they need to be defined before the callbacks
            let breakpointComponents = [];
            let currentResponse = "";

            const initialComponents = {
                breakpoints: [],
                currentStatus: "처리 중...",
                isThinking: true,
            };

            const statusMessageId = await conversationStore.addMessage(
                currentConvId,
                {
                    id: `status-${Date.now()}-${Math.random()
                        .toString(36)
                        .substr(2, 9)}`,
                    role: "assistant",
                    content: JSON.stringify(initialComponents),
                    isStreaming: true,
                    isThinking: true,
                }
            );

            if (!statusMessageId) {
                throw new Error("Failed to create status message");
            }

            // Orchestrator SSE 연결
            const payload = {
                message: content,
                session_id: currentConvId,
                user_id: "demo-user", // Demo user ID
                collection: "general",
            };

            const streamResult = await connectOrchestratorStream(
                payload,
                {
                    onIntent: (data) => {
                        console.log("Intent event:", data);
                        simulationPhase.value = `Intent: ${data.intent}`;
                    },
                    onPlanCreated: (data) => {
                        console.log("Plan created event:", data);
                        const tasks = data.tasks || [];

                        // Convert tasks to todo list
                        const todoItems = tasks.map((task) => ({
                            id: task.task_id,
                            text: task.description,
                            completed: false,
                            taskType: task.task_type,
                        }));

                        currentTodoList.value = todoItems;

                        // Add todo list as breakpoint component
                        breakpointComponents.push({
                            id: `todo-${Date.now()}`,
                            isTodoList: true,
                            todoList: todoItems,
                            timestamp: Date.now(),
                        });

                        // Update message
                        updateMessageComponents(
                            currentConvId,
                            statusMessageId,
                            breakpointComponents,
                            "",
                            false,
                            false
                        );
                    },
                    onTaskStatus: (data) => {
                        console.log("Task status event:", data);
                        const { task_id, status, description } = data;

                        if (status === "in_progress") {
                            // Add breakpoint for in-progress task
                            breakpointComponents.push({
                                id: `task-${task_id}`,
                                content: `${description} 중...`,
                                status: getStatusText(description),
                                timestamp: Date.now(),
                            });

                            updateMessageComponents(
                                currentConvId,
                                statusMessageId,
                                breakpointComponents,
                                currentResponse,
                                true,
                                false
                            );
                        } else if (status === "completed") {
                            // Update todo item
                            updateTodoItem(task_id, true);

                            // Update todo list in breakpoint component
                            updateTodoListInBreakpoints(breakpointComponents);

                            updateMessageComponents(
                                currentConvId,
                                statusMessageId,
                                breakpointComponents,
                                currentResponse,
                                true,
                                false
                            );
                        }
                    },
                    onTaskResult: (data) => {
                        console.log("Task result event:", data);
                        const { task_id, content } = data;

                        // Update breakpoint with result
                        const breakpoint = breakpointComponents.find(
                            (b) => b.id === `task-${task_id}`
                        );
                        if (breakpoint) {
                            breakpoint.content = content || breakpoint.content;
                        }

                        updateMessageComponents(
                            currentConvId,
                            statusMessageId,
                            breakpointComponents,
                            currentResponse,
                            true,
                            false
                        );
                    },
                    onResponseChunk: (data) => {
                        console.log("Response chunk event:", data);
                        const { chunk } = data;
                        currentResponse += chunk;
                        streamingContent.value = currentResponse;

                        updateMessageComponents(
                            currentConvId,
                            statusMessageId,
                            breakpointComponents,
                            currentResponse,
                            true,
                            false
                        );
                    },
                    onDone: (data) => {
                        console.log("Done event:", data);
                        isStreaming.value = false;
                        isThinking.value = false;
                        isLoading.value = false; // Fix: Reset isLoading in onDone

                        // Mark all remaining todos as complete
                        currentTodoList.value.forEach((item) => {
                            if (!item.completed) {
                                item.completed = true;
                            }
                        });

                        // Update todo list in breakpoint component
                        updateTodoListInBreakpoints(breakpointComponents);

                        // Final update with complete response
                        const finalComponents = {
                            breakpoints: breakpointComponents,
                            finalResponse: data?.response || currentResponse,
                            isThinking: false,
                        };

                        conversationStore.updateMessage(
                            currentConvId,
                            statusMessageId,
                            {
                                role: "assistant",
                                content: JSON.stringify(finalComponents),
                                isStreaming: false,
                                isThinking: false,
                            }
                        );
                    },
                    onError: (error) => {
                        console.error("Orchestrator stream error:", error);
                        uiStore.setError(`스트림 오류: ${error.message}`);
                        isStreaming.value = false;
                        isThinking.value = false;
                        isLoading.value = false; // Fix: Reset isLoading in onError
                    },
                },
                streamController,
                300000 // 5 minute timeout
            );

            // Store controller from result
            streamController = streamResult.controller;

            // Log completion status
            if (streamResult.done) {
                console.log("Stream completed successfully with 'done' event");
            } else {
                console.warn(
                    "Stream completed but 'done' event was not received - onDone was called anyway to reset UI"
                );
                // Double-check that isLoading is false (safety net)
                if (isLoading.value) {
                    console.warn(
                        "isLoading was still true after stream completion - forcing reset"
                    );
                    isLoading.value = false;
                }
            }
        } catch (error) {
            console.error("Orchestrator stream error:", error);
            uiStore.setError("스트림 연결에 실패했습니다.");
            // Reset all states on error
            isLoading.value = false;
            isThinking.value = false;
            isStreaming.value = false;
        } finally {
            // CRITICAL SAFETY NET: Always ensure isLoading is false
            // This executes after stream completes (due to await)
            // Use nextTick to ensure Vue reactivity updates
            setTimeout(() => {
                if (isLoading.value) {
                    console.warn(
                        "isLoading was still true in finally block - forcing reset"
                    );
                    isLoading.value = false;
                }
                isStreaming.value = false;
                isThinking.value = false;
            }, 0);
        }
    };

    // Helper function to get status text
    const getStatusText = (description) => {
        const desc = description.toLowerCase();
        if (desc.includes("검색")) {
            return "검색 중...";
        } else if (desc.includes("분석")) {
            return "분석 중...";
        } else if (desc.includes("생성")) {
            return "생성 중...";
        }
        return "처리 중...";
    };

    // Helper function to update todo list in breakpoint component
    const updateTodoListInBreakpoints = (breakpointComponents) => {
        const todoComponent = breakpointComponents.find((b) => b.isTodoList);
        if (todoComponent) {
            todoComponent.todoList = [...currentTodoList.value];
        }
    };

    // Helper function to update message components
    const updateMessageComponents = (
        conversationId,
        messageId,
        breakpoints,
        currentResponse,
        isStreamingFlag,
        isThinkingFlag
    ) => {
        const components = {
            breakpoints: breakpoints,
            currentResponse: currentResponse,
            isStreaming: isStreamingFlag,
            isThinking: isThinkingFlag,
        };

        conversationStore.updateMessage(conversationId, messageId, {
            role: "assistant",
            content: JSON.stringify(components),
            isStreaming: isStreamingFlag,
            isThinking: isThinkingFlag,
        });
    };

    // 메시지 전송 (시뮬레이션용)
    const sendMessage = async (messageData) => {
        return await startSimulation(messageData);
    };

    return {
        isLoading,
        isThinking,
        isStreaming,
        streamingContent,
        simulationPhase,
        currentPhase,
        currentTodoList,
        updateTodoItem,
        sendMessage,
    };
});

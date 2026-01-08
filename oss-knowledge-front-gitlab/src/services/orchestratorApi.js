/**
 * Orchestrator API 서비스 모듈
 * Orchestrator 서비스와의 SSE 통신을 담당
 */

// Orchestrator URL
const ORCHESTRATOR_URL =
    import.meta.env.VITE_ORCHESTRATOR_URL || "http://localhost:8000";

// API 헤더 설정
const getHeaders = () => {
    const headers = {
        "Content-Type": "application/json",
    };

    // 인증 토큰 추가
    const token = localStorage.getItem("authToken");
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    return headers;
};

/**
 * Orchestrator SSE 스트림 연결
 * @param {Object} payload - 메시지 정보
 * @param {string} payload.message - 사용자 메시지
 * @param {string} payload.session_id - 세션 ID
 * @param {string} payload.user_id - 사용자 ID
 * @param {string} payload.collection - 컬렉션 (선택)
 * @param {Array} payload.attachments - 첨부 파일 (선택)
 * @param {Object} callbacks - 이벤트 콜백 함수들
 * @param {Function} callbacks.onIntent - Intent 분류 이벤트 콜백
 * @param {Function} callbacks.onPlanCreated - Plan 생성 이벤트 콜백
 * @param {Function} callbacks.onTaskStatus - Task 상태 업데이트 콜백
 * @param {Function} callbacks.onTaskResult - Task 결과 콜백
 * @param {Function} callbacks.onResponseChunk - 응답 청크 콜백
 * @param {Function} callbacks.onDone - 완료 콜백
 * @param {Function} callbacks.onError - 에러 콜백
 * @param {AbortController} abortController - 선택적 AbortController
 * @param {number} timeoutMs - 타임아웃 시간 (밀리초, 기본값: 5분)
 * @returns {Promise<{controller: AbortController, done: boolean}>} Promise that resolves when stream completes
 */
export const connectOrchestratorStream = async (
    payload,
    callbacks = {},
    abortController = null,
    timeoutMs = 300000 // 5 minutes default timeout
) => {
    const controller = abortController || new AbortController();
    let doneEventReceived = false;
    let streamCompleted = false;
    let onDoneCalled = false; // Track if onDone has been called to prevent double calls

    return new Promise((resolve, reject) => {
        // Set up timeout
        const timeoutId = setTimeout(() => {
            if (!streamCompleted) {
                console.warn("Stream timeout - aborting connection");
                controller.abort();
                streamCompleted = true;
                try {
                    callbacks.onError?.(
                        new Error(
                            "Stream timeout - no response received within timeout period"
                        )
                    );
                    callbacks.onDone?.(); // Call onDone even on timeout
                } catch (err) {
                    console.error("Error in timeout callbacks:", err);
                }
                resolve({ controller, done: false });
            }
        }, timeoutMs);

        // Helper to clean up and resolve
        const completeStream = (success = true) => {
            if (streamCompleted) return;
            streamCompleted = true;
            clearTimeout(timeoutId);
            if (success) {
                resolve({ controller, done: doneEventReceived });
            }
        };

        // Start stream processing
        (async () => {
            try {
                // 중단 상태 확인
                if (controller.signal.aborted) {
                    completeStream(true);
                    return;
                }

                const response = await fetch(
                    `${ORCHESTRATOR_URL}/chat/stream`,
                    {
                        method: "POST",
                        headers: getHeaders(),
                        body: JSON.stringify(payload),
                        signal: controller.signal,
                    }
                );

                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(
                        `API Error: ${response.status} - ${errorText}`
                    );
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();

                let buffer = "";

                while (true) {
                    const { done, value } = await reader.read();

                    if (done) {
                        // 마지막 이벤트 처리 - process any remaining buffer
                        if (buffer.trim()) {
                            // Try to process remaining buffer as complete events
                            const remainingLines = buffer.split("\n");
                            for (const line of remainingLines) {
                                if (line.trim() && line.startsWith("data:")) {
                                    const jsonStr = line.substring(5).trim();
                                    if (jsonStr && jsonStr.startsWith("{")) {
                                        try {
                                            const event = JSON.parse(jsonStr);
                                            handleEvent(event);
                                        } catch (parseError) {
                                            console.warn(
                                                "SSE Parse error on final buffer:",
                                                parseError,
                                                jsonStr
                                            );
                                        }
                                    }
                                }
                            }
                            // Also try processing as a complete event block
                            processEvent(buffer.trim());
                        }

                        // ALWAYS call onDone when stream ends to ensure UI state is reset
                        // The done event is just metadata - stream ending is what matters
                        if (!onDoneCalled) {
                            if (!doneEventReceived) {
                                console.warn(
                                    "Stream ended without 'done' event - calling onDone anyway to reset UI"
                                );
                            } else {
                                console.warn(
                                    "Done event was received but onDone wasn't called - calling it now"
                                );
                            }
                            // Call onDone with empty data if done event wasn't received
                            onDoneCalled = true;
                            try {
                                callbacks.onDone?.({});
                            } catch (err) {
                                console.error(
                                    "Error calling onDone callback (stream end):",
                                    err
                                );
                            }
                        } else {
                            console.log(
                                "onDone already called, stream ending normally"
                            );
                        }

                        completeStream(true);
                        break;
                    }

                    // 청크를 버퍼에 추가
                    const chunk = decoder.decode(value, { stream: true });
                    buffer += chunk;

                    // 완전한 이벤트들을 처리 (SSE 형식: data: {json}\n\n)
                    let eventEndIndex;
                    while ((eventEndIndex = buffer.indexOf("\n\n")) !== -1) {
                        const eventText = buffer.substring(0, eventEndIndex);
                        buffer = buffer.substring(eventEndIndex + 2); // '\n\n' 제거

                        processEvent(eventText);
                    }
                }

                // 이벤트 처리 함수
                function processEvent(eventText) {
                    if (!eventText || !eventText.trim()) {
                        return;
                    }

                    // SSE 형식 파싱: data: {json}
                    const lines = eventText.split("\n");
                    for (const line of lines) {
                        if (line.startsWith("data:")) {
                            const jsonStr = line.substring(5).trim();
                            if (!jsonStr || !jsonStr.startsWith("{")) {
                                return;
                            }

                            try {
                                const event = JSON.parse(jsonStr);
                                handleEvent(event);
                            } catch (parseError) {
                                console.warn(
                                    "SSE Parse error:",
                                    parseError,
                                    jsonStr
                                );
                            }
                            break;
                        }
                    }
                }

                // 이벤트 타입별 처리
                function handleEvent(event) {
                    const { type, data } = event;

                    switch (type) {
                        case "intent":
                            callbacks.onIntent?.(data);
                            break;

                        case "plan_created":
                            callbacks.onPlanCreated?.(data);
                            break;

                        case "task_status":
                            callbacks.onTaskStatus?.(data);
                            break;

                        case "task_result":
                            callbacks.onTaskResult?.(data);
                            break;

                        case "response_chunk":
                            callbacks.onResponseChunk?.(data);
                            break;

                        case "done":
                            doneEventReceived = true;
                            console.log(
                                "Done event received in handleEvent, calling onDone callback"
                            );
                            if (!onDoneCalled) {
                                onDoneCalled = true;
                                try {
                                    callbacks.onDone?.(data);
                                } catch (err) {
                                    console.error(
                                        "Error calling onDone callback:",
                                        err
                                    );
                                }
                            } else {
                                console.warn(
                                    "onDone already called, skipping duplicate call"
                                );
                            }
                            // Don't complete stream here - wait for reader to finish
                            break;

                        case "error":
                            callbacks.onError?.(
                                new Error(data?.error || "Unknown error")
                            );
                            // Continue processing - error event doesn't end stream
                            break;

                        default:
                            console.warn("Unknown event type:", type);
                    }
                }
            } catch (error) {
                if (
                    error &&
                    (error.name === "AbortError" || error.code === 20)
                ) {
                    // 사용자에 의해 중단됨
                    try {
                        callbacks.onDone?.();
                    } catch (_) {}
                    completeStream(true);
                    return;
                }
                console.error("Failed to connect orchestrator stream:", error);
                callbacks.onError?.(error);
                // Call onDone even on error to ensure UI state is reset
                try {
                    callbacks.onDone?.();
                } catch (err) {
                    console.error("Error in onDone callback:", err);
                }
                // Don't call completeStream here - reject the promise instead
                if (!streamCompleted) {
                    streamCompleted = true;
                    clearTimeout(timeoutId);
                    reject(error);
                }
            }
        })();
    });
};

/**
 * 비스트리밍 채팅 API (동기)
 * @param {Object} payload - 메시지 정보
 * @returns {Promise<Object>} 응답 데이터
 */
export const sendChatMessageAPI = async (payload) => {
    try {
        const response = await fetch(`${ORCHESTRATOR_URL}/chat`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} - ${errorText}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to send chat message:", error);
        throw error;
    }
};

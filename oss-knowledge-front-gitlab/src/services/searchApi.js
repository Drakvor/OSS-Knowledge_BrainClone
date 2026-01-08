/**
 * Search API 서비스 모듈 (Python Backend)
 * 검색, RAG, 채팅, Graph RAG 관련 기능
 */

// Search Engine 백엔드 URL (Java Backend) - Chat functionality uses Backend
const SEARCH_ENGINE_URL =
    import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

// Search Server URL for other search operations
const SEARCH_SERVER_URL =
    import.meta.env.VITE_SEARCH_API_BASE_URL || "http://localhost:8002";

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

// ===== 채팅/검색 API =====

/**
 * 비스트리밍 메시지 전송 API (기본적으로 스트리밍 사용)
 * @param {Object} payload - 메시지 정보
 * @param {string} payload.message - 사용자 메시지
 * @param {string} payload.conversationId - 대화 ID
 * @param {Array} payload.selectedDepartments - 선택된 부서 목록
 * @param {Object} payload.searchOptions - 검색 옵션
 * @returns {Promise<Object>} 응답 데이터
 */
export const sendMessageAPI = async (payload) => {
    try {
        const response = await fetch(
            `${SEARCH_ENGINE_URL}/chat/search-engine`,
            {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify(payload),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} - ${errorText}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to send message:", error);
        throw error;
    }
};

/**
 * EventSource를 이용한 스트리밍 메시지 전송 API
 * @param {Object} payload - 메시지 정보
 * @param {Function} onMessage - 메시지 수신 콜백
 * @param {Function} onError - 에러 콜백
 * @param {Function} onComplete - 완료 콜백
 * @returns {Promise<void>}
 */
export const sendStreamingMessageWithEventSourceAPI = async (
    payload,
    onMessage,
    onError,
    onComplete
) => {
    try {
        // 먼저 POST 요청으로 스트리밍 시작
        const response = await fetch(
            `${SEARCH_ENGINE_URL}/chat/search-engine?stream=true`,
            {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify(payload),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} - ${errorText}`);
        }

        // 응답 헤더에서 스트림 ID나 URL을 가져올 수 있다면 사용
        const streamUrl = `${SEARCH_ENGINE_URL}/chat/search-engine?stream=true`;

        // EventSource로 연결
        const eventSource = new EventSource(streamUrl);

        eventSource.addEventListener("metadata", function (event) {
            try {
                const data = JSON.parse(event.data);
                onMessage?.(data);
            } catch (e) {
                console.warn("Failed to parse metadata:", e);
            }
        });

        eventSource.addEventListener("content", function (event) {
            try {
                const data = JSON.parse(event.data);
                onMessage?.(data);
            } catch (e) {
                console.warn("Failed to parse content:", e);
            }
        });

        eventSource.addEventListener("done", function (event) {
            try {
                const data = JSON.parse(event.data);
                onMessage?.(data);
            } catch (e) {
                console.warn("Failed to parse done:", e);
            }
            eventSource.close();
            onComplete?.();
        });

        eventSource.addEventListener("error", function (event) {
            try {
                const data = JSON.parse(event.data);
                onError?.(new Error(data.data?.error || "Unknown error"));
            } catch (e) {
                onError?.(new Error("Stream error"));
            }
            eventSource.close();
        });

        eventSource.onerror = function (event) {
            onError?.(new Error("EventSource connection error"));
            eventSource.close();
        };

        // 타임아웃 설정 (60초)
        setTimeout(() => {
            if (eventSource.readyState !== EventSource.CLOSED) {
                eventSource.close();
                onComplete?.();
            }
        }, 60000);

        // Return the EventSource so callers can stop streaming
        return eventSource;
    } catch (error) {
        console.error(
            "Failed to send streaming message with EventSource:",
            error
        );
        onError?.(error);
        throw error;
    }
};

/**
 * 스트리밍 메시지 전송 API (fetch 방식)
 * @param {Object} payload - 메시지 정보
 * @param {Function} onMessage - 메시지 수신 콜백
 * @param {Function} onError - 에러 콜백
 * @param {Function} onComplete - 완료 콜백
 * @returns {Promise<void>}
 */
export const sendStreamingMessageAPI = async (
    payload,
    onMessage,
    onError,
    onComplete,
    abortController // optional AbortController provided by caller
) => {
    try {
        const controller = abortController || new AbortController();
        
        // fetch 시작 전 중단 상태 확인 - 중단된 경우 스트림을 시작하지 않음
        if (controller.signal.aborted) {
            return; // 조기 종료, 스트림이 시작되지 않음
        }
        
        const response = await fetch(
            `${SEARCH_ENGINE_URL}/chat/search-engine?stream=true`,
            {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify(payload),
                signal: controller.signal,
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} - ${errorText}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        let buffer = '';
        let currentEventType = null;
        let currentEventData = [];
        
        while (true) {
            const { done, value } = await reader.read();

            if (done) {
                // 마지막 이벤트 처리
                if (currentEventData.length > 0) {
                    processEvent(currentEventType, currentEventData.join('\n'));
                }
                onComplete?.();
                break;
            }

            // 청크를 버퍼에 추가
            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;

            // 완전한 이벤트들을 처리
            let eventEndIndex;
            while ((eventEndIndex = buffer.indexOf('\n\n')) !== -1) {
                const eventText = buffer.substring(0, eventEndIndex);
                buffer = buffer.substring(eventEndIndex + 2); // '\n\n' 제거
                
                processCompleteEvent(eventText);
            }
        }

        // 완전한 이벤트 처리 함수
        function processCompleteEvent(eventText) {
            const lines = eventText.split('\n');
            let eventType = null;
            let eventData = [];

            for (const line of lines) {
                const trimmedLine = line.trim();
                
                if (trimmedLine.startsWith('event:')) {
                    eventType = line.substring(6).trim();
                } else if (line.startsWith('data:')) {
                    const data = line.substring(5).trim();
                    eventData.push(data);
                } else if (trimmedLine.startsWith(':')) {
                    // 주석 라인 무시
                    continue;
                }
            }

            // 이벤트 데이터가 있으면 처리
            if (eventData.length > 0) {
                processEvent(eventType, eventData.join('\n'));
            }
        }

        // 이벤트 처리 함수
        function processEvent(eventType, eventData) {
            if (!eventData || eventData.trim() === '') {
                return;
            }

            // 비JSON 데이터는 무시
            if (!eventData.trim().startsWith('{')) {
                return;
            }

            try {
                const data = JSON.parse(eventData);
                // ping 이벤트는 무시
                if (data.type === 'ping') {
                    return;
                }
                onMessage?.(data);
            } catch (parseError) {
                console.warn("SSE Parse error:", parseError);
            }
        }
    } catch (error) {
        if (error && (error.name === 'AbortError' || error.code === 20)) {
            // Aborted by user; treat as complete for UI cleanup
            try { onComplete?.(); } catch (_) {}
            return;
        }
        console.error("Failed to send streaming message:", error);
        onError?.(error);
        throw error;
    }
};

/**
 * 문서 검색 API
 * @param {Object} searchParams - 검색 파라미터
 * @param {string} searchParams.query - 검색어
 * @param {Array} searchParams.collections - 검색할 컬렉션 목록
 * @param {number} searchParams.limit - 결과 수 제한
 * @param {number} searchParams.threshold - 유사도 임계값
 * @returns {Promise<Object>} 검색 결과
 */
export const searchDocumentsAPI = async (searchParams) => {
    try {
        const response = await fetch(`${SEARCH_SERVER_URL}/search/documents`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(searchParams),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Search failed: ${response.status} - ${errorText}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to search documents:", error);
        throw error;
    }
};

/**
 * 의미 검색 API
 * @param {Object} searchParams - 검색 파라미터
 * @param {string} searchParams.query - 검색어
 * @param {Array} searchParams.collections - 검색할 컬렉션 목록
 * @param {number} searchParams.topK - 상위 K개 결과
 * @returns {Promise<Object>} 의미 검색 결과
 */
export const semanticSearchAPI = async (searchParams) => {
    try {
        const response = await fetch(`${SEARCH_SERVER_URL}/search/semantic`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(searchParams),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Semantic search failed: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to perform semantic search:", error);
        throw error;
    }
};

/**
 * 하이브리드 검색 API (키워드 + 의미 검색)
 * @param {Object} searchParams - 검색 파라미터
 * @param {string} searchParams.query - 검색어
 * @param {Array} searchParams.collections - 검색할 컬렉션 목록
 * @param {number} searchParams.alpha - 하이브리드 가중치 (0-1)
 * @returns {Promise<Object>} 하이브리드 검색 결과
 */
export const hybridSearchAPI = async (searchParams) => {
    try {
        const response = await fetch(`${SEARCH_SERVER_URL}/search/hybrid`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(searchParams),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Hybrid search failed: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to perform hybrid search:", error);
        throw error;
    }
};

// ===== Graph RAG API =====

/**
 * Graph RAG 노드 목록 조회 API
 * @returns {Promise<Array>} 노드 목록
 */
export const getGraphNodesAPI = async () => {
    try {
        const response = await fetch(`${SEARCH_SERVER_URL}/graph/nodes`, {
            headers: getHeaders(),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to fetch graph nodes:", error);
        throw error;
    }
};

/**
 * Graph RAG 관계 목록 조회 API
 * @returns {Promise<Array>} 관계 목록
 */
export const getGraphEdgesAPI = async () => {
    try {
        const response = await fetch(`${SEARCH_SERVER_URL}/graph/edges`, {
            headers: getHeaders(),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to fetch graph edges:", error);
        throw error;
    }
};

/**
 * Graph RAG 노드 생성 API
 * @param {Object} nodeData - 노드 데이터
 * @param {string} nodeData.name - 노드명
 * @param {string} nodeData.type - 노드 타입
 * @param {Object} nodeData.properties - 노드 속성
 * @returns {Promise<Object>} 생성된 노드 정보
 */
export const createGraphNodeAPI = async (nodeData) => {
    try {
        const response = await fetch(`${SEARCH_SERVER_URL}/graph/nodes`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(nodeData),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} - ${errorText}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to create graph node:", error);
        throw error;
    }
};

/**
 * Graph RAG 노드 수정 API
 * @param {string} nodeId - 노드 ID
 * @param {Object} nodeData - 수정할 노드 데이터
 * @returns {Promise<Object>} 수정된 노드 정보
 */
export const updateGraphNodeAPI = async (nodeId, nodeData) => {
    try {
        const response = await fetch(
            `${SEARCH_SERVER_URL}/graph/nodes/${nodeId}`,
            {
                method: "PUT",
                headers: getHeaders(),
                body: JSON.stringify(nodeData),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} - ${errorText}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to update graph node:", error);
        throw error;
    }
};

/**
 * Graph RAG 노드 삭제 API
 * @param {string} nodeId - 노드 ID
 * @returns {Promise<Object>} 삭제 결과
 */
export const deleteGraphNodeAPI = async (nodeId) => {
    try {
        const response = await fetch(
            `${SEARCH_SERVER_URL}/graph/nodes/${nodeId}`,
            {
                method: "DELETE",
                headers: getHeaders(),
            }
        );

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to delete graph node:", error);
        throw error;
    }
};

/**
 * Graph RAG 관계 생성 API
 * @param {Object} edgeData - 관계 데이터
 * @param {string} edgeData.sourceId - 시작 노드 ID
 * @param {string} edgeData.targetId - 끝 노드 ID
 * @param {string} edgeData.relationship - 관계 타입
 * @param {number} edgeData.strength - 관계 강도
 * @returns {Promise<Object>} 생성된 관계 정보
 */
export const createGraphEdgeAPI = async (edgeData) => {
    try {
        const response = await fetch(`${SEARCH_SERVER_URL}/graph/edges`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(edgeData),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} - ${errorText}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to create graph edge:", error);
        throw error;
    }
};

/**
 * Graph RAG 관계 수정 API
 * @param {string} edgeId - 관계 ID
 * @param {Object} edgeData - 수정할 관계 데이터
 * @returns {Promise<Object>} 수정된 관계 정보
 */
export const updateGraphEdgeAPI = async (edgeId, edgeData) => {
    try {
        const response = await fetch(
            `${SEARCH_SERVER_URL}/graph/edges/${edgeId}`,
            {
                method: "PUT",
                headers: getHeaders(),
                body: JSON.stringify(edgeData),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} - ${errorText}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to update graph edge:", error);
        throw error;
    }
};

/**
 * Graph RAG 관계 삭제 API
 * @param {string} edgeId - 관계 ID
 * @returns {Promise<Object>} 삭제 결과
 */
export const deleteGraphEdgeAPI = async (edgeId) => {
    try {
        const response = await fetch(
            `${SEARCH_SERVER_URL}/graph/edges/${edgeId}`,
            {
                method: "DELETE",
                headers: getHeaders(),
            }
        );

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to delete graph edge:", error);
        throw error;
    }
};

/**
 * Graph RAG 관계 추론 API
 * @param {string} nodeId - 노드 ID
 * @returns {Promise<Object>} 추론된 관계 정보
 */
export const inferGraphRelationsAPI = async (nodeId) => {
    try {
        const response = await fetch(
            `${SEARCH_SERVER_URL}/graph/nodes/${nodeId}/infer-relations`,
            {
                method: "POST",
                headers: getHeaders(),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} - ${errorText}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to infer graph relations:", error);
        throw error;
    }
};

/**
 * Graph RAG 네트워크 분석 API
 * @returns {Promise<Object>} 네트워크 분석 결과
 */
export const analyzeGraphNetworkAPI = async () => {
    try {
        const response = await fetch(`${SEARCH_SERVER_URL}/graph/analyze`, {
            method: "POST",
            headers: getHeaders(),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} - ${errorText}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to analyze graph network:", error);
        throw error;
    }
};

/**
 * Graph RAG 관계 강도 업데이트 API
 * @param {string} edgeId - 관계 ID
 * @param {number} strength - 새로운 강도 값
 * @returns {Promise<Object>} 업데이트 결과
 */
export const updateEdgeStrengthAPI = async (edgeId, strength) => {
    try {
        const response = await fetch(
            `${SEARCH_SERVER_URL}/graph/edges/${edgeId}/strength`,
            {
                method: "PATCH",
                headers: getHeaders(),
                body: JSON.stringify({ strength }),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} - ${errorText}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to update edge strength:", error);
        throw error;
    }
};

/**
 * Graph RAG 노드 위치 업데이트 API
 * @param {string} nodeId - 노드 ID
 * @param {number} x - X 좌표
 * @param {number} y - Y 좌표
 * @returns {Promise<Object>} 업데이트 결과
 */
export const updateNodePositionAPI = async (nodeId, x, y) => {
    try {
        const response = await fetch(
            `${SEARCH_SERVER_URL}/graph/nodes/${nodeId}/position`,
            {
                method: "PATCH",
                headers: getHeaders(),
                body: JSON.stringify({ x, y }),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} - ${errorText}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to update node position:", error);
        throw error;
    }
};

// ===== RAG 쿼리 API =====

/**
 * RAG 질의응답 API
 * @param {Object} queryParams - 질의 파라미터
 * @param {string} queryParams.question - 질문
 * @param {Array} queryParams.collections - 검색할 컬렉션 목록
 * @param {Object} queryParams.ragOptions - RAG 옵션
 * @returns {Promise<Object>} RAG 응답
 */
export const ragQueryAPI = async (queryParams) => {
    try {
        const response = await fetch(`${SEARCH_SERVER_URL}/rag/query`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(queryParams),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `RAG query failed: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to perform RAG query:", error);
        throw error;
    }
};

/**
 * Graph RAG 질의응답 API
 * @param {Object} queryParams - 질의 파라미터
 * @param {string} queryParams.question - 질문
 * @param {Array} queryParams.collections - 검색할 컬렉션 목록
 * @param {Object} queryParams.graphOptions - Graph RAG 옵션
 * @returns {Promise<Object>} Graph RAG 응답
 */
export const graphRagQueryAPI = async (queryParams) => {
    try {
        const response = await fetch(`${SEARCH_SERVER_URL}/rag/graph-query`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(queryParams),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Graph RAG query failed: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to perform Graph RAG query:", error);
        throw error;
    }
};

// ===== 검색 히스토리 API =====

/**
 * 검색 히스토리 조회 API
 * @param {Object} params - 조회 파라미터
 * @param {number} params.limit - 결과 수 제한
 * @param {number} params.offset - 오프셋
 * @returns {Promise<Array>} 검색 히스토리
 */
export const getSearchHistoryAPI = async (params = {}) => {
    try {
        const queryString = new URLSearchParams(params).toString();
        const response = await fetch(
            `${SEARCH_SERVER_URL}/search/history?${queryString}`,
            {
                headers: getHeaders(),
            }
        );

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to get search history:", error);
        throw error;
    }
};

/**
 * 검색 히스토리 삭제 API
 * @param {string} historyId - 히스토리 ID
 * @returns {Promise<Object>} 삭제 결과
 */
export const deleteSearchHistoryAPI = async (historyId) => {
    try {
        const response = await fetch(
            `${SEARCH_SERVER_URL}/search/history/${historyId}`,
            {
                method: "DELETE",
                headers: getHeaders(),
            }
        );

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to delete search history:", error);
        throw error;
    }
};

// ===== 추천 API =====

/**
 * 관련 문서 추천 API
 * @param {Object} params - 추천 파라미터
 * @param {string} params.documentId - 기준 문서 ID
 * @param {Array} params.collections - 검색할 컬렉션 목록
 * @param {number} params.limit - 결과 수 제한
 * @returns {Promise<Array>} 추천 문서 목록
 */
export const getRelatedDocumentsAPI = async (params) => {
    try {
        const response = await fetch(
            `${SEARCH_SERVER_URL}/recommend/documents`,
            {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify(params),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Recommendation failed: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to get related documents:", error);
        throw error;
    }
};

/**
 * 질문 제안 API
 * @param {Object} params - 제안 파라미터
 * @param {string} params.context - 컨텍스트
 * @param {Array} params.collections - 검색할 컬렉션 목록
 * @returns {Promise<Array>} 제안된 질문 목록
 */
export const getSuggestedQuestionsAPI = async (params) => {
    try {
        const response = await fetch(
            `${SEARCH_SERVER_URL}/recommend/questions`,
            {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify(params),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Question suggestion failed: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to get suggested questions:", error);
        throw error;
    }
};

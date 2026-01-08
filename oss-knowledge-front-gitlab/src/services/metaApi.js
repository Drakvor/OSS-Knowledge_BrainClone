/**
 * Meta API 서비스 모듈 (Java Backend)
 * 부서 관리, 사용자 인증, 권한 관리, 대화 관리 등
 */

import { fileToText } from "@/utils/fileHandler";

// API 기본 URL
const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

// JWT 토큰 저장
let authToken = null;

// JWT 토큰 설정
export const setAuthToken = (token) => {
    authToken = token;
};

// JWT 토큰 가져오기
export const getAuthToken = () => {
    return authToken;
};

// API 헤더 설정
const getHeaders = () => {
    const headers = {
        "Content-Type": "application/json",
    };

    // authToken이 없으면 localStorage에서 가져오기
    const token = authToken || localStorage.getItem("authToken");
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    return headers;
};


// ===== 인증 관련 API =====

/**
 * 로그인 API
 * @param {string} username - 사용자명
 * @param {string} password - 비밀번호
 * @returns {Promise<Object>} 인증 정보
 */
export const loginAPI = async (username, password) => {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ username, password }),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Login failed: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        
        // 토큰 저장
        if (data.accessToken) {
            setAuthToken(data.accessToken);
            localStorage.setItem("authToken", data.accessToken);
            if (data.refreshToken) {
                localStorage.setItem("refreshToken", data.refreshToken);
            }
            localStorage.setItem("username", username);
        }

        return data;
    } catch (error) {
        console.error("Login failed:", error);
        throw error;
    }
};

/**
 * 임시 토큰 발급 API (개발용)
 * @param {string} userId - 사용자 ID
 * @returns {Promise<Object>} 토큰 정보
 */
export const getAuthTokenAPI = async (userId = "test-user") => {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/token`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ userId }),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Token generation failed: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        
        // 토큰 저장
        if (data.accessToken) {
            setAuthToken(data.accessToken);
            localStorage.setItem("authToken", data.accessToken);
            localStorage.setItem("username", userId);
        }

        return data;
    } catch (error) {
        console.error("Token generation failed:", error);
        throw error;
    }
};

// ===== 채팅 세션 관리 API =====

/**
 * 채팅 세션 목록 조회 API
 * @param {number} page - 페이지 번호 (0부터 시작)
 * @param {number} size - 페이지 크기
 * @returns {Promise<Object>} 세션 목록 (페이지네이션 포함)
 */
export const getChatSessionsAPI = async (page = 0, size = 20) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/sessions?page=${page}&size=${size}`, {
            headers: getHeaders(),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to fetch chat sessions:", error);
        throw error;
    }
};

/**
 * 최근 채팅 세션 조회 API
 * @param {number} limit - 조회할 개수
 * @returns {Promise<Array>} 최근 세션 목록
 */
export const getRecentChatSessionsAPI = async (limit = 10) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/sessions/recent?limit=${limit}`, {
            headers: getHeaders(),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to fetch recent chat sessions:", error);
        throw error;
    }
};

/**
 * 채팅 세션 상세 조회 API
 * @param {string} sessionId - 세션 ID
 * @returns {Promise<Object>} 세션 상세 정보
 */
export const getChatSessionAPI = async (sessionId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
            headers: getHeaders(),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to fetch chat session:", error);
        throw error;
    }
};

/**
 * 채팅 세션 생성 API
 * @param {Object} sessionData - 세션 정보
 * @returns {Promise<Object>} 생성된 세션 정보
 */
export const createChatSessionAPI = async (sessionData) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/sessions`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(sessionData),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to create chat session:", error);
        throw error;
    }
};

/**
 * 채팅 세션 수정 API
 * @param {string} sessionId - 세션 ID
 * @param {Object} sessionData - 수정할 세션 정보
 * @returns {Promise<Object>} 수정된 세션 정보
 */
export const updateChatSessionAPI = async (sessionId, sessionData) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
            method: "PUT",
            headers: getHeaders(),
            body: JSON.stringify(sessionData),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to update chat session:", error);
        throw error;
    }
};

/**
 * 채팅 세션 삭제 API
 * @param {string} sessionId - 세션 ID
 * @returns {Promise<Object>} 삭제 결과
 */
export const deleteChatSessionAPI = async (sessionId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
            method: "DELETE",
            headers: getHeaders(),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        // DELETE 요청은 보통 빈 응답을 반환하므로 JSON 파싱하지 않음
        return { success: true, status: response.status };
    } catch (error) {
        console.error("Failed to delete chat session:", error);
        throw error;
    }
};

// ===== 채팅 메시지 관리 API =====

/**
 * 채팅 메시지 목록 조회 API
 * @param {string} sessionId - 세션 ID
 * @param {number} page - 페이지 번호
 * @param {number} size - 페이지 크기
 * @returns {Promise<Array>} 메시지 목록
 */
export const getChatMessagesAPI = async (sessionId, page = 0, size = 50) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/messages?page=${page}&size=${size}`, {
            headers: getHeaders(),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to fetch chat messages:", error);
        throw error;
    }
};

/**
 * 채팅 메시지 시간순 조회 API
 * @param {string} sessionId - 세션 ID
 * @returns {Promise<Array>} 시간순 정렬된 메시지 목록
 */
export const getChatMessagesOrderedAPI = async (sessionId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/messages/ordered`, {
            headers: getHeaders(),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to fetch ordered chat messages:", error);
        throw error;
    }
};

/**
 * 채팅 메시지 생성 API
 * @param {string} sessionId - 세션 ID
 * @param {Object} messageData - 메시지 정보
 * @returns {Promise<Object>} 생성된 메시지 정보
 */
export const createChatMessageAPI = async (sessionId, messageData) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/messages`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(messageData),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to create chat message:", error);
        throw error;
    }
};

/**
 * 채팅 메시지 삭제 API
 * @param {string} messageId - 메시지 ID
 * @returns {Promise<void>} 결과 없음 (204)
 */
export const deleteChatMessageAPI = async (messageId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/messages/${messageId}`, {
            method: "DELETE",
            headers: getHeaders(),
        });

        if (response.status === 204) return;
        if (response.status === 404) return; // already gone
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
    } catch (error) {
        console.error("Failed to delete chat message:", error);
        throw error;
    }
};

// ===== 채팅 메시지 피드백 관리 API =====

/**
 * 메시지 피드백 생성 API
 * @param {string} messageId - 메시지 ID
 * @param {Object} feedbackData - 피드백 정보
 * @returns {Promise<Object>} 생성된 피드백 정보
 */
export const createMessageFeedbackAPI = async (messageId, feedbackData) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/messages/${messageId}/feedback`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(feedbackData),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to create message feedback:", error);
        throw error;
    }
};

/**
 * 메시지 피드백 조회 API
 * @param {string} messageId - 메시지 ID
 * @returns {Promise<Array>} 피드백 목록
 */
export const getMessageFeedbacksAPI = async (messageId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/messages/${messageId}/feedback`, {
            headers: getHeaders(),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to fetch message feedbacks:", error);
        throw error;
    }
};

/**
 * 메시지 피드백 통계 조회 API
 * @param {string} messageId - 메시지 ID
 * @returns {Promise<Object>} 피드백 통계 정보
 */
export const getMessageFeedbackStatsAPI = async (messageId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/messages/${messageId}/feedback/stats`, {
            headers: getHeaders(),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to fetch message feedback stats:", error);
        throw error;
    }
};

// ===== 기존 대화 관리 API (하위 호환성) =====

/**
 * 대화 목록 조회 API (기존 호환성)
 * @returns {Promise<Array>} 대화 목록
 */
export const getConversationsAPI = async () => {
    try {
        const sessions = await getRecentChatSessionsAPI(50);
        // 기존 형식으로 변환
        return sessions.map(session => ({
            id: session.id,
            sessionId: session.id,
            title: session.title,
            likes: 0,
            liked: false,
            createdAt: session.createdAt
        }));
    } catch (error) {
        console.error("Failed to fetch conversations:", error);
        throw error;
    }
};

/**
 * 대화 삭제 API (기존 호환성)
 * @param {string} conversationId - 대화 ID
 * @returns {Promise<Object>} 삭제 결과
 */
export const deleteConversationAPI = async (conversationId) => {
    return await deleteChatSessionAPI(conversationId);
};

// ===== RAG 부서 관리 API =====

/**
 * RAG 부서 목록 조회 API
 * @returns {Promise<Array>} 부서 목록
 */
export const getRAGDepartmentsAPI = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/rag-departments`, {
            headers: getHeaders(),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to fetch RAG departments:", error);
        throw error;
    }
};

/**
 * RAG 부서 상세 조회 API
 * @param {string} id - 부서 ID
 * @returns {Promise<Object>} 부서 정보
 */
export const getRAGDepartmentByIdAPI = async (id) => {
    try {
        const response = await fetch(`${API_BASE_URL}/rag-departments/${id}`, {
            headers: getHeaders(),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to fetch RAG department:", error);
        throw error;
    }
};

/**
 * RAG 부서 생성 API
 * @param {Object} departmentData - 부서 정보
 * @returns {Promise<Object>} 생성된 부서 정보
 */
export const createRAGDepartmentAPI = async (departmentData) => {
    try {
        const response = await fetch(`${API_BASE_URL}/rag-departments`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(departmentData),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} - ${errorText}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to create RAG department:", error);
        throw error;
    }
};

/**
 * RAG 부서 수정 API
 * @param {string} id - 부서 ID
 * @param {Object} departmentData - 수정할 부서 정보
 * @returns {Promise<Object>} 수정된 부서 정보
 */
export const updateRAGDepartmentAPI = async (id, departmentData) => {
    try {
        const response = await fetch(`${API_BASE_URL}/rag-departments/${id}`, {
            method: "PUT",
            headers: getHeaders(),
            body: JSON.stringify(departmentData),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} - ${errorText}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to update RAG department:", error);
        throw error;
    }
};

/**
 * RAG 부서 삭제 API
 * @param {string} id - 부서 ID
 * @returns {Promise<Object>} 삭제 결과
 */
export const deleteRAGDepartmentAPI = async (id) => {
    try {
        const response = await fetch(`${API_BASE_URL}/rag-departments/${id}`, {
            method: "DELETE",
            headers: getHeaders(),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to delete RAG department:", error);
        throw error;
    }
};

/**
 * RAG 부서 상태 업데이트 API
 * @param {string} id - 부서 ID
 * @param {string} status - 상태 (active/inactive)
 * @returns {Promise<Object>} 업데이트 결과
 */
export const updateRAGDepartmentStatusAPI = async (id, status) => {
    try {
        const response = await fetch(
            `${API_BASE_URL}/rag-departments/${id}/status`,
            {
                method: "PATCH",
                headers: getHeaders(),
                body: JSON.stringify({ status }),
            }
        );

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to update RAG department status:", error);
        throw error;
    }
};

/**
 * RAG 부서 통계 조회 API
 * @returns {Promise<Object>} 부서 통계 정보
 */
export const getRAGDepartmentStatsAPI = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/rag-departments/stats`, {
            headers: getHeaders(),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to fetch RAG department stats:", error);
        throw error;
    }
};

// ===== 파일 업로드 관리 API =====

/**
 * 파일 업로드 API (일반)
 * @param {File} file - 업로드할 파일
 * @returns {Promise<Object>} 업로드 결과
 */
export const uploadFileAPI = async (file) => {
    try {
        // 텍스트 파일을 UTF-8 문자열로 변환
        const content = await fileToText(file);

        // 파일 확장자로 Content-Type 결정
        const ext = file.name.split('.').pop().toLowerCase();
        const contentTypeMap = {
            'txt': 'text/plain',
            'md': 'text/markdown',
            'py': 'text/x-python',
            'js': 'text/javascript',
            'ts': 'text/typescript',
            'json': 'application/json',
            'yaml': 'text/yaml',
            'yml': 'text/yaml',
            'sh': 'text/x-shellscript',
            'bash': 'text/x-shellscript',
            'java': 'text/x-java-source'
        };
        const contentType = contentTypeMap[ext] || 'text/plain';

        // JSON 페이로드 구성
        const requestBody = {
            filename: file.name,
            content: content,
            contentType: contentType
        };

        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("File upload failed:", error);
        throw error;
    }
};

// ===== 문서 관리 API (PostgreSQL 기반) =====

/**
 * 일반 문서 목록 조회 API
 * @returns {Promise<Array>} 문서 목록
 */
export const getDocumentsAPI = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/documents`, {
            headers: getHeaders(),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to fetch documents:", error);
        throw error;
    }
};


/**
 * 일반 문서 업로드 API
 * @param {Array<File>} files - 업로드할 파일들
 * @returns {Promise<Object>} 업로드 결과
 */
export const uploadDocumentsAPI = async (files) => {
    try {
        // 모든 파일을 변환하여 배열로 구성
        const fileDataArray = await Promise.all(
            files.map(async (file) => {
                // 파일 확장자로 Content-Type 결정
                const ext = file.name.split('.').pop().toLowerCase();
                const contentTypeMap = {
                    'txt': 'text/plain',
                    'md': 'text/markdown',
                    'py': 'text/x-python',
                    'js': 'text/javascript',
                    'ts': 'text/typescript',
                    'json': 'application/json',
                    'yaml': 'text/yaml',
                    'yml': 'text/yaml',
                    'sh': 'text/x-shellscript',
                    'bash': 'text/x-shellscript',
                    'java': 'text/x-java-source'
                };
                const contentType = contentTypeMap[ext] || 'text/plain';

                // 텍스트 파일을 UTF-8 문자열로 변환
                const content = await fileToText(file);

                return {
                    filename: file.name,
                    content: content,
                    contentType: contentType
                };
            })
        );

        // JSON 페이로드 구성
        const requestBody = {
            files: fileDataArray
        };

        const response = await fetch(`${API_BASE_URL}/documents/upload`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Document upload failed:", error);
        throw error;
    }
};

/**
 * 부서별 문서 업로드 API
 * @param {Array<File>} files - 업로드할 파일들
 * @param {string} departmentId - 부서 ID
 * @returns {Promise<Object>} 업로드 결과
 */
export const uploadDepartmentDocumentsAPI = async (files, departmentId) => {
    try {
        // 모든 파일을 변환하여 배열로 구성
        const fileDataArray = await Promise.all(
            files.map(async (file) => {
                // 파일 확장자로 Content-Type 결정
                const ext = file.name.split('.').pop().toLowerCase();
                const contentTypeMap = {
                    'txt': 'text/plain',
                    'md': 'text/markdown',
                    'py': 'text/x-python',
                    'js': 'text/javascript',
                    'ts': 'text/typescript',
                    'json': 'application/json',
                    'yaml': 'text/yaml',
                    'yml': 'text/yaml',
                    'sh': 'text/x-shellscript',
                    'bash': 'text/x-shellscript',
                    'java': 'text/x-java-source'
                };
                const contentType = contentTypeMap[ext] || 'text/plain';

                // 텍스트 파일을 UTF-8 문자열로 변환
                const content = await fileToText(file);

                return {
                    filename: file.name,
                    content: content,
                    contentType: contentType
                };
            })
        );

        // JSON 페이로드 구성
        const requestBody = {
            files: fileDataArray
        };

        const response = await fetch(
            `${API_BASE_URL}/documents/department/${departmentId}/upload`,
            {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify(requestBody),
            }
        );

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Department document upload failed:", error);
        throw error;
    }
};

/**
 * 일반 문서 다운로드 API
 * @param {string} documentId - 문서 ID
 * @returns {Promise<Blob>} 파일 Blob
 */
export const downloadDocumentAPI = async (documentId) => {
    try {
        const response = await fetch(
            `${API_BASE_URL}/documents/${documentId}/download`,
            {
                headers: getHeaders(),
            }
        );

        if (!response.ok) {
            throw new Error(`Download failed: ${response.status}`);
        }

        return await response.blob();
    } catch (error) {
        console.error("Document download failed:", error);
        throw error;
    }
};

/**
 * 부서별 문서 다운로드 API
 * @param {string} documentId - 문서 ID
 * @param {string} departmentId - 부서 ID
 * @returns {Promise<Blob>} 파일 Blob
 */
export const downloadDepartmentDocumentAPI = async (
    documentId,
    departmentId
) => {
    try {
        const response = await fetch(
            `${API_BASE_URL}/documents/department/${departmentId}/${documentId}/download`,
            {
                headers: getHeaders(),
            }
        );

        if (!response.ok) {
            throw new Error(`Download failed: ${response.status}`);
        }

        return await response.blob();
    } catch (error) {
        console.error("Department document download failed:", error);
        throw error;
    }
};

/**
 * 일반 문서 삭제 API
 * @param {string} documentId - 문서 ID
 * @returns {Promise<Object>} 삭제 결과
 */
export const deleteDocumentAPI = async (documentId) => {
    try {
        const response = await fetch(
            `${API_BASE_URL}/documents/${documentId}`,
            {
                method: "DELETE",
                headers: getHeaders(),
            }
        );

        if (!response.ok) {
            throw new Error(`Delete failed: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Document delete failed:", error);
        throw error;
    }
};

/**
 * 부서별 문서 삭제 API
 * @param {string} documentId - 문서 ID
 * @param {string} departmentId - 부서 ID
 * @returns {Promise<Object>} 삭제 결과
 */
export const deleteDepartmentDocumentAPI = async (documentId, departmentId) => {
    try {
        const response = await fetch(
            `${API_BASE_URL}/documents/department/${departmentId}/${documentId}`,
            {
                method: "DELETE",
                headers: getHeaders(),
            }
        );

        if (!response.ok) {
            throw new Error(`Delete failed: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Department document delete failed:", error);
        throw error;
    }
};

// ===== Azure File Share API =====

/**
 * Azure File Share 연결 상태 확인 API
 * @returns {Promise<Object>} 연결 상태
 */
export const checkAzureFileShareConnectionAPI = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/azure/check`, {
            headers: getHeaders(),
        });

        if (!response.ok) {
            throw new Error(`Connection check failed: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to check Azure File Share connection:", error);
        throw error;
    }
};

/**
 * Azure File Share 동기화 API
 * @returns {Promise<Object>} 동기화 결과
 */
export const syncAzureFileShareAPI = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/azure/sync`, {
            method: "POST",
            headers: getHeaders(),
        });

        if (!response.ok) {
            throw new Error(`Sync failed: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to sync Azure File Share:", error);
        throw error;
    }
};

// ===== 시스템 관리 API =====

/**
 * 헬스 체크 API
 * @returns {Promise<Object>} 시스템 상태
 */
export const healthCheckAPI = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/health`, {
            headers: getHeaders(),
        });

        if (!response.ok) {
            throw new Error(`Health check failed: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Health check failed:", error);
        throw error;
    }
};

/**
 * 임베딩 후 문서 추가 API (PostgreSQL)
 * @param {Object} documentData - 문서 정보
 * @param {string} documentData.documentName - 문서명
 * @param {string} documentData.documentPath - 문서 경로
 * @param {string} documentData.fileType - 파일 타입
 * @param {number} documentData.fileSize - 파일 크기
 * @param {string} documentData.container - 컨테이너/부서
 * @param {string} documentData.embeddingStatus - 임베딩 상태
 * @returns {Promise<Object>} 추가 결과
 */
export const addDocumentAfterEmbeddingAPI = async (documentData) => {
    try {
        const response = await fetch(
            `${API_BASE_URL}/documents/add-after-embedding`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(documentData),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Document addition failed: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to add document after embedding:", error);
        throw error;
    }
};

// ===== 채팅 제목 생성 API =====

/**
 * LLM을 사용한 채팅 제목 생성 API
 * @param {string} message - 사용자 메시지
 * @param {string} language - 언어 (기본값: ko)
 * @returns {Promise<Object>} 생성된 제목
 */
export const generateChatTitleAPI = async (message, language = "ko") => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/generate-title`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({
                message: message,
                language: language,
            }),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Title generation failed: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to generate chat title:", error);
        throw error;
    }
};
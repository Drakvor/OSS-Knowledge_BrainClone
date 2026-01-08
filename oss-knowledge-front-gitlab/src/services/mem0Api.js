/**
 * MEM0 API 서비스 모듈
 * 사용자 메모리 관리 기능
 * 현재 Mem0분석중으로 아직 사용중이지 않은 js 파일
 */

// MEM0 백엔드 URL
const MEM0_URL = import.meta.env.VITE_MEM0_API_BASE_URL || "http://localhost:8005";

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

// ===== 메모리 CRUD API =====

/**
 * 메모리 추가 API
 * @param {Object} memoryData - 메모리 정보
 * @param {string} memoryData.message - 메시지
 * @param {string} memoryData.user_id - 사용자 ID
 * @param {Object} memoryData.metadata - 메타데이터
 * @returns {Promise<Object>} 추가 결과
 */
export const addMemoryAPI = async (memoryData) => {
    try {
        const response = await fetch(`${MEM0_URL}/memory/add`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(memoryData),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} - ${errorText}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to add memory:", error);
        throw error;
    }
};

/**
 * 사용자 메모리 전체 조회 API
 * @param {string} userId - 사용자 ID
 * @returns {Promise<Array>} 메모리 목록
 */
export const getMemoriesAPI = async (userId) => {
    try {
        const response = await fetch(`${MEM0_URL}/memory/get/${userId}`, {
            headers: getHeaders(),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        return data.memories || [];
    } catch (error) {
        console.error("Failed to get memories:", error);
        throw error;
    }
};

/**
 * 메모리 검색 API
 * @param {Object} searchParams - 검색 파라미터
 * @param {string} searchParams.query - 검색어
 * @param {string} searchParams.user_id - 사용자 ID
 * @returns {Promise<Array>} 검색 결과
 */
export const searchMemoriesAPI = async (searchParams) => {
    try {
        const response = await fetch(`${MEM0_URL}/memory/search`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(searchParams),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        return data.results || [];
    } catch (error) {
        console.error("Failed to search memories:", error);
        throw error;
    }
};

/**
 * 메모리 삭제 API (만약 있다면)
 * @param {string} memoryId - 메모리 ID
 * @returns {Promise<Object>} 삭제 결과
 */
export const deleteMemoryAPI = async (memoryId) => {
    try {
        const response = await fetch(`${MEM0_URL}/memory/${memoryId}`, {
            method: "DELETE",
            headers: getHeaders(),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to delete memory:", error);
        throw error;
    }
};

// ===== 통계 API =====

/**
 * 메모리 통계 조회 API
 * @param {string} userId - 사용자 ID
 * @returns {Promise<Object>} 통계 정보
 */
export const getMemoryStatsAPI = async (userId) => {
    try {
        const memories = await getMemoriesAPI(userId);
        
        // 통계 계산
        const stats = {
            total: memories.length,
            preferences: memories.filter(m => m.type === 'preference').length,
            patterns: memories.filter(m => m.type === 'pattern').length,
            context: memories.filter(m => m.type === 'context').length,
            history: memories.filter(m => m.type === 'history').length
        };
        
        return stats;
    } catch (error) {
        console.error("Failed to get memory stats:", error);
        throw error;
    }
};

// ===== 편의 함수 =====

/**
 * 사용자 선호도 조회
 * @param {string} userId - 사용자 ID
 * @returns {Promise<Array>} 선호도 목록
 */
export const getUserPreferencesAPI = async (userId) => {
    try {
        const searchParams = {
            query: "user preferences collections favorite",
            user_id: userId
        };
        return await searchMemoriesAPI(searchParams);
    } catch (error) {
        console.error("Failed to get user preferences:", error);
        throw error;
    }
};

/**
 * 검색 패턴 조회
 * @param {string} userId - 사용자 ID
 * @returns {Promise<Array>} 패턴 목록
 */
export const getUserPatternsAPI = async (userId) => {
    try {
        const searchParams = {
            query: "search patterns timing frequency",
            user_id: userId
        };
        return await searchMemoriesAPI(searchParams);
    } catch (error) {
        console.error("Failed to get user patterns:", error);
        throw error;
    }
};


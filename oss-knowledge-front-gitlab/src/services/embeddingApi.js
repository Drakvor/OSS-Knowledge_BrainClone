/**
 * Embedding API 서비스 모듈 (Python Backend)
 * 문서 처리, 임베딩, 청킹, 벡터 저장 등
 */

import { fileToBase64, fileToText } from "@/utils/fileHandler";

// 임베딩 백엔드 URL
const EMBEDDING_BACKEND_URL =
    import.meta.env.VITE_EMBEDDING_API_BASE_URL || "http://localhost:8000";

// API 헤더 설정
const getHeaders = () => {
    return {
        "Content-Type": "application/json",
    };
};

// Note: FormData 헤더는 더 이상 사용하지 않음 - 모든 파일 업로드는 JSON으로 전환됨

// ===== 문서 처리 API =====

/**
 * Excel 파일 처리 API
 * @param {File} file - 처리할 Excel 파일
 * @param {string} container - 컨테이너명 (기본: "general")
 * @param {Object} options - 처리 옵션
 * @param {boolean} options.generateEmbeddings - 임베딩 생성 여부
 * @param {string} options.chunkingStrategy - 청킹 전략
 * @returns {Promise<Object>} 처리 결과
 */
export const processExcelFileAPI = async (
    file,
    container = "general",
    options = {}
) => {
    try {
        // Excel 파일을 Base64로 변환
        const contentBase64 = await fileToBase64(file);

        // JSON 페이로드 구성
        const requestBody = {
            filename: file.name,
            content_base64: contentBase64,
            container: container,
            ...options,
        };

        const response = await fetch(`${EMBEDDING_BACKEND_URL}/process/excel`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Excel processing failed: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to process Excel file:", error);
        throw error;
    }
};

/**
 * Markdown 파일 처리 API
 * @param {File} file - 처리할 Markdown 파일
 * @param {string} container - 컨테이너명 (기본: "general")
 * @param {Object} options - 처리 옵션
 * @param {boolean} options.generateEmbeddings - 임베딩 생성 여부
 * @param {string} options.chunkingStrategy - 청킹 전략
 * @returns {Promise<Object>} 처리 결과
 */
export const processMarkdownFileAPI = async (
    file,
    container = "general",
    options = {}
) => {
    try {
        // Markdown 파일을 UTF-8 텍스트로 변환
        const content = await fileToText(file);

        // JSON 페이로드 구성
        const requestBody = {
            filename: file.name,
            content: content,
            container: container,
            ...options,
        };

        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/process/markdown`,
            {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify(requestBody),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Markdown processing failed: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to process Markdown file:", error);
        throw error;
    }
};

/**
 * Markdown 청킹 미리보기 API
 * @param {File} file - 미리보기할 Markdown 파일
 * @param {string} container - 컨테이너명 (기본: "general")
 * @param {Object} options - 청킹 옵션
 * @param {string} options.chunkingStrategy - 청킹 전략
 * @param {number} options.chunkSize - 청크 크기
 * @param {number} options.overlap - 중복 크기
 * @returns {Promise<Object>} 청킹 미리보기 결과
 */
export const previewMarkdownChunkingAPI = async (
    file,
    container = "general",
    options = {}
) => {
    try {
        // Markdown 파일을 UTF-8 텍스트로 변환
        const content = await fileToText(file);

        // JSON 페이로드 구성
        const requestBody = {
            filename: file.name,
            content: content,
            container: container,
            ...options,
        };

        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/process/markdown/preview`,
            {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify(requestBody),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Markdown chunking preview failed: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to preview Markdown chunking:", error);
        throw error;
    }
};

/**
 * Markdown 최종 처리 확인 API (사용자 편집 청크)
 * @param {Object} requestData - 처리 요청 데이터
 * @param {string} requestData.filename - 파일명
 * @param {number} requestData.fileSize - 파일 크기
 * @param {string} requestData.container - 컨테이너명
 * @param {Array} requestData.chunks - 청크 배열
 * @param {boolean} requestData.generateEmbeddings - 임베딩 생성 여부
 * @param {string} requestData.embeddingModel - 임베딩 모델명
 * @returns {Promise<Object>} 처리 결과
 */
export const confirmMarkdownProcessingAPI = async (requestData) => {
    try {
        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/process/markdown/confirm`,
            {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify(requestData),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Markdown processing confirmation failed: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to confirm Markdown processing:", error);
        throw error;
    }
};

// ===== 청킹 관련 API =====

/**
 * 문서 청킹 API (일반)
 * @param {string} documentId - 문서 ID
 * @param {Object} chunkingSettings - 청킹 설정
 * @returns {Promise<Object>} 청킹 결과
 */
export const chunkDocumentAPI = async (documentId, chunkingSettings) => {
    try {
        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/chunk/document/${documentId}`,
            {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify(chunkingSettings),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Document chunking failed: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to chunk document:", error);
        throw error;
    }
};

/**
 * 부서별 문서 청킹 API
 * @param {string} documentId - 문서 ID
 * @param {string} departmentId - 부서 ID
 * @param {Object} chunkingSettings - 청킹 설정
 * @returns {Promise<Object>} 청킹 결과
 */
export const chunkDepartmentDocumentAPI = async (
    documentId,
    departmentId,
    chunkingSettings
) => {
    try {
        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/chunk/department/${departmentId}/document/${documentId}`,
            {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify(chunkingSettings),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Department document chunking failed: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to chunk department document:", error);
        throw error;
    }
};

/**
 * 청킹 설정 유효성 검사 API
 * @param {Object} chunkingSettings - 청킹 설정
 * @returns {Promise<Object>} 유효성 검사 결과
 */
export const validateChunkingSettingsAPI = async (chunkingSettings) => {
    try {
        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/chunk/validate-settings`,
            {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify(chunkingSettings),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Chunking settings validation failed: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to validate chunking settings:", error);
        throw error;
    }
};

/**
 * 청크 품질 분석 API
 * @param {Array} chunks - 분석할 청크 배열
 * @returns {Promise<Object>} 품질 분석 결과
 */
export const analyzeChunkQualityAPI = async (chunks) => {
    try {
        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/chunk/analyze-quality`,
            {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify({ chunks }),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Chunk quality analysis failed: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to analyze chunk quality:", error);
        throw error;
    }
};

// ===== 임베딩 관련 API =====

/**
 * 청크 임베딩 API
 * @param {Array} chunks - 임베딩할 청크 배열
 * @param {string} departmentId - 부서 ID (선택적)
 * @returns {Promise<Object>} 임베딩 결과
 */
export const embedChunksAPI = async (chunks, departmentId = null) => {
    try {
        const requestBody = {
            chunks,
            departmentId,
        };

        const response = await fetch(`${EMBEDDING_BACKEND_URL}/embed/chunks`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Chunk embedding failed: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to embed chunks:", error);
        throw error;
    }
};

// ===== 작업 상태 관리 API =====

/**
 * 처리 작업 상태 조회 API
 * @param {string} jobId - 작업 ID
 * @returns {Promise<Object>} 작업 상태
 */
export const getProcessingStatusAPI = async (jobId) => {
    try {
        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/status/${jobId}`,
            {
                headers: getHeaders(),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Failed to get processing status: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to get processing status:", error);
        throw error;
    }
};

// ===== 시스템 정보 API =====

/**
 * 사용 가능한 컨테이너 목록 조회 API
 * @returns {Promise<Array>} 컨테이너 목록
 */
export const getAvailableContainersAPI = async () => {
    try {
        const response = await fetch(`${EMBEDDING_BACKEND_URL}/containers`, {
            headers: getHeaders(),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Failed to get available containers: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to get available containers:", error);
        throw error;
    }
};

/**
 * 처리 기능 정보 조회 API
 * @returns {Promise<Object>} 처리 기능 정보
 */
export const getProcessingCapabilitiesAPI = async () => {
    try {
        const response = await fetch(`${EMBEDDING_BACKEND_URL}/capabilities`, {
            headers: getHeaders(),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Failed to get processing capabilities: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to get processing capabilities:", error);
        throw error;
    }
};

// ===== Qdrant 관리 API =====

/**
 * Qdrant 컬렉션 목록 조회 API
 * @returns {Promise<Array>} 컬렉션 목록
 */
export const getQdrantCollectionsAPI = async () => {
    try {
        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/qdrant/collections`,
            {
                headers: getHeaders(),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Failed to get Qdrant collections: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to get Qdrant collections:", error);
        throw error;
    }
};

/**
 * Qdrant 컬렉션 정보 조회 API
 * @param {string} collectionName - 컬렉션명
 * @returns {Promise<Object>} 컬렉션 정보
 */
export const getQdrantCollectionInfoAPI = async (collectionName) => {
    try {
        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/qdrant/collections/${encodeURIComponent(collectionName)}/info`,
            {
                headers: getHeaders(),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Failed to get Qdrant collection info: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to get Qdrant collection info:", error);
        throw error;
    }
};

/**
 * 문서의 청크 목록 조회 API
 * @param {string} collectionName - 컬렉션명
 * @param {string} documentName - 문서명
 * @param {number} limit - 조회할 청크 수 (기본값: 100)
 * @returns {Promise<Array>} 청크 목록
 */
export const getDocumentChunksAPI = async (
    collectionName,
    documentName,
    limit = 100
) => {
    try {
        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/qdrant/collections/${encodeURIComponent(collectionName)}/chunks`,
            {
                method: "POST",
                headers: {
                    ...getHeaders(),
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    document_name: documentName,
                    limit: limit,
                }),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Failed to get document chunks: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to get document chunks:", error);
        throw error;
    }
};

/**
 * 문서 삭제 API
 * @param {string} collectionName - 컬렉션명
 * @param {string} documentName - 문서명
 * @returns {Promise<Object>} 삭제 결과
 */
export const deleteDocumentAPI = async (collectionName, documentName) => {
    try {
        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/qdrant/collections/${encodeURIComponent(collectionName)}/documents/${encodeURIComponent(
                documentName
            )}`,
            {
                method: "DELETE",
                headers: getHeaders(),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Failed to delete document: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to delete document:", error);
        throw error;
    }
};

/**
 * 컬렉션의 벡터 수 조회 API
 * @param {string} collectionName - 컬렉션명
 * @returns {Promise<Object>} 벡터 수 정보
 */
export const getCollectionVectorCountAPI = async (collectionName) => {
    try {
        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/qdrant/collections/${encodeURIComponent(collectionName)}/count`,
            {
                headers: getHeaders(),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Failed to get collection vector count: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to get collection vector count:", error);
        throw error;
    }
};

/**
 * 컬렉션의 디스크 사용량 조회 API
 * @param {string} collectionName - 컬렉션명
 * @returns {Promise<Object>} 디스크 사용량 정보
 */
export const getCollectionDiskUsageAPI = async (collectionName) => {
    try {
        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/qdrant/collections/${encodeURIComponent(collectionName)}/disk-usage`,
            {
                headers: getHeaders(),
            }
        );

        if (!response.ok) {
            // 디스크 사용량 API가 없는 경우 기본값 반환
            console.warn(
                `Disk usage API not available for ${collectionName}, returning default values`
            );
            return {
                collection_name: collectionName,
                disk_usage_mb: 0,
                estimated_size: "N/A",
            };
        }

        return await response.json();
    } catch (error) {
        console.warn(
            "Failed to get collection disk usage, returning default values:",
            error
        );
        // 에러를 던지지 않고 기본값 반환
        return {
            collection_name: collectionName,
            disk_usage_mb: 0,
            estimated_size: "N/A",
        };
    }
};

/**
 * 컬렉션 생성 API
 * @param {string} departmentName - 부서명 (컬렉션명으로 사용)
 * @returns {Promise<Object>} 생성 결과
 */
export const createCollectionAPI = async (departmentName) => {
    try {
        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/qdrant/collections`,
            {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify({ name: departmentName }),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Failed to create collection: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to create collection:", error);
        throw error;
    }
};

/**
 * 컬렉션 삭제 API
 * @param {string} departmentName - 부서명 (컬렉션명)
 * @returns {Promise<Object>} 삭제 결과
 */
export const deleteCollectionAPI = async (departmentName) => {
    try {
        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/qdrant/collections/${encodeURIComponent(departmentName)}`,
            {
                method: "DELETE",
                headers: getHeaders(),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Failed to delete collection: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to delete collection:", error);
        throw error;
    }
};

/**
 * 모든 컬렉션 목록 조회 API
 * @returns {Promise<Array>} 컬렉션 목록
 */
export const listCollectionsAPI = async () => {
    try {
        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/qdrant/collections/list`,
            {
                headers: getHeaders(),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Failed to list collections: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to list collections:", error);
        throw error;
    }
};

/**
 * 특정 컬렉션 정보 조회 API
 * @param {string} departmentName - 부서명 (컬렉션명)
 * @returns {Promise<Object>} 컬렉션 정보
 */
export const getCollectionInfoAPI = async (departmentName) => {
    try {
        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/qdrant/collections/${encodeURIComponent(departmentName)}/info`,
            {
                headers: getHeaders(),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Failed to get collection info: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to get collection info:", error);
        throw error;
    }
};

/**
 * 컬렉션의 모든 문서 목록 조회 API
 * @param {string} collectionName - 컬렉션명
 * @returns {Promise<Object>} 문서 목록
 */
export const getCollectionDocumentsAPI = async (collectionName) => {
    try {
        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/qdrant/collections/${encodeURIComponent(collectionName)}/documents`,
            {
                headers: getHeaders(),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Failed to get collection documents: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to get collection documents:", error);
        throw error;
    }
};

// ===== 유틸리티 함수 =====

/**
 * 부서명을 컬렉션명으로 변환하는 함수
 * @param {string} departmentName - 부서명
 * @returns {string} 컬렉션명
 */
export const getCollectionNameForDepartment = (departmentName) => {
    // 특수문자만 제거하고 대소문자 유지, 공백은 그대로 유지
    return departmentName.replace(/[^a-zA-Z0-9가-힣 ]/g, "_");
};

// ===== 테스트 API =====

/**
 * 스트리밍 테스트 API
 * @returns {Promise<Object>} 테스트 결과
 */
export const testStreamingAPI = async () => {
    try {
        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/test/streaming`,
            {
                headers: getHeaders(),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Streaming test failed: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Streaming test failed:", error);
        throw error;
    }
};

/**
 * LLM 청킹 제안 API
 * @param {File} file - 분석할 마크다운 파일
 * @param {string} container - 컨테이너명 (기본: "general")
 * @returns {Promise<Object>} LLM이 제안한 청크 목록
 */
export const getLLMChunkingSuggestionsAPI = async (
    file,
    container = "general"
) => {
    try {
        // Markdown 파일을 UTF-8 텍스트로 변환
        const content = await fileToText(file);

        // JSON 페이로드 구성
        const requestBody = {
            filename: file.name,
            content: content,
            container: container,
        };

        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/process/markdown/llm-suggest`,
            {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify(requestBody),
            }
        );

        if (!response.ok) {
            if (response.status === 413) {
                throw new Error(
                    "파일이 너무 큽니다. 1MB 이하의 파일만 LLM 분석이 가능합니다."
                );
            }
            const errorText = await response.text();
            throw new Error(
                `LLM 청킹 제안을 가져오는데 실패했습니다: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to get LLM chunking suggestions:", error);
        throw error;
    }
};

/**
 * Excel 청킹 미리보기 API
 * @param {File} file - 미리보기할 Excel 파일
 * @param {string} container - 컨테이너명 (기본: "general")
 * @param {Object} options - 청킹 옵션
 * @param {string} options.chunking_strategy - 청킹 전략
 * @param {number} options.chunk_size - 청크 크기
 * @param {number} options.overlap - 중복 크기
 * @returns {Promise<Object>} 청킹 미리보기 결과
 */
export const previewExcelChunkingAPI = async (
    file,
    container = "general",
    options = {}
) => {
    try {
        // Excel 파일을 Base64로 변환
        const contentBase64 = await fileToBase64(file);

        // JSON 페이로드 구성
        const requestBody = {
            filename: file.name,
            content_base64: contentBase64,
            container: container,
            ...options,
        };

        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/process/excel/preview`,
            {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify(requestBody),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Excel chunking preview failed: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to preview Excel chunking:", error);
        throw error;
    }
};

/**
 * Excel LLM 청킹 제안 API
 * @param {File} file - 분석할 Excel 파일
 * @param {string} container - 컨테이너명 (기본: "general")
 * @returns {Promise<Object>} LLM 제안 결과
 */
export const suggestExcelLLMChunkingAPI = async (
    file,
    container = "general"
) => {
    try {
        // Excel 파일을 Base64로 변환
        const contentBase64 = await fileToBase64(file);

        // JSON 페이로드 구성
        const requestBody = {
            filename: file.name,
            content_base64: contentBase64,
            container: container,
        };

        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/process/excel/llm-suggest`,
            {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify(requestBody),
            }
        );

        if (!response.ok) {
            if (response.status === 413) {
                throw new Error(
                    "파일이 너무 큽니다. 10MB 이하의 파일만 LLM 분석이 가능합니다."
                );
            }
            const errorText = await response.text();
            throw new Error(
                `Excel LLM chunking suggestions failed: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to get Excel LLM chunking suggestions:", error);
        throw error;
    }
};

/**
 * Excel 최종 처리 확인 API (사용자 편집 청크)
 * @param {Object} requestData - 처리 요청 데이터
 * @param {string} requestData.filename - 파일명
 * @param {string} requestData.container - 컨테이너명
 * @param {Array} requestData.chunks - 청크 배열
 * @param {boolean} requestData.generateEmbeddings - 임베딩 생성 여부
 * @param {string} requestData.embeddingModel - 임베딩 모델명
 * @returns {Promise<Object>} 처리 결과
 */
export const confirmExcelProcessingAPI = async (requestData) => {
    try {
        const response = await fetch(
            `${EMBEDDING_BACKEND_URL}/process/excel/confirm`,
            {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify(requestData),
            }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Excel processing confirmation failed: ${response.status} - ${errorText}`
            );
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to confirm Excel processing:", error);
        throw error;
    }
};

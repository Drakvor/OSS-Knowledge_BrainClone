import { defineStore } from "pinia";
import { ref } from "vue";
// Meta API - Azure File Share 관련
import {
    checkAzureFileShareConnectionAPI,
    syncAzureFileShareAPI,
} from "@/services/metaApi";

// Embedding API - 임베딩 백엔드
import {
    processExcelFileAPI,
    processMarkdownFileAPI,
    previewMarkdownChunkingAPI,
    previewExcelChunkingAPI,
    confirmMarkdownProcessingAPI,
    confirmExcelProcessingAPI,
    getProcessingStatusAPI,
    getAvailableContainersAPI,
    getProcessingCapabilitiesAPI,
    getLLMChunkingSuggestionsAPI,
    suggestExcelLLMChunkingAPI,
} from "@/services/embeddingApi";

export const useDataUploadStore = defineStore("dataUpload", () => {
    // 상태
    const documents = ref([]);
    const isLoading = ref(false);
    const isSyncing = ref(false);
    const error = ref(null);
    const azureConnectionStatus = ref(null);

    // 문서 목록 가져오기
    const fetchDocuments = async () => {
        isLoading.value = true;
        error.value = null;

        try {
            // Qdrant에서 문서 목록 조회 (임시로 더미 데이터 사용)
            // TODO: Qdrant API로 문서 목록 조회 구현
        } catch (err) {
            error.value = err.message;
            // 개발 중에는 더미 데이터 사용
            const dummyData = [
                {
                    id: "1",
                    name: "OSS-Knowledge-Guide.pdf",
                    size: 1024000,
                    status: "processed",
                    uploadedAt: new Date().toISOString(),
                },
                {
                    id: "2",
                    name: "User-Manual.docx",
                    size: 2048000,
                    status: "processing",
                    uploadedAt: new Date(Date.now() - 3600000).toISOString(),
                },
                {
                    id: "3",
                    name: "API-Documentation.pdf",
                    size: 1536000,
                    status: "processed",
                    uploadedAt: new Date(Date.now() - 7200000).toISOString(),
                },
                {
                    id: "4",
                    name: "Troubleshooting-Guide.pdf",
                    size: 3072000,
                    status: "processed",
                    uploadedAt: new Date(Date.now() - 10800000).toISOString(),
                },
            ];

            documents.value = dummyData;

            // 백엔드 연결 실패 시에도 에러를 던지지 않고 계속 진행
            console.log(
                "백엔드 연결 실패, 더미 데이터로 계속 진행:",
                err.message
            );
        } finally {
            isLoading.value = false;
        }
    };

    // 파일 업로드
    const uploadFiles = async (files) => {
        isLoading.value = true;
        error.value = null;

        try {
            // 파일 업로드 - Qdrant에서만 관리
            // TODO: Qdrant API로 파일 업로드 구현

            // 업로드된 파일들을 문서 목록에 추가
            const newDocuments = files.map((file, index) => ({
                id: Date.now() + index,
                name: file.name,
                size: file.size,
                status: "processing",
                uploadedAt: new Date().toISOString(),
            }));

            documents.value.unshift(...newDocuments);

            return { success: true, uploadedFiles: files.length };
        } catch (err) {
            error.value = err.message;
            throw err;
        } finally {
            isLoading.value = false;
        }
    };

    // 문서 다운로드
    const downloadDocument = async (documentId, departmentId) => {
        try {
            // This function is kept for compatibility but the actual download
            // logic is now handled directly in the Vue components using the document object
            // which has the download_url in its metadata
            throw new Error("다운로드는 문서 객체에서 직접 처리됩니다.");
        } catch (err) {
            error.value = err.message;
            throw err;
        }
    };

    // 문서 삭제
    const deleteDocument = async (id) => {
        isLoading.value = true;
        error.value = null;

        try {
            // Qdrant에서 문서 삭제
            // TODO: Qdrant API로 문서 삭제 구현
            documents.value = documents.value.filter((doc) => doc.id !== id);
        } catch (err) {
            error.value = err.message;
            // 개발 중에는 로컬에서만 제거
            documents.value = documents.value.filter((doc) => doc.id !== id);
            throw err;
        } finally {
            isLoading.value = false;
        }
    };

    // 문서 상태 업데이트
    const updateDocumentStatus = (id, status) => {
        const doc = documents.value.find((d) => d.id === id);
        if (doc) {
            doc.status = status;
        }
    };

    // 모든 문서 가져오기
    const getAllDocuments = () => {
        try {
            return [...(documents.value || [])];
        } catch (error) {
            console.log("모든 문서 조회 중 오류, 빈 배열 반환:", error.message);
            return [];
        }
    };

    // Azure File Share 연결 상태 확인
    const checkAzureConnection = async () => {
        try {
            const response = await checkAzureFileShareConnectionAPI();
            azureConnectionStatus.value = response;
            return response;
        } catch (err) {
            error.value = err.message;
            throw err;
        }
    };

    // Azure File Share 동기화
    const syncAzureFileShare = async () => {
        isSyncing.value = true;
        error.value = null;

        try {
            const response = await syncAzureFileShareAPI();
            // 동기화 후 문서 목록 새로고침
            await fetchDocuments();
            return response;
        } catch (err) {
            error.value = err.message;
            throw err;
        } finally {
            isSyncing.value = false;
        }
    };

    // ===== 임베딩 백엔드 연동 함수들 =====

    // Excel 파일 처리
    const processExcelFile = async (
        file,
        container = "general",
        options = {}
    ) => {
        isLoading.value = true;
        error.value = null;

        try {
            const result = await processExcelFileAPI(file, container, options);

            // 처리 완료 후 문서 목록에 추가
            const newDocument = {
                id: result.job_id,
                name: file.name,
                size: file.size,
                status: "processed",
                uploadedAt: new Date().toISOString(),
                container: container,
                type: "excel",
                jobId: result.job_id,
            };

            documents.value.unshift(newDocument);

            // 임베딩 성공 - Qdrant에서만 관리
            console.log("✅ Document embedded successfully in Qdrant");

            return result;
        } catch (err) {
            error.value = err.message;
            throw err;
        } finally {
            isLoading.value = false;
        }
    };

    // Markdown 파일 처리
    const processMarkdownFile = async (
        file,
        container = "general",
        options = {}
    ) => {
        isLoading.value = true;
        error.value = null;

        try {
            const result = await processMarkdownFileAPI(
                file,
                container,
                options
            );

            // 처리 완료 후 문서 목록에 추가
            const newDocument = {
                id: result.job_id,
                name: file.name,
                size: file.size,
                status: "processed",
                uploadedAt: new Date().toISOString(),
                container: container,
                type: "markdown",
                jobId: result.job_id,
            };

            documents.value.unshift(newDocument);

            // 임베딩 성공 - Qdrant에서만 관리
            console.log("✅ Document embedded successfully in Qdrant");

            return result;
        } catch (err) {
            error.value = err.message;
            throw err;
        } finally {
            isLoading.value = false;
        }
    };

    // Markdown 청킹 미리보기
    const previewMarkdownChunking = async (
        file,
        container = "general",
        options = {}
    ) => {
        isLoading.value = true;
        error.value = null;

        try {
            const result = await previewMarkdownChunkingAPI(
                file,
                container,
                options
            );
            return result;
        } catch (err) {
            error.value = err.message;
            throw err;
        } finally {
            isLoading.value = false;
        }
    };

    // Excel 청킹 미리보기
    const previewExcelChunking = async (
        file,
        container = "general",
        options = {}
    ) => {
        isLoading.value = true;
        error.value = null;

        try {
            const result = await previewExcelChunkingAPI(
                file,
                container,
                options
            );
            return result;
        } catch (err) {
            error.value = err.message;
            throw err;
        } finally {
            isLoading.value = false;
        }
    };

    // Markdown 최종 처리 (사용자 편집 청크)
    const confirmMarkdownProcessing = async (requestData) => {
        isLoading.value = true;
        error.value = null;

        try {
            const result = await confirmMarkdownProcessingAPI(requestData);

            // 처리 완료 후 문서 목록에 추가
            const newDocument = {
                id: result.job_id,
                name: requestData.filename,
                size: requestData.fileSize || 0,
                status: "processed",
                uploadedAt: new Date().toISOString(),
                container: requestData.container,
                type: "markdown",
                jobId: result.job_id,
                chunksCount: requestData.chunks.length,
            };

            documents.value.unshift(newDocument);

            // 임베딩 성공 - Qdrant에서만 관리
            console.log("✅ Document embedded successfully in Qdrant");

            return result;
        } catch (err) {
            error.value = err.message;
            throw err;
        } finally {
            isLoading.value = false;
        }
    };

    // 처리 작업 상태 조회
    const getProcessingStatus = async (jobId) => {
        try {
            const result = await getProcessingStatusAPI(jobId);
            return result;
        } catch (err) {
            error.value = err.message;
            throw err;
        }
    };

    // 사용 가능한 컨테이너 목록 조회
    const getAvailableContainers = async () => {
        try {
            const result = await getAvailableContainersAPI();
            return result;
        } catch (err) {
            error.value = err.message;
            throw err;
        }
    };

    // 처리 기능 정보 조회
    const getProcessingCapabilities = async () => {
        try {
            const result = await getProcessingCapabilitiesAPI();
            return result;
        } catch (err) {
            error.value = err.message;
            throw err;
        }
    };

    // 파일 타입에 따른 자동 처리
    const processFile = async (file, container = "general", options = {}) => {
        const fileExtension = file.name.split(".").pop().toLowerCase();

        switch (fileExtension) {
            case "xlsx":
            case "xls":
                return await processExcelFile(file, container, options);
            case "md":
            case "markdown":
                return await processMarkdownFile(file, container, options);
            default:
                throw new Error(
                    `지원하지 않는 파일 형식입니다: ${fileExtension}`
                );
        }
    };

    // 청크 임베딩 (기존 함수 - 호환성 유지)
    const embedChunks = async (chunks) => {
        isLoading.value = true;
        error.value = null;

        try {
            // 실제로는 백엔드 API 호출
            // 임시로 성공 응답 시뮬레이션
            await new Promise((resolve) => setTimeout(resolve, 3000)); // 3초 대기

            // 임베딩 완료 후 문서 상태 업데이트
            const newDocuments = chunks.map((chunk, index) => ({
                id: Date.now() + index,
                name: `chunk_${index + 1}`,
                size: chunk.content.length,
                status: "processed",
                uploadedAt: new Date().toISOString(),
                chunkId: chunk.id,
                qualityScore: chunk.qualityScore,
            }));

            documents.value.unshift(...newDocuments);

            return { success: true, embeddedChunks: chunks.length };
        } catch (err) {
            error.value = err.message;
            throw err;
        } finally {
            isLoading.value = false;
        }
    };

    // 에러 초기화
    const clearError = () => {
        error.value = null;
    };

    // Excel 최종 처리 (사용자 편집 청크)
    const confirmExcelProcessing = async (requestData) => {
        isLoading.value = true;
        error.value = null;

        try {
            const result = await confirmExcelProcessingAPI(requestData);

            // 처리 완료 후 문서 목록에 추가
            const newDocument = {
                id: result.job_id,
                name: requestData.filename,
                size: 0,
                status: "processed",
                uploadedAt: new Date().toISOString(),
                container: requestData.container,
                type: "excel",
                jobId: result.job_id,
                chunksCount: requestData.chunks.length,
            };

            documents.value.unshift(newDocument);

            return result;
        } catch (err) {
            error.value = err.message;
            throw err;
        } finally {
            isLoading.value = false;
        }
    };

    // LLM 청킹 제안 가져오기
    const getLLMChunkingSuggestions = async (file, container = "general") => {
        try {
            const response = await getLLMChunkingSuggestionsAPI(
                file,
                container
            );
            return response;
        } catch (error) {
            console.error("Failed to get LLM chunking suggestions:", error);
            throw error;
        }
    };

    // Excel LLM 청킹 제안 가져오기
    const getExcelLLMChunkingSuggestions = async (file, container = "general") => {
        try {
            const response = await suggestExcelLLMChunkingAPI(
                file,
                container
            );
            return response;
        } catch (error) {
            console.error("Failed to get Excel LLM chunking suggestions:", error);
            throw error;
        }
    };

    return {
        documents,
        isLoading,
        isSyncing,
        error,
        azureConnectionStatus,
        fetchDocuments,
        uploadFiles,
        downloadDocument,
        deleteDocument,
        updateDocumentStatus,
        getAllDocuments,
        checkAzureConnection,
        syncAzureFileShare,
        embedChunks,
        clearError,
        // 임베딩 백엔드 연동 함수들
        processExcelFile,
        processMarkdownFile,
        previewMarkdownChunking,
        previewExcelChunking,
        confirmMarkdownProcessing,
        confirmExcelProcessing,
        getProcessingStatus,
        getAvailableContainers,
        getProcessingCapabilities,
        processFile,
        getLLMChunkingSuggestions,
        getExcelLLMChunkingSuggestions,
    };
});

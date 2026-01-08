<template>
    <div
        v-if="isVisible"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
        <div
            class="bg-white rounded-xl shadow-xl max-w-7xl w-full mx-4 max-h-[95vh] flex flex-col"
        >
            <!-- 고정 헤더 -->
            <div class="flex-shrink-0 p-6 border-b border-gray-200 bg-white rounded-t-xl">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-4">
                        <div class="text-4xl">{{ department?.icon }}</div>
                        <div>
                            <h3
                                class="text-xl font-semibold"
                                style="color: var(--color-gray-900)"
                            >
                                {{ department?.name }}
                            </h3>
                            <p
                                class="text-sm"
                                style="color: var(--color-gray-600)"
                            >
                                {{ department?.description }}
                            </p>
                        </div>
                    </div>
                    <button
                        @click="closeModal"
                        class="p-2 transition-colors rounded-lg hover:bg-gray-100"
                        style="color: var(--color-gray-400)"
                    >
                        <svg
                            class="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M6 18L18 6M6 6l12 12"
                            />
                        </svg>
                    </button>
                </div>
            </div>

            <!-- 스크롤 가능한 컨텐츠 -->
            <div class="flex-1 overflow-y-auto p-6">

                <!-- 시스템 정보 -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <div
                        class="p-4 border rounded-lg"
                        style="border-color: var(--color-border-light)"
                    >
                        <div
                            class="text-sm"
                            style="color: var(--color-gray-500)"
                        >
                            상태
                        </div>
                        <div class="mt-1">
                            <span
                                :class="[
                                    'px-2 py-1 text-xs rounded-full font-medium',
                                    department?.status === 'active'
                                        ? 'badge-success'
                                        : department?.status === 'inactive'
                                        ? 'badge-error'
                                        : 'badge-warning',
                                ]"
                            >
                                {{ getStatusText(department?.status) }}
                            </span>
                        </div>
                    </div>

                    <div
                        class="p-4 border rounded-lg"
                        style="border-color: var(--color-border-light)"
                    >
                        <div
                            class="text-sm"
                            style="color: var(--color-gray-500)"
                        >
                            문서 수
                        </div>
                        <div
                            class="mt-1 text-lg font-semibold"
                            style="color: var(--color-gray-900)"
                        >
                            {{ documents.length }}개
                        </div>
                    </div>

                    <div
                        class="p-4 border rounded-lg"
                        style="border-color: var(--color-border-light)"
                    >
                        <div
                            class="text-sm"
                            style="color: var(--color-gray-500)"
                        >
                            이번 달 쿼리
                        </div>
                        <div
                            class="mt-1 text-lg font-semibold"
                            style="color: var(--color-gray-900)"
                        >
                            {{ department?.monthlyQueries || 0 }}회
                        </div>
                    </div>

                    <div
                        class="p-4 border rounded-lg"
                        style="border-color: var(--color-border-light)"
                    >
                        <div
                            class="text-sm"
                            style="color: var(--color-gray-500)"
                        >
                            디스크 사용량
                        </div>
                        <div
                            class="mt-1 text-lg font-semibold"
                            style="color: var(--color-gray-900)"
                        >
                            {{ formatFileSize(diskUsage) }}
                        </div>
                        <div class="text-xs text-gray-500 mt-1">
                            전체 {{ formatDiskUsagePercentage(diskUsagePercentage) }}% 사용
                        </div>
                        <!-- 사용량 바 -->
                        <div class="mt-2 w-full bg-gray-200 rounded-full h-2">
                            <div 
                                class="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                :style="{ width: Math.min(100, Math.max(0, diskUsagePercentage || 0)) + '%' }"
                            ></div>
                        </div>
                    </div>
                </div>

                <!-- 키워드 -->
                <div v-if="department?.keywords?.length" class="mb-6">
                    <h4
                        class="text-sm font-medium mb-2"
                        style="color: var(--color-gray-700)"
                    >
                        키워드
                    </h4>
                    <div class="flex flex-wrap gap-2">
                        <span
                            v-for="keyword in department.keywords"
                            :key="keyword"
                            class="px-3 py-1 text-xs rounded-full"
                            style="
                                background-color: var(--color-primary-100);
                                color: var(--color-primary-700);
                            "
                        >
                            {{ keyword }}
                        </span>
                    </div>
                </div>

                <!-- Qdrant 벡터 데이터베이스 정보 -->
                <div class="mb-6">
                    <h4
                        class="text-lg font-semibold mb-4"
                        style="color: var(--color-gray-900)"
                    >
                        Qdrant 벡터 데이터베이스
                    </h4>
                    
                    <!-- 컬렉션 정보 카드 -->
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                        <div
                            class="p-4 border rounded-lg"
                            style="border-color: var(--color-border-light)"
                        >
                            <div class="flex items-center">
                                <div class="w-8 h-8 rounded-lg flex items-center justify-center bg-purple-100">
                                    <svg class="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"/>
                                    </svg>
                                </div>
                                <div class="ml-3">
                                    <div
                                        class="text-sm"
                                        style="color: var(--color-gray-500)"
                                    >
                                        컬렉션명
                                    </div>
                                    <div
                                        class="text-sm font-medium"
                                        style="color: var(--color-gray-900)"
                                    >
                                        {{ getCollectionName() }}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div
                            class="p-4 border rounded-lg"
                            style="border-color: var(--color-border-light)"
                        >
                            <div class="flex items-center">
                                <div class="w-8 h-8 rounded-lg flex items-center justify-center bg-blue-100">
                                    <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                                    </svg>
                                </div>
                                <div class="ml-3">
                                    <div
                                        class="text-sm"
                                        style="color: var(--color-gray-500)"
                                    >
                                        벡터 수
                                    </div>
                                    <div
                                        class="text-sm font-medium"
                                        style="color: var(--color-gray-900)"
                                    >
                                        {{ collectionInfo?.vectors_count || 0 }}개
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div
                            class="p-4 border rounded-lg"
                            style="border-color: var(--color-border-light)"
                        >
                            <div class="flex items-center">
                                <div class="w-8 h-8 rounded-lg flex items-center justify-center bg-green-100">
                                    <svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                    </svg>
                                </div>
                                <div class="ml-3">
                                    <div
                                        class="text-sm"
                                        style="color: var(--color-gray-500)"
                                    >
                                        상태
                                    </div>
                                    <div
                                        class="text-sm font-medium"
                                        :style="{ color: getCollectionStatusColor(collectionInfo?.status) }"
                                    >
                                        {{ getCollectionStatusText(collectionInfo?.status) }}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 컬렉션 상세 정보 -->
                    <div v-if="collectionInfo" class="bg-gray-50 rounded-lg p-4">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                            <div>
                                <span class="font-medium text-gray-700">벡터 차원:</span>
                                <span class="ml-2 text-gray-600">{{ collectionInfo.config?.vector_size || 'N/A' }}</span>
                            </div>
                            <div>
                                <span class="font-medium text-gray-700">거리 함수:</span>
                                <span class="ml-2 text-gray-600">{{ collectionInfo.config?.distance || 'N/A' }}</span>
                            </div>
                            <div>
                                <span class="font-medium text-gray-700">인덱싱된 벡터:</span>
                                <span class="ml-2 text-gray-600">{{ collectionInfo.indexed_vectors_count || 0 }}개</span>
                            </div>
                            <div>
                                <span class="font-medium text-gray-700">총 청크 수:</span>
                                <span class="ml-2 text-gray-600">{{ collectionInfo.points_count || 0 }}개</span>
                            </div>
                        </div>
                    </div>

                </div>

                <!-- 문서 관리 섹션 -->
                <div
                    class="border-t pt-6"
                    style="border-color: var(--color-border-light)"
                >
                    <div class="flex items-center justify-between mb-4">
                        <h4
                            class="text-lg font-semibold"
                            style="color: var(--color-gray-900)"
                        >
                            문서 관리
                        </h4>
                        <div class="flex items-center space-x-3">
                            <!-- 문서 검색 -->
                            <div class="relative">
                                <input
                                    v-model="documentSearchQuery"
                                    type="text"
                                    placeholder="문서 검색..."
                                    class="pl-8 pr-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    style="border-color: var(--color-border-light); color: var(--color-gray-700);"
                                />
                                <svg
                                    class="absolute left-2.5 top-2.5 w-4 h-4"
                                    style="color: var(--color-gray-400)"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        stroke-linecap="round"
                                        stroke-linejoin="round"
                                        stroke-width="2"
                                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                                    />
                                </svg>
                            </div>
                            <button
                                @click="showUploadModal = true"
                                class="btn btn-primary btn-sm"
                            >
                                <svg
                                    class="w-4 h-4 mr-1"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        stroke-linecap="round"
                                        stroke-linejoin="round"
                                        stroke-width="2"
                                        d="M12 4v16m8-8H4"
                                    />
                                </svg>
                                문서 업로드
                            </button>
                            <div class="relative group">
                                <button
                                    @click="refreshDocuments"
                                    class="p-2 transition-colors rounded-lg hover:bg-gray-50"
                                    style="color: var(--color-gray-400)"
                                >
                                <svg
                                    class="w-4 h-4"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        stroke-linecap="round"
                                        stroke-linejoin="round"
                                        stroke-width="2"
                                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                                    />
                                </svg>
                                </button>
                                <!-- 툴팁 -->
                                <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-10">
                                    문서 목록 새로고침
                                    <div class="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-800"></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 문서 목록 -->
                    <div v-if="filteredDocuments.length > 0" class="space-y-3">
                        <div
                            v-for="doc in filteredDocuments"
                            :key="doc.id"
                            class="flex items-center justify-between p-4 border rounded-xl transition-all duration-200 hover:shadow-md"
                            style="
                                border-color: var(--color-border-light);
                                background-color: var(--color-bg-primary);
                            "
                        >
                            <div class="flex items-center space-x-4">
                                <div
                                    class="w-10 h-10 rounded-xl flex items-center justify-center"
                                    style="
                                        background: linear-gradient(
                                            135deg,
                                            var(--color-success-50),
                                            var(--color-success-100)
                                        );
                                    "
                                >
                                    <svg
                                        class="w-5 h-5"
                                        style="color: var(--color-success-600)"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                    >
                                        <path
                                            stroke-linecap="round"
                                            stroke-linejoin="round"
                                            stroke-width="2"
                                            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                                        />
                                    </svg>
                                </div>
                                <div>
                                    <h3
                                        class="text-sm font-medium"
                                        style="color: var(--color-gray-900)"
                                    >
                                        {{ doc.name }}
                                    </h3>
                                    <p
                                        class="text-xs"
                                        style="color: var(--color-gray-500)"
                                    >
                                        {{ formatDate(doc.uploadedAt || doc.upload_date || doc.created_at) }}
                                        <span v-if="doc.chunkCount || doc.chunk_count" class="ml-1 text-blue-600">
                                            • {{ doc.chunkCount || doc.chunk_count || 0 }}개 청크
                                        </span>
                                    </p>
                                </div>
                            </div>
                            <div class="flex items-center space-x-2">
                                <div class="relative group">
                                    <div
                                        :class="[
                                            'w-6 h-6 rounded-full flex items-center justify-center',
                                            getStatusIcon(doc.status).bgColor
                                        ]"
                                    >
                                        <svg
                                            class="w-4 h-4"
                                            :class="getStatusIcon(doc.status).color"
                                            fill="none"
                                            stroke="currentColor"
                                            viewBox="0 0 24 24"
                                        >
                                            <path
                                                stroke-linecap="round"
                                                stroke-linejoin="round"
                                                stroke-width="2"
                                                :d="getStatusIcon(doc.status).icon"
                                            />
                                        </svg>
                                    </div>
                                    <!-- 툴팁 -->
                                    <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-10">
                                        {{ getStatusIcon(doc.status).tooltip }}
                                        <div class="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-800"></div>
                                    </div>
                                </div>
                                <div class="relative group">
                                    <button
                                        @click="viewChunks(doc)"
                                        class="p-2 transition-all duration-200 rounded-lg hover:bg-green-50"
                                        style="color: var(--color-gray-400)"
                                    >
                                    <svg
                                        class="w-4 h-4"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                    >
                                        <path
                                            stroke-linecap="round"
                                            stroke-linejoin="round"
                                            stroke-width="2"
                                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                                        />
                                    </svg>
                                    </button>
                                    <!-- 툴팁 -->
                                    <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-10">
                                        청킹 조각 보기
                                        <div class="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-800"></div>
                                    </div>
                                </div>
                                <div class="relative group" v-if="(doc.metadata?.upload_status || doc.upload_status) === 'completed'">
                                    <button
                                        @click="downloadDocument(doc)"
                                    class="p-2 transition-all duration-200 rounded-lg hover:bg-blue-50"
                                    style="color: var(--color-gray-400)"
                                    title="다운로드"
                                    :disabled="!(doc.metadata?.download_url || doc.download_url)"
                                >
                                    <svg
                                        class="w-4 h-4"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                    >
                                        <path
                                            stroke-linecap="round"
                                            stroke-linejoin="round"
                                            stroke-width="2"
                                            d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                                        />
                                    </svg>
                                    </button>
                                    <!-- 툴팁 -->
                                    <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-10">
                                        문서 다운로드
                                        <div class="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-800"></div>
                                    </div>
                                </div>
                                <div class="relative group">
                                    <button
                                    @click="deleteDocument(doc)"
                                    class="p-2 transition-all duration-200 rounded-lg hover:bg-red-50"
                                    style="color: var(--color-gray-400)"
                                    title="삭제"
                                >
                                    <svg
                                        class="w-4 h-4"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                    >
                                        <path
                                            stroke-linecap="round"
                                            stroke-linejoin="round"
                                            stroke-width="2"
                                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                        />
                                    </svg>
                                    </button>
                                    <!-- 툴팁 -->
                                    <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-10">
                                        문서 삭제
                                        <div class="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-800"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 빈 상태 -->
                    <div v-else class="text-center py-12">
                        <div
                            class="mx-auto w-16 h-16 rounded-full flex items-center justify-center mb-4"
                            style="
                                background: linear-gradient(
                                    135deg,
                                    var(--color-gray-100),
                                    var(--color-gray-200)
                                );
                            "
                        >
                            <svg
                                class="w-8 h-8"
                                style="color: var(--color-gray-400)"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    stroke-width="2"
                                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                                />
                            </svg>
                        </div>
                        <p style="color: var(--color-gray-500)">
                            {{ documentSearchQuery.trim() ? '검색 결과가 없습니다' : `${department?.name}에 업로드된 문서가 없습니다` }}
                        </p>
                        <button
                            @click="showUploadModal = true"
                            class="btn btn-primary btn-sm mt-3"
                        >
                            첫 문서 업로드하기
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- 문서 업로드 모달 -->
        <div
            v-if="showUploadModal"
            class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        >
            <div class="bg-white rounded-xl shadow-xl max-w-lg w-full mx-4">
                <div class="p-6">
                    <div class="flex items-center justify-between mb-6">
                        <h4
                            class="text-lg font-semibold"
                            style="color: var(--color-gray-900)"
                        >
                            {{ department?.name }}에 문서 업로드
                        </h4>
                        <button
                            @click="showUploadModal = false"
                            class="p-2 transition-colors rounded-lg hover:bg-gray-100"
                            style="color: var(--color-gray-400)"
                        >
                            <svg
                                class="w-5 h-5"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    stroke-width="2"
                                    d="M6 18L18 6M6 6l12 12"
                                />
                            </svg>
                        </button>
                    </div>

                    <!-- 간단한 파일 업로드 -->
                    <div class="space-y-4">
                        <div
                            @drop="handleDrop"
                            @dragover.prevent
                            @dragenter="handleDragEnter"
                            @dragleave="handleDragLeave"
                            :class="[
                                'border-2 border-dashed rounded-xl p-6 text-center transition-all duration-300',
                                isDragOver
                                    ? 'border-primary-400 bg-primary-50'
                                    : 'border-gray-300 hover:border-primary-300',
                            ]"
                        >
                            <div class="space-y-3">
                                <div
                                    class="mx-auto w-12 h-12 rounded-full flex items-center justify-center"
                                    style="
                                        background: linear-gradient(
                                            135deg,
                                            var(--color-primary-100),
                                            var(--color-secondary-100)
                                        );
                                    "
                                >
                                    <svg
                                        class="w-6 h-6"
                                        style="color: var(--color-primary-600)"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                    >
                                        <path
                                            stroke-linecap="round"
                                            stroke-linejoin="round"
                                            stroke-width="2"
                                            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                                        />
                                    </svg>
                                </div>
                                <div>
                                    <p
                                        class="text-sm font-medium"
                                        style="color: var(--color-gray-900)"
                                    >
                                        파일을 드래그하여 업로드하거나
                                    </p>
                                    <button
                                        @click="triggerFileInput"
                                        class="btn btn-primary btn-sm mt-2"
                                    >
                                        파일 선택
                                    </button>
                                    <input
                                        ref="fileInput"
                                        type="file"
                                        multiple
                                        accept=".pdf,.txt,.md,.doc,.docx"
                                        @change="handleFileSelect"
                                        class="hidden"
                                    />
                                </div>
                            </div>
                        </div>

                        <!-- 선택된 파일 목록 -->
                        <div v-if="selectedFiles.length > 0" class="space-y-2">
                            <h5
                                class="text-sm font-medium"
                                style="color: var(--color-gray-700)"
                            >
                                선택된 파일
                            </h5>
                            <div
                                v-for="(file, index) in selectedFiles"
                                :key="index"
                                class="flex items-center justify-between p-2 rounded-lg"
                                style="
                                    background-color: var(--color-bg-tertiary);
                                "
                            >
                                <span
                                    class="text-sm"
                                    style="color: var(--color-gray-900)"
                                    >{{ file.name }}</span
                                >
                                <button
                                    @click="removeFile(index)"
                                    class="p-1 text-red-500 hover:bg-red-50 rounded"
                                >
                                    <svg
                                        class="w-4 h-4"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                    >
                                        <path
                                            stroke-linecap="round"
                                            stroke-linejoin="round"
                                            stroke-width="2"
                                            d="M6 18L18 6M6 6l12 12"
                                        />
                                    </svg>
                                </button>
                            </div>
                        </div>

                        <!-- 업로드 버튼 -->
                        <div
                            v-if="selectedFiles.length > 0"
                            class="flex justify-end space-x-3 pt-4"
                        >
                            <button
                                @click="showUploadModal = false"
                                class="px-4 py-2 text-sm font-medium border rounded-lg transition-colors hover:bg-gray-50"
                                style="
                                    border-color: var(--color-border-light);
                                    color: var(--color-gray-700);
                                "
                            >
                                취소
                            </button>
                            <button
                                @click="uploadFiles"
                                :disabled="isUploading"
                                class="btn btn-primary btn-sm disabled:opacity-50"
                            >
                                <span
                                    v-if="isUploading"
                                    class="flex items-center"
                                >
                                    <svg
                                        class="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                                        fill="none"
                                        viewBox="0 0 24 24"
                                    >
                                        <circle
                                            class="opacity-25"
                                            cx="12"
                                            cy="12"
                                            r="10"
                                            stroke="currentColor"
                                            stroke-width="4"
                                        ></circle>
                                        <path
                                            class="opacity-75"
                                            fill="currentColor"
                                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                        ></path>
                                    </svg>
                                    업로드 중...
                                </span>
                                <span v-else>업로드</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 청킹 조각 상세 보기 모달 -->
        <div 
            v-if="showChunksModal"
            class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        >
            <div class="bg-white rounded-xl shadow-xl max-w-[95vw] w-full mx-4 max-h-[95vh] flex flex-col">
                <!-- 고정 헤더 -->
                <div class="flex-shrink-0 p-6 border-b border-gray-200 bg-white rounded-t-xl">
                    <div class="flex items-center justify-between">
                        <div>
                            <h3 class="text-xl font-semibold text-gray-900">
                                {{ selectedDocument?.name }} - 청킹 조각
                            </h3>
                            <p class="text-sm text-gray-600 mt-1">
                                총 {{ selectedDocumentChunks.length }}개의 청킹 조각
                            </p>
                        </div>
                        <button
                            @click="showChunksModal = false"
                            class="p-2 transition-colors rounded-lg hover:bg-gray-100 text-gray-400"
                        >
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                            </svg>
                        </button>
                    </div>
                </div>

                <!-- 스크롤 가능한 컨텐츠 -->
                <div class="flex-1 overflow-y-auto p-6">

                    <!-- 로딩 상태 -->
                    <div v-if="isLoadingChunks" class="flex justify-center items-center py-12">
                        <div class="text-center">
                            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                            <p class="text-gray-600">청킹 조각을 불러오는 중...</p>
                        </div>
                    </div>

                    <!-- 청킹 조각 목록 -->
                    <div v-else class="space-y-4 max-h-[70vh] overflow-y-auto">
                        <div
                            v-for="(chunk, index) in selectedDocumentChunks"
                            :key="chunk.id"
                            class="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                        >
                            <div class="flex items-start justify-between mb-3">
                                <div class="flex items-center space-x-3">
                                    <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                                        청크 {{ index + 1 }}
                                    </span>
                                    <span class="text-xs text-gray-500">
                                        위치: {{ chunk.startPosition }} - {{ chunk.endPosition }}
                                    </span>
                                </div>
                                <div class="flex items-center space-x-2">
                                    <span class="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                                        품질: {{ chunk.qualityScore }}/10
                                    </span>
                                    <span class="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs">
                                        의미: {{ chunk.semanticScore }}/10
                                    </span>
                                    <span class="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs">
                                        중복: {{ chunk.duplicateScore }}%
                                    </span>
                                </div>
                            </div>
                            <div class="bg-gray-50 rounded p-4 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap break-words">
                                {{ chunk.content }}
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { useDataUploadStore } from "@/stores/dataUpload";
import { 
    getQdrantCollectionInfoAPI, 
    getDocumentChunksAPI,
    getCollectionNameForDepartment,
    getCollectionDocumentsAPI,
    deleteDocumentAPI
} from "@/services/embeddingApi";

const props = defineProps({
    isVisible: {
        type: Boolean,
        default: false,
    },
    department: {
        type: Object,
        default: null,
    },
});

const emit = defineEmits(["close"]);

const dataUploadStore = useDataUploadStore();

// 반응형 상태
const showUploadModal = ref(false);
const selectedFiles = ref([]);
const isDragOver = ref(false);
const isUploading = ref(false);
const fileInput = ref(null);
const showChunksModal = ref(false);
const selectedDocumentChunks = ref([]);
const selectedDocument = ref(null);
const collectionInfo = ref(null);
const isLoadingChunks = ref(false);
const qdrantDocuments = ref([]);

// 문서 검색
const documentSearchQuery = ref('');

// 계산된 속성
const documents = computed(() => {
    if (!props.department) return [];
    // Qdrant에서 실제 벡터로 저장된 문서 목록 사용
    return qdrantDocuments.value;
});

// 검색된 문서 목록
const filteredDocuments = computed(() => {
    if (!documentSearchQuery.value.trim()) {
        return documents.value;
    }
    
    const query = documentSearchQuery.value.toLowerCase();
    return documents.value.filter(doc => 
        doc.name.toLowerCase().includes(query) ||
        doc.type.toLowerCase().includes(query) ||
        (doc.metadata && JSON.stringify(doc.metadata).toLowerCase().includes(query))
    );
});

// 디스크 사용량 관련 computed 속성들
const diskUsage = ref(0);
const diskUsagePercentage = ref(0);

// 디스크 사용량 로드
const loadDiskUsage = async () => {
    try {
        const usage = await getDepartmentDiskUsage();
        const percentage = await getDepartmentDiskUsagePercentage();
        
        // 안전한 값 설정
        diskUsage.value = usage && !isNaN(usage) ? usage : 0;
        diskUsagePercentage.value = percentage && !isNaN(percentage) ? percentage : 0;
        
        console.log(`디스크 사용량 로드 완료: ${diskUsage.value} bytes (${diskUsagePercentage.value}%)`);
    } catch (error) {
        console.error("디스크 사용량 로드 실패:", error);
        diskUsage.value = 0;
        diskUsagePercentage.value = 0;
    }
};

// 상태 텍스트
const getStatusText = (status) => {
    const statusMap = {
        active: "활성",
        inactive: "비활성",
        maintenance: "점검중",
        processed: "처리완료",
        processing: "처리중",
        failed: "실패",
    };
    return statusMap[status] || status;
};

// 상태 아이콘과 툴팁
const getStatusIcon = (status) => {
    const statusConfig = {
        active: {
            icon: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
            color: "text-green-600",
            bgColor: "bg-green-100",
            tooltip: "활성 상태 - 정상 작동 중"
        },
        inactive: {
            icon: "M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z",
            color: "text-gray-600",
            bgColor: "bg-gray-100",
            tooltip: "비활성 상태 - 사용 중지됨"
        },
        maintenance: {
            icon: "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z",
            color: "text-yellow-600",
            bgColor: "bg-yellow-100",
            tooltip: "점검 중 - 일시적으로 사용 불가"
        },
        processed: {
            icon: "M5 13l4 4L19 7",
            color: "text-green-600",
            bgColor: "bg-green-100",
            tooltip: "처리 완료 - 임베딩 및 저장 완료"
        },
        processing: {
            icon: "M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15",
            color: "text-blue-600",
            bgColor: "bg-blue-100",
            tooltip: "처리 중 - 임베딩 및 저장 진행 중"
        },
        failed: {
            icon: "M6 18L18 6M6 6l12 12",
            color: "text-red-600",
            bgColor: "bg-red-100",
            tooltip: "처리 실패 - 오류 발생으로 처리 중단"
        }
    };
    return statusConfig[status] || statusConfig.processed;
};

// 파일 크기 포맷팅
const formatFileSize = (bytes) => {
    if (!bytes || bytes === 0 || isNaN(bytes)) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

// 디스크 사용량 퍼센트 포맷팅
const formatDiskUsagePercentage = (percentage) => {
    if (!percentage || isNaN(percentage)) return "0";
    return Math.round(percentage).toString();
};

// 점수 포맷팅 (NaN 처리)
const formatScore = (score) => {
    if (!score || isNaN(score) || !isFinite(score)) return "0.0";
    return Math.round(score * 10) / 10;
};

// 날짜 포맷팅
const formatDate = (dateStr) => {
    if (!dateStr) return "날짜 없음";
    
    try {
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) return "날짜 없음";
        
        return date.toLocaleDateString("ko-KR", {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    } catch (error) {
        console.error("날짜 포맷팅 오류:", error);
        return "날짜 없음";
    }
};

// 파일 업로드 관련 메서드
const triggerFileInput = () => {
    fileInput.value?.click();
};

const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    addFiles(files);
    event.target.value = "";
};

const handleDrop = (event) => {
    event.preventDefault();
    isDragOver.value = false;

    const files = Array.from(event.dataTransfer.files);
    addFiles(files);
};

const addFiles = (files) => {
    const validFiles = files.filter((file) => {
        if (file.size > 10 * 1024 * 1024) {
            alert(`${file.name}은(는) 10MB를 초과합니다.`);
            return false;
        }

        const allowedTypes = [".pdf", ".txt", ".md", ".doc", ".docx"];
        const fileExtension = "." + file.name.split(".").pop().toLowerCase();
        if (!allowedTypes.includes(fileExtension)) {
            alert(`${file.name}은(는) 지원하지 않는 형식입니다.`);
            return false;
        }

        return true;
    });

    selectedFiles.value.push(...validFiles);
};

const removeFile = (index) => {
    selectedFiles.value.splice(index, 1);
};

const uploadFiles = async () => {
    if (selectedFiles.value.length === 0) return;

    isUploading.value = true;

    try {
        await dataUploadStore.uploadFiles(
            selectedFiles.value,
            props.department.id
        );
        selectedFiles.value = [];
        showUploadModal.value = false;
        alert("파일 업로드가 완료되었습니다.");
    } catch (error) {
        alert("업로드 중 오류가 발생했습니다: " + error.message);
    } finally {
        isUploading.value = false;
    }
};

// 드래그 이벤트
const handleDragEnter = () => {
    isDragOver.value = true;
};

const handleDragLeave = () => {
    isDragOver.value = false;
};

// 문서 관리 메서드
const downloadDocument = async (doc) => {
    try {
        // Check if file was successfully uploaded to Azure
        const uploadStatus = doc.metadata?.upload_status || doc.upload_status || "unknown";
        const downloadUrl = doc.metadata?.download_url || doc.download_url;
        
        if (uploadStatus !== "completed") {
            alert("파일이 Azure File Share에 업로드되지 않았습니다. 다운로드할 수 없습니다.");
            return;
        }
        
        if (!downloadUrl) {
            alert("다운로드 링크를 찾을 수 없습니다.");
            return;
        }
        
        // Open download URL directly (it's a SAS token URL from Azure)
        window.open(downloadUrl, '_blank');
    } catch (error) {
        alert("다운로드 중 오류가 발생했습니다: " + error.message);
    }
};

const deleteDocument = async (doc) => {
    if (confirm(`"${doc.name}" 문서를 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.`)) {
        try {
            const collectionName = getCollectionNameForDepartment(props.department.name);
            const result = await deleteDocumentAPI(collectionName, doc.name);
            
            // 성공 메시지 표시
            alert(`문서가 성공적으로 삭제되었습니다.\n삭제된 청크 수: ${result.deleted_chunks}개`);
            
            // 문서 목록 새로고침
            await loadAllData();
            
        } catch (error) {
            console.error("문서 삭제 실패:", error);
            alert("삭제 중 오류가 발생했습니다: " + error.message);
        }
    }
};

// 청킹 조각 보기
const viewChunks = async (doc) => {
    try {
        selectedDocument.value = doc;
        isLoadingChunks.value = true;
        
        // 올바른 컬렉션 이름 생성
        const collectionName = getCollectionNameForDepartment(props.department.name);
        console.log(`부서: ${props.department.name} -> 컬렉션: ${collectionName}`);
        
        // 실제 API 호출로 청킹 데이터 조회
        const chunksData = await getDocumentChunksAPI(collectionName, doc.name);
        
        // API 응답을 UI에 맞게 변환
        const rawChunks = chunksData.chunks || chunksData || [];
        selectedDocumentChunks.value = rawChunks.map(chunk => ({
            id: chunk.chunk_id || chunk.id,
            content: chunk.content || '',
            qualityScore: chunk.quality_score || chunk.qualityScore || 0,
            semanticScore: chunk.semantic_score || chunk.semanticScore || 0,
            duplicateScore: chunk.duplicate_score || chunk.duplicateScore || 0,
            startPosition: chunk.start_position || chunk.startPosition || 0,
            endPosition: chunk.end_position || chunk.endPosition || 0,
            chunkType: chunk.chunk_type || chunk.chunkType || 'text',
            metadata: chunk.metadata || {}
        }));
        
        showChunksModal.value = true;
    } catch (error) {
        console.error("청킹 조각 조회 실패:", error);
        // API 실패 시 목업 데이터로 fallback
        selectedDocumentChunks.value = generateMockChunks(doc.name);
        showChunksModal.value = true;
        alert("실제 데이터 조회에 실패하여 샘플 데이터를 표시합니다.");
    } finally {
        isLoadingChunks.value = false;
    }
};

// 목업 청킹 데이터 생성
const generateMockChunks = (documentName) => {
    const sampleChunks = [
        {
            id: "chunk_1",
            content: `${documentName}에 대한 개요를 설명합니다. 이 문서는 주요 개념과 사용법을 다룹니다.`,
            qualityScore: 8,
            semanticScore: 7,
            duplicateScore: 5,
            startPosition: 0,
            endPosition: 120
        },
        {
            id: "chunk_2", 
            content: "시스템의 주요 기능과 특징을 설명합니다. 사용자는 이러한 기능을 통해 효율적으로 작업할 수 있습니다.",
            qualityScore: 9,
            semanticScore: 8,
            duplicateScore: 2,
            startPosition: 121,
            endPosition: 240
        },
        {
            id: "chunk_3",
            content: "설치 및 설정 방법에 대한 상세한 가이드를 제공합니다. 단계별로 따라하면 쉽게 설정할 수 있습니다.",
            qualityScore: 7,
            semanticScore: 6,
            duplicateScore: 8,
            startPosition: 241,
            endPosition: 360
        }
    ];
    
    return sampleChunks;
};

// 디스크 사용량 계산 (컬렉션 정보 API 사용)
const getDepartmentDiskUsage = async () => {
    try {
        if (!props.department) return 0;
        
        // 올바른 컬렉션 이름 생성
        const collectionName = getCollectionNameForDepartment(props.department.name);
        
        // 컬렉션 정보에서 디스크 사용량 조회
        const collectionInfo = await getQdrantCollectionInfoAPI(collectionName);
        
        // 1. 실제 disk_data_size가 있는 경우 사용
        if (collectionInfo && collectionInfo.disk_data_size && !isNaN(collectionInfo.disk_data_size) && collectionInfo.disk_data_size > 0) {
            return collectionInfo.disk_data_size;
        }
        
        // 2. WAL 용량 기반 추정 (32MB 기본값)
        if (collectionInfo && collectionInfo.wal_config && collectionInfo.wal_config.wal_capacity_mb) {
            const walCapacityBytes = collectionInfo.wal_config.wal_capacity_mb * 1024 * 1024;
            return walCapacityBytes;
        }
        
        // 3. 벡터 수 기반 추정 계산
        if (collectionInfo && collectionInfo.vectors_count && collectionInfo.config) {
            const vectorSize = collectionInfo.config.vector_size || 3072;
            const vectorsCount = collectionInfo.vectors_count;
            
            // 벡터 데이터 크기 (float32 = 4 bytes per dimension)
            const vectorDataSize = vectorsCount * vectorSize * 4;
            
            // 메타데이터와 인덱스 오버헤드 (약 20% 추가)
            const estimatedSize = vectorDataSize * 1.2;
            
            return Math.round(estimatedSize);
        }
        
        // 4. API 실패 시 문서 크기 기반으로 fallback
        if (documents.value && documents.value.length > 0) {
            const totalSize = documents.value.reduce((total, doc) => {
                const size = doc.size || doc.fileSize || 0;
                return total + (size && !isNaN(size) ? size : 0);
            }, 0);
            return totalSize;
        }
        
        return 0;
    } catch (error) {
        console.error("디스크 사용량 조회 실패:", error);
        return 0;
    }
};

// 디스크 사용량 퍼센트 계산 (실제 API 사용)
const getDepartmentDiskUsagePercentage = async () => {
    try {
        const totalUsage = await getDepartmentDiskUsage();
        const totalCapacity = 100 * 1024 * 1024 * 1024; // 100GB
        
        if (!totalUsage || totalUsage === 0) return 0;
        
        const percentage = (totalUsage / totalCapacity) * 100;
        return Math.min(100, Math.max(0, Math.round(percentage)));
    } catch (error) {
        console.error("디스크 사용량 퍼센트 계산 실패:", error);
        return 0;
    }
};

const refreshDocuments = () => {
    // Qdrant에서 실제 문서 목록 새로고침
    loadQdrantDocuments();
};

// Qdrant 컬렉션 정보 관련 함수들
const getCollectionName = () => {
    if (!props.department) return '';
    return getCollectionNameForDepartment(props.department.name);
};

const getCollectionStatusText = (status) => {
    const statusMap = {
        'green': '정상',
        'yellow': '경고',
        'red': '오류',
        'unknown': '알 수 없음'
    };
    return statusMap[status] || status || '알 수 없음';
};

const getCollectionStatusColor = (status) => {
    const colorMap = {
        'green': '#10b981', // green-500
        'yellow': '#f59e0b', // yellow-500
        'red': '#ef4444', // red-500
        'unknown': '#6b7280' // gray-500
    };
    return colorMap[status] || '#6b7280';
};


// Qdrant에서 문서 목록 가져오기
const loadQdrantDocuments = async () => {
    try {
        if (!props.department) return;
        
        const collectionName = getCollectionName();
        console.log(`Qdrant 문서 목록 로드 - 부서: ${props.department.name} -> 컬렉션: ${collectionName}`);
        
        const response = await getCollectionDocumentsAPI(collectionName);
        console.log('Qdrant 문서 목록 응답:', response);
        
        if (response && response.documents) {
            // Qdrant 문서 데이터를 UI에 맞게 변환
            qdrantDocuments.value = response.documents.map(doc => ({
                id: `qdrant-${doc.document_name}`,
                name: doc.document_name,
                size: doc.file_size || 0,
                uploadedAt: doc.upload_date || new Date().toISOString(),
                status: doc.status || 'processed',
                type: doc.file_type || 'unknown',
                chunkCount: doc.chunk_count || 0,
                container: doc.container || collectionName,
                metadata: doc.metadata || {}
            }));
        } else {
            qdrantDocuments.value = [];
        }
        
        console.log('Qdrant 문서 목록 로드 완료:', qdrantDocuments.value);
    } catch (error) {
        console.error('Qdrant 문서 목록 로드 실패:', error);
        qdrantDocuments.value = [];
    }
};

// 모달 닫기
const closeModal = () => {
    emit("close");
    showUploadModal.value = false;
    selectedFiles.value = [];
};

// props 변경 감지
watch(
    () => props.isVisible,
    (newVal) => {
        if (newVal) {
            // 모달이 열릴 때 모든 데이터를 한 번에 로드
            if (props.department?.id) {
                loadAllData();
            }
        } else {
            showUploadModal.value = false;
            selectedFiles.value = [];
            collectionInfo.value = null;
            qdrantDocuments.value = [];
        }
    }
);

// 모든 데이터를 한 번에 로드하는 함수
const loadAllData = async () => {
    try {
        if (!props.department) return;
        
        const collectionName = getCollectionNameForDepartment(props.department.name);
        
        // 1. 컬렉션 정보 한 번만 가져오기
        const collectionInfoData = await getQdrantCollectionInfoAPI(collectionName);
        collectionInfo.value = collectionInfoData;
        
        // 2. 문서 목록 가져오기
        const response = await getCollectionDocumentsAPI(collectionName);
        if (response && response.documents) {
            qdrantDocuments.value = response.documents.map(doc => ({
                id: `qdrant-${doc.document_name}`,
                name: doc.document_name,
                size: doc.file_size || 0,
                fileSize: doc.file_size || 0, // 백업 필드
                uploadedAt: doc.upload_date || new Date().toISOString(),
                upload_date: doc.upload_date, // 백업 필드
                created_at: doc.upload_date, // 백업 필드
                status: doc.status || 'processed',
                type: doc.file_type || 'unknown',
                chunkCount: doc.chunk_count || 0,
                chunk_count: doc.chunk_count || 0, // 백업 필드
                container: doc.container || collectionName,
                metadata: doc.metadata || {}
            }));
        } else {
            qdrantDocuments.value = [];
        }
        
        // 3. 디스크 사용량 계산 (이미 가져온 컬렉션 정보 사용)
        await calculateDiskUsageFromCollectionInfo(collectionInfoData);
        
    } catch (error) {
        console.error('데이터 로드 실패:', error);
        // 실패 시 개별적으로 로드 시도
        loadQdrantDocuments();
        loadDiskUsage();
    }
};

// 컬렉션 정보에서 디스크 사용량 계산
const calculateDiskUsageFromCollectionInfo = async (collectionInfoData) => {
    try {
        // 1. 실제 disk_data_size가 있는 경우 사용
        if (collectionInfoData && collectionInfoData.disk_data_size && !isNaN(collectionInfoData.disk_data_size) && collectionInfoData.disk_data_size > 0) {
            diskUsage.value = collectionInfoData.disk_data_size;
        }
        // 2. WAL 용량 기반 추정
        else if (collectionInfoData && collectionInfoData.wal_config && collectionInfoData.wal_config.wal_capacity_mb) {
            diskUsage.value = collectionInfoData.wal_config.wal_capacity_mb * 1024 * 1024;
        }
        // 3. 벡터 수 기반 추정 계산
        else if (collectionInfoData && collectionInfoData.vectors_count && collectionInfoData.config) {
            const vectorSize = collectionInfoData.config.vector_size || 3072;
            const vectorsCount = collectionInfoData.vectors_count;
            const vectorDataSize = vectorsCount * vectorSize * 4;
            diskUsage.value = Math.round(vectorDataSize * 1.2);
        }
        // 4. 문서 크기 기반 fallback
        else if (documents.value && documents.value.length > 0) {
            diskUsage.value = documents.value.reduce((total, doc) => {
                const size = doc.size || doc.fileSize || 0;
                return total + (size && !isNaN(size) ? size : 0);
            }, 0);
        }
        else {
            diskUsage.value = 0;
        }
        
        // 퍼센트 계산
        const totalCapacity = 100 * 1024 * 1024 * 1024; // 100GB
        if (diskUsage.value > 0) {
            const percentage = (diskUsage.value / totalCapacity) * 100;
            diskUsagePercentage.value = Math.min(100, Math.max(0, Math.round(percentage)));
        } else {
            diskUsagePercentage.value = 0;
        }
        
        console.log(`디스크 사용량 로드 완료: ${diskUsage.value} bytes (${diskUsagePercentage.value}%)`);
    } catch (error) {
        console.error("디스크 사용량 계산 실패:", error);
        diskUsage.value = 0;
        diskUsagePercentage.value = 0;
    }
};
</script>

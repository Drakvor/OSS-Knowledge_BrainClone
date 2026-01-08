<template>
    <MainLayout>
        <div
            class="h-full flex flex-col"
            style="background-color: var(--color-bg-primary)"
        >
            <!-- 헤더 -->
            <div
                class="bg-white border-b px-6 py-4"
                style="border-color: var(--color-border-light)"
            >
                <div class="max-w-6xl mx-auto">
                    <h1
                        class="text-2xl font-bold"
                        style="color: var(--color-gray-900)"
                    >
                        데이터 업로드
                    </h1>
                    <p class="mt-1" style="color: var(--color-gray-600)">
                        RAG 시스템에 사용할 문서를 업로드하세요
                    </p>
                </div>
            </div>

            <!-- 메인 컨텐츠 -->
            <div class="flex-1 overflow-y-auto">
                <div class="flex flex-col">
                    <!-- 상단: 파일 업로드 영역과 사이드바 -->
                    <div class="flex">
                        <!-- 메인 컨텐츠 영역 -->
                        <div class="flex-1 max-w-6xl mx-auto p-6 space-y-6">
                            <!-- 업로드 영역 -->
                            <div
                                class="bg-white rounded-xl shadow-md border-0 overflow-hidden"
                            >
                                <div class="p-6">
                                    <div class="text-center mb-6">
                                        <h2
                                            class="text-2xl font-bold mb-2"
                                            style="color: var(--color-gray-900)"
                                        >
                                            파일 업로드
                                        </h2>
                                        <p class="text-gray-600 text-sm">
                                            문서를 업로드하여 지식 베이스를
                                            구축하세요
                                        </p>
                                    </div>

                                    <!-- 기존 데이터 확인 알림 제거됨 -->

                                    <!-- 부서 선택 -->
                                    <div class="mb-6">
                                        <label
                                            class="block text-base font-semibold mb-3 text-center"
                                            style="color: var(--color-gray-800)"
                                        >
                                            업로드 대상 선택
                                        </label>
                                        <div
                                            class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 max-w-3xl mx-auto"
                                        >
                                            <button
                                                v-for="dept in departments"
                                                :key="dept.id"
                                                @click="
                                                    selectDepartment(dept.id)
                                                "
                                                :class="[
                                                    'group relative p-4 rounded-xl border-2 transition-all duration-200 text-center transform',
                                                    selectedDepartment ===
                                                    dept.id
                                                        ? 'border-blue-500 bg-blue-100 scale-105 shadow-lg'
                                                        : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50 hover:scale-105',
                                                ]"
                                            >
                                                <div
                                                    :class="[
                                                        'text-2xl mb-2 transition-all duration-200',
                                                        selectedDepartment ===
                                                        dept.id
                                                            ? 'scale-110'
                                                            : '',
                                                    ]"
                                                >
                                                    {{ dept.icon }}
                                                </div>
                                                <div
                                                    class="text-xs font-medium mb-1"
                                                    style="
                                                        color: var(
                                                            --color-gray-900
                                                        );
                                                    "
                                                >
                                                    {{ dept.name }}
                                                </div>
                                                <div
                                                    class="text-xs"
                                                    style="
                                                        color: var(
                                                            --color-gray-600
                                                        );
                                                    "
                                                >
                                                    {{ dept.description }}
                                                </div>
                                                <div
                                                    v-if="
                                                        selectedDepartment ===
                                                        dept.id
                                                    "
                                                    class="absolute top-2 right-2 w-3 h-3 rounded-full bg-blue-500 shadow-sm"
                                                ></div>
                                            </button>
                                        </div>
                                        <div
                                            v-if="selectedDepartment"
                                            class="mt-4 text-center"
                                        >
                                            <div
                                                class="inline-flex items-center px-3 py-1.5 rounded-full bg-primary-100 text-primary-800 text-sm"
                                            >
                                                <svg
                                                    class="w-3 h-3 mr-1.5"
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
                                                <span class="font-medium">{{
                                                    getSelectedDepartmentName()
                                                }}</span>
                                                <span
                                                    class="ml-2 text-xs opacity-75"
                                                    >{{
                                                        getSelectedDepartmentDescription()
                                                    }}</span
                                                >
                                            </div>
                                        </div>
                                    </div>

                                    <!-- 드래그 앤 드롭 영역 -->
                                    <div
                                        @drop="handleDrop"
                                        @dragover.prevent="handleDragOver"
                                        @dragenter.prevent="handleDragEnter"
                                        @dragleave.prevent="handleDragLeave"
                                        :class="[
                                            'border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 relative',
                                            isUploading
                                                ? 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-50'
                                                : isDragOver
                                                ? 'border-primary-400 bg-primary-50'
                                                : 'border-gray-300 hover:border-primary-300 hover:bg-gray-50',
                                        ]"
                                    >
                                        <div class="space-y-4">
                                            <div
                                                class="mx-auto w-16 h-16 rounded-full flex items-center justify-center bg-primary-100"
                                            >
                                                <svg
                                                    class="w-8 h-8 text-primary-600"
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
                                                    class="text-lg font-medium mb-2"
                                                    style="
                                                        color: var(
                                                            --color-gray-900
                                                        );
                                                    "
                                                >
                                                    {{
                                                        selectedDepartment
                                                            ? `${getSelectedDepartmentName()}에 파일을 드래그하여 업로드하거나`
                                                            : "파일을 드래그하여 업로드하거나"
                                                    }}
                                                </p>
                                                <button
                                                    @click="triggerFileInput"
                                                    :disabled="isUploading"
                                                    class="inline-flex items-center px-4 py-2 font-medium rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                                                    style="
                                                        background-color: var(
                                                            --color-primary-600
                                                        );
                                                        color: white;
                                                    "
                                                    @mouseover="
                                                        $event.target.style.backgroundColor =
                                                            'var(--color-primary-700)'
                                                    "
                                                    @mouseout="
                                                        $event.target.style.backgroundColor =
                                                            'var(--color-primary-600)'
                                                    "
                                                >
                                                    <svg
                                                        class="w-4 h-4 mr-2"
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
                                                    파일 선택
                                                </button>
                                                <input
                                                    ref="fileInput"
                                                    type="file"
                                                    accept=".xlsx,.xls,.md,.markdown"
                                                    @change="handleFileSelect"
                                                    class="hidden"
                                                />
                                            </div>
                                            <div
                                                class="flex items-center justify-center space-x-4 text-sm"
                                                style="
                                                    color: var(
                                                        --color-gray-500
                                                    );
                                                "
                                            >
                                                <span class="flex items-center">
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
                                                            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                                                        />
                                                    </svg>
                                                    XLSX, XLS, MD, MARKDOWN
                                                </span>
                                                <span class="flex items-center">
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
                                                            d="M13 10V3L4 14h7v7l9-11h-7z"
                                                        />
                                                    </svg>
                                                    최대 10MB
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- 선택된 파일 목록 -->
                                    <div
                                        v-if="selectedFiles.length > 0"
                                        class="mt-6"
                                    >
                                        <div class="text-center mb-3">
                                            <h3
                                                class="text-base font-semibold mb-1"
                                                style="
                                                    color: var(
                                                        --color-gray-900
                                                    );
                                                "
                                            >
                                                선택된 파일
                                            </h3>
                                            <p
                                                v-if="selectedDepartment"
                                                class="text-sm"
                                                style="
                                                    color: var(
                                                        --color-primary-600
                                                    );
                                                "
                                            >
                                                →
                                                {{
                                                    getSelectedDepartmentName()
                                                }}에 업로드됩니다
                                            </p>
                                        </div>
                                        <div
                                            class="space-y-2 max-w-2xl mx-auto"
                                        >
                                            <div
                                                v-for="(
                                                    file, index
                                                ) in selectedFiles"
                                                :key="index"
                                                class="flex items-center justify-between p-3 rounded-lg transition-colors duration-200 hover:bg-gray-50"
                                                style="
                                                    background: var(
                                                        --color-primary-50
                                                    );
                                                    border: 1px solid
                                                        var(--color-primary-200);
                                                "
                                            >
                                                <div
                                                    class="flex items-center space-x-3"
                                                >
                                                    <div
                                                        class="w-8 h-8 rounded-lg flex items-center justify-center bg-primary-500"
                                                    >
                                                        <svg
                                                            class="w-4 h-4 text-white"
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
                                                    <div>
                                                        <p
                                                            class="text-sm font-medium"
                                                            style="
                                                                color: var(
                                                                    --color-gray-900
                                                                );
                                                            "
                                                        >
                                                            {{ file.name }}
                                                        </p>
                                                        <p
                                                            class="text-xs"
                                                            style="
                                                                color: var(
                                                                    --color-primary-600
                                                                );
                                                            "
                                                        >
                                                            {{
                                                                formatFileSize(
                                                                    file.size
                                                                )
                                                            }}
                                                        </p>
                                                    </div>
                                                </div>
                                                <button
                                                    @click="removeFile(index)"
                                                    :disabled="isUploading"
                                                    class="p-1.5 transition-colors duration-200 rounded hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed"
                                                    style="
                                                        color: var(
                                                            --color-gray-400
                                                        );
                                                    "
                                                >
                                                    <svg
                                                        class="w-4 h-4 hover:text-red-500"
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
                                    </div>

                                    <!-- 업로드 버튼 -->
                                    <div
                                        v-if="selectedFiles.length > 0"
                                        class="mt-6 text-center"
                                    >
                                        <button
                                            @click="startChunkingProcess"
                                            :disabled="isUploading"
                                            class="inline-flex items-center px-6 py-3 bg-green-500 text-white font-semibold rounded-lg hover:bg-green-600 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
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
                                                처리 중...
                                            </span>
                                            <span
                                                v-else
                                                class="flex items-center"
                                            >
                                                <svg
                                                    class="w-4 h-4 mr-2"
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
                                                임베딩 처리
                                            </span>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- RAG 선택 시 오른쪽 사이드바 -->
                        <div
                            v-if="selectedDepartment"
                            class="w-80 bg-white border-l border-gray-200 flex flex-col"
                            style="height: calc(100vh - 100px)"
                        >
                            <div class="p-6 flex flex-col h-full">
                                <div
                                    class="flex items-center justify-between mb-4 flex-shrink-0"
                                >
                                    <h3
                                        class="text-lg font-semibold"
                                        style="color: var(--color-gray-900)"
                                    >
                                        {{ getSelectedDepartmentName() }} 문서
                                    </h3>
                                    <button
                                        @click="selectedDepartment = null"
                                        class="p-1 rounded-lg hover:bg-gray-100 transition-colors"
                                        style="color: var(--color-gray-400)"
                                        title="닫기"
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

                                <div class="mb-4 flex-shrink-0">
                                    <p
                                        class="text-sm"
                                        style="color: var(--color-gray-600)"
                                    >
                                        {{ getSelectedDepartmentDescription() }}
                                    </p>
                                    <p
                                        class="text-xs mt-1"
                                        style="color: var(--color-gray-500)"
                                    >
                                        총 {{ departmentDocuments.length }}개
                                        문서
                                    </p>
                                </div>

                                <!-- 로딩 상태 -->
                                <div
                                    v-if="loadingDocuments"
                                    class="text-center py-8 flex-1 flex items-center justify-center"
                                >
                                    <div
                                        class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"
                                    ></div>
                                    <p
                                        class="text-sm mt-2"
                                        style="color: var(--color-gray-500)"
                                    >
                                        문서 목록을 불러오는 중...
                                    </p>
                                </div>

                                <!-- 문서 목록 -->
                                <div
                                    v-else-if="departmentDocuments.length > 0"
                                    class="space-y-3 flex-1 overflow-y-auto"
                                    style="max-height: calc(100vh - 280px)"
                                >
                                    <div
                                        v-for="doc in departmentDocuments"
                                        :key="doc.id"
                                        class="p-3 border rounded-lg transition-all duration-200 hover:shadow-sm"
                                        style="
                                            border-color: var(
                                                --color-border-light
                                            );
                                            background-color: var(
                                                --color-bg-primary
                                            );
                                        "
                                    >
                                        <div class="flex items-start space-x-3">
                                            <div
                                                class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                                                style="
                                                    background: linear-gradient(
                                                        135deg,
                                                        var(--color-success-50),
                                                        var(--color-success-100)
                                                    );
                                                "
                                            >
                                                <svg
                                                    class="w-4 h-4"
                                                    style="
                                                        color: var(
                                                            --color-success-600
                                                        );
                                                    "
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
                                            <div class="flex-1 min-w-0">
                                                <h4
                                                    class="text-sm font-medium truncate"
                                                    style="
                                                        color: var(
                                                            --color-gray-900
                                                        );
                                                    "
                                                >
                                                    {{
                                                        doc.documentName ||
                                                        doc.name
                                                    }}
                                                </h4>
                                                <p
                                                    class="text-xs mt-1"
                                                    style="
                                                        color: var(
                                                            --color-gray-500
                                                        );
                                                    "
                                                >
                                                    {{
                                                        formatFileSize(
                                                            doc.fileSize ||
                                                                doc.size
                                                        )
                                                    }}
                                                    •
                                                    {{
                                                        formatDate(
                                                            doc.uploadDate ||
                                                                doc.uploadedAt
                                                        )
                                                    }}
                                                    <span
                                                        v-if="doc.chunkCount"
                                                        class="ml-1 text-blue-600"
                                                    >
                                                        • {{ doc.chunkCount }}개
                                                        청크
                                                    </span>
                                                </p>
                                                <div class="mt-2">
                                                    <span
                                                        :class="[
                                                            'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
                                                            doc.status ===
                                                                'processed' ||
                                                            doc.status ===
                                                                'active'
                                                                ? 'bg-green-100 text-green-800'
                                                                : doc.status ===
                                                                  'processing'
                                                                ? 'bg-yellow-100 text-yellow-800'
                                                                : 'bg-red-100 text-red-800',
                                                        ]"
                                                    >
                                                        {{
                                                            getStatusText(
                                                                doc.status
                                                            )
                                                        }}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- 빈 상태 -->
                                <div
                                    v-else
                                    class="text-center py-8 flex-1 flex flex-col items-center justify-center"
                                >
                                    <div
                                        class="mx-auto w-12 h-12 rounded-full flex items-center justify-center mb-3"
                                        style="
                                            background: linear-gradient(
                                                135deg,
                                                var(--color-gray-100),
                                                var(--color-gray-200)
                                            );
                                        "
                                    >
                                        <svg
                                            class="w-6 h-6"
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
                                    <p
                                        class="text-sm"
                                        style="color: var(--color-gray-500)"
                                    >
                                        {{ getSelectedDepartmentName() }}에
                                        업로드된 문서가 없습니다
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 하단: 청킹 미리보기 영역 (전체 화면 너비) -->
                    <div
                        v-if="showChunkingInterface"
                        class="bg-white border-t border-gray-200 overflow-y-auto relative"
                    >
                        <!-- LLM 로딩 오버레이 (전체 화면) -->
                        <div
                            v-if="isLoadingLLMChunking"
                            class="absolute inset-0 bg-white bg-opacity-95 flex items-center justify-center z-50"
                        >
                            <div class="flex flex-col items-center space-y-6">
                                <!-- 로딩 스피너 (큰 버전) -->
                                <div class="relative w-24 h-24">
                                    <div
                                        class="absolute inset-0 border-8 border-purple-200 rounded-full"
                                    ></div>
                                    <div
                                        class="absolute inset-0 border-8 border-purple-600 rounded-full border-t-transparent animate-spin"
                                    ></div>
                                </div>

                                <!-- 로딩 메시지 -->
                                <div class="text-center max-w-md">
                                    <div
                                        class="text-2xl font-bold text-purple-800 mb-2"
                                    >
                                        ✨ AI가 문서를 분석하고 있습니다
                                    </div>
                                    <div class="text-base text-purple-600 mb-4">
                                        문서의 의미와 구조를 분석하여 최적의
                                        청크를 제안합니다
                                    </div>
                                    <div class="text-sm text-gray-500">
                                        약 10-30초 소요됩니다. 잠시만
                                        기다려주세요...
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="p-6">
                            <div class="grid grid-cols-1 xl:grid-cols-5 gap-6">
                                <!-- 청킹 설정 (좌측) -->
                                <div class="xl:col-span-1">
                                    <ChunkingSettings
                                        v-model="chunkingSettings"
                                        :document-length="documentLength"
                                        :file="selectedFile"
                                        :container="selectedContainer"
                                        :isUsingLLMSuggestions="isUsingLLMChunking"
                                        @settings-changed="
                                            handleSettingsChanged
                                        "
                                        @llm-suggestions-received="
                                            handleLLMSuggestionsReceived
                                        "
                                        @llm-suggestions-disabled="
                                            handleLLMSuggestionsDisabled
                                        "
                                        @llm-loading-start="
                                            isLoadingLLMChunking = true
                                        "
                                        @llm-loading-end="
                                            isLoadingLLMChunking = false
                                        "
                                    />
                                </div>

                                <!-- 청킹 미리보기 (우측 - 전체 영역 사용) -->
                                <div class="xl:col-span-4">
                                    <ChunkingPreview
                                        v-if="chunks.length > 0"
                                        v-model:chunks="chunks"
                                        :is-regenerating="isRegenerating"
                                        @proceed-to-embedding="
                                            proceedToEmbedding
                                        "
                                    >
                                        <template #ai-suggestion-button>
                                            <!-- AI 청킹 제안 받기 버튼 -->
                                            <button
                                                v-if="!isUsingLLMChunking"
                                                @click="requestLLMSuggestions"
                                                :disabled="isLoadingLLMChunking"
                                                class="px-4 py-2 rounded-lg font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed border-2 border-purple-500 bg-gradient-to-r from-purple-50 to-blue-50 hover:from-purple-100 hover:to-blue-100 text-purple-700 text-sm"
                                            >
                                                <div class="flex items-center space-x-2">
                                                    <span class="text-lg">✨</span>
                                                    <span class="font-bold">
                                                        AI 청킹 제안 받기
                                                    </span>
                                                </div>
                                            </button>
                                        </template>
                                        <template #ai-using-badge>
                                            <!-- AI 제안 사용 중 배지 -->
                                            <div
                                                v-if="isUsingLLMChunking"
                                                class="inline-flex items-center gap-2"
                                            >
                                                <button
                                                    @click="handleLLMSuggestionsDisabled"
                                                    class="px-4 py-2 rounded-lg font-medium transition-all duration-200 border-2 border-purple-500 bg-gradient-to-r from-purple-50 to-blue-50 hover:from-purple-100 hover:to-blue-100 text-purple-700 text-sm"
                                                    title="수동 설정으로 전환"
                                                >
                                                    <div class="flex items-center space-x-2">
                                                        <span class="text-lg">🤖</span>
                                                        <span class="font-bold">
                                                            AI 제안 사용 중
                                                        </span>
                                                        <svg
                                                            class="w-4 h-4 ml-1"
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
                                                    </div>
                                                </button>
                                                <!-- Reasoning 보기 버튼 (쪽지 아이콘) -->
                                                <div 
                                                    v-if="isUsingLLMChunking && !hasViewedReasoning"
                                                    class="relative inline-block"
                                                >
                                                    <button
                                                        ref="reasoningTooltipRef"
                                                        @click="
                                                            showReasoningModal = true;
                                                            hasViewedReasoning = true;
                                                        "
                                                        class="p-2 rounded-lg hover:bg-purple-50 transition-colors text-purple-600 hover:text-purple-700 inline-flex items-center justify-center"
                                                    >
                                                        <svg
                                                            class="w-5 h-5"
                                                            fill="none"
                                                            stroke="currentColor"
                                                            viewBox="0 0 24 24"
                                                            style="display: block;"
                                                        >
                                                            <path
                                                                stroke-linecap="round"
                                                                stroke-linejoin="round"
                                                                stroke-width="2"
                                                                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                                                            />
                                                        </svg>
                                                    </button>
                                                </div>
                                                <!-- 툴팁 - Teleport로 body에 렌더링하여 컨테이너 제약 없음 -->
                                                <Teleport to="body">
                                                    <div 
                                                        v-if="isUsingLLMChunking && !hasViewedReasoning && tooltipPosition"
                                                        class="fixed px-3 py-2 bg-gray-800 text-white text-xs rounded-lg whitespace-nowrap z-[10000] shadow-lg pointer-events-none"
                                                        :style="{
                                                            left: tooltipPosition.left + 'px',
                                                            top: tooltipPosition.top + 'px',
                                                            transform: 'translateX(-50%)'
                                                        }"
                                                    >
                                                        AI가 청킹한 이유를 확인해보세요!
                                                        <div class="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-800"></div>
                                                    </div>
                                                </Teleport>
                                            </div>
                                        </template>
                                    </ChunkingPreview>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 기존 데이터 확인 모달 제거됨 -->

        <!-- 임베딩 처리 중 전체 화면 오버레이 -->
        <div
            v-if="isUploading"
            class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        >
            <div
                class="bg-white rounded-xl shadow-xl p-8 text-center max-w-md mx-4"
            >
                <div
                    class="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"
                ></div>
                <h3 class="text-lg font-semibold text-gray-900 mb-2">
                    임베딩 처리 중...
                </h3>
                <p class="text-sm text-gray-600">
                    파일을 처리하고 있습니다. 잠시만 기다려주세요.
                </p>
            </div>
        </div>

        <!-- AI 청킹 Reasoning 팝업 -->
        <LLMChunkingReasoningModal
            v-model="showReasoningModal"
            :reasonings="llmReasonings"
        />
    </MainLayout>
</template>
<script setup>
import { ref, computed, onMounted, watch, onBeforeUnmount, nextTick } from "vue";
import { Teleport } from "vue";
import { useDataUploadStore } from "@/stores/dataUpload";
import { useRAGDepartmentsStore } from "@/stores/ragDepartments";
import {
    getQdrantCollectionInfoAPI,
    getCollectionNameForDepartment,
    getCollectionDocumentsAPI,
} from "@/services/embeddingApi";
import MainLayout from "@/components/layout/MainLayout.vue";
import ChunkingSettings from "@/components/upload/ChunkingSettings.vue";
import ChunkingPreview from "@/components/upload/ChunkingPreview.vue";
import LLMChunkingReasoningModal from "@/components/modals/LLMChunkingReasoningModal.vue";

const dataUploadStore = useDataUploadStore();
const ragDepartmentsStore = useRAGDepartmentsStore();

// 반응형 상태
const selectedFiles = ref([]);
const isDragOver = ref(false);
const isUploading = ref(false);
const fileInput = ref(null);
const selectedDepartment = ref(null); // Will be set in onMounted
const activeTab = ref(null); // No longer using "general"
const departmentDocuments = ref([]);
const loadingDocuments = ref(false);

// 청킹 관련 상태
const showChunkingInterface = ref(false);
const chunks = ref([]);
const documentLength = ref(0);
const isRegenerating = ref(false);
const chunkingSettings = ref({
    chunkingMethod: "sentence",
    chunkSize: 500,
    overlapSize: 50,
    minChunkSize: 100,
    preferSentenceBoundary: true,
    preferParagraphBoundary: false,
});

// LLM 청킹 관련 상태
const isUsingLLMChunking = ref(false);
const isLoadingLLMChunking = ref(false);
const selectedFile = ref(null);
const selectedContainer = ref("general");
const llmReasonings = ref([]); // AI 청킹 reasoning 목록
const showReasoningModal = ref(false); // reasoning 팝업 표시 여부
const hasViewedReasoning = ref(false); // reasoning 버튼을 한 번이라도 클릭했는지 여부
const reasoningTooltipRef = ref(null); // reasoning 툴팁 버튼 ref
const tooltipPosition = ref(null); // 툴팁 위치
let tooltipCleanup = null; // tooltip 이벤트 리스너 정리 함수

// 계산된 속성 (활성화된 부서만)
const departments = computed(() =>
    ragDepartmentsStore.departments.filter((dept) => dept.status === "active")
);

// 문서 관련 계산된 속성
const documents = computed(() => dataUploadStore.documents);

// 선택된 부서 이름 가져오기
const getSelectedDepartmentName = () => {
    if (!selectedDepartment.value) return null;
    const dept = ragDepartmentsStore.getDepartmentById(
        selectedDepartment.value
    );
    return dept ? dept.name : null;
};

// 선택된 부서 설명 가져오기
const getSelectedDepartmentDescription = () => {
    if (!selectedDepartment.value) return "";
    const dept = ragDepartmentsStore.getDepartmentById(
        selectedDepartment.value
    );
    return dept ? dept.description : "";
};

// 부서 선택 함수
const selectDepartment = (departmentId) => {
    selectedDepartment.value = departmentId;
};

// 파일 선택 트리거
const triggerFileInput = () => {
    fileInput.value?.click();
};

// 파일 선택 처리 (하나의 파일만 선택, 새 파일 선택 시 기존 파일 대체)
const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    // 새로운 파일을 선택하면 기존 파일을 모두 제거하고 새 파일만 추가
    selectedFiles.value = [];
    addFiles(files);
    event.target.value = ""; // 같은 파일 재선택 가능하도록
};

// 드래그 앤 드롭 처리 (하나의 파일만 선택, 새 파일 드롭 시 기존 파일 대체)
const handleDrop = (event) => {
    event.preventDefault();
    event.stopPropagation();

    if (isUploading.value) {
        return;
    }

    isDragOver.value = false;

    const files = Array.from(event.dataTransfer.files);
    // 새로운 파일을 드롭하면 기존 파일을 모두 제거하고 새 파일만 추가
    selectedFiles.value = [];
    addFiles(files);
};

const handleDragOver = (event) => {
    event.preventDefault();
    event.stopPropagation();
};

// 파일 추가 (하나의 파일만 추가)
const addFiles = (files) => {
    const validFiles = files.filter((file) => {
        // 파일 크기 체크 (10MB)
        if (file.size > 10 * 1024 * 1024) {
            alert(`${file.name}은(는) 10MB를 초과합니다.`);
            return false;
        }

        // 파일 형식 체크 (임베딩 백엔드에서 지원하는 형식)
        const allowedTypes = [".xlsx", ".xls", ".md", ".markdown"];
        const fileExtension = "." + file.name.split(".").pop().toLowerCase();
        if (!allowedTypes.includes(fileExtension)) {
            alert(
                `${
                    file.name
                }은(는) 지원하지 않는 형식입니다. 지원 형식: ${allowedTypes.join(
                    ", "
                )}`
            );
            return false;
        }

        return true;
    });

    // 첫 번째 유효한 파일만 추가 (하나의 파일만 처리)
    if (validFiles.length > 0) {
        selectedFiles.value.push(validFiles[0]);
        if (validFiles.length > 1) {
            alert(`하나의 파일만 처리됩니다. 첫 번째 파일 "${validFiles[0].name}"만 추가되었습니다.`);
        }
    }
};

// 파일 제거
const removeFile = (index) => {
    selectedFiles.value.splice(index, 1);
};

// 청킹 프로세스 시작
const startChunkingProcess = async () => {
    if (selectedFiles.value.length === 0) return;

    // RAG 선택 검증
    const container = getSelectedDepartmentName();
    if (!container) {
        alert("RAG가 선택되지 않았습니다. 다시 한 번 선택해주세요.");
        return;
    }

    isUploading.value = true;

    try {
        const results = [];

        for (const file of selectedFiles.value) {
            const fileExtension = file.name.split(".").pop().toLowerCase();

            // Markdown 파일은 청킹 미리보기 필요
            if (fileExtension === "md" || fileExtension === "markdown") {
                const preview = await dataUploadStore.previewMarkdownChunking(
                    file,
                    container,
                    {
                        chunking_strategy:
                            chunkingSettings.value.chunkingMethod,
                        chunk_size: chunkingSettings.value.chunkSize,
                        overlap: chunkingSettings.value.overlapSize,
                    }
                );

                // 청킹 미리보기 결과를 상태에 저장
                chunks.value = preview.chunks.map((chunk) => ({
                    id: chunk.chunk_id,
                    content: chunk.content,
                    qualityScore: Math.floor(Math.random() * 3) + 7, // 임시 점수
                    semanticScore: Math.floor(Math.random() * 3) + 6,
                    duplicateScore: Math.floor(Math.random() * 20),
                    isExpanded: false,
                }));

                documentLength.value = preview.content_length;
                showChunkingInterface.value = true;

                // LLM 청킹을 위한 파일 정보 설정
                selectedFile.value = file;
                selectedContainer.value = container;
                
                // 새 파일 선택 시 AI 청킹 상태 초기화
                isUsingLLMChunking.value = false;
                hasViewedReasoning.value = false;

                // 첫 번째 파일만 미리보기하고 중단
                break;
            }

            // Excel 파일은 청킹 미리보기 필요
            if (fileExtension === "xlsx" || fileExtension === "xls") {
                // Excel 전략으로 매핑 (Markdown 전략이면 기본값 사용)
                const excelStrategies = ["row_based", "column_based"];
                const currentStrategy = chunkingSettings.value.chunkingMethod;
                const excelStrategy = excelStrategies.includes(currentStrategy) 
                    ? currentStrategy 
                    : "row_based"; // 기본 Excel 전략
                
                // Excel의 경우 chunk_size는 행/열 수이므로 기본값 10 사용 (Markdown의 500은 문자 수)
                const excelChunkSize = (currentStrategy && excelStrategies.includes(currentStrategy)) 
                    ? Math.min(chunkingSettings.value.chunkSize || 10, 100)
                    : 10;
                // Excel overlap은 최대 10 (행/열 수, 문자 수가 아님)
                const excelOverlap = Math.min(chunkingSettings.value.overlapSize || 0, 10);
                
                const preview = await dataUploadStore.previewExcelChunking(
                    file,
                    container,
                    {
                        chunking_strategy: excelStrategy,
                        chunk_size: excelChunkSize,
                        overlap: excelOverlap,
                    }
                );

                // 청킹 미리보기 결과를 상태에 저장
                chunks.value = preview.chunks.map((chunk) => ({
                    id: chunk.chunk_id,
                    content: chunk.content,
                    qualityScore: Math.floor(Math.random() * 3) + 7, // 임시 점수
                    semanticScore: Math.floor(Math.random() * 3) + 6,
                    duplicateScore: Math.floor(Math.random() * 20),
                    isExpanded: false,
                }));

                documentLength.value = preview.content_length;
                showChunkingInterface.value = true;

                // LLM 청킹을 위한 파일 정보 설정
                selectedFile.value = file;
                selectedContainer.value = container;
                
                // 새 파일 선택 시 AI 청킹 상태 초기화
                isUsingLLMChunking.value = false;
                hasViewedReasoning.value = false;

                // 첫 번째 파일만 미리보기하고 중단
                break;
            }

            // 기타 파일은 바로 처리 (기존 로직)
            // Excel은 위에서 처리되므로 여기서는 제외
        }
    } catch (error) {
        alert("처리 중 오류가 발생했습니다: " + error.message);
    } finally {
        isUploading.value = false;
    }
};

// 청킹 처리 (임시 목업)
const processChunking = async (uploadResult) => {
    // 실제로는 백엔드 API 호출
    // 임시로 목업 데이터 생성
    const mockChunks = generateMockChunks();
    chunks.value = mockChunks;
    documentLength.value = mockChunks.reduce(
        (sum, chunk) => sum + chunk.content.length,
        0
    );
};

// 목업 청크 생성
const generateMockChunks = () => {
    const sampleTexts = [
        "이 문서는 OSS Knowledge 시스템에 대한 개요를 설명합니다. 오픈소스 소프트웨어의 지식을 체계적으로 관리하고 활용하기 위한 플랫폼입니다.",
        "시스템의 주요 기능으로는 문서 업로드, 청킹, 임베딩, 검색 등이 있습니다. 각 기능은 사용자의 요구사항에 맞춰 최적화되어 있습니다.",
        "청킹 기능은 문서를 의미 있는 단위로 나누어 검색 성능을 향상시킵니다. 다양한 청킹 전략을 지원하여 사용자가 원하는 방식으로 문서를 분할할 수 있습니다.",
        "임베딩 과정에서는 text-3-large 모델을 사용하여 고품질의 벡터 표현을 생성합니다. 이를 통해 정확하고 관련성 높은 검색 결과를 제공할 수 있습니다.",
        "검색 기능은 자연어 쿼리를 이해하고 관련 문서를 찾아줍니다. 사용자는 직관적인 질문을 통해 원하는 정보를 빠르게 찾을 수 있습니다.",
    ];

    return sampleTexts.map((text, index) => ({
        id: `chunk_${index + 1}`,
        content: text,
        qualityScore: Math.floor(Math.random() * 3) + 7, // 7-9점
        semanticScore: Math.floor(Math.random() * 3) + 6, // 6-8점
        duplicateScore: Math.floor(Math.random() * 20), // 0-19%
        isExpanded: false,
    }));
};

// 설정 변경 핸들러
const handleSettingsChanged = () => {
    // 설정이 변경되면 청킹 재생성
    regenerateChunks();
};

// 청킹 재생성 (디바운스 적용)
let regenerateTimeout = null;
const regenerateChunks = async () => {
    // 기존 타이머 취소
    if (regenerateTimeout) {
        clearTimeout(regenerateTimeout);
    }

    // 디바운스 적용 (300ms)
    regenerateTimeout = setTimeout(async () => {
        isRegenerating.value = true;

        try {
            if (selectedFiles.value.length === 0) return;

            const file = selectedFiles.value[0];
            const container = getSelectedDepartmentName();

            // 파일 유형에 따라 올바른 청킹 프리뷰 API 호출
            const fileExtension = file.name.split(".").pop().toLowerCase();
            let preview;
            if (fileExtension === "md" || fileExtension === "markdown") {
                preview = await dataUploadStore.previewMarkdownChunking(
                    file,
                    container,
                    {
                        chunking_strategy: chunkingSettings.value.chunkingMethod,
                        chunk_size: chunkingSettings.value.chunkSize,
                        overlap: chunkingSettings.value.overlapSize,
                    }
                );
            } else if (fileExtension === "xlsx" || fileExtension === "xls") {
                // Excel 전략 매핑 및 파라미터 정규화
                const excelStrategies = ["row_based", "column_based"];
                const currentStrategy = chunkingSettings.value.chunkingMethod;
                const excelStrategy = excelStrategies.includes(currentStrategy)
                    ? currentStrategy
                    : "row_based";
                const excelChunkSize = (currentStrategy && excelStrategies.includes(currentStrategy))
                    ? Math.min(chunkingSettings.value.chunkSize || 10, 100)
                    : 10;
                const excelOverlap = Math.min(chunkingSettings.value.overlapSize || 0, 10);

                preview = await dataUploadStore.previewExcelChunking(
                    file,
                    container,
                    {
                        chunking_strategy: excelStrategy,
                        chunk_size: excelChunkSize,
                        overlap: excelOverlap,
                    }
                );
            } else {
                throw new Error("지원되지 않는 파일 형식입니다. (.md, .markdown, .xlsx, .xls)");
            }

            // 청킹 미리보기 결과를 상태에 저장
            chunks.value = preview.chunks.map((chunk) => ({
                id: chunk.chunk_id,
                content: chunk.content,
                qualityScore: Math.floor(Math.random() * 3) + 7,
                semanticScore: Math.floor(Math.random() * 3) + 6,
                duplicateScore: Math.floor(Math.random() * 20),
                isExpanded: false,
            }));

            documentLength.value = preview.content_length;
        } catch (error) {
            alert("청킹 재생성 중 오류가 발생했습니다: " + error.message);
        } finally {
            isRegenerating.value = false;
        }
    }, 300);
};

// 임베딩 진행
const proceedToEmbedding = async (finalChunks) => {
    isUploading.value = true;

    try {
        const container = getSelectedDepartmentName();
        
        if (!container) {
            alert("부서를 선택해주세요.");
            isUploading.value = false;
            return;
        }

        // 파일 타입 확인
        const fileExtension = selectedFile.value?.name.split(".").pop().toLowerCase();
        const isExcel = fileExtension === "xlsx" || fileExtension === "xls";

        // Excel 또는 Markdown 파일 최종 처리
        const result = isExcel
            ? await dataUploadStore.confirmExcelProcessing({
                filename: selectedFile.value?.name || "document.xlsx",
                container: container,
                chunks: finalChunks.map((chunk) => ({
                    chunk_id: chunk.id,
                    content: chunk.content,
                    chunk_type: chunk.chunk_type || "text",
                    metadata: chunk.metadata || {},
                })),
                generate_embeddings: true,
                embedding_model: "text-embedding-3-large",
            })
            : await dataUploadStore.confirmMarkdownProcessing({
                filename: selectedFile.value?.name || "document.md",
                fileSize: selectedFile.value?.size || 0,
                container: container,
                departmentId: selectedDepartment.value,
                chunks: finalChunks.map((chunk) => ({
                    chunk_id: chunk.id,
                    content: chunk.content,
                    chunk_type: "text",
                    start_position: 0,
                    end_position: chunk.content.length,
                    metadata: {},
                })),
                create_graph: false,
                detect_relationships: false,
                detect_domains: false,
                generate_embeddings: true,
            embedding_model: "text-embedding-3-large",
        });

        // 처리 결과 저장
        const uploadResult = {
            filename: selectedFiles.value[0]?.name || "document.md",
            container: container,
            chunks: finalChunks.length,
            embeddings: finalChunks.length,
            status: "completed",
            timestamp: new Date(),
            jobId: result.job_id,
        };

        // 성공 메시지
        alert(
            `임베딩이 완료되었습니다! ${
                finalChunks.length
            }개의 청크가 처리되었습니다.${
                selectedDepartment.value
                    ? ` (${getSelectedDepartmentName()})`
                    : ""
            }`
        );

        // 초기화
        selectedFiles.value = [];
        showChunkingInterface.value = false;
        chunks.value = [];
        documentLength.value = 0;

        // 문서 목록 새로고침
        if (selectedDepartment.value) {
            await fetchDepartmentDocuments(selectedDepartment.value);
        }
    } catch (error) {
        alert("임베딩 중 오류가 발생했습니다: " + error.message);
    } finally {
        isUploading.value = false;
    }
};

// 기존 파일 업로드 함수 (호환성을 위해 유지)
const uploadFiles = async () => {
    if (selectedFiles.value.length === 0) return;

    isUploading.value = true;

    try {
        // 임베딩 백엔드를 통한 파일 처리
        const results = [];
        for (const file of selectedFiles.value) {
            const container = getSelectedDepartmentName();
            const result = await dataUploadStore.processFile(file, container);
            results.push(result);
        }

        selectedFiles.value = [];
        alert(
            `파일 처리가 완료되었습니다! ${
                results.length
            }개 파일이 임베딩되었습니다.${
                selectedDepartment.value
                    ? ` (${getSelectedDepartmentName()})`
                    : ""
            }`
        );
    } catch (error) {
        alert("처리 중 오류가 발생했습니다: " + error.message);
    } finally {
        isUploading.value = false;
    }
};

// 파일 크기 포맷팅
const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

// 날짜 포맷팅
const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("ko-KR", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
};

// 드래그 이벤트 처리
const handleDragEnter = (event) => {
    event.preventDefault();
    event.stopPropagation();

    if (isUploading.value) {
        return;
    }

    isDragOver.value = true;
};

const handleDragLeave = (event) => {
    event.preventDefault();
    event.stopPropagation();

    // Only change state if we're actually leaving the drop zone
    if (!event.currentTarget.contains(event.relatedTarget)) {
        isDragOver.value = false;
    }
};

// 문서 관리 관련 메서드들
const getCurrentDocuments = () => {
    if (!activeTab.value) {
        return [];
    }
    return dataUploadStore.getDepartmentDocuments(activeTab.value);
};

const getDepartmentDocuments = (departmentId) => {
    return departmentDocuments.value;
};

const getDepartmentName = (departmentId) => {
    const dept = ragDepartmentsStore.getDepartmentById(departmentId);
    return dept ? dept.name : "알 수 없음";
};

const getAllDocumentsCount = () => {
    return dataUploadStore.getAllDocuments().length;
};

const refreshDocuments = async () => {
    if (selectedDepartment.value) {
        await fetchDepartmentDocuments(selectedDepartment.value);
    }
};

// Track ongoing requests to prevent duplicate calls
const ongoingRequests = new Set();

const fetchDepartmentDocuments = async (departmentId) => {
    if (!departmentId) return;

    // Prevent duplicate requests for the same department
    if (ongoingRequests.has(departmentId)) {
        console.log(
            `⏳ Request for department ${departmentId} already in progress, skipping`
        );
        return;
    }

    console.log(`📄 Fetching documents for department ${departmentId}`);

    // Check if user is authenticated before trying to fetch department documents
    const token = localStorage.getItem("authToken");
    if (!token) {
        console.warn(
            "User not authenticated. Department documents will not be loaded."
        );
        departmentDocuments.value = [];
        return;
    }

    ongoingRequests.add(departmentId);
    loadingDocuments.value = true;

    try {
        // Get department info to get the collection name
        const department = ragDepartmentsStore.getDepartmentById(departmentId);
        if (!department) {
            console.error(`Department not found: ${departmentId}`);
            departmentDocuments.value = [];
            return;
        }

        // Convert department name to collection name
        const collectionName = getCollectionNameForDepartment(department.name);
        console.log(
            `🔍 Fetching Qdrant collection info for: ${collectionName}`
        );

        // Get Qdrant collection documents
        const collectionDocuments = await getCollectionDocumentsAPI(
            collectionName
        );
        console.log(
            `✅ Successfully fetched Qdrant collection documents for ${collectionName}:`,
            collectionDocuments
        );

        // Transform Qdrant collection documents to document format
        if (
            collectionDocuments &&
            collectionDocuments.documents &&
            collectionDocuments.documents.length > 0
        ) {
            departmentDocuments.value = collectionDocuments.documents
                .map(
                    (doc) => ({
                        id: `qdrant-${doc.document_name}`,
                        name: doc.document_name,
                        size: doc.file_size || 0,
                        uploadedAt: doc.upload_date || new Date().toISOString(),
                        status: doc.status || "processed",
                        type: doc.file_type || "unknown",
                        path: `qdrant://${collectionName}/${doc.document_name}`,
                        chunkCount: doc.chunk_count || 0,
                        container: doc.container || collectionName,
                        metadata: doc.metadata || {},
                    })
                )
                .sort((a, b) => {
                    // 시간순으로 정렬 (최신 문서가 위에 오도록)
                    const dateA = new Date(a.uploadedAt);
                    const dateB = new Date(b.uploadedAt);
                    return dateB - dateA; // 내림차순 (최신이 먼저)
                });
        } else {
            // No documents in collection, show empty state
            departmentDocuments.value = [];
        }
    } catch (error) {
        console.error(
            `❌ Failed to fetch Qdrant collection documents for department ${departmentId}:`,
            error
        );

        // If collection doesn't exist or has no documents, show empty state
        if (
            error.message.includes("404") ||
            error.message.includes("not found")
        ) {
            console.log(
                `📭 Collection not found or empty for department ${departmentId}`
            );
            departmentDocuments.value = [];
        } else {
            // For other errors, show empty state but log the error
            departmentDocuments.value = [];
        }
    } finally {
        ongoingRequests.delete(departmentId);
        loadingDocuments.value = false;
    }
};

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

const deleteDocument = async (id) => {
    if (confirm("이 문서를 삭제하시겠습니까?")) {
        try {
            const departmentId = activeTab.value;
            await dataUploadStore.deleteDocument(id, departmentId);
        } catch (error) {
            alert("삭제 중 오류가 발생했습니다: " + error.message);
        }
    }
};

const getStatusText = (status) => {
    const statusMap = {
        processed: "처리완료",
        processing: "처리중",
        failed: "실패",
    };
    return statusMap[status] || status;
};

// RAG 선택 시 문서 목록 자동 로드 (debounced to prevent multiple rapid calls)
let fetchTimeout = null;
watch(selectedDepartment, async (newDepartmentId, oldDepartmentId) => {
    console.log(
        `🔄 Department changed from ${oldDepartmentId} to ${newDepartmentId}`
    );

    // Clear any existing timeout
    if (fetchTimeout) {
        clearTimeout(fetchTimeout);
    }

    // Debounce the fetch call by 100ms (reduced from 300ms for faster response)
    fetchTimeout = setTimeout(async () => {
        if (newDepartmentId) {
            await fetchDepartmentDocuments(newDepartmentId);
        } else {
            departmentDocuments.value = [];
        }
    }, 100);
});

// 컴포넌트 마운트 시 부서 목록 로드
// LLM 청킹 제안 처리
const handleLLMSuggestionsReceived = (response) => {
    try {
        isLoadingLLMChunking.value = false; // Clear loading state

        // Reasoning 데이터 저장 (팝업 표시용)
        llmReasonings.value = response.suggested_chunks.map(
            (chunk, index) => ({
                chunkIndex: index + 1,
                reasoning: chunk.reasoning || "AI가 자동으로 청킹했습니다.",
                content: chunk.content?.substring(0, 100) + "..." || "", // 미리보기용
            })
        );

        // LLM 응답을 기존 청크 형식으로 변환
        const transformedChunks = response.suggested_chunks.map(
            (chunk, index) => ({
                id: `llm-chunk-${index}`,
                content: chunk.content,
                startPosition: chunk.start_position,
                endPosition: chunk.end_position,
                reasoning: chunk.reasoning,
                semanticScore: chunk.semantic_score,
                isLLMSuggested: true,
            })
        );

        // 청크 업데이트
        chunks.value = transformedChunks;

        // LLM 모드 활성화
        isUsingLLMChunking.value = true;

        // 새로운 제안을 받으면 reasoning 버튼을 다시 표시
        hasViewedReasoning.value = false;

        console.log(
            `LLM 청킹 제안을 받았습니다: ${response.total_chunks}개 청크`
        );
    } catch (error) {
        isLoadingLLMChunking.value = false; // Clear loading state on error
        console.error("LLM 제안 처리 중 오류:", error);
        alert("LLM 제안을 처리하는 중 오류가 발생했습니다.");
    }
};

// LLM 청킹 제안 요청
const requestLLMSuggestions = async () => {
    if (!selectedFile.value) {
        alert("파일을 먼저 선택해주세요.");
        return;
    }

    // 파일 크기 확인 (1MB)
    const MAX_LLM_FILE_SIZE = 1024 * 1024; // 1MB
    if (selectedFile.value.size > MAX_LLM_FILE_SIZE) {
        alert(
            "파일이 너무 큽니다. LLM 청킹 제안은 1MB 이하의 파일만 지원합니다."
        );
        return;
    }

    try {
        isLoadingLLMChunking.value = true;

        // LLM 청킹 제안 요청
        // Excel 파일인지 확인
        const fileExtension = selectedFile.value?.name.split(".").pop().toLowerCase();
        const isExcel = fileExtension === "xlsx" || fileExtension === "xls";

        const response = isExcel
            ? await dataUploadStore.getExcelLLMChunkingSuggestions(
                selectedFile.value,
                selectedContainer.value || "general"
            )
            : await dataUploadStore.getLLMChunkingSuggestions(
                selectedFile.value,
                selectedContainer.value || "general"
            );

        // 제안된 청크 처리
        handleLLMSuggestionsReceived(response);
    } catch (error) {
        isLoadingLLMChunking.value = false;
        console.error("LLM 청킹 제안 요청 실패:", error);
        alert(`LLM 청킹 제안을 가져오는데 실패했습니다: ${error.message}`);
    }
};

// LLM 청킹 제안 비활성화
const handleLLMSuggestionsDisabled = () => {
    isUsingLLMChunking.value = false;
    // 수동 청킹 설정으로 청크 재생성
    regenerateChunks();
    console.log("LLM 청킹 제안이 비활성화되었습니다.");
};

// 툴팁 위치 업데이트
const updateTooltipPosition = () => {
    nextTick(() => {
        if (reasoningTooltipRef.value) {
            const rect = reasoningTooltipRef.value.getBoundingClientRect();
            const header = document.querySelector('header');
            const headerHeight = header ? header.getBoundingClientRect().height : 80;
            const tooltipHeight = 40; // tooltip 높이 대략값
            const margin = 8; // 여백
            const calculatedTop = rect.top - tooltipHeight - margin;
            
            // 헤더 아래로 제한 (최소 top 값을 헤더 높이 + 여백으로)
            const minTop = headerHeight + margin;
            
            tooltipPosition.value = {
                left: rect.left + rect.width / 2, // 버튼 중앙
                top: Math.max(calculatedTop, minTop), // 헤더 아래로 제한
            };
        }
    });
};

// 버튼이 표시될 때 자동으로 tooltip 위치 계산
watch(
    () => isUsingLLMChunking.value && !hasViewedReasoning.value,
    (shouldShow) => {
        if (shouldShow) {
            // 짧은 딜레이 후 위치 계산 (DOM 렌더링 대기)
            setTimeout(() => {
                updateTooltipPosition();
                // 스크롤 및 리사이즈 시에도 위치 업데이트
                const updateOnScroll = () => updateTooltipPosition();
                window.addEventListener('scroll', updateOnScroll, true);
                window.addEventListener('resize', updateOnScroll);
                
                // cleanup 함수 저장
                tooltipCleanup = () => {
                    window.removeEventListener('scroll', updateOnScroll, true);
                    window.removeEventListener('resize', updateOnScroll);
                };
            }, 100);
        } else {
            tooltipPosition.value = null;
            // 이벤트 리스너 정리
            if (tooltipCleanup) {
                tooltipCleanup();
                tooltipCleanup = null;
            }
        }
    },
    { immediate: true }
);

onMounted(() => {
    // 부서 목록만 로드 (문서는 RAG 관리 페이지에서 관리)
    dataUploadStore.fetchDocuments();
    
    // 첫 번째 부서를 기본 선택
    if (departments.value.length > 0) {
        selectedDepartment.value = departments.value[0].id;
        activeTab.value = departments.value[0].id;
    }
});

onBeforeUnmount(() => {
    // 타이머 정리
    if (regenerateTimeout) {
        clearTimeout(regenerateTimeout);
    }
    if (fetchTimeout) {
        clearTimeout(fetchTimeout);
    }
    // tooltip 이벤트 리스너 정리
    if (tooltipCleanup) {
        tooltipCleanup();
    }
});
</script>

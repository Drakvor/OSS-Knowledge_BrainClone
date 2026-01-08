<template>
    <div
        class="bg-white rounded-xl shadow-md border-0 overflow-hidden relative"
    >
        <div class="p-4">
            <div class="text-center mb-4">
                <h2
                    class="text-lg font-bold mb-1"
                    style="color: var(--color-gray-900)"
                >
                    청킹 설정
                </h2>
                <p class="text-gray-600 text-xs">문서 분할 설정</p>
            </div>

            <!-- 청킹 방식 선택 -->
            <div
                class="mb-4"
                :class="{
                    'opacity-50 pointer-events-none': props.isUsingLLMSuggestions,
                }"
            >
                <label
                    class="block text-sm font-semibold mb-2"
                    style="color: var(--color-gray-800)"
                >
                    청킹 방식
                </label>
                <div class="space-y-2">
                    <button
                        v-for="method in chunkingMethods"
                        :key="method.value"
                        @click="
                            () => {
                                settings.chunkingMethod = method.value;
                                emit('settingsChanged');
                            }
                        "
                        :class="[
                            'w-full p-3 rounded-lg border-2 transition-all duration-200 text-left',
                            settings.chunkingMethod === method.value
                                ? 'border-blue-500 bg-blue-100'
                                : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50',
                        ]"
                    >
                        <div class="flex items-center space-x-2">
                            <span class="text-lg">{{ method.icon }}</span>
                            <div>
                                <div
                                    class="text-sm font-medium"
                                    style="color: var(--color-gray-900)"
                                >
                                    {{ method.name }}
                                </div>
                                <div
                                    class="text-xs"
                                    style="color: var(--color-gray-600)"
                                >
                                    {{ method.description }}
                                </div>
                            </div>
                        </div>
                    </button>
                </div>
            </div>

            <!-- 청크 크기 설정 (Excel: 행 수, Markdown: 문자 수) -->
            <div
                class="mb-4"
                :class="{
                    'opacity-50 pointer-events-none': props.isUsingLLMSuggestions,
                }"
            >
                <label
                    class="block text-sm font-semibold mb-2"
                    style="color: var(--color-gray-800)"
                >
                    {{ isExcelFile ? (settings.chunkingMethod === 'column_based' ? '열 수' : '행 수') : '청크 크기' }}
                </label>
                <div v-if="!isExcelFile" class="grid grid-cols-2 gap-2">
                    <button
                        v-for="size in chunkSizes"
                        :key="size.value"
                        @click="
                            () => {
                                settings.chunkSize = size.value;
                                emit('settingsChanged');
                            }
                        "
                        :class="[
                            'p-2 rounded-lg border-2 transition-all duration-200 text-center',
                            settings.chunkSize === size.value
                                ? 'border-blue-500 bg-blue-100'
                                : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50',
                        ]"
                    >
                        <div
                            class="text-xs font-medium"
                            style="color: var(--color-gray-900)"
                        >
                            {{ size.label }}
                        </div>
                        <div
                            class="text-xs mt-1"
                            style="color: var(--color-gray-600)"
                        >
                            {{ size.value }}자
                        </div>
                    </button>
                </div>
                <div v-else class="grid grid-cols-2 gap-2">
                    <button
                        v-for="size in excelChunkSizes"
                        :key="size.value"
                        @click="
                            () => {
                                settings.chunkSize = size.value;
                                emit('settingsChanged');
                            }
                        "
                        :class="[
                            'p-2 rounded-lg border-2 transition-all duration-200 text-center',
                            settings.chunkSize === size.value
                                ? 'border-blue-500 bg-blue-100'
                                : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50',
                        ]"
                    >
                        <div
                            class="text-xs font-medium"
                            style="color: var(--color-gray-900)"
                        >
                            {{ size.label }}
                        </div>
                        <div
                            class="text-xs mt-1"
                            style="color: var(--color-gray-600)"
                        >
                            {{ size.value }}{{ settings.chunkingMethod === 'column_based' ? '열' : '행' }}
                        </div>
                    </button>
                </div>

                <!-- 커스텀 크기 입력 -->
                <div class="mt-2">
                    <div class="flex items-center space-x-2">
                        <input
                            v-if="!isExcelFile"
                            v-model.number="customChunkSize"
                            type="number"
                            min="100"
                            max="2000"
                            step="50"
                            class="flex-1 px-2 py-1.5 border border-gray-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent"
                            placeholder="500"
                        />
                        <input
                            v-else
                            v-model.number="customChunkSize"
                            type="number"
                            min="1"
                            max="100"
                            step="1"
                            class="flex-1 px-2 py-1.5 border border-gray-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent"
                            placeholder="10"
                        />
                        <button
                            @click="applyCustomSize()"
                            class="px-2 py-1.5 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition-colors"
                        >
                            적용
                        </button>
                    </div>
                </div>
            </div>

            <!-- 청크 겹침 설정 (Excel: 행 중복, Markdown: 문자 중복) -->
            <div
                class="mb-4"
                :class="{
                    'opacity-50 pointer-events-none': props.isUsingLLMSuggestions,
                }"
            >
                <label
                    class="block text-sm font-semibold mb-2"
                    style="color: var(--color-gray-800)"
                >
                    {{ isExcelFile ? (settings.chunkingMethod === 'column_based' ? '열 중복' : '행 중복') : '청크 겹침' }}
                </label>
                <div v-if="!isExcelFile" class="grid grid-cols-2 gap-2">
                    <button
                        v-for="overlap in overlapSizes"
                        :key="overlap.value"
                        @click="
                            () => {
                                settings.overlapSize = overlap.value;
                                emit('settingsChanged');
                            }
                        "
                        :class="[
                            'p-2 rounded-lg border-2 transition-all duration-200 text-center',
                            settings.overlapSize === overlap.value
                                ? 'border-blue-500 bg-blue-100'
                                : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50',
                        ]"
                    >
                        <div
                            class="text-xs font-medium"
                            style="color: var(--color-gray-900)"
                        >
                            {{ overlap.label }}
                        </div>
                        <div
                            class="text-xs mt-1"
                            style="color: var(--color-gray-600)"
                        >
                            {{ overlap.value }}자
                        </div>
                    </button>
                </div>
                <div v-else class="grid grid-cols-2 gap-2">
                    <button
                        v-for="overlap in excelOverlapSizes"
                        :key="overlap.value"
                        @click="
                            () => {
                                settings.overlapSize = overlap.value;
                                emit('settingsChanged');
                            }
                        "
                        :class="[
                            'p-2 rounded-lg border-2 transition-all duration-200 text-center',
                            settings.overlapSize === overlap.value
                                ? 'border-blue-500 bg-blue-100'
                                : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50',
                        ]"
                    >
                        <div
                            class="text-xs font-medium"
                            style="color: var(--color-gray-900)"
                        >
                            {{ overlap.label }}
                        </div>
                        <div
                            class="text-xs mt-1"
                            style="color: var(--color-gray-600)"
                        >
                            {{ overlap.value }}{{ settings.chunkingMethod === 'column_based' ? '열' : '행' }}
                        </div>
                    </button>
                </div>
            </div>

            <!-- 고급 설정 -->
            <div
                class="mb-4"
                :class="{
                    'opacity-50 pointer-events-none': props.isUsingLLMSuggestions,
                }"
            >
                <div class="flex items-center justify-between mb-2">
                    <label
                        class="text-sm font-semibold"
                        style="color: var(--color-gray-800)"
                    >
                        고급 설정
                    </label>
                    <button
                        @click="showAdvanced = !showAdvanced"
                        class="text-xs text-blue-600 hover:text-blue-700 transition-colors"
                    >
                        {{ showAdvanced ? "숨기기" : "보기" }}
                    </button>
                </div>

                <div
                    v-if="showAdvanced"
                    class="space-y-3 p-3 bg-gray-50 rounded-lg"
                >
                    <!-- 최소 청크 크기 -->
                    <div>
                        <label
                            class="block text-xs font-medium mb-1"
                            style="color: var(--color-gray-700)"
                        >
                            최소 청크 크기
                        </label>
                        <input
                            v-model.number="settings.minChunkSize"
                            type="number"
                            min="50"
                            max="500"
                            step="25"
                            class="w-full px-2 py-1.5 border border-gray-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>

                    <!-- 문장 경계 우선 -->
                    <div class="flex items-center space-x-2">
                        <input
                            v-model="settings.preferSentenceBoundary"
                            type="checkbox"
                            id="sentenceBoundary"
                            class="w-3 h-3 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                        <label
                            for="sentenceBoundary"
                            class="text-xs font-medium"
                            style="color: var(--color-gray-700)"
                        >
                            문장 경계 우선
                        </label>
                    </div>

                    <!-- 단락 경계 우선 -->
                    <div class="flex items-center space-x-2">
                        <input
                            v-model="settings.preferParagraphBoundary"
                            type="checkbox"
                            id="paragraphBoundary"
                            class="w-3 h-3 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                        <label
                            for="paragraphBoundary"
                            class="text-xs font-medium"
                            style="color: var(--color-gray-700)"
                        >
                            단락 경계 우선
                        </label>
                    </div>
                </div>
            </div>

            <!-- 미리보기 정보 -->
            <div class="bg-blue-50 rounded-lg p-3">
                <div class="flex items-center space-x-1 mb-2">
                    <svg
                        class="w-4 h-4 text-blue-600"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                    </svg>
                    <span class="text-xs font-medium text-blue-800"
                        >예상 결과</span
                    >
                </div>
                <div class="text-xs text-blue-700 space-y-1">
                    <p>• 크기: {{ settings.chunkSize }}자</p>
                    <p>• 겹침: {{ settings.overlapSize }}자</p>
                    <p>
                        • 방식:
                        {{ getChunkingMethodName(settings.chunkingMethod) }}
                    </p>
                    <p v-if="estimatedChunks > 0">
                        • 예상: {{ estimatedChunks }}개
                    </p>
                </div>
            </div>
        </div>

        <!-- LLM 로딩 오버레이 -->
        <div
            v-if="isRequestingLLM"
            class="absolute inset-0 bg-white bg-opacity-90 flex flex-col items-center justify-center z-50 rounded-xl"
        >
            <div class="flex flex-col items-center space-y-4">
                <!-- 로딩 스피너 -->
                <div class="relative w-16 h-16">
                    <div
                        class="absolute inset-0 border-4 border-purple-200 rounded-full"
                    ></div>
                    <div
                        class="absolute inset-0 border-4 border-purple-600 rounded-full border-t-transparent animate-spin"
                    ></div>
                </div>

                <!-- 로딩 메시지 -->
                <div class="text-center">
                    <div class="text-lg font-semibold text-purple-800 mb-1">
                        AI가 문서를 분석 중입니다...
                    </div>
                    <div class="text-sm text-purple-600">
                        약 10-30초 소요됩니다
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { useDataUploadStore } from "@/stores/dataUpload";

// Props
const props = defineProps({
    modelValue: {
        type: Object,
        default: () => ({
            chunkingMethod: "sentence",
            chunkSize: 500,
            overlapSize: 50,
            minChunkSize: 100,
            preferSentenceBoundary: true,
            preferParagraphBoundary: false,
        }),
    },
    documentLength: {
        type: Number,
        default: 0,
    },
    file: {
        type: File,
        default: null,
    },
    container: {
        type: String,
        default: "general",
    },
    isUsingLLMSuggestions: {
        type: Boolean,
        default: false,
    },
});

// Emits
const emit = defineEmits([
    "update:modelValue",
    "settingsChanged",
    "llmSuggestionsReceived",
    "llmSuggestionsDisabled",
    "llmLoadingStart",
    "llmLoadingEnd",
]);

// 반응형 상태
const showAdvanced = ref(false);
const customChunkSize = ref(500);

// LLM 청킹 관련 상태
const isRequestingLLM = ref(false);
// isUsingLLMSuggestions는 이제 prop으로 받음

// Store
const dataUploadStore = useDataUploadStore();

// 청킹 방식 옵션
// Excel 파일인지 확인
const isExcelFile = computed(() => {
    if (!props.file) return false;
    const ext = props.file.name.split(".").pop().toLowerCase();
    return ext === "xlsx" || ext === "xls";
});

const chunkingMethods = computed(() => {
    if (isExcelFile.value) {
        // Excel 전용 청킹 방식
        return [
            {
                value: "row_based",
                name: "행 기반",
                description: "행 단위로 그룹화",
                icon: "📊",
            },
            {
                value: "column_based",
                name: "열 기반",
                description: "열 단위로 그룹화",
                icon: "📑",
            },
        ];
    }
    // Markdown 전용 청킹 방식
    return [
        {
            value: "sentence",
            name: "문장 단위",
            description: "문장 경계에서 분할",
            icon: "📝",
        },
        {
            value: "paragraph",
            name: "단락 단위",
            description: "단락 경계에서 분할",
            icon: "📄",
        },
        {
            value: "fixed",
            name: "고정 길이",
            description: "정확한 문자 수로 분할",
            icon: "📏",
        },
    ];
});

// 청크 크기 옵션
const chunkSizes = [
    { value: 300, label: "소형" },
    { value: 500, label: "중형" },
    { value: 800, label: "대형" },
    { value: 1000, label: "초대형" },
];

// Excel용 청크 크기 옵션 (행/열 수, 최대 100)
const excelChunkSizes = [
    { value: 5, label: "매우 작게" },
    { value: 10, label: "작게" },
    { value: 20, label: "보통" },
    { value: 50, label: "크게" },
    { value: 100, label: "최대" },
];

// 겹침 크기 옵션 (Markdown용 - 문자 수)
const overlapSizes = [
    { value: 0, label: "없음" },
    { value: 25, label: "소량" },
    { value: 50, label: "보통" },
    { value: 100, label: "많음" },
];

// Excel용 겹침 크기 옵션 (행/열 수, 최대 10)
const excelOverlapSizes = [
    { value: 0, label: "없음" },
    { value: 2, label: "소량" },
    { value: 5, label: "보통" },
    { value: 10, label: "많음" },
];


// 설정 객체
const settings = ref({ ...props.modelValue });

// 예상 청크 수 계산 (순환 참조 방지)
const estimatedChunks = computed(() => {
    if (props.documentLength === 0) return 0;

    // 현재 설정값을 직접 사용하여 계산
    const currentChunkSize = settings.value.chunkSize;
    const currentOverlapSize = settings.value.overlapSize;
    const effectiveChunkSize = currentChunkSize - currentOverlapSize;

    if (effectiveChunkSize <= 0) return 0;

    return Math.ceil(props.documentLength / effectiveChunkSize);
});

// 청킹 방식 이름 가져오기
const getChunkingMethodName = (method) => {
    const found = chunkingMethods.value.find((m) => m.value === method);
    return found ? found.name : method;
};

// 커스텀 크기 적용
const applyCustomSize = () => {
    if (!isExcelFile.value) {
    if (customChunkSize.value >= 100 && customChunkSize.value <= 2000) {
        settings.value.chunkSize = customChunkSize.value;
        emit("settingsChanged");
        }
    } else {
        if (customChunkSize.value >= 1 && customChunkSize.value <= 100) {
            settings.value.chunkSize = customChunkSize.value;
            emit("settingsChanged");
        }
    }
};


// 설정 변경 감지 (디바운스 적용)
let settingsTimeout = null;
watch(
    settings,
    (newSettings) => {
        // 기존 타이머 취소
        if (settingsTimeout) {
            clearTimeout(settingsTimeout);
        }

        // 디바운스 적용 (100ms)
        settingsTimeout = setTimeout(() => {
            emit("update:modelValue", newSettings);
        }, 100);
    },
    { deep: true }
);

// Props 변경 감지 (즉시 반영)
watch(
    () => props.modelValue,
    (newValue) => {
        // 기존 타이머 취소
        if (settingsTimeout) {
            clearTimeout(settingsTimeout);
        }

        settings.value = { ...newValue };
    },
    { deep: true, immediate: true }
);

// LLM 청킹 제안 요청
const requestLLMSuggestions = async () => {
    if (!props.file) {
        alert("파일을 먼저 선택해주세요.");
        return;
    }

    // 파일 크기 확인 (1MB)
    const MAX_LLM_FILE_SIZE = 1024 * 1024; // 1MB
    if (props.file.size > MAX_LLM_FILE_SIZE) {
        alert(
            "파일이 너무 큽니다. LLM 청킹 제안은 1MB 이하의 파일만 지원합니다."
        );
        return;
    }

    try {
        isRequestingLLM.value = true;
        emit("llmLoadingStart"); // Notify parent

        // LLM 청킹 제안 요청
        const response = await dataUploadStore.getLLMChunkingSuggestions(
            props.file,
            props.container || "general"
        );

        // 제안된 청크를 부모 컴포넌트로 전달
        emit("llmSuggestionsReceived", response);
    } catch (error) {
        console.error("LLM 청킹 제안 요청 실패:", error);
        alert(`LLM 청킹 제안을 가져오는데 실패했습니다: ${error.message}`);
    } finally {
        isRequestingLLM.value = false;
        emit("llmLoadingEnd"); // Notify parent
    }
};

// LLM 제안 비활성화
const disableLLMSuggestions = () => {
    emit("llmSuggestionsDisabled");
};
</script>

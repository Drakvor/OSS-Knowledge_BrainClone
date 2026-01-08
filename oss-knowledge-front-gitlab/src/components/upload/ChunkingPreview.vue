<template>
    <div class="bg-white rounded-xl shadow-md border-0 overflow-hidden">
        <div class="p-6">
            <div class="mb-6">
                <!-- 헤더 첫 번째 줄: 제목 + AI 버튼 -->
                <div class="flex items-center justify-between mb-2" style="overflow: visible; position: relative; z-index: 10;">
                    <div class="flex items-center gap-3" style="overflow: visible; position: relative; z-index: 10;">
                        <h2
                            class="text-2xl font-bold"
                            style="color: var(--color-gray-900)"
                        >
                            청킹 미리보기
                        </h2>
                        <span class="text-gray-400">·</span>
                        <!-- AI 청킹 제안 받기 버튼 (slot으로 받기) -->
                        <slot name="ai-suggestion-button"></slot>
                        <!-- AI 제안 사용 중 배지 (slot으로 받기) -->
                        <slot name="ai-using-badge"></slot>
                    </div>
                    <button
                        @click="toggleEditMode"
                        :class="[
                            'px-4 py-2 rounded-lg font-medium transition-colors',
                            editMode
                                ? 'bg-blue-500 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200',
                        ]"
                    >
                        {{ editMode ? "편집 완료" : "편집 모드" }}
                    </button>
                </div>
                <!-- 헤더 두 번째 줄: 설명 -->
                <p class="text-gray-600 text-sm">
                    문서가 {{ chunks.length }}개의 청크로 나뉘었습니다
                </p>
            </div>

            <!-- 청크 통계 -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div class="bg-blue-50 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-blue-600">
                        {{ chunks.length }}
                    </div>
                    <div class="text-sm text-blue-800">총 청크 수</div>
                </div>
                <div class="bg-green-50 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-green-600">
                        {{ averageChunkSize }}
                    </div>
                    <div class="text-sm text-green-800">평균 크기</div>
                </div>
                <div class="bg-yellow-50 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-yellow-600">
                        {{ minChunkSize }}
                    </div>
                    <div class="text-sm text-yellow-800">최소 크기</div>
                </div>
                <div class="bg-red-50 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-red-600">
                        {{ maxChunkSize }}
                    </div>
                    <div class="text-sm text-red-800">최대 크기</div>
                </div>
            </div>

            <!-- 청킹 재생성 중 로딩 상태 -->
            <div
                v-if="isRegenerating"
                class="flex items-center justify-center py-12"
            >
                <div class="text-center">
                    <div
                        class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"
                    ></div>
                    <p class="text-gray-600">청킹을 재생성하고 있습니다...</p>
                </div>
            </div>

            <!-- 청크 목록 -->
            <div
                v-else
                class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 max-h-96 overflow-y-auto"
            >
                <div
                    v-for="(chunk, index) in chunks"
                    :key="chunk.id"
                    :class="[
                        'group relative p-4 rounded-lg border-2 transition-all duration-200',
                        editMode
                            ? 'border-gray-200 hover:border-blue-300 hover:shadow-md'
                            : 'border-gray-100 hover:border-gray-200',
                        selectedChunks.includes(chunk.id)
                            ? 'border-blue-500 bg-blue-50'
                            : 'bg-white',
                    ]"
                >
                    <!-- 청크 헤더 -->
                    <div class="flex items-center justify-between mb-3">
                        <div class="flex items-center space-x-3">
                            <div class="flex items-center space-x-2">
                                <span class="text-sm font-medium text-gray-500"
                                    >#{{ index + 1 }}</span
                                >
                                <span
                                    class="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded-full"
                                >
                                    {{ chunk.content.length }}자
                                </span>
                                <span
                                    class="text-xs px-2 py-1 bg-blue-100 text-blue-600 rounded-full"
                                >
                                    {{ estimateTokens(chunk.content) }}토큰
                                </span>
                            </div>
                        </div>

                        <!-- 편집 모드 버튼들 -->
                        <div
                            v-if="editMode"
                            class="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                            <div class="relative group/button">
                                <button
                                    @click.stop="selectChunk(chunk.id)"
                                    @mouseenter.stop="showTooltip($event, 'select', index)"
                                    @mouseleave.stop="hideTooltip('select', index)"
                                    :class="[
                                        'p-1.5 rounded transition-colors',
                                        selectedChunks.includes(chunk.id)
                                            ? 'bg-blue-500 text-white'
                                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
                                    ]"
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
                                            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                                        />
                                    </svg>
                                </button>
                                <!-- 툴팁 -->
                                <div
                                    v-if="getTooltipState('select', index).show"
                                    :style="getTooltipState('select', index).style"
                                    class="fixed px-2 py-1 bg-gray-900 text-white text-xs rounded whitespace-nowrap pointer-events-none z-[9999]"
                                >
                                    {{ selectedChunks.includes(chunk.id) ? '선택 해제' : '청크 선택 (병합용)' }}
                                    <div
                                        :class="[
                                            getTooltipState('select', index).arrowClass,
                                            getTooltipState('select', index).arrowClass?.includes('top-full') 
                                                ? 'border-t-gray-900' 
                                                : 'border-b-gray-900'
                                        ]"
                                        class="absolute left-1/2 transform -translate-x-1/2 border-4 border-transparent"
                                    ></div>
                                </div>
                            </div>
                            <div class="relative group/button">
                                <button
                                    @click.stop="splitChunk(index)"
                                    @mouseenter.stop="showTooltip($event, 'split', index)"
                                    @mouseleave.stop="hideTooltip('split', index)"
                                    class="p-1.5 bg-yellow-100 text-yellow-600 rounded hover:bg-yellow-200 transition-colors"
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
                                            d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4"
                                        />
                                    </svg>
                                </button>
                                <!-- 툴팁 -->
                                <div
                                    v-if="getTooltipState('split', index).show"
                                    :style="getTooltipState('split', index).style"
                                    class="fixed px-2 py-1 bg-gray-900 text-white text-xs rounded whitespace-nowrap pointer-events-none z-[9999]"
                                >
                                    청크 분할 (반으로 나누기)
                                    <div
                                        :class="[
                                            getTooltipState('split', index).arrowClass,
                                            getTooltipState('split', index).arrowClass?.includes('top-full') 
                                                ? 'border-t-gray-900' 
                                                : 'border-b-gray-900'
                                        ]"
                                        class="absolute left-1/2 transform -translate-x-1/2 border-4 border-transparent"
                                    ></div>
                                </div>
                            </div>
                            <div class="relative group/button">
                                <button
                                    @click.stop="deleteChunk(index)"
                                    @mouseenter.stop="showTooltip($event, 'delete', index)"
                                    @mouseleave.stop="hideTooltip('delete', index)"
                                    class="p-1.5 bg-red-100 text-red-600 rounded hover:bg-red-200 transition-colors"
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
                                <div
                                    v-if="getTooltipState('delete', index).show"
                                    :style="getTooltipState('delete', index).style"
                                    class="fixed px-2 py-1 bg-gray-900 text-white text-xs rounded whitespace-nowrap pointer-events-none z-[9999]"
                                >
                                    청크 삭제
                                    <div
                                        :class="[
                                            getTooltipState('delete', index).arrowClass,
                                            getTooltipState('delete', index).arrowClass?.includes('top-full') 
                                                ? 'border-t-gray-900' 
                                                : 'border-b-gray-900'
                                        ]"
                                        class="absolute left-1/2 transform -translate-x-1/2 border-4 border-transparent"
                                    ></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 청크 내용 -->
                    <div class="text-sm text-gray-700 leading-relaxed">
                        <!-- 편집 모드: textarea로 직접 수정 가능 -->
                        <textarea
                            v-if="editMode"
                            :value="chunk.content"
                            @input="(e) => handleChunkContentInput(e, index)"
                            class="w-full p-2 border border-gray-300 rounded-md text-sm resize-y focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent min-h-[100px]"
                            :style="{ height: 'auto' }"
                            placeholder="청크 내용을 입력하세요"
                        ></textarea>
                        <!-- 일반 모드: 읽기 전용 -->
                        <div v-else>
                            <div
                                v-if="
                                    chunk.isExpanded || chunk.content.length <= 150
                                "
                            >
                                {{ chunk.content }}
                            </div>
                            <div v-else>
                                {{ chunk.content.substring(0, 150) }}...
                                <button
                                    @click="expandChunk(chunk.id)"
                                    class="text-blue-600 hover:text-blue-700 ml-1 font-medium text-xs"
                                >
                                    더 보기
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- 청크 품질 지표 -->
                    <div
                        class="mt-3 flex items-center space-x-4 text-xs text-gray-500"
                    >
                        <div class="flex items-center space-x-1">
                            <div
                                :class="[
                                    'w-2 h-2 rounded-full',
                                    getQualityColor(chunk.qualityScore),
                                ]"
                            ></div>
                            <span>품질: {{ chunk.qualityScore }}/10</span>
                        </div>
                        <div
                            v-if="chunk.semanticScore"
                            class="flex items-center space-x-1"
                        >
                            <span
                                >의미연속성: {{ chunk.semanticScore }}/10</span
                            >
                        </div>
                        <div
                            v-if="chunk.duplicateScore"
                            class="flex items-center space-x-1"
                        >
                            <span>중복도: {{ chunk.duplicateScore }}%</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 일괄 작업 버튼 (편집 모드) -->
            <div
                v-if="editMode && selectedChunks.length > 0"
                class="mt-6 p-4 bg-blue-50 rounded-lg"
            >
                <div class="flex items-center justify-between">
                    <span class="text-sm font-medium text-blue-800">
                        {{ selectedChunks.length }}개 청크 선택됨
                    </span>
                    <div class="flex items-center space-x-2">
                        <button
                            @click="mergeSelectedChunks"
                            class="px-3 py-1.5 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 transition-colors"
                        >
                            병합
                        </button>
                        <button
                            @click="deleteSelectedChunks"
                            class="px-3 py-1.5 bg-red-500 text-white text-sm rounded-lg hover:bg-red-600 transition-colors"
                        >
                            삭제
                        </button>
                        <button
                            @click="clearSelection"
                            class="px-3 py-1.5 bg-gray-500 text-white text-sm rounded-lg hover:bg-gray-600 transition-colors"
                        >
                            선택 해제
                        </button>
                    </div>
                </div>
            </div>

            <!-- 최종 확인 -->
            <div class="mt-6 p-4 bg-green-50 rounded-lg">
                <div class="flex items-center justify-between">
                    <div>
                        <h3 class="text-lg font-semibold text-green-800 mb-1">
                            청킹 완료
                        </h3>
                        <p class="text-sm text-green-700">
                            {{ chunks.length }}개의 청크가 준비되었습니다.
                            임베딩을 진행하시겠습니까?
                        </p>
                    </div>
                    <button
                        @click="proceedToEmbedding"
                        :disabled="chunks.length === 0"
                        class="px-6 py-3 bg-green-500 text-white font-semibold rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        임베딩 시작
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";

// Props
const props = defineProps({
    chunks: {
        type: Array,
        default: () => [],
    },
    isRegenerating: {
        type: Boolean,
        default: false,
    },
});

// Emits
const emit = defineEmits(["update:chunks", "proceed-to-embedding"]);

// 반응형 상태
const editMode = ref(false);
const selectedChunks = ref([]);
const tooltipStates = ref({});

// 툴팁 상태 가져오기 (안전한 접근)
const getTooltipState = (type, index) => {
    const key = `${type}-${index}`;
    return tooltipStates.value[key] || { show: false };
};

// 계산된 속성
const averageChunkSize = computed(() => {
    if (props.chunks.length === 0) return 0;
    const total = props.chunks.reduce(
        (sum, chunk) => sum + chunk.content.length,
        0
    );
    return Math.round(total / props.chunks.length);
});

const minChunkSize = computed(() => {
    if (props.chunks.length === 0) return 0;
    return Math.min(...props.chunks.map((chunk) => chunk.content.length));
});

const maxChunkSize = computed(() => {
    if (props.chunks.length === 0) return 0;
    return Math.max(...props.chunks.map((chunk) => chunk.content.length));
});

// 토큰 수 추정 (대략적)
const estimateTokens = (text) => {
    // 한국어는 보통 1토큰당 1.5-2자 정도
    return Math.ceil(text.length / 1.7);
};

// 품질 점수에 따른 색상
const getQualityColor = (score) => {
    if (score >= 8) return "bg-green-500";
    if (score >= 6) return "bg-yellow-500";
    return "bg-red-500";
};

// 청크 확장/축소
const expandChunk = (chunkId) => {
    const chunk = props.chunks.find((c) => c.id === chunkId);
    if (chunk) {
        chunk.isExpanded = true;
    }
};

// 편집 모드 토글
const toggleEditMode = () => {
    editMode.value = !editMode.value;
    if (!editMode.value) {
        selectedChunks.value = [];
    }
};

// 청크 선택
const selectChunk = (chunkId) => {
    const index = selectedChunks.value.indexOf(chunkId);
    if (index > -1) {
        selectedChunks.value.splice(index, 1);
    } else {
        selectedChunks.value.push(chunkId);
    }
};

// 청크 분할
const splitChunk = (index) => {
    try {
        const chunk = props.chunks[index];
        if (!chunk) {
            console.warn('Chunk not found at index:', index);
            return;
        }

        const midPoint = Math.floor(chunk.content.length / 2);
        const splitPoint = chunk.content.lastIndexOf(".", midPoint) + 1 || midPoint;

        const newChunks = [
            {
                ...chunk,
                id: `${chunk.id}_1`,
                content: chunk.content.substring(0, splitPoint).trim(),
                qualityScore: Math.max(1, chunk.qualityScore - 1),
                isExpanded: false,
            },
            {
                ...chunk,
                id: `${chunk.id}_2`,
                content: chunk.content.substring(splitPoint).trim(),
                qualityScore: Math.max(1, chunk.qualityScore - 1),
                isExpanded: false,
            },
        ];

        const updatedChunks = [...props.chunks];
        updatedChunks.splice(index, 1, ...newChunks);
        emit("update:chunks", updatedChunks);
    } catch (error) {
        console.error('Error splitting chunk:', error);
    }
};

// 청크 삭제
const deleteChunk = (index) => {
    const updatedChunks = [...props.chunks];
    updatedChunks.splice(index, 1);
    emit("update:chunks", updatedChunks);
};

// 청크 내용 입력 핸들러
const handleChunkContentInput = (event, index) => {
    const newContent = event.target.value;
    updateChunkContent(index, newContent);
    // textarea 높이 자동 조정
    event.target.style.height = 'auto';
    event.target.style.height = event.target.scrollHeight + 'px';
};

// 청크 내용 업데이트
const updateChunkContent = (index, newContent) => {
    const updatedChunks = [...props.chunks];
    if (updatedChunks[index]) {
        updatedChunks[index] = {
            ...updatedChunks[index],
            content: newContent,
        };
        emit("update:chunks", updatedChunks);
    }
};

// 선택된 청크 병합
const mergeSelectedChunks = () => {
    if (selectedChunks.value.length < 2) return;

    const selectedChunkObjects = props.chunks.filter((chunk) =>
        selectedChunks.value.includes(chunk.id)
    );

    const mergedContent = selectedChunkObjects
        .map((chunk) => chunk.content)
        .join("\n\n");

    const mergedChunk = {
        id: `merged_${Date.now()}`,
        content: mergedContent,
        qualityScore: Math.round(
            selectedChunkObjects.reduce(
                (sum, chunk) => sum + chunk.qualityScore,
                0
            ) / selectedChunkObjects.length
        ),
        semanticScore: null,
        duplicateScore: null,
        isExpanded: false,
    };

    const updatedChunks = props.chunks.filter(
        (chunk) => !selectedChunks.value.includes(chunk.id)
    );

    // 선택된 청크들의 첫 번째 위치에 삽입
    const firstSelectedIndex = props.chunks.findIndex((chunk) =>
        selectedChunks.value.includes(chunk.id)
    );
    updatedChunks.splice(firstSelectedIndex, 0, mergedChunk);

    emit("update:chunks", updatedChunks);
    selectedChunks.value = [];
};

// 선택된 청크 삭제
const deleteSelectedChunks = () => {
    const updatedChunks = props.chunks.filter(
        (chunk) => !selectedChunks.value.includes(chunk.id)
    );
    emit("update:chunks", updatedChunks);
    selectedChunks.value = [];
};

// 선택 해제
const clearSelection = () => {
    selectedChunks.value = [];
};

// 임베딩 진행
const proceedToEmbedding = () => {
    emit("proceed-to-embedding", props.chunks);
};

// 툴팁 표시
const showTooltip = (event, type, index) => {
    if (!event || !event.currentTarget) return;
    
    try {
        const button = event.currentTarget;
        const rect = button.getBoundingClientRect();
        const tooltipKey = `${type}-${index}`;
        
        // 버튼 위쪽 공간 확인
        const spaceAbove = rect.top;
        const tooltipHeight = 30; // 툴팁 예상 높이
        const margin = 8; // 여백
        
        // 위에 공간이 충분하면 위로, 아니면 아래로
        const showAbove = spaceAbove > tooltipHeight + margin;
        
        let top, left, arrowClass;
        
        if (showAbove) {
            // 위로 표시
            top = `${rect.top - tooltipHeight - margin}px`;
            arrowClass = 'top-full -mt-1';
        } else {
            // 아래로 표시
            top = `${rect.bottom + margin}px`;
            arrowClass = 'bottom-full -mb-1';
        }
        
        // 버튼 중앙 정렬
        left = `${rect.left + rect.width / 2}px`;
        
        // 반응성을 유지하면서 업데이트
        tooltipStates.value = {
            ...tooltipStates.value,
            [tooltipKey]: {
                show: true,
                style: {
                    top: top,
                    left: left,
                    transform: 'translateX(-50%)',
                },
                arrowClass: arrowClass,
            },
        };
    } catch (error) {
        console.warn('Tooltip error:', error);
    }
};

// 툴팁 숨기기
const hideTooltip = (type, index) => {
    const tooltipKey = `${type}-${index}`;
    if (tooltipStates.value[tooltipKey]) {
        tooltipStates.value = {
            ...tooltipStates.value,
            [tooltipKey]: {
                ...tooltipStates.value[tooltipKey],
                show: false,
            },
        };
    }
};

// 청크 변경 감지
watch(
    () => props.chunks,
    () => {
        selectedChunks.value = [];
        // 툴팁 상태 초기화 (반응성 유지)
        const keys = Object.keys(tooltipStates.value);
        const newState = {};
        keys.forEach(key => {
            newState[key] = { ...tooltipStates.value[key], show: false };
        });
        tooltipStates.value = newState;
    },
    { deep: true }
);
</script>

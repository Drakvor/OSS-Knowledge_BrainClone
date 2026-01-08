<template>
    <div
        v-if="modelValue"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        @click.self="$emit('update:modelValue', false)"
    >
        <div
            class="bg-white rounded-xl shadow-2xl max-w-3xl w-full mx-4 max-h-[80vh] flex flex-col"
        >
            <!-- 헤더 -->
            <div class="flex items-center justify-between p-6 border-b border-gray-200">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center">
                        <span class="text-xl">🤖</span>
                    </div>
                    <div>
                        <h2 class="text-xl font-bold text-gray-900">
                            AI 청킹 설명
                        </h2>
                        <p class="text-sm text-gray-600">
                            문서가 어떻게 청킹되었는지 확인하세요
                        </p>
                    </div>
                </div>
                <button
                    @click="$emit('update:modelValue', false)"
                    class="p-2 rounded-lg hover:bg-gray-100 transition-colors"
                >
                    <svg
                        class="w-6 h-6 text-gray-600"
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

            <!-- 본문 -->
            <div class="flex-1 overflow-y-auto p-6 space-y-4">
                <div
                    v-for="reasoning in reasonings"
                    :key="reasoning.chunkIndex"
                    class="p-4 bg-purple-50 rounded-lg border border-purple-200"
                >
                    <div class="flex items-start gap-3">
                        <div class="flex-shrink-0 w-8 h-8 rounded-full bg-purple-500 text-white flex items-center justify-center font-bold text-sm">
                            {{ reasoning.chunkIndex }}
                        </div>
                        <div class="flex-1">
                            <p class="text-sm font-medium text-purple-900 mb-1">
                                청크 {{ reasoning.chunkIndex }}의 청킹 이유:
                            </p>
                            <p class="text-sm text-gray-700 leading-relaxed">
                                {{ reasoning.reasoning }}
                            </p>
                            <div
                                v-if="reasoning.content"
                                class="mt-2 p-2 bg-white rounded text-xs text-gray-600 border border-gray-200"
                            >
                                <span class="font-medium">미리보기:</span>
                                {{ reasoning.content }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 푸터 -->
            <div class="p-6 border-t border-gray-200 flex justify-end">
                <button
                    @click="$emit('update:modelValue', false)"
                    class="px-6 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors font-medium"
                >
                    닫기
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { watch, onBeforeUnmount } from "vue";

const props = defineProps({
    modelValue: {
        type: Boolean,
        default: false,
    },
    reasonings: {
        type: Array,
        default: () => [],
    },
});

const emit = defineEmits(["update:modelValue"]);

// ESC 키 핸들러
const handleEscKey = (event) => {
    if (event.key === "Escape" && props.modelValue) {
        emit("update:modelValue", false);
    }
};

// 모달이 열릴 때 ESC 키 리스너 추가
watch(
    () => props.modelValue,
    (isOpen) => {
        if (isOpen) {
            window.addEventListener("keydown", handleEscKey);
        } else {
            window.removeEventListener("keydown", handleEscKey);
        }
    }
);

// 컴포넌트 언마운트 시 리스너 제거
onBeforeUnmount(() => {
    window.removeEventListener("keydown", handleEscKey);
});
</script>


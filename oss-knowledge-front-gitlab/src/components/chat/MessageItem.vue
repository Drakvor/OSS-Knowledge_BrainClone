<template>
    <div
        class="px-6 py-6 last:pb-4 group hover:bg-gray-50/50 transition-colors duration-200"
        style="border-bottom: 1px solid rgba(0, 0, 0, 0.05)"
    >
        <div class="max-w-xl lg:max-w-2xl xl:max-w-3xl mx-auto">
            <div class="flex gap-3">
                <!-- 아바타 -->
                <div class="flex-shrink-0 mt-1">
                    <div
                        v-if="message.role === 'assistant'"
                        class="w-7 h-7 rounded-full flex items-center justify-center"
                        style="
                            background: linear-gradient(
                                135deg,
                                var(--color-primary-500),
                                var(--color-primary-600)
                            );
                        "
                    >
                        <svg
                            class="w-3.5 h-3.5 text-white"
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
                    </div>
                    <div
                        v-else
                        class="w-7 h-7 rounded-full bg-gray-700 flex items-center justify-center text-white font-medium text-xs"
                    >
                        {{ getUserInitials }}
                    </div>
                </div>

                <!-- 메시지 내용 -->
                <div class="flex-1 min-w-0">
                    <!-- 역할 표시 -->
                    <div class="mb-2">
                        <span class="text-sm font-medium text-gray-700">
                            {{
                                message.role === "assistant"
                                    ? "Brain Clone"
                                    : getUserDisplayName
                            }}
                        </span>
                    </div>

                    <!-- 파일 첨부 표시 -->
                    <div
                        v-if="message.files && message.files.length > 0"
                        class="mb-3"
                    >
                        <div class="flex flex-wrap gap-2">
                            <div
                                v-for="(file, index) in message.files"
                                :key="index"
                                class="inline-flex items-center gap-2 px-2 py-1.5 bg-gray-50 border border-gray-200 rounded-md text-sm hover:bg-gray-100 transition-colors"
                            >
                                <span class="text-base">{{
                                    getFileIcon(file.type)
                                }}</span>
                                <div class="flex flex-col">
                                    <span class="font-medium text-gray-800">{{
                                        file.name
                                    }}</span>
                                    <span class="text-xs text-gray-500">{{
                                        formatFileSize(file.size)
                                    }}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 멘션된 부서 표시 (User 메시지에서만) -->
                    <div
                        v-if="
                            message.role === 'user' &&
                            filteredMentionedDepartments &&
                            filteredMentionedDepartments.length > 0
                        "
                        class="mb-3"
                    >
                        <div class="flex items-center gap-2 mb-1.5">
                            <span class="text-xs font-medium text-gray-600"
                                >멘션된 부서:</span
                            >
                        </div>
                        <div class="flex flex-wrap gap-1.5">
                            <MentionTag
                                v-for="dept in filteredMentionedDepartments"
                                :key="dept.id"
                                :department="dept"
                                :removable="false"
                            />
                        </div>
                    </div>

                    <!-- Mock Message Component (for JSON content) -->
                    <MockMessageComponent
                        v-if="isMockMessage"
                        :message="message"
                    />

                    <!-- Regular Message Content -->
                    <template v-else>
                        <!-- 메시지 텍스트 -->
                        <div
                            v-if="message.isThinking"
                            class="flex items-center gap-3 text-sm text-teal-600"
                        >
                            <!-- 동글뱅이 스피너 -->
                            <div class="flex items-center justify-center">
                                <div
                                    class="w-5 h-5 border-2 border-teal-200 border-t-teal-500 rounded-full animate-spin"
                                ></div>
                            </div>
                            <!-- 텍스트 애니메이션 -->
                            <div class="flex items-center">
                                <span class="animate-pulse">{{
                                    message.content
                                }}</span>
                                <span class="ml-1 animate-bounce">.</span>
                                <span
                                    class="ml-0.5 animate-bounce"
                                    style="animation-delay: 0.1s"
                                    >.</span
                                >
                                <span
                                    class="ml-0.5 animate-bounce"
                                    style="animation-delay: 0.2s"
                                    >.</span
                                >
                            </div>
                        </div>
                        <div
                            v-else
                            class="message-content prose prose-sm max-w-none text-gray-800 leading-relaxed"
                        >
                            <!-- 스트리밍 중일 때는 마크다운만 표시 -->
                            <template v-if="showStreamingContent">
                                <div
                                    v-html="
                                        parseMarkdownContent(streamingContent)
                                    "
                                ></div>
                            </template>
                            <!-- 일반 메시지 -->
                            <template v-else>
                                <div
                                    v-html="
                                        parseMarkdownContent(message.content)
                                    "
                                ></div>
                            </template>
                        </div>
                    </template>

                    <!-- Sources section (Assistant messages with sources) -->
                    <div
                        v-if="message.role === 'assistant' && message.sources && message.sources.length > 0"
                        class="mt-4 pt-4 border-t border-gray-200"
                    >
                        <div class="text-sm font-medium text-gray-700 mb-2">출처:</div>
                        <div class="space-y-2">
                            <div
                                v-for="(source, index) in message.sources"
                                :key="index"
                                class="flex items-center justify-between text-sm"
                            >
                                <span class="text-gray-600">{{ source.filename }}</span>
                                <div class="flex items-center gap-2">
                                    <a
                                        v-if="source.download_url && source.upload_status === 'completed'"
                                        :href="source.download_url"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        class="text-teal-600 hover:text-teal-700 hover:underline text-xs"
                                    >
                                        다운로드
                                    </a>
                                    <span
                                        v-else-if="source.upload_status === 'failed'"
                                        class="text-red-500 text-xs"
                                    >
                                        파일을 다운로드할 수 없습니다
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 메시지 액션 버튼들 (Assistant 메시지에만 표시) -->
                    <div
                        v-if="message.role === 'assistant'"
                        class="flex items-center gap-1 mt-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                    >
                        <button
                            @click="copyMessage"
                            class="inline-flex items-center gap-1 px-2 py-1 text-xs text-gray-400 hover:text-teal-600 hover:bg-teal-50 rounded transition-all duration-200"
                            title="복사 (Ctrl+C)"
                        >
                            <svg
                                class="w-3 h-3"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    stroke-width="2"
                                    d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                                />
                            </svg>
                            복사
                        </button>

                        <button
                            @click="openFeedbackModal"
                            class="inline-flex items-center gap-1 px-2 py-1 text-xs text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded transition-all duration-200"
                            title="평가하기"
                        >
                            <svg
                                class="w-3 h-3"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    stroke-width="2"
                                    d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
                                />
                            </svg>
                            평가하기
                        </button>
                    </div>

                    <!-- 평가 영역 (평가하기 버튼 클릭 시 표시) -->
                    <div
                        v-if="showFeedback"
                        class="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200"
                    >
                        <div class="mb-3">
                            <label
                                class="block text-sm font-medium text-gray-700 mb-2"
                            >
                                이 답변이 도움이 되었나요?
                            </label>
                            <div class="flex items-center gap-1">
                                <button
                                    v-for="star in 5"
                                    :key="star"
                                    @click="setRating(star)"
                                    class="text-2xl transition-colors duration-200"
                                    :class="
                                        star <= feedbackRating
                                            ? 'text-yellow-400'
                                            : 'text-gray-300'
                                    "
                                >
                                    ★
                                </button>
                                <span class="ml-2 text-sm text-gray-600">
                                    {{
                                        feedbackRating > 0
                                            ? `${feedbackRating}/5`
                                            : "별점을 선택해주세요"
                                    }}
                                </span>
                            </div>
                        </div>

                        <div class="mb-3">
                            <label
                                class="block text-sm font-medium text-gray-700 mb-2"
                            >
                                개선사항이나 의견을 남겨주세요
                            </label>
                            <textarea
                                v-model="feedbackComment"
                                placeholder="답변에 대한 의견이나 개선사항을 자유롭게 작성해주세요. 여러분의 피드백이 더 나은 서비스로 이어집니다."
                                class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                rows="3"
                            ></textarea>
                        </div>

                        <div class="flex items-center justify-between">
                            <span class="text-xs text-gray-500">
                                피드백은 익명으로 수집되며, 서비스 개선에
                                활용됩니다.
                            </span>
                            <div class="flex gap-2">
                                <button
                                    @click="cancelFeedback"
                                    class="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-200 rounded-md transition-colors duration-200"
                                >
                                    취소
                                </button>
                                <button
                                    @click="submitFeedback"
                                    :disabled="feedbackRating === 0"
                                    class="px-3 py-1.5 text-sm bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors duration-200"
                                >
                                    피드백 전송
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- 시간 표시 -->
                    <div class="text-xs text-gray-400 mt-2">
                        {{ formatTime(message.timestamp) }}
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { storeToRefs } from "pinia";
import { parseMarkdown } from "@/utils/markdown";
import { formatFileSize, getFileIcon } from "@/utils/fileHandler";
import { useUIStore } from "@/stores/ui";
import { useAuthStore } from "@/stores/auth";
import { useConversationStore } from "@/stores/conversation";
import { useChatStore } from "@/stores/chat";
import { createMessageFeedbackAPI } from "@/services/metaApi";
import MentionTag from "./MentionTag.vue";
import MockMessageComponent from "./MockMessageComponent.vue";

const props = defineProps({
    message: {
        type: Object,
        required: true,
    },
});

const uiStore = useUIStore();
const authStore = useAuthStore();
const chatStore = useChatStore();

// 스트리밍 관련 반응형 데이터
const { streamingContent, isStreaming } = storeToRefs(chatStore);

// 평가 관련 상태
const showFeedback = ref(false);
const feedbackRating = ref(0);
const feedbackComment = ref("");

// 사용자 정보 computed 속성들
const getUserInitials = computed(() => {
    if (!authStore.user) return "U";

    if (authStore.user.fullName) {
        // fullName이 있으면 첫 글자들 사용
        return authStore.user.fullName
            .split(" ")
            .map((name) => name.charAt(0))
            .join("")
            .toUpperCase()
            .slice(0, 2);
    } else if (authStore.user.username) {
        // username이 있으면 첫 글자 사용
        return authStore.user.username.charAt(0).toUpperCase();
    }

    return "U";
});

const getUserDisplayName = computed(() => {
    if (!authStore.user) return "사용자";

    return authStore.user.fullName || authStore.user.username || "사용자";
});

// 스트리밍 표시 여부
const showStreamingContent = computed(() => {
    return (
        props.message.isStreaming &&
        props.message.role === "assistant" &&
        streamingContent.value &&
        streamingContent.value.length > 0
    );
});

// 마크다운 파싱 함수 (템플릿에서 직접 사용)
const parseMarkdownContent = (content) => {
    return parseMarkdown(content);
};

// Mock message detection (JSON content)
const isMockMessage = computed(() => {
    try {
        const parsed = JSON.parse(props.message.content);
        return (
            parsed &&
            typeof parsed === "object" &&
            (parsed.breakpoints ||
                parsed.currentStatus ||
                parsed.currentResponse ||
                parsed.finalResponse)
        );
    } catch (error) {
        return false;
    }
});

// general 부서를 제외한 멘션된 부서 필터링 (메시지별 메타데이터 기준)
const filteredMentionedDepartments = computed(() => {
    const meta = props.message?.metadata || {};
    let mentioned =
        meta.mentioned_departments ||
        meta.mentionedDepartments ||
        props.message.mentionedDepartments ||
        [];

    // 문자열 멘션을 객체로 정규화
    mentioned = mentioned.map((item) =>
        typeof item === "string" ? { name: item } : item
    );

    return mentioned.filter((dept) => {
        const name = (dept?.name || "").toLowerCase();
        const slug = (dept?.slug || "").toLowerCase();
        return name !== "general" && slug !== "general" && name !== "";
    });
});

// 시간 포맷팅
const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "방금 전";
    if (diffMins < 60) return `${diffMins}분 전`;
    if (diffHours < 24) return `${diffHours}시간 전`;
    if (diffDays < 7) return `${diffDays}일 전`;

    return date.toLocaleDateString("ko-KR", {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
};

// 메시지 복사
const copyMessage = async () => {
    try {
        await navigator.clipboard.writeText(props.message.content);
        uiStore.setSuccess("메시지가 클립보드에 복사되었습니다.");
    } catch (err) {
        uiStore.setError("복사에 실패했습니다.");
    }
};

// 평가하기 모달 열기
const openFeedbackModal = () => {
    showFeedback.value = true;
    feedbackRating.value = 0;
    feedbackComment.value = "";
};

// 별점 설정
const setRating = (rating) => {
    feedbackRating.value = rating;
};

// 피드백 취소
const cancelFeedback = () => {
    showFeedback.value = false;
    feedbackRating.value = 0;
    feedbackComment.value = "";
};

// 사용자 질문 ID 찾기
const findUserQuestionId = (message) => {
    if (message.role === "user") {
        // 사용자 메시지인 경우 진짜 ID가 있으면 사용, 없으면 가상 ID 사용
        return message.realId || message.id;
    } else if (message.role === "assistant") {
        // assistant 메시지인 경우 해당하는 사용자 질문 찾기
        const conversationStore = useConversationStore();
        const messages = conversationStore.currentConversation?.messages || [];
        const currentIndex = messages.findIndex((m) => m.id === message.id);

        if (currentIndex > 0) {
            // 이전 메시지들 중에서 가장 가까운 사용자 메시지 찾기
            for (let i = currentIndex - 1; i >= 0; i--) {
                if (messages[i].role === "user") {
                    return messages[i].realId || messages[i].id;
                }
            }
        }

        // 찾지 못한 경우 현재 메시지 ID 반환 (fallback)
        return message.id;
    }

    return message.id;
};

// 피드백 전송
const submitFeedback = async () => {
    if (feedbackRating.value === 0) {
        uiStore.setError("별점을 선택해주세요.");
        return;
    }

    try {
        const feedbackData = {
            rating: feedbackRating.value,
            comment: feedbackComment.value || null,
            feedbackType: "general",
            isAnonymous: true,
            metadata: {
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
            },
        };

        // 백엔드 API로 피드백 전송 (사용자 질문 ID 사용)
        // assistant 메시지의 경우 해당하는 사용자 질문 ID를 찾아서 사용
        const userMessageId = findUserQuestionId(props.message);
        await createMessageFeedbackAPI(userMessageId, feedbackData);

        // 성공 메시지 표시
        uiStore.setSuccess(
            "피드백이 성공적으로 전송되었습니다. 서비스 개선에 활용하겠습니다."
        );

        // 평가 영역 닫기
        cancelFeedback();
    } catch (error) {
        console.error("피드백 전송 실패:", error);
        uiStore.setError("피드백 전송에 실패했습니다. 다시 시도해주세요.");
    }
};
</script>

<style scoped>
/* 메시지 내용 스타일링 */
.message-content :deep(p) {
    @apply mb-3 last:mb-0 leading-relaxed;
}

.message-content :deep(pre) {
    @apply bg-gray-50 rounded-lg p-3 mb-3 overflow-x-auto border border-gray-200;
}

.message-content :deep(code) {
    @apply bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono;
}

.message-content :deep(pre code) {
    @apply bg-transparent p-0;
}

.message-content :deep(ul) {
    @apply list-disc pl-5 mb-3 space-y-1;
}

.message-content :deep(ol) {
    @apply list-decimal pl-5 mb-3 space-y-1;
}

.message-content :deep(blockquote) {
    @apply border-l-4 border-blue-300 pl-3 italic my-3 bg-blue-50 py-2 rounded-r-md;
}

.message-content :deep(h1) {
    @apply text-xl font-bold mb-3 mt-5 first:mt-0;
}

.message-content :deep(h2) {
    @apply text-lg font-bold mb-2 mt-4 first:mt-0;
}

.message-content :deep(h3) {
    @apply text-base font-bold mb-2 mt-3 first:mt-0;
}

.message-content :deep(table) {
    @apply w-full border-collapse border border-gray-300 mb-3 rounded-lg overflow-hidden;
}

.message-content :deep(th) {
    @apply border border-gray-300 px-3 py-2 bg-gray-50 font-semibold;
}

.message-content :deep(td) {
    @apply border border-gray-300 px-3 py-2;
}

/* 스트리밍 응답 */
.streaming-response {
    white-space: pre-wrap;
    word-break: break-word;
    line-height: 1.6;
    padding: 1rem 0;
}
</style>

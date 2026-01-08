<template>
    <div
        ref="scrollContainer"
        class="h-full overflow-y-auto bg-white"
        style="contain: layout"
        @scroll="handleScroll"
    >
        <!-- 환영 메시지 -->
        <div
            v-if="!messages || messages.length === 0"
            class="h-full flex items-center justify-center"
        >
            <div
                class="text-center max-w-xl lg:max-w-2xl xl:max-w-3xl mx-auto px-6 pb-32"
            >
                <div class="mb-8">
                    <div
                        class="w-16 h-16 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-teal-400 to-emerald-500 flex items-center justify-center"
                    >
                        <svg
                            class="w-8 h-8 text-white"
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
                    <h1 class="text-3xl font-semibold text-gray-900 mb-2">
                        안녕하세요!
                    </h1>
                    <p class="text-lg text-gray-600">무엇을 도와드릴까요?</p>
                </div>

                <!-- 예시 질문들 -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-8">
                    <button
                        v-for="suggestion in suggestions"
                        :key="suggestion.text"
                        @click="handleSuggestionClick(suggestion.text)"
                        :class="[
                            'p-4 text-left bg-white rounded-2xl transition-all duration-200 group shadow-sm hover:shadow-md relative h-24',
                            suggestion.text === 'demo' 
                                ? 'border-2 border-red-400 hover:border-red-500 hover:bg-red-50' 
                                : 'border border-gray-200 hover:border-teal-300 hover:bg-teal-50'
                        ]"
                    >
                        <!-- 콜렉션 태그 -->
                        <div class="absolute top-2 right-2">
                            <span
                                v-if="suggestion.text === 'demo'"
                                class="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800 border border-red-200 animate-pulse"
                            >
                                ⭐ DEMO
                            </span>
                            <span
                                v-else
                                class="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-teal-100 text-teal-800 border border-teal-200"
                            >
                                🔧 SOP
                            </span>
                        </div>

                        <div class="flex items-start gap-3 pr-16 h-full">
                            <span class="text-xl">{{ suggestion.icon }}</span>
                            <div class="flex-1">
                                <p
                                    :class="[
                                        'font-medium text-sm',
                                        suggestion.text === 'demo' 
                                            ? 'text-red-700 group-hover:text-red-800' 
                                            : 'text-gray-900 group-hover:text-teal-600'
                                    ]"
                                >
                                    {{ suggestion.title }}
                                </p>
                                <p
                                    :class="[
                                        'text-xs mt-1 line-clamp-2',
                                        suggestion.text === 'demo' 
                                            ? 'text-red-500' 
                                            : 'text-gray-500'
                                    ]"
                                >
                                    {{ suggestion.description }}
                                </p>
                            </div>
                        </div>
                    </button>
                </div>
            </div>
        </div>

        <!-- 메시지 목록 -->
        <div v-else class="pt-6 pb-4" style="contain: layout">
            <MessageItem
                v-for="message in messages"
                :key="message.id"
                :message="message"
            />

            <!-- 하단 여백 -->
            <div class="h-4"></div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useConversationStore } from "@/stores/conversation";
import { useChatStore } from "@/stores/chat";
import { parseMarkdown } from "@/utils/markdown";
import MessageItem from "./MessageItem.vue";

const router = useRouter();
const conversationStore = useConversationStore();
const chatStore = useChatStore();

const scrollContainer = ref(null);
const streamingMessageRef = ref(null);
const isUserScrolling = ref(false);
const lastScrollTop = ref(0);
let scrollTimeout = null;
let isAutoScrolling = ref(false);

// 제안 질문들
const suggestions = ref([
    {
        icon: "🎬",
        title: "데모 체험하기",
        description: "AI 어시스턴트의 사고 과정을 시뮬레이션으로 확인해보세요",
        text: "demo",
    },
    {
        icon: "🚨",
        title: "장애 대응 SOP 검색",
        description: "장애 유형별 대응 절차를 찾아보세요",
        text: "WAS 서버 장애 시 대응 SOP를 알려주세요",
    },
    {
        icon: "🔍",
        title: "트러블슈팅 가이드",
        description: "시스템 문제 해결 방법을 검색해보세요",
        text: "DB 커넥션 풀 고갈 문제 해결 방법을 알려주세요",
    },
    {
        icon: "📋",
        title: "에스컬레이션 절차",
        description: "장애 에스컬레이션 프로세스를 확인하세요",
        text: "Level 2 에스컬레이션 절차와 승인자를 알려주세요",
    },
]);

// 현재 대화의 메시지
const messages = computed(() => {
    return conversationStore.currentConversation?.messages || [];
});

// 스트리밍 메시지 HTML (제거됨)

// 제안 클릭 처리
const handleSuggestionClick = async (text) => {
    // 데모 버튼인 경우 라우터로 이동
    if (text === "demo") {
        router.push("/demo-chat");
        return;
    }

    // 현재 대화가 없으면 새 대화 생성
    if (!conversationStore.currentConversationId) {
        await conversationStore.createNewConversation();
    }
    
    // 올바른 형태로 메시지 데이터 전달
    chatStore.sendMessage({
        content: text,
        mentionedDepartments: [],
        files: []
    });
};

// 🔥 더 강력한 스크롤 함수
const scrollToBottom = (force = false) => {
    if (!scrollContainer.value) return;

    // 디버깅용 로그
    console.log("🔄 스크롤 시도:", {
        force,
        isUserScrolling: isUserScrolling.value,
        scrollHeight: scrollContainer.value.scrollHeight,
        clientHeight: scrollContainer.value.clientHeight,
    });

    nextTick(() => {
        if (!scrollContainer.value) return;

        const container = scrollContainer.value;
        const shouldScroll = force || !isUserScrolling.value || isNearBottom();

        if (shouldScroll) {
            isAutoScrolling.value = true;

            // 즉시 스크롤 (GPU 부하 최소화)
            container.scrollTo({
                top: container.scrollHeight,
                behavior: "auto",
            });

            setTimeout(() => {
                isAutoScrolling.value = false;
            }, 500);

            console.log(
                "✅ 스크롤 완료:",
                container.scrollTop,
                container.scrollHeight
            );
        }
    });
};

// 하단 근처인지 체크
const isNearBottom = () => {
    if (!scrollContainer.value) return true;

    const container = scrollContainer.value;
    const threshold = 50;
    return (
        container.scrollHeight - container.scrollTop - container.clientHeight <=
        threshold
    );
};

// 사용자 스크롤 감지
const handleScroll = () => {
    if (isAutoScrolling.value) return; // 자동 스크롤 중에는 무시

    if (!scrollContainer.value) return;

    const currentScrollTop = scrollContainer.value.scrollTop;

    if (currentScrollTop < lastScrollTop.value && !isNearBottom()) {
        // 위로 스크롤하고 하단이 아닌 경우
        isUserScrolling.value = true;
        console.log("👆 사용자 스크롤 감지");
    } else if (isNearBottom()) {
        // 하단 근처로 돌아온 경우
        isUserScrolling.value = false;
        console.log("👇 하단 근처 도달");
    }

    lastScrollTop.value = currentScrollTop;

    // 타임아웃 클리어
    if (scrollTimeout) {
        clearTimeout(scrollTimeout);
    }

    scrollTimeout = setTimeout(() => {
        isUserScrolling.value = false;
        console.log("⏰ 스크롤 타임아웃 - 자동 스크롤 재활성화");
    }, 2000);
};

// 메시지 변경 감지 (새 메시지 추가 시에만 스크롤)
watch(
    () => messages.value.length,
    (newLength, oldLength) => {
        // 새 메시지가 추가된 경우에만 스크롤
        if (newLength > (oldLength || 0)) {
            console.log("📝 새 메시지 추가 감지:", { newLength, oldLength });
            // DOM 업데이트를 위해 약간의 지연 추가
            setTimeout(() => {
                console.log("🔄 새 메시지로 인한 스크롤 실행");
                scrollToBottom(true);
            }, 50);
        }
    }
);

// 스트리밍 완료 시에만 스크롤 (스트리밍 중에는 스크롤하지 않음)
watch(
    () => chatStore.isStreaming,
    (isStreaming, wasStreaming) => {
        // 스트리밍이 완료된 경우에만 스크롤
        if (!isStreaming && wasStreaming) {
            console.log("✅ 스트리밍 완료 - 최종 스크롤 실행");
            nextTick(() => {
                scrollToBottom(true);
            });
        }
    }
);

// thinking 상태 변경 시 스크롤 (응답 생성중 메시지가 나타날 때)
watch(
    () => chatStore.isThinking,
    (isThinking, wasThinking) => {
        if (isThinking && !wasThinking) {
            console.log("🧠 Thinking 상태 시작 - 스크롤 실행");
            // thinking 상태가 시작될 때 스크롤 (약간의 지연을 두어 DOM 업데이트 완료 후)
            setTimeout(() => {
                console.log("🔄 Thinking 상태로 인한 스크롤 실행");
                scrollToBottom(true);
            }, 100);
        }
    }
);

onMounted(() => {
    console.log("🚀 MessageList 마운트됨");

    if (scrollContainer.value) {
        console.log("📏 컨테이너 크기:", {
            clientHeight: scrollContainer.value.clientHeight,
            scrollHeight: scrollContainer.value.scrollHeight,
        });
    }

    nextTick(() => {
        scrollToBottom(true);
    });
});
</script>

<template>
    <div>
        <!-- 파일 업로드 컴포넌트 -->
        <FileUpload ref="fileUploadRef" />

        <!-- 메인 입력 영역 -->
        <div class="relative mb-6">
            <!-- 입력창 컨테이너 -->
            <div
                :class="[
                    'relative rounded-xl border transition-all duration-200',
                    isFocused
                        ? 'shadow-lg ring-2'
                        : 'shadow-sm hover:shadow-md',
                ]"
                :style="[
                    'background-color: var(--color-bg-primary)',
                    isFocused
                        ? 'border-color: var(--color-primary-300); box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04); box-shadow: 0 0 0 2px var(--color-primary-50)'
                        : 'border-color: var(--color-border-light); box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
                    !isFocused && 'border-color: var(--color-border-light)'
                ]"
            >
                <!-- 멘션 드롭다운 -->
                <MentionDropdown
                    :show="showMentionDropdown"
                    :search-query="mentionSearchQuery"
                    @select="handleMentionSelect"
                    @close="closeMentionDropdown"
                    @update:search-query="mentionSearchQuery = $event"
                />
                <!-- 텍스트 입력 영역 -->
                <div class="max-w-xl lg:max-w-2xl xl:max-w-3xl mx-auto w-full">
                    <div class="relative">
                        <!-- 멘션 태그들 -->
                        <div v-if="mentionedDepartments.length > 0" class="flex flex-wrap gap-2 p-3 pb-1">
                            <MentionTag
                                v-for="dept in mentionedDepartments"
                                :key="dept.id"
                                :department="dept"
                                :removable="true"
                                @remove="removeMention"
                            />
                        </div>
                        
                        <textarea
                            ref="textareaRef"
                            v-model="message"
                            @input="handleInput"
                            @keydown="handleKeydown"
                            @focus="isFocused = true"
                            @blur="isFocused = false"
                            @compositionstart="handleCompositionStart"
                            @compositionend="handleCompositionEnd"
                            :placeholder="placeholder"
                            :disabled="chatStore.isStreaming"
                            class="w-full px-6 py-3 bg-transparent resize-none focus:outline-none min-h-[44px] max-h-[200px] placeholder-gray-400 text-gray-900 leading-relaxed whitespace-pre-wrap break-words chat-textarea"
                            rows="1"
                            style="
                                word-wrap: break-word;
                                overflow-wrap: break-word;
                            "
                        ></textarea>
                    </div>

                    <!-- 하단 버튼 영역 -->
                    <div class="flex items-center justify-between px-4 py-2 bg-gray-50/50 border-t border-gray-100">
                        <!-- 왼쪽: 액션 버튼들 -->
                        <div class="flex items-center gap-2">
                            <!-- 파일 첨부 버튼 (+) -->
                            <button
                                @click="$refs.fileUploadRef.openFileDialog()"
                                :disabled="chatStore.isStreaming"
                                class="p-2 text-gray-500 hover:text-gray-700 disabled:opacity-50 transition-all duration-200 rounded-lg hover:bg-gray-100 border border-gray-200"
                                title="파일 첨부 (Ctrl+U)"
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
                                        d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                                    />
                                </svg>
                            </button>

                            <!-- @ 멘션 버튼 -->
                            <button
                                @click="triggerMention"
                                :disabled="chatStore.isStreaming"
                                class="p-2 text-gray-500 hover:text-gray-700 disabled:opacity-50 transition-all duration-200 rounded-lg hover:bg-gray-100 font-bold text-lg border border-gray-200"
                                title="부서 멘션 (@)"
                            >
                                @
                            </button>

                            <!-- 검색 버튼 (드롭다운) -->
                            <div class="relative search-dropdown-container">
                                <button
                                    @click="toggleSearchDropdown"
                                    :disabled="chatStore.isStreaming"
                                    :class="[
                                        'px-3 py-2 text-sm disabled:opacity-50 transition-all duration-200 rounded-lg border font-medium flex items-center gap-1',
                                        selectedSearchType === '검색'
                                            ? 'text-gray-600 hover:text-gray-800 hover:bg-gray-100 border-gray-200'
                                            : 'text-white bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 border-emerald-500'
                                    ]"
                                    title="검색 옵션"
                                >
                                    {{ selectedSearchType }}
                                    <svg
                                        v-if="selectedSearchType === '검색'"
                                        class="w-4 h-4"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                    >
                                        <path
                                            stroke-linecap="round"
                                            stroke-linejoin="round"
                                            stroke-width="2"
                                            d="M19 9l-7 7-7-7"
                                        />
                                    </svg>
                                    <button
                                        v-else
                                        @click.stop="resetSearchType"
                                        class="ml-1 p-0.5 rounded-full hover:bg-white/20 transition-colors"
                                        title="검색 타입 초기화"
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
                                                d="M6 18L18 6M6 6l12 12"
                                            />
                                        </svg>
                                    </button>
                                </button>

                                <!-- 검색 드롭다운 메뉴 -->
                                <Transition
                                    enter-active-class="transition-all duration-200 ease-out"
                                    enter-from-class="opacity-0 scale-95 translate-y-1"
                                    enter-to-class="opacity-100 scale-100 translate-y-0"
                                    leave-active-class="transition-all duration-150 ease-in"
                                    leave-from-class="opacity-100 scale-100 translate-y-0"
                                    leave-to-class="opacity-0 scale-95 translate-y-1"
                                >
                                    <div
                                        v-if="showSearchDropdown"
                                        class="absolute bottom-full left-0 mb-3 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1"
                                        style="z-index: 9999;"
                                    >
                                        <button
                                            @click="insertSearchKeyword('KMS')"
                                            class="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                                        >
                                            KMS 검색
                                        </button>
                                        <button
                                            @click="insertSearchKeyword('Works AI')"
                                            class="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                                        >
                                            Works AI 검색
                                        </button>
                                        <button
                                            @click="insertSearchKeyword('WEB')"
                                            class="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                                        >
                                            WEB 검색
                                        </button>
                                    </div>
                                </Transition>
                            </div>
                        </div>

                        <!-- 오른쪽: 모델 선택 및 전송/중지 버튼 -->
                        <div class="flex items-center gap-2">
                            <!-- 모델 선택 드롭다운 -->
                            <div class="relative">
                                <select
                                    v-model="selectedModel"
                                    :disabled="chatStore.isStreaming"
                                    class="px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
                                    title="모델 선택"
                                >
                                    <option value="gpt-4.1-mini">GPT-4.1 Mini</option>
                                    <option value="gpt-4o">GPT-4o</option>
                                    <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                                </select>
                            </div>

                            <!-- 전송 버튼 -->
                            <button
                                v-if="!chatStore.isStreaming"
                                @click="sendMessage"
                                :disabled="!canSend"
                                :class="[
                                    'px-4 py-2 rounded-lg transition-all duration-200 flex items-center gap-2 text-sm font-medium',
                                    canSend
                                        ? 'bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-600 hover:to-emerald-600 text-white shadow-sm hover:shadow-md'
                                        : 'bg-gray-200 text-gray-400 cursor-not-allowed',
                                ]"
                                title="전송 (Enter)"
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
                                        d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                                    />
                                </svg>
                                전송
                            </button>

                            <!-- 중지 버튼 -->
                            <button
                                v-else
                                @click="stopGeneration"
                                class="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-all duration-200 shadow-sm hover:shadow-md flex items-center gap-2 text-sm font-medium"
                                title="생성 중지"
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
                                        d="M21 12H3"
                                    />
                                </svg>
                                중지
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 하단 정보 -->
            <div class="flex items-center justify-between mt-2 px-2">
                <div class="flex items-center gap-4 text-xs text-gray-400">
                    <span
                        v-if="chatStore.isStreaming"
                        class="flex items-center gap-2"
                    >
                        <div class="flex space-x-1">
                            <div
                                class="w-2 h-2 bg-teal-500 rounded-full animate-pulse"
                            ></div>
                            <div
                                class="w-2 h-2 bg-teal-500 rounded-full animate-pulse"
                                style="animation-delay: 0.2s"
                            ></div>
                            <div
                                class="w-2 h-2 bg-teal-500 rounded-full animate-pulse"
                                style="animation-delay: 0.4s"
                            ></div>
                        </div>
                        Brain Clone이 응답하고 있습니다...
                    </span>
                    <span v-else class="flex items-center gap-3">
                        <span class="flex items-center gap-1">
                            <kbd
                                class="px-1.5 py-0.5 bg-gray-100 rounded text-xs border border-gray-200 font-mono"
                                >Enter</kbd
                            >전송
                        </span>
                        <span class="flex items-center gap-1">
                            <kbd
                                class="px-1.5 py-0.5 bg-gray-100 rounded text-xs border border-gray-200 font-mono"
                                >Shift+Enter</kbd
                            >줄바꿈
                        </span>
                        <span class="flex items-center gap-1">
                            <kbd
                                class="px-1.5 py-0.5 bg-gray-100 rounded text-xs border border-gray-200 font-mono"
                                >@</kbd
                            >멘션
                        </span>
                    </span>
                </div>

                <div class="flex items-center gap-3 text-xs text-gray-400">
                    <!-- 컨텍스트 사용량 표시 -->
                    <div 
                        class="flex items-center gap-2 relative group cursor-pointer"
                        @mouseenter="showTooltip = true"
                        @mouseleave="showTooltip = false"
                    >
                        <div class="flex items-center gap-1">
                            <svg class="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <span class="font-medium">{{ formatTokenCount(totalTokensUsed) }}</span>
                        </div>
                        
                        <div class="flex items-center gap-1">
                            <span class="text-xs">{{ usagePercentage }}%</span>
                            <div class="w-8 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                <div 
                                    class="h-full transition-all duration-300 ease-out"
                                    :class="progressBarClass"
                                    :style="{ width: `${Math.min(usagePercentage, 100)}%` }"
                                ></div>
                            </div>
                        </div>
                        
                        <!-- 호버 툴팁 -->
                        <div 
                            v-if="showTooltip"
                            class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg shadow-lg z-50 whitespace-nowrap"
                        >
                            <div class="text-center">
                                <div class="font-medium">{{ formatTokenCount(totalTokensUsed) }} / {{ formatTokenCount(maxTokens) }}</div>
                                <div class="text-gray-300">{{ usagePercentage }}% 사용</div>
                            </div>
                            <!-- 화살표 -->
                            <div class="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
                        </div>
                    </div>
                    
                    <span>{{ message.length }}/4000</span>
                    <span
                        v-if="chatStore.uploadedFiles.length > 0"
                        class="flex items-center gap-1"
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
                                d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
                            />
                        </svg>
                        {{ chatStore.uploadedFiles.length }}개 파일
                    </span>
                </div>
            </div>
        </div>

        <!-- 드래그 앤 드롭 오버레이 -->
        <Transition
            enter-active-class="transition-all duration-200 ease-out"
            enter-from-class="opacity-0 scale-95"
            enter-to-class="opacity-100 scale-100"
            leave-active-class="transition-all duration-150 ease-in"
            leave-from-class="opacity-100 scale-100"
            leave-to-class="opacity-0 scale-95"
        >
            <div
                v-if="isDragging"
                @drop.prevent="handleDrop"
                @dragover.prevent
                @dragleave="handleDragLeave"
                class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center backdrop-blur-sm"
            >
                <div
                    class="bg-white rounded-2xl p-12 shadow-2xl border-2 border-dashed border-teal-300 max-w-md text-center"
                >
                    <div
                        class="w-16 h-16 mx-auto mb-6 rounded-full bg-teal-100 flex items-center justify-center"
                    >
                        <svg
                            class="w-8 h-8 text-teal-500"
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
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">
                        파일을 여기에 놓으세요
                    </h3>
                    <p class="text-gray-500">
                        파일을 드래그하여 업로드하세요
                    </p>
                </div>
            </div>
        </Transition>
    </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from "vue";
import { useChatStore } from "@/stores/chat";
import { useConversationStore } from "@/stores/conversation";
import FileUpload from "./FileUpload.vue";
import MentionDropdown from "./MentionDropdown.vue";
import MentionTag from "./MentionTag.vue";

const chatStore = useChatStore();
const conversationStore = useConversationStore();

const message = ref("");
const textareaRef = ref(null);
const fileUploadRef = ref(null);
const isDragging = ref(false);
const isFocused = ref(false);
const isComposing = ref(false);
const shouldSendOnCompositionEnd = ref(false);
const showTooltip = ref(false);

// 멘션 관련 상태
const showMentionDropdown = ref(false);
const mentionSearchQuery = ref("");
const mentionedDepartments = ref([]);
const mentionStartIndex = ref(-1);

// 검색 드롭다운 상태
const showSearchDropdown = ref(false);
const selectedSearchType = ref('검색');

// 모델 선택 상태
const selectedModel = ref('gpt-4.1-mini');

const placeholder = computed(() => {
    return chatStore.isStreaming
        ? "응답을 기다리는 중..."
        : "Brain Clone에게 메시지를 보내세요...";
});

const canSend = computed(() => {
    return (
        (message.value.trim() || chatStore.uploadedFiles.length > 0) &&
        !chatStore.isStreaming
    );
});

// 컨텍스트 사용량 관련 computed 속성들
const totalTokensUsed = computed(() => {
    return conversationStore.currentConversation?.totalTokensUsed || 0;
});

const currentModel = computed(() => {
    return conversationStore.currentConversation?.llmModel || 'gpt-4.1-mini';
});

const maxTokens = computed(() => {
    const MODEL_MAX_TOKENS = {
        'gpt-4o': 128000,
        'gpt-4o-mini': 128000,
        'gpt-4-turbo': 128000,
        'gpt-4': 8192,
        'gpt-4-32k': 32768,
        'gpt-3.5-turbo': 4096,
        'gpt-3.5-turbo-16k': 16384,
        'gpt-4.1-mini': 128000,
    };
    return MODEL_MAX_TOKENS[currentModel.value] || MODEL_MAX_TOKENS['gpt-4.1-mini'];
});

const usagePercentage = computed(() => {
    if (maxTokens.value === 0) return 0;
    return Math.round((totalTokensUsed.value / maxTokens.value) * 100);
});

const progressBarClass = computed(() => {
    const percentage = usagePercentage.value;
    
    if (percentage < 50) {
        return 'bg-green-500';
    } else if (percentage < 75) {
        return 'bg-yellow-500';
    } else if (percentage < 90) {
        return 'bg-orange-500';
    } else {
        return 'bg-red-500';
    }
});

const formatTokenCount = (count) => {
    if (count === 0) return '0';
    if (count < 1000) return count.toString();
    if (count < 1000000) return `${(count / 1000).toFixed(1)}K`;
    return `${(count / 1000000).toFixed(1)}M`;
};

// 텍스트 영역 높이 자동 조절
const adjustHeight = () => {
    if (textareaRef.value) {
        // 현재 커서 위치 저장
        const cursorPosition = textareaRef.value.selectionStart;

        // 높이 재설정
        textareaRef.value.style.height = "auto";
        const scrollHeight = textareaRef.value.scrollHeight;
        const maxHeight = 200; // max-h-[200px]와 일치
        const newHeight = Math.min(scrollHeight, maxHeight);

        textareaRef.value.style.height = newHeight + "px";

        // 스크롤이 필요한 경우 스크롤 조정
        if (scrollHeight > maxHeight) {
            textareaRef.value.style.overflowY = "auto";
        } else {
            textareaRef.value.style.overflowY = "hidden";
        }

        // 커서 위치 복원
        textareaRef.value.setSelectionRange(cursorPosition, cursorPosition);
    }
};

// 키보드 이벤트 처리
const handleKeydown = (event) => {
    // 멘션 드롭다운이 열려있으면 모든 네비게이션 키 차단
    if (showMentionDropdown.value) {
        console.log('ChatInput: 멘션 드롭다운 열려있음, 키 차단:', event.key)
        if (['ArrowUp', 'ArrowDown', 'Enter', 'Escape', 'Tab'].includes(event.key)) {
            event.preventDefault();
            event.stopPropagation();
            event.stopImmediatePropagation();
            return false;
        }
    }
    
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        // If composition is active, wait for it to complete
        if (isComposing.value) {
            // Mark that we should send when composition ends
            shouldSendOnCompositionEnd.value = true;
            return;
        } else {
            sendMessage();
        }
    } else if (event.ctrlKey && event.key === "u") {
        event.preventDefault();
        fileUploadRef.value?.openFileDialog();
    } else if (event.key === "Escape") {
        // ESC 키로 드롭다운들 닫기
        if (showMentionDropdown.value) {
            closeMentionDropdown();
        }
        if (showSearchDropdown.value) {
            showSearchDropdown.value = false;
        }
    }
    // 다른 키 입력들은 기본 동작을 방해하지 않음
};

// 텍스트 변경 감지 (input 이벤트에서 처리)
const handleInput = () => {
    // 텍스트 변경 시 높이 조정
    adjustHeight();
    
    // @ 멘션 감지 (드롭다운이 이미 열려있지 않을 때만)
    if (!showMentionDropdown.value) {
        checkForMention();
    }
};

// 메시지 전송
const sendMessage = () => {
    if (!canSend.value) return;

    // 멘션된 부서 정보와 선택된 모델과 함께 메시지 전송
    const messageData = {
        content: message.value,
        mentionedDepartments: mentionedDepartments.value,
        files: chatStore.uploadedFiles,
        selectedModel: selectedModel.value
    };

    chatStore.sendMessage(messageData);
    message.value = "";
    // mentionedDepartments.value = []; // 부서 선택 유지

    // Reset textarea immediately without nextTick
    if (textareaRef.value) {
        textareaRef.value.style.height = "auto";
        textareaRef.value.style.overflowY = "hidden";
        textareaRef.value.focus();
    }
};

// 생성 중지
const stopGeneration = () => {
    chatStore.stopStreaming();
};

// @ 멘션 감지
const checkForMention = () => {
    const cursorPosition = textareaRef.value?.selectionStart || 0;
    const textBeforeCursor = message.value.substring(0, cursorPosition);
    
    // @ 패턴 찾기 (빈 검색어도 허용)
    const mentionMatch = textBeforeCursor.match(/@([^@\s]*)$/);
    
    if (mentionMatch) {
        mentionStartIndex.value = mentionMatch.index;
        mentionSearchQuery.value = mentionMatch[1];
        showMentionDropdown.value = true;
    } else {
        closeMentionDropdown();
    }
};

// 멘션 드롭다운 닫기
const closeMentionDropdown = () => {
    showMentionDropdown.value = false;
    mentionSearchQuery.value = "";
    mentionStartIndex.value = -1;
};

// 멘션 선택 처리
const handleMentionSelect = (department) => {
    if (mentionStartIndex.value >= 0) {
        // @ 검색어 부분을 완전히 제거하고 커서 위치만 조정
        const beforeMention = message.value.substring(0, mentionStartIndex.value);
        const afterMention = message.value.substring(mentionStartIndex.value + mentionSearchQuery.value.length + 1);
        message.value = beforeMention + afterMention;
        
        // 멘션된 부서 목록에 추가 (중복 방지)
        if (!mentionedDepartments.value.find(d => d.id === department.id)) {
            mentionedDepartments.value.push(department);
        }
        
        // 커서 위치 조정 (멘션 텍스트가 제거된 위치)
        nextTick(() => {
            const newCursorPosition = mentionStartIndex.value;
            textareaRef.value?.setSelectionRange(newCursorPosition, newCursorPosition);
            textareaRef.value?.focus();
        });
    }
    
    closeMentionDropdown();
};

// 멘션 제거
const removeMention = (department) => {
    const index = mentionedDepartments.value.findIndex(d => d.id === department.id);
    if (index > -1) {
        mentionedDepartments.value.splice(index, 1);
    }
    
    // 텍스트에는 @부서명이 남아있지 않으므로 제거 로직 불필요
};

// @ 멘션 버튼 클릭 처리
const triggerMention = () => {
    if (!textareaRef.value) return;
    
    const cursorPosition = textareaRef.value.selectionStart;
    const textBeforeCursor = message.value.substring(0, cursorPosition);
    
    // 현재 커서 위치에 @ 추가
    const newText = textBeforeCursor + '@';
    message.value = newText + message.value.substring(cursorPosition);
    
    // 커서를 @ 뒤로 이동
    nextTick(() => {
        const newCursorPosition = cursorPosition + 1;
        textareaRef.value?.setSelectionRange(newCursorPosition, newCursorPosition);
        textareaRef.value?.focus();
        
        // 멘션 드롭다운 열기
        mentionStartIndex.value = cursorPosition;
        mentionSearchQuery.value = "";
        showMentionDropdown.value = true;
    });
};

// 검색 드롭다운 토글
const toggleSearchDropdown = () => {
    showSearchDropdown.value = !showSearchDropdown.value;
};

// 검색 키워드 삽입
const insertSearchKeyword = (keyword) => {
    // 버튼 텍스트만 변경하고 채팅 입력창에는 아무것도 추가하지 않음
    selectedSearchType.value = `${keyword} 검색`;
    
    // 드롭다운 닫기
    showSearchDropdown.value = false;
};

// 검색 타입 초기화
const resetSearchType = () => {
    selectedSearchType.value = '검색';
};

// 드래그 앤 드롭 처리
let dragCounter = 0;

const handleDragEnter = (event) => {
    event.preventDefault();
    dragCounter++;
    isDragging.value = true;
};

const handleDragLeave = (event) => {
    event.preventDefault();
    dragCounter--;
    if (dragCounter === 0) {
        isDragging.value = false;
    }
};

const handleDragOver = (event) => {
    event.preventDefault();
};

const handleDrop = (event) => {
    event.preventDefault();
    isDragging.value = false;
    dragCounter = 0;

    const files = Array.from(event.dataTransfer.files);
    files.forEach((file) => {
        chatStore.addFile(file);
    });
};

// Composition start handler
const handleCompositionStart = () => {
    isComposing.value = true;
    shouldSendOnCompositionEnd.value = false;
};

// Composition end handler
const handleCompositionEnd = () => {
    isComposing.value = false;
    if (shouldSendOnCompositionEnd.value) {
        shouldSendOnCompositionEnd.value = false;
        sendMessage();
    }
};

// 전역 키보드 단축키 처리
const handleGlobalKeydown = (event) => {
    // Ctrl/Cmd + K로 채팅 입력창에 포커스
    if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault();
        textareaRef.value?.focus();
    }
    
    // Ctrl/Cmd + /로 도움말 표시 (향후 구현)
    if ((event.ctrlKey || event.metaKey) && event.key === '/') {
        event.preventDefault();
        // TODO: 도움말 모달 표시
        console.log('도움말 단축키');
    }
};

// 외부 클릭으로 드롭다운 닫기
const handleClickOutside = (event) => {
    // 검색 드롭다운이 열려있고 클릭이 외부라면 닫기
    if (showSearchDropdown.value) {
        const searchDropdown = event.target.closest('.search-dropdown-container');
        if (!searchDropdown) {
            showSearchDropdown.value = false;
        }
    }
};

// 전역 드래그 이벤트 리스너
onMounted(() => {
    document.addEventListener("dragenter", handleDragEnter);
    document.addEventListener("dragover", handleDragOver);
    document.addEventListener("dragleave", handleDragLeave);
    document.addEventListener("keydown", handleGlobalKeydown);
    document.addEventListener("click", handleClickOutside);

    // 텍스트 영역 초기화
    nextTick(() => {
        if (textareaRef.value) {
            textareaRef.value.style.height = "auto";
            textareaRef.value.style.overflowY = "hidden";
            adjustHeight();
        }
    });
});

onUnmounted(() => {
    document.removeEventListener("dragenter", handleDragEnter);
    document.removeEventListener("dragover", handleDragOver);
    document.removeEventListener("dragleave", handleDragLeave);
    document.removeEventListener("keydown", handleGlobalKeydown);
    document.removeEventListener("click", handleClickOutside);
});
</script>

<style scoped>
/* 입력창 최대 너비 제한 및 가운데 정렬 */
.relative.mb-6 {
    max-width: 800px;
    margin-left: auto;
    margin-right: auto;
}

/* 반응형 최대 너비 */
@media (max-width: 1024px) {
    .relative.mb-6 {
        max-width: 500px;
    }
}

@media (max-width: 768px) {
    .relative.mb-6 {
        max-width: calc(100% - 2rem);
        margin-left: 1rem;
        margin-right: 1rem;
    }
}

@media (max-width: 480px) {
    .relative.mb-6 {
        max-width: calc(100% - 1rem);
        margin-left: 0.5rem;
        margin-right: 0.5rem;
    }
}
</style>

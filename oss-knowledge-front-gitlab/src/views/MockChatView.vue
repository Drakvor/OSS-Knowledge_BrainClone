<template>
    <MainLayout>
        <MockChatContainer />
    </MainLayout>
</template>

<script setup>
import { onMounted, onUnmounted } from "vue";
import MainLayout from "@/components/layout/MainLayout.vue";
import MockChatContainer from "@/components/chat/MockChatContainer.vue";
import { useConversationStore } from "@/stores/conversation";

const conversationStore = useConversationStore();

// 데모용으로 대화방 생성을 막기 위해 원본 함수 백업
let originalCreateNewConversation = null;

onMounted(() => {
    // 원본 함수 백업
    originalCreateNewConversation = conversationStore.createNewConversation;
    
    // 데모용으로 대화방 생성 비활성화 (하지만 가상 대화방은 반환)
    conversationStore.createNewConversation = async () => {
        console.log("Demo mode: Using virtual conversation");
        const demoConv = {
            id: "demo-conversation-" + Date.now(),
            title: "새 대화", // 초기 제목을 "새 대화"로 설정 (LLM이 동적으로 생성)
            messages: [],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
        };
        
        // 가상 대화방을 conversationStore에 추가
        conversationStore.conversations.push(demoConv);
        conversationStore.currentConversationId = demoConv.id;
        
        return demoConv;
    };
});

onUnmounted(() => {
    // 데모용 가상 대화방 제거
    if (conversationStore.currentConversationId && 
        conversationStore.currentConversationId.startsWith("demo-conversation-")) {
        const index = conversationStore.conversations.findIndex(
            conv => conv.id === conversationStore.currentConversationId
        );
        if (index !== -1) {
            conversationStore.conversations.splice(index, 1);
        }
        conversationStore.currentConversationId = null;
    }
    
    // 원본 함수 복원
    if (originalCreateNewConversation) {
        conversationStore.createNewConversation = originalCreateNewConversation;
    }
});
</script>

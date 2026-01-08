<template>
  <router-view />
</template>

<script setup>
import { onMounted } from "vue";
import { useConversationStore } from "@/stores/conversation";
import { useAuthStore } from "@/stores/auth";

const conversationStore = useConversationStore();
const authStore = useAuthStore();

onMounted(async () => {
    // 인증된 사용자만 대화 목록 로드
    if (authStore.isAuthenticated) {
        try {
            await conversationStore.loadConversations();
        } catch (error) {
            console.error("Failed to load conversations on app start:", error);
        }
    }
});
</script>

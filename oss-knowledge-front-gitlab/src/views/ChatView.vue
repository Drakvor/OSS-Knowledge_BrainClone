<template>
  <MainLayout>
    <ChatContainer />
  </MainLayout>
</template>

<script setup>
import { onMounted } from 'vue'
import MainLayout from '@/components/layout/MainLayout.vue'
import ChatContainer from '@/components/chat/ChatContainer.vue'
import { useRAGDepartmentsStore } from '@/stores/ragDepartments'

const ragDepartmentsStore = useRAGDepartmentsStore()

// 채팅 화면 진입 시 부서 데이터 로드
onMounted(async () => {
  try {
    // 부서 데이터가 아직 로드되지 않았다면 로드
    if (ragDepartmentsStore.departments.length === 0) {
      await ragDepartmentsStore.fetchDepartments()
    }
  } catch (error) {
    console.error('부서 데이터 로드 실패:', error)
  }
})
</script>
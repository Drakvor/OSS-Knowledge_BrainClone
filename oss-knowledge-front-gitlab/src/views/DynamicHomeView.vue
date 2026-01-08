<template>
  <MainLayout>
    <div class="dynamic-home">
      <component :is="currentView" />
    </div>
  </MainLayout>
</template>

<script setup>
import { computed } from 'vue'
import { useUIStore } from '@/stores/ui'
import MainLayout from '@/components/layout/MainLayout.vue'
import ChatView from './ChatView.vue'
import AgentView from './AgentView.vue'

const uiStore = useUIStore()

const currentView = computed(() => {
  return uiStore.isAgentMode ? AgentView : ChatView
})
</script>

<style scoped>
.dynamic-home {
  @apply h-full;
}
</style> 
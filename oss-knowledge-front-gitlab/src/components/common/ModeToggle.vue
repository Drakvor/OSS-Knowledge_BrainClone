<template>
  <div class="mode-toggle-container">
    <div 
      class="mode-toggle"
      @click="toggleMode"
    >
      <div class="toggle-track">
        <div class="toggle-thumb" :class="{ 'translate-x-6': isAgentMode }">
          <div class="thumb-icon">
            <svg v-if="isKnowledgeMode" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
        </div>
        <div class="toggle-labels">
          <span class="label knowledge-label" :class="{ 'active': isKnowledgeMode }">RAG</span>
          <span class="label agent-label" :class="{ 'active': isAgentMode }">Agent</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useUIStore } from '@/stores/ui'

const uiStore = useUIStore()

const isAgentMode = computed(() => uiStore.isAgentMode)
const isKnowledgeMode = computed(() => uiStore.isKnowledgeMode)

const toggleMode = () => {
  uiStore.toggleMode()
}
</script>

<style scoped>
.mode-toggle-container {
  display: flex;
  align-items: center;
  justify-content: center;
}

.mode-toggle {
  position: relative;
  cursor: pointer;
  user-select: none;
}

.toggle-track {
  position: relative;
  width: 100px;
  height: 36px;
  background: linear-gradient(135deg, var(--color-gray-100) 0%, var(--color-gray-200) 100%);
  border: 1px solid var(--color-border-medium);
  border-radius: 18px;
  padding: 3px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.toggle-thumb {
  position: absolute;
  top: 3px;
  left: 1px;
  width: 30px;
  height: 30px;
  background: white;
  border-radius: 15px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
}

.toggle-thumb.translate-x-6 {
  transform: translateX(67px);
}

.thumb-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-gray-500);
  transition: color 0.3s ease;
}

.toggle-labels {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 8px;
  z-index: 1;
}

.label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-gray-500);
  transition: all 0.3s ease;
}

.label.active {
  color: var(--color-gray-700);
}

.knowledge-label {
  margin-left: 4px;
}

.agent-label {
  margin-right: 4px;
}

/* 호버 효과 */
.mode-toggle:hover .toggle-track {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.mode-toggle:hover .toggle-thumb {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
}

/* 활성 상태 효과 */
.mode-toggle:active .toggle-track {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.mode-toggle:active .toggle-thumb {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
</style> 
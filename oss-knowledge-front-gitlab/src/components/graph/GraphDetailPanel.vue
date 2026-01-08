<template>
  <Transition
    enter-active-class="transition-all duration-300 ease-out"
    enter-from-class="translate-x-full opacity-0"
    enter-to-class="translate-x-0 opacity-100"
    leave-active-class="transition-all duration-300 ease-in"
    leave-from-class="translate-x-0 opacity-100"
    leave-to-class="translate-x-full opacity-0"
  >
    <div
      v-if="isVisible"
      ref="sidebarRef"
      class="fixed inset-y-0 right-0 w-96 bg-white shadow-2xl border-l border-gray-200 z-50 flex flex-col"
      style="background-color: var(--color-bg-primary); border-color: var(--color-border-light); cursor: default;"
      tabindex="-1"
      @mouseenter="handleSidebarMouseEnter"
      @mouseleave="handleSidebarMouseLeave"
      @wheel="handleSidebarWheel"
    >
      <!-- 헤더 -->
      <div class="flex items-center justify-between p-6 border-b" style="border-color: var(--color-border-light)">
        <div class="flex items-center gap-3">
          <div 
            class="w-10 h-10 rounded-full flex items-center justify-center text-lg"
            :style="{ backgroundColor: getNodeColor(node?.type) }"
          >
            {{ node?.icon || '📄' }}
          </div>
          <div>
            <h2 class="text-lg font-semibold text-gray-900">{{ node?.label || '노드 정보' }}</h2>
            <p class="text-sm text-gray-500">{{ getNodeTypeText(node?.type) }}</p>
          </div>
        </div>
        <button
          @click="$emit('close')"
          class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-all duration-200"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <!-- 컨텐츠 -->
      <div class="flex-1 overflow-y-auto">
        <!-- 기본 정보 -->
        <div class="p-6 border-b" style="border-color: var(--color-border-light)">
          <h3 class="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            기본 정보
          </h3>
          <div class="space-y-3">
            <div>
              <label class="text-xs font-medium text-gray-500 uppercase tracking-wide">제목</label>
              <p class="text-sm text-gray-900 mt-1">{{ node?.label }}</p>
            </div>
            <div>
              <label class="text-xs font-medium text-gray-500 uppercase tracking-wide">타입</label>
              <div class="flex items-center gap-2 mt-1">
                <span 
                  class="px-2 py-1 text-xs font-medium rounded-full"
                  :style="{ 
                    backgroundColor: getNodeColor(node?.type) + '20', 
                    color: getNodeColor(node?.type) 
                  }"
                >
                  {{ getNodeTypeText(node?.type) }}
                </span>
              </div>
            </div>
            <div>
              <label class="text-xs font-medium text-gray-500 uppercase tracking-wide">부서</label>
              <p class="text-sm text-gray-900 mt-1">{{ getDepartmentName(node?.departmentId) }}</p>
            </div>
            <div>
              <label class="text-xs font-medium text-gray-500 uppercase tracking-wide">중요도</label>
              <div class="flex items-center gap-2 mt-1">
                <div 
                  class="w-2 h-2 rounded-full"
                  :style="{ backgroundColor: getImportanceColor(node?.importance) }"
                ></div>
                <span class="text-sm text-gray-900">{{ getImportanceText(node?.importance) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 연결 정보 -->
        <div class="p-6 border-b" style="border-color: var(--color-border-light)">
          <h3 class="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
            </svg>
            연결 정보
          </h3>
          <div class="space-y-3">
            <div class="grid grid-cols-2 gap-4">
              <div class="text-center p-3 bg-gray-50 rounded-lg">
                <div class="text-2xl font-bold text-blue-600">{{ connectionStats.total }}</div>
                <div class="text-xs text-gray-500">총 연결</div>
              </div>
              <div class="text-center p-3 bg-gray-50 rounded-lg">
                <div class="text-2xl font-bold text-green-600">{{ connectionStats.active }}</div>
                <div class="text-xs text-gray-500">활성 연결</div>
              </div>
            </div>
            
            <!-- 연결 타입별 통계 -->
            <div>
              <label class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2 block">연결 타입별</label>
              <div class="space-y-2">
                <div 
                  v-for="(count, type) in connectionStats.byType" 
                  :key="type"
                  class="flex items-center justify-between text-sm"
                >
                  <div class="flex items-center gap-2">
                    <div 
                      class="w-3 h-3 rounded-full"
                      :style="{ backgroundColor: getEdgeColor(type) }"
                    ></div>
                    <span class="text-gray-700">{{ getRelationTypeText(type) }}</span>
                  </div>
                  <span class="font-medium text-gray-900">{{ count }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 관련 노드 -->
        <div class="p-6 border-b" style="border-color: var(--color-border-light)">
          <h3 class="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
            </svg>
            관련 노드
          </h3>
          <div class="space-y-2 max-h-48 overflow-y-auto">
            <div 
              v-for="relatedNode in relatedNodes" 
              :key="relatedNode.id"
              @click="$emit('select-node', relatedNode)"
              class="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors duration-200"
            >
              <div 
                class="w-8 h-8 rounded-full flex items-center justify-center text-sm"
                :style="{ backgroundColor: getNodeColor(relatedNode.type) }"
              >
                {{ relatedNode.icon || '📄' }}
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-900 truncate">{{ relatedNode.label }}</p>
                <p class="text-xs text-gray-500">{{ getNodeTypeText(relatedNode.type) }}</p>
              </div>
              <div 
                class="px-2 py-1 text-xs font-medium rounded-full"
                :style="{ 
                  backgroundColor: getEdgeColor(relatedNode.relationType) + '20', 
                  color: getEdgeColor(relatedNode.relationType) 
                }"
              >
                {{ getRelationTypeText(relatedNode.relationType) }}
              </div>
            </div>
          </div>
        </div>

        <!-- 메타데이터 -->
        <div v-if="node?.metadata" class="p-6">
          <h3 class="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            메타데이터
          </h3>
          <div class="space-y-2">
            <div 
              v-for="(value, key) in node.metadata" 
              :key="key"
              class="flex justify-between text-sm"
            >
              <span class="text-gray-500">{{ key }}</span>
              <span class="text-gray-900 font-medium">{{ value }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 액션 버튼들 -->
      <div class="p-6 border-t" style="border-color: var(--color-border-light)">
        <div class="flex gap-3">
          <button
            @click="$emit('edit-node', node)"
            class="flex-1 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors duration-200 flex items-center justify-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
            </svg>
            편집
          </button>
          <button
            @click="$emit('add-connection', node)"
            class="flex-1 px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition-colors duration-200 flex items-center justify-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
            연결 추가
          </button>
          <button
            @click="$emit('delete-node', node)"
            class="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors duration-200"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'

const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false
  },
  node: {
    type: Object,
    default: null
  },
  departments: {
    type: Array,
    default: () => []
  },
  relatedNodes: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'select-node', 'edit-node', 'add-connection', 'delete-node'])

const sidebarRef = ref(null)

// 사이드바가 열릴 때 포커스 설정
watch(() => props.isVisible, (isVisible) => {
  if (isVisible) {
    nextTick(() => {
      if (sidebarRef.value) {
        sidebarRef.value.focus()
        // 사이드바 내부의 첫 번째 스크롤 가능한 요소로 스크롤
        const scrollableElement = sidebarRef.value.querySelector('.overflow-y-auto')
        if (scrollableElement) {
          scrollableElement.scrollTop = 0
        }
      }
    })
  }
})

// 사이드바 마우스 이벤트 처리
const handleSidebarMouseEnter = () => {
  // 사이드바에 마우스가 들어오면 커서를 기본으로 변경
  document.body.style.cursor = 'default'
  // 그래프 컨테이너의 스크롤을 비활성화
  const graphContainer = document.querySelector('.graph-container')
  if (graphContainer) {
    graphContainer.style.overflow = 'hidden'
  }
}

const handleSidebarMouseLeave = () => {
  // 사이드바에서 마우스가 나가면 커서를 원래대로 복원
  document.body.style.cursor = ''
  // 그래프 컨테이너의 스크롤을 다시 활성화
  const graphContainer = document.querySelector('.graph-container')
  if (graphContainer) {
    graphContainer.style.overflow = ''
  }
}

// 사이드바 내부 휠 이벤트 처리
const handleSidebarWheel = (event) => {
  // 사이드바 내부에서 휠 이벤트가 발생하면 이벤트 전파를 막아서
  // 메인 그래프 영역으로 스크롤이 전달되지 않도록 함
  event.stopPropagation()
}

// 연결 통계 계산
const connectionStats = computed(() => {
  if (!props.node || !props.relatedNodes) {
    return { total: 0, active: 0, byType: {} }
  }

  const byType = {}
  props.relatedNodes.forEach(node => {
    const type = node.relationType || 'unknown'
    byType[type] = (byType[type] || 0) + 1
  })

  return {
    total: props.relatedNodes.length,
    active: props.relatedNodes.filter(n => n.isActive).length,
    byType
  }
})

// 유틸리티 함수들
const getNodeColor = (type) => {
  const colors = {
    'document': '#3b82f6',
    'chunk': '#8b5cf6',
    'concept': '#06b6d4',
    'process': '#10b981'
  }
  return colors[type] || '#6b7280'
}

const getNodeTypeText = (type) => {
  const typeMap = {
    'document': '문서',
    'chunk': '청크',
    'concept': '개념',
    'process': '프로세스'
  }
  return typeMap[type] || type
}

const getDepartmentName = (departmentId) => {
  const dept = props.departments.find(d => d.id === departmentId)
  return dept ? dept.name : '알 수 없음'
}

const getImportanceColor = (importance) => {
  const colors = {
    'high': '#ef4444',
    'medium': '#f59e0b',
    'low': '#10b981'
  }
  return colors[importance] || '#6b7280'
}

const getImportanceText = (importance) => {
  const textMap = {
    'high': '높음',
    'medium': '보통',
    'low': '낮음'
  }
  return textMap[importance] || '보통'
}

const getEdgeColor = (type) => {
  const colors = {
    'semantic': '#3b82f6',
    'dependency': '#f59e0b',
    'reference': '#8b5cf6',
    'hierarchical': '#10b981',
    'temporal': '#06b6d4',
    'causal': '#ef4444'
  }
  return colors[type] || '#6b7280'
}

const getRelationTypeText = (type) => {
  const typeMap = {
    'semantic': '의미적 연관',
    'dependency': '의존성',
    'reference': '참조',
    'hierarchical': '계층적',
    'temporal': '시간적',
    'causal': '인과관계'
  }
  return typeMap[type] || type
}
</script>

<style scoped>
/* 스크롤바 스타일링 */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #f1f5f9;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 사이드바 영역에서 커서 강제 설정 */
.fixed.inset-y-0.right-0 {
  cursor: default !important;
}

.fixed.inset-y-0.right-0 * {
  cursor: default !important;
}

/* 버튼과 클릭 가능한 요소는 포인터 커서 유지 */
.fixed.inset-y-0.right-0 button,
.fixed.inset-y-0.right-0 [role="button"],
.fixed.inset-y-0.right-0 .cursor-pointer {
  cursor: pointer !important;
}

/* 입력 필드는 텍스트 커서 유지 */
.fixed.inset-y-0.right-0 input,
.fixed.inset-y-0.right-0 textarea,
.fixed.inset-y-0.right-0 select {
  cursor: text !important;
}
</style>

<template>
  <MainLayout>
    <div class="agent-view">
      <!-- 상단 설명 텍스트 -->
    <div class="agent-description">
      <p class="description-text">AI 기반 작업 처리 및 자동화</p>
    </div>

    <!-- 메인 컨텐츠 -->
    <div class="agent-content">
      <div class="content-layout">
        <!-- 왼쪽: AI 응답 및 액션 처리 영역 -->
        <div class="main-content">
          <!-- AI 응답 및 액션 처리 영역 -->
          <div class="action-section" v-if="currentAction">
            <!-- AI 분석 결과 -->
            <div class="ai-analysis">
              <div class="analysis-header">
                <div class="ai-avatar">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <div class="analysis-content">
                  <h3 class="analysis-title">{{ currentAction.title }}</h3>
                  <p class="analysis-description">{{ currentAction.description }}</p>
                </div>
              </div>
            </div>

            <!-- 필요한 정보 수집 -->
            <div class="info-collection" v-if="currentAction.requiredFields.length > 0">
              <div class="collection-header">
                <h4 class="collection-title">추가 정보가 필요합니다</h4>
                <p class="collection-subtitle">다음 정보를 입력해주세요</p>
              </div>
              
              <div class="fields-container">
                <div 
                  v-for="field in currentAction.requiredFields" 
                  :key="field.id"
                  class="field-item"
                >
                  <label class="field-label">{{ field.label }}</label>
                  
                  <!-- 텍스트 입력 -->
                  <input 
                    v-if="field.type === 'text'"
                    v-model="field.value"
                    :placeholder="field.placeholder"
                    class="field-input"
                  />
                  
                  <!-- 선택 입력 -->
                  <select 
                    v-else-if="field.type === 'select'"
                    v-model="field.value"
                    class="field-select"
                  >
                    <option value="">{{ field.placeholder }}</option>
                    <option 
                      v-for="option in field.options" 
                      :key="option.value" 
                      :value="option.value"
                    >
                      {{ option.label }}
                    </option>
                  </select>
                  
                  <!-- 날짜 입력 -->
                  <input 
                    v-else-if="field.type === 'date'"
                    v-model="field.value"
                    type="datetime-local"
                    class="field-input"
                  />
                </div>
              </div>
              
              <div class="action-buttons">
                <button 
                  @click="executeAction"
                  :disabled="!isAllFieldsFilled"
                  class="execute-btn"
                >
                  <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  실행
                </button>
                <button @click="cancelAction" class="cancel-btn">
                  취소
                </button>
              </div>
            </div>

            <!-- 실행 결과 -->
            <div class="execution-result" v-if="executionResult">
              <div class="result-header">
                <div class="result-icon" :class="executionResult.success ? 'success' : 'error'">
                  <svg v-if="executionResult.success" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
                <div class="result-content">
                  <h4 class="result-title">{{ executionResult.title }}</h4>
                  <p class="result-message">{{ executionResult.message }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 오른쪽: 최근 작업 히스토리 -->
        <div class="sidebar-content" v-if="actionHistory.length > 0">
          <div class="history-section">
            <h2 class="section-title">최근 작업</h2>
            <div class="history-list">
              <div 
                v-for="item in actionHistory" 
                :key="item.id"
                class="history-item"
              >
                <div class="history-icon">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div class="history-content">
                  <h4 class="history-title">{{ item.title }}</h4>
                  <p class="history-prompt">{{ item.prompt }}</p>
                  <p v-if="item.result" class="history-result">{{ item.result }}</p>
                  <span class="history-time">{{ formatTime(item.timestamp) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 프롬프트 입력 영역 - 하단 고정 -->
    <div class="prompt-section">
      <div class="prompt-container">
        <div class="prompt-input-wrapper">
          <div class="prompt-input-container">
            <textarea
              v-model="userPrompt"
              placeholder="원하는 작업을 자연어로 입력하세요. 예시:
• AI개통오더고 계약번호 S00130530에 현장작업자 할당해줘
• VOC 처리해줘
• 계약번호 S00130531 정보 조회해줘"
              class="prompt-input"
              rows="2"
              @keydown.ctrl.enter="processPrompt"
            ></textarea>
            <button 
              @click="processPrompt"
              :disabled="!userPrompt.trim() || isProcessing"
              class="prompt-submit-btn"
            >
              <svg v-if="!isProcessing" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              </svg>
              <svg v-else class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
        </div>
        <div class="prompt-hint">
          <span class="text-sm text-gray-500">Ctrl + Enter로 실행</span>
        </div>
      </div>
    </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useUIStore } from '@/stores/ui'
import MainLayout from '@/components/layout/MainLayout.vue'

const uiStore = useUIStore()

// 상태 관리
const userPrompt = ref('')
const isProcessing = ref(false)
const currentAction = ref(null)
const executionResult = ref(null)
const actionHistory = ref([])

// 모든 필드가 채워졌는지 확인
const isAllFieldsFilled = computed(() => {
  if (!currentAction.value?.requiredFields) return false
  return currentAction.value.requiredFields.every(field => field.value && field.value.trim())
})

// 프롬프트 처리
const processPrompt = async () => {
  if (!userPrompt.value.trim() || isProcessing.value) return
  
  isProcessing.value = true
  
  try {
    // AI 분석 시뮬레이션 (실제로는 API 호출)
    await simulateAIAnalysis(userPrompt.value)
  } catch (error) {
    console.error('프롬프트 처리 오류:', error)
    uiStore.setError('프롬프트 처리 중 오류가 발생했습니다.')
  } finally {
    isProcessing.value = false
  }
}

// Mock 데이터
const mockData = {
  contracts: [
    { id: 'S00130530', name: 'AI개통오더고', status: 'active', type: 'AI' },
    { id: 'S00130531', name: '네트워크설치', status: 'pending', type: 'Network' },
    { id: 'S00130532', name: '서버점검', status: 'completed', type: 'Maintenance' },
    { id: 'S00130533', name: '보안업데이트', status: 'active', type: 'Security' }
  ],
  workers: [
    { id: 'worker1', name: '김철수', level: '전문가', department: 'AI팀', status: 'available' },
    { id: 'worker2', name: '이영희', level: '중급자', department: '네트워크팀', status: 'available' },
    { id: 'worker3', name: '박민수', level: '초급자', department: '인프라팀', status: 'busy' },
    { id: 'worker4', name: '정수진', level: '전문가', department: '보안팀', status: 'available' },
    { id: 'worker5', name: '최영수', level: '중급자', department: 'AI팀', status: 'available' }
  ],
  managers: [
    { id: 'manager1', name: '김매니저', department: 'WM', email: 'kim.manager@company.com' },
    { id: 'manager2', name: '이매니저', department: 'LEAN', email: 'lee.manager@company.com' },
    { id: 'manager3', name: '박매니저', department: '운영팀', email: 'park.manager@company.com' },
    { id: 'manager4', name: '정매니저', department: 'AI팀', email: 'jung.manager@company.com' }
  ]
}

// AI 분석 시뮬레이션
const simulateAIAnalysis = async (prompt) => {
  // 실제로는 AI API를 호출하여 분석
  await new Promise(resolve => setTimeout(resolve, 1500))
  
  // 계약번호 추출
  const contractMatch = prompt.match(/계약번호\s+([A-Z0-9]+)/i)
  const contractId = contractMatch ? contractMatch[1] : null
  const contract = contractId ? mockData.contracts.find(c => c.id === contractId) : null
  
  // 예시: 현장작업자 할당 요청 분석
  if (prompt.includes('현장작업자 할당') || prompt.includes('작업자 할당')) {
    const availableWorkers = mockData.workers.filter(w => w.status === 'available')
    
    currentAction.value = {
      id: 'assign-worker',
      title: '현장작업자 할당',
      description: contract 
        ? `계약번호 ${contract.id} (${contract.name})에 현장작업자를 할당합니다.`
        : '현장작업자를 할당합니다.',
      contract: contract,
      requiredFields: [
        {
          id: 'worker',
          label: '작업자 선택',
          type: 'select',
          placeholder: '작업자를 선택하세요',
          value: '',
          options: availableWorkers.map(w => ({
            value: w.id,
            label: `${w.name} (${w.level}) - ${w.department}`
          }))
        },
        {
          id: 'deadline',
          label: '마감일시',
          type: 'date',
          placeholder: '마감일시를 선택하세요',
          value: ''
        },
        {
          id: 'priority',
          label: '우선순위',
          type: 'select',
          placeholder: '우선순위를 선택하세요',
          value: '',
          options: [
            { value: 'low', label: '낮음' },
            { value: 'medium', label: '보통' },
            { value: 'high', label: '높음' },
            { value: 'urgent', label: '긴급' }
          ]
        }
      ]
    }
  } else if (prompt.includes('VOC') || prompt.includes('고객문의')) {
    currentAction.value = {
      id: 'process-voc',
      title: 'VOC 처리',
      description: '고객 문의사항을 처리합니다.',
      requiredFields: [
        {
          id: 'priority',
          label: '우선순위',
          type: 'select',
          placeholder: '우선순위를 선택하세요',
          value: '',
          options: [
            { value: 'low', label: '낮음' },
            { value: 'medium', label: '보통' },
            { value: 'high', label: '높음' },
            { value: 'urgent', label: '긴급' }
          ]
        },
        {
          id: 'assignee',
          label: '담당자',
          type: 'select',
          placeholder: '담당자를 선택하세요',
          value: '',
          options: mockData.managers.map(m => ({
            value: m.id,
            label: `${m.name} (${m.department})`
          }))
        },
        {
          id: 'category',
          label: '문의 카테고리',
          type: 'select',
          placeholder: '카테고리를 선택하세요',
          value: '',
          options: [
            { value: 'technical', label: '기술 문의' },
            { value: 'billing', label: '결제 문의' },
            { value: 'service', label: '서비스 문의' },
            { value: 'complaint', label: '불만 사항' },
            { value: 'suggestion', label: '건의 사항' }
          ]
        }
      ]
    }
  } else if (prompt.includes('계약') || prompt.includes('오더')) {
    currentAction.value = {
      id: 'contract-info',
      title: '계약 정보 조회',
      description: '계약 정보를 조회합니다.',
      contract: contract,
      requiredFields: [
        {
          id: 'action',
          label: '수행할 작업',
          type: 'select',
          placeholder: '작업을 선택하세요',
          value: '',
          options: [
            { value: 'view', label: '계약 정보 보기' },
            { value: 'update', label: '계약 정보 수정' },
            { value: 'cancel', label: '계약 취소' },
            { value: 'extend', label: '계약 연장' }
          ]
        }
      ]
    }
  } else {
    // 기본 응답
    currentAction.value = {
      id: 'general',
      title: '작업 분석',
      description: '요청하신 작업을 분석했습니다. 추가 정보가 필요합니다.',
      requiredFields: [
        {
          id: 'details',
          label: '상세 정보',
          type: 'text',
          placeholder: '추가 정보를 입력하세요',
          value: ''
        }
      ]
    }
  }
  
  executionResult.value = null
}

// 액션 실행
const executeAction = async () => {
  if (!isAllFieldsFilled.value) return
  
  try {
    // 실제 액션 실행 시뮬레이션
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 실행 결과 생성
    let resultMessage = ''
    
    if (currentAction.value.id === 'assign-worker') {
      const worker = mockData.workers.find(w => w.id === currentAction.value.requiredFields.find(f => f.id === 'worker').value)
      const priority = currentAction.value.requiredFields.find(f => f.id === 'priority').value
      const deadline = currentAction.value.requiredFields.find(f => f.id === 'deadline').value
      
      resultMessage = `작업자 ${worker.name}이(가) 계약번호 ${currentAction.value.contract?.id || 'N/A'}에 할당되었습니다. 우선순위: ${priority}, 마감일시: ${new Date(deadline).toLocaleString('ko-KR')}`
    } else if (currentAction.value.id === 'process-voc') {
      const assignee = mockData.managers.find(m => m.id === currentAction.value.requiredFields.find(f => f.id === 'assignee').value)
      const priority = currentAction.value.requiredFields.find(f => f.id === 'priority').value
      const category = currentAction.value.requiredFields.find(f => f.id === 'category').value
      
      resultMessage = `VOC가 ${assignee.name}에게 할당되었습니다. 우선순위: ${priority}, 카테고리: ${category}`
    } else if (currentAction.value.id === 'contract-info') {
      const action = currentAction.value.requiredFields.find(f => f.id === 'action').value
      resultMessage = `계약번호 ${currentAction.value.contract?.id || 'N/A'}에 대한 ${action} 작업이 완료되었습니다.`
    } else {
      resultMessage = `${currentAction.value.title}이 성공적으로 실행되었습니다.`
    }
    
    executionResult.value = {
      success: true,
      title: '작업 완료',
      message: resultMessage
    }
    
    // 히스토리에 추가
    actionHistory.value.unshift({
      id: Date.now(),
      title: currentAction.value.title,
      prompt: userPrompt.value,
      timestamp: new Date(),
      result: resultMessage
    })
    
    // 성공 메시지 표시
    uiStore.setSuccess('작업이 성공적으로 완료되었습니다.')
    
    // 폼 초기화
    userPrompt.value = ''
    currentAction.value = null
    
  } catch (error) {
    executionResult.value = {
      success: false,
      title: '작업 실패',
      message: '작업 실행 중 오류가 발생했습니다.'
    }
    uiStore.setError('작업 실행 중 오류가 발생했습니다.')
  }
}

// 액션 취소
const cancelAction = () => {
  currentAction.value = null
  executionResult.value = null
  userPrompt.value = ''
}

// 시간 포맷팅
const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return '방금 전'
  if (diffMins < 60) return `${diffMins}분 전`
  if (diffHours < 24) return `${diffHours}시간 전`
  if (diffDays < 7) return `${diffDays}일 전`

  return date.toLocaleDateString('ko-KR', {
    month: 'short',
    day: 'numeric',
  })
}
</script>

<style scoped>
.agent-view {
  @apply h-full flex flex-col;
  background-color: var(--color-bg-primary);
}

.agent-content {
  @apply flex-1 overflow-y-auto p-6;
  background-color: var(--color-bg-primary);
}

/* 상단 설명 텍스트 */
.agent-description {
  @apply px-6 py-3 flex-shrink-0;
  background-color: var(--color-bg-primary);
  border-bottom: 1px solid var(--color-border-light);
}

.description-text {
  @apply text-sm text-gray-600 font-medium;
}

.agent-content {
  @apply flex-1 overflow-y-auto p-6;
}

.content-layout {
  @apply flex gap-6 max-w-7xl mx-auto;
}

.main-content {
  @apply flex-1 min-w-0;
}

.sidebar-content {
  @apply w-80 flex-shrink-0;
}

/* 프롬프트 섹션 */
.prompt-section {
  @apply flex-shrink-0 mb-6;
  background-color: var(--color-bg-primary);
}

.prompt-container {
  @apply max-w-4xl mx-auto px-6;
}

.prompt-input-wrapper {
  @apply relative;
}

.prompt-input-container {
  @apply relative rounded-2xl border transition-all duration-200 shadow-md hover:shadow-lg;
  background-color: var(--color-bg-primary);
  border-color: var(--color-border-light);
}

.prompt-input-container:focus-within {
  border-color: var(--color-primary-300);
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  box-shadow: 0 0 0 4px var(--color-primary-50);
}

.prompt-input {
  @apply w-full p-4 pr-16 bg-transparent resize-none focus:outline-none;
  @apply text-gray-900 placeholder-gray-500;
  border: none;
}

.prompt-submit-btn {
  @apply absolute right-3 top-1/2 transform -translate-y-1/2 p-2 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200;
  background-color: var(--color-primary-600);
}

.prompt-submit-btn:hover:not(:disabled) {
  background-color: var(--color-primary-700);
}

.prompt-hint {
  @apply mt-2 text-center;
}

/* 액션 섹션 */
.action-section {
  @apply max-w-4xl mx-auto mb-8;
}

.ai-analysis {
  @apply bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6;
}

.analysis-header {
  @apply flex items-start gap-4;
}

.ai-avatar {
  @apply w-10 h-10 bg-slate-100 text-slate-600 rounded-lg flex items-center justify-center flex-shrink-0;
}

.analysis-content {
  @apply flex-1;
}

.analysis-title {
  @apply text-lg font-semibold text-gray-900 mb-2;
}

.analysis-description {
  @apply text-gray-600;
}

/* 정보 수집 */
.info-collection {
  @apply bg-white rounded-lg shadow-sm border border-gray-200 p-6;
}

.collection-header {
  @apply mb-6;
}

.collection-title {
  @apply text-lg font-semibold text-gray-900 mb-1;
}

.collection-subtitle {
  @apply text-gray-600;
}

.fields-container {
  @apply space-y-4 mb-6;
}

.field-item {
  @apply space-y-2;
}

.field-label {
  @apply block text-sm font-medium text-gray-700;
}

.field-input,
.field-select {
  @apply w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-500 focus:border-transparent;
}

.action-buttons {
  @apply flex gap-3 justify-end;
}

.execute-btn {
  @apply px-4 py-2 bg-slate-600 text-white rounded-lg font-medium hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center;
}

.cancel-btn {
  @apply px-4 py-2 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2;
}

/* 실행 결과 */
.execution-result {
  @apply bg-white rounded-lg shadow-sm border border-gray-200 p-6 mt-6;
}

.result-header {
  @apply flex items-start gap-4;
}

.result-icon {
  @apply w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0;
}

.result-icon.success {
  @apply bg-green-100 text-green-600;
}

.result-icon.error {
  @apply bg-red-100 text-red-600;
}

.result-content {
  @apply flex-1;
}

.result-title {
  @apply text-lg font-semibold text-gray-900 mb-1;
}

.result-message {
  @apply text-gray-600;
}

/* 히스토리 섹션 */
.history-section {
  @apply max-w-4xl mx-auto;
}

.section-title {
  @apply text-xl font-semibold text-gray-900 mb-4;
}

.history-list {
  @apply space-y-3;
}

.history-item {
  @apply bg-white rounded-lg p-4 shadow-sm border border-gray-200 flex items-start gap-4;
}

.history-icon {
  @apply w-8 h-8 bg-green-100 text-green-600 rounded-lg flex items-center justify-center flex-shrink-0;
}

.history-content {
  @apply flex-1;
}

.history-title {
  @apply font-semibold text-gray-900 mb-1;
}

.history-prompt {
  @apply text-sm text-gray-600 mb-1;
}

.history-result {
  @apply text-sm text-green-600 mb-1 font-medium;
}

.history-time {
  @apply text-xs text-gray-500;
}
</style> 
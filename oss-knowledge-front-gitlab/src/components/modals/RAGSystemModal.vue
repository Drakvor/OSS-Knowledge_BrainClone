<template>
  <div v-if="isVisible" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
      <div class="p-6">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-semibold" style="color: var(--color-gray-900)">
            {{ isEdit ? 'RAG 시스템 편집' : '새 RAG 시스템 추가' }}
          </h3>
          <button
            @click="closeModal"
            class="p-2 transition-colors rounded-lg hover:bg-gray-100"
            style="color: var(--color-gray-400)"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <form @submit.prevent="saveDepartment" class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-2" style="color: var(--color-gray-700)">시스템 이름</label>
            <input
              v-model="formData.name"
              type="text"
              required
              class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              style="border-color: var(--color-border-light)"
              placeholder="예: 기술지원팀"
            >
          </div>

          <div>
            <label class="block text-sm font-medium mb-2" style="color: var(--color-gray-700)">설명</label>
            <textarea
              v-model="formData.description"
              required
              rows="3"
              class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              style="border-color: var(--color-border-light)"
              placeholder="이 RAG 시스템의 용도를 설명해주세요"
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium mb-2" style="color: var(--color-gray-700)">아이콘</label>
            <div class="grid grid-cols-8 gap-2">
              <button
                v-for="icon in availableIcons"
                :key="icon"
                type="button"
                @click="selectIcon(icon)"
                :class="[
                  'p-3 text-2xl border-2 rounded-lg transition-all duration-200 transform',
                  formData.icon === icon 
                    ? 'border-blue-500 bg-blue-100 scale-105 shadow-md' 
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50 hover:scale-105'
                ]"
              >
                {{ icon }}
              </button>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium mb-2" style="color: var(--color-gray-700)">키워드 (쉼표로 구분)</label>
            <input
              v-model="keywordsInput"
              type="text"
              class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              style="border-color: var(--color-border-light)"
              placeholder="예: 기술, 지원, 문제, 해결"
            >
          </div>

          <div class="flex items-center space-x-2">
            <input
              v-model="formData.status"
              type="checkbox"
              true-value="active"
              false-value="inactive"
              class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            >
            <label 
              @click="toggleSystemStatus"
              class="text-sm cursor-pointer hover:text-primary-600 transition-colors duration-200" 
              style="color: var(--color-gray-700)"
            >
              시스템 활성화
            </label>
          </div>

          <div class="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              @click="closeModal"
              class="px-4 py-2 text-sm font-medium border rounded-lg transition-colors hover:bg-gray-50"
              style="border-color: var(--color-border-light); color: var(--color-gray-700)"
            >
              취소
            </button>
            <button
              type="submit"
              class="btn btn-primary"
            >
              {{ isEdit ? '저장' : '추가' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false
  },
  department: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'save'])

// 계산된 속성
const isEdit = computed(() => !!props.department)

// 폼 데이터
const formData = ref({
  name: '',
  description: '',
  icon: '🏢',
  status: 'active',
  keywords: []
})

const keywordsInput = ref('')

// 사용 가능한 아이콘
const availableIcons = ['🏢', '🔧', '👥', '💳', '📈', '💻', '🔒', '⚙️', '📊', '🎯', '🚀', '💡', '📋', '🔍', '📞', '💬']

// 폼 초기화
const resetForm = () => {
  formData.value = {
    name: '',
    description: '',
    icon: '🏢',
    status: 'active',
    keywords: []
  }
  keywordsInput.value = ''
}

// props 변경 감지
watch(() => props.department, (newDept) => {
  if (newDept) {
    formData.value = {
      name: newDept.name,
      description: newDept.description,
      icon: newDept.icon,
      status: newDept.status || 'active',
      keywords: newDept.keywords || []
    }
    keywordsInput.value = (newDept.keywords || []).join(', ')
  } else {
    resetForm()
  }
}, { immediate: true })

// 저장
const saveDepartment = () => {
  const departmentData = {
    ...formData.value,
    keywords: keywordsInput.value.split(',').map(k => k.trim()).filter(k => k)
  }
  
  emit('save', departmentData)
}

// 아이콘 선택
const selectIcon = (icon) => {
  formData.value.icon = icon
}

// 시스템 활성화 토글
const toggleSystemStatus = () => {
  formData.value.status = formData.value.status === 'active' ? 'inactive' : 'active'
}

// 모달 닫기
const closeModal = () => {
  emit('close')
  resetForm()
}
</script>

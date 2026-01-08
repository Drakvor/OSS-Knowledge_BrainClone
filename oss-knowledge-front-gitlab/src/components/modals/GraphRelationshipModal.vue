<template>
  <div v-if="isVisible" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl shadow-xl max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
      <div class="p-6">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-semibold text-gray-900">
            {{ isEdit ? '관계 편집' : '새 관계 추가' }}
          </h3>
          <button
            @click="closeModal"
            class="text-gray-400 hover:text-gray-600"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <form @submit.prevent="saveRelationship" class="space-y-4">
          <!-- 소스 노드 선택 -->
          <div>
            <label class="block text-sm font-medium mb-2 text-gray-700">시작 노드</label>
            <select
              v-model="formData.source"
              required
              class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              :disabled="isEdit"
            >
              <option value="">노드를 선택하세요</option>
              <option 
                v-for="node in availableNodes" 
                :key="node.id" 
                :value="node.id"
              >
                {{ node.icon }} {{ node.label }}
              </option>
            </select>
          </div>

          <!-- 타겟 노드 선택 -->
          <div>
            <label class="block text-sm font-medium mb-2 text-gray-700">끝 노드</label>
            <select
              v-model="formData.target"
              required
              class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              :disabled="isEdit"
            >
              <option value="">노드를 선택하세요</option>
              <option 
                v-for="node in availableNodes" 
                :key="node.id" 
                :value="node.id"
                :disabled="node.id === formData.source"
              >
                {{ node.icon }} {{ node.label }}
              </option>
            </select>
          </div>

          <!-- 관계 타입 -->
          <div>
            <label class="block text-sm font-medium mb-2 text-gray-700">관계 타입</label>
            <select
              v-model="formData.type"
              required
              class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">관계 타입을 선택하세요</option>
              <option value="semantic">의미적 연관</option>
              <option value="dependency">의존성</option>
              <option value="reference">참조</option>
              <option value="hierarchical">계층적</option>
              <option value="temporal">시간적</option>
              <option value="causal">인과관계</option>
            </select>
          </div>

          <!-- 관계 라벨 -->
          <div>
            <label class="block text-sm font-medium mb-2 text-gray-700">관계 라벨</label>
            <input
              v-model="formData.label"
              type="text"
              required
              class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="예: 상호 연관, 참조, 포함"
            >
          </div>

          <!-- 관계 강도 -->
          <div>
            <label class="block text-sm font-medium mb-2 text-gray-700">
              관계 강도: {{ Math.round(formData.strength * 100) }}%
            </label>
            <input
              v-model="formData.strength"
              type="range"
              min="0"
              max="1"
              step="0.1"
              class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            >
            <div class="flex justify-between text-xs text-gray-500 mt-1">
              <span>약함</span>
              <span>보통</span>
              <span>강함</span>
            </div>
          </div>

          <!-- 관계 설명 -->
          <div>
            <label class="block text-sm font-medium mb-2 text-gray-700">관계 설명</label>
            <textarea
              v-model="formData.description"
              rows="3"
              class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="이 관계에 대한 자세한 설명을 입력하세요"
            ></textarea>
          </div>

          <!-- 관계 방향성 -->
          <div class="flex items-center space-x-4">
            <label class="flex items-center">
              <input
                v-model="formData.directional"
                type="checkbox"
                class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              >
              <span class="ml-2 text-sm text-gray-700">방향성 있는 관계</span>
            </label>
          </div>

          <!-- 관계 가중치 -->
          <div>
            <label class="block text-sm font-medium mb-2 text-gray-700">관계 가중치</label>
            <input
              v-model="formData.weight"
              type="number"
              min="0"
              max="10"
              step="0.1"
              class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="관계의 중요도 (0-10)"
            >
          </div>

          <!-- 관계 메타데이터 -->
          <div>
            <label class="block text-sm font-medium mb-2 text-gray-700">메타데이터</label>
            <div class="space-y-2">
              <input
                v-model="formData.metadata.source"
                type="text"
                class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="관계 생성 근거 (예: 자동 추론, 수동 입력)"
              >
              <input
                v-model="formData.metadata.confidence"
                type="number"
                min="0"
                max="1"
                step="0.1"
                class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="신뢰도 (0-1)"
              >
            </div>
          </div>

          <div class="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              @click="closeModal"
              class="px-4 py-2 text-sm font-medium border rounded-lg hover:bg-gray-50"
            >
              취소
            </button>
            <button
              type="submit"
              class="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700"
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
import { ref, computed, watch } from 'vue'

const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false
  },
  relationship: {
    type: Object,
    default: null
  },
  nodes: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'save'])

// 계산된 속성
const isEdit = computed(() => !!props.relationship)

// 폼 데이터
const formData = ref({
  source: '',
  target: '',
  type: '',
  label: '',
  strength: 0.5,
  description: '',
  directional: false,
  weight: 1,
  metadata: {
    source: '',
    confidence: 0.8
  }
})

// 사용 가능한 노드들 (소스와 타겟이 다른 노드들)
const availableNodes = computed(() => {
  return props.nodes.filter(node => 
    node.id !== formData.value.source || !formData.value.source
  )
})

// 폼 초기화
const resetForm = () => {
  formData.value = {
    source: '',
    target: '',
    type: '',
    label: '',
    strength: 0.5,
    description: '',
    directional: false,
    weight: 1,
    metadata: {
      source: '',
      confidence: 0.8
    }
  }
}

// props 변경 감지
watch(() => props.relationship, (newRelationship) => {
  if (newRelationship) {
    formData.value = {
      source: newRelationship.source || '',
      target: newRelationship.target || '',
      type: newRelationship.type || '',
      label: newRelationship.label || '',
      strength: newRelationship.strength || 0.5,
      description: newRelationship.description || '',
      directional: newRelationship.directional || false,
      weight: newRelationship.weight || 1,
      metadata: {
        source: newRelationship.metadata?.source || '',
        confidence: newRelationship.metadata?.confidence || 0.8
      }
    }
  } else {
    resetForm()
  }
}, { immediate: true })

// 저장
const saveRelationship = () => {
  const relationshipData = {
    ...formData.value,
    metadata: {
      ...formData.value.metadata,
      updatedAt: new Date().toISOString()
    }
  }
  
  emit('save', relationshipData)
}

// 모달 닫기
const closeModal = () => {
  emit('close')
  resetForm()
}
</script>

<style scoped>
/* 커스텀 슬라이더 스타일 */
input[type="range"]::-webkit-slider-thumb {
  appearance: none;
  height: 20px;
  width: 20px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: 2px solid #ffffff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

input[type="range"]::-moz-range-thumb {
  height: 20px;
  width: 20px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: 2px solid #ffffff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
</style>

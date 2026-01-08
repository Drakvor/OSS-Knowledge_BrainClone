<template>
  <div
    v-if="show"
    class="mention-dropdown absolute bottom-full left-0 mb-2 w-80 bg-white rounded-xl shadow-lg border border-gray-200 z-50 max-h-64 overflow-hidden"
    style="border-color: var(--color-border-light)"
  >
    <!-- 검색 입력창 -->
    <div class="p-3 border-b" style="border-color: var(--color-border-light)">
      <div class="relative">
        <input
          ref="searchInput"
          :value="searchQuery"
          type="text"
          placeholder="부서 검색..."
          class="w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          style="border-color: var(--color-border-light)"
          @keydown="handleSearchKeydown"
          @keydown.capture="handleSearchKeydown"
          @input="handleSearchInput"
        />
        <svg
          class="absolute right-3 top-2.5 w-4 h-4 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>
    </div>

    <!-- 부서 목록 -->
    <div ref="scrollContainer" class="max-h-48 overflow-y-auto">
      <div
        v-for="(department, index) in filteredDepartments"
        :key="department.id"
        :ref="el => itemRefs[index] = el"
        @click="selectDepartment(department)"
        @mouseenter="hoveredIndex = index"
        :class="[
          'flex items-center gap-3 p-3 cursor-pointer transition-colors duration-150',
          hoveredIndex === index ? 'bg-teal-50' : 'hover:bg-gray-50',
          selectedIndex === index ? 'bg-teal-100 border-l-2 border-teal-500' : ''
        ]"
      >
        <!-- 부서 아이콘 -->
        <div class="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-lg">
          {{ department.icon }}
        </div>

        <!-- 부서 정보 -->
        <div class="flex-1 min-w-0">
          <div class="font-medium text-sm text-gray-900 truncate">
            {{ department.name }}
          </div>
          <div class="text-xs text-gray-500 truncate">
            {{ department.description }}
          </div>
        </div>

        <!-- 선택 표시 -->
        <div
          v-if="selectedIndex === index"
          class="flex-shrink-0 w-5 h-5 text-teal-500"
        >
          <svg fill="currentColor" viewBox="0 0 20 20">
            <path
              fill-rule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clip-rule="evenodd"
            />
          </svg>
        </div>
      </div>

      <!-- 결과가 없을 때 -->
      <div
        v-if="filteredDepartments.length === 0"
        class="p-4 text-center text-sm text-gray-500"
      >
        검색 결과가 없습니다.
      </div>
    </div>

    <!-- 하단 정보 -->
    <div class="p-2 border-t text-xs text-gray-400 text-center" style="border-color: var(--color-border-light)">
      <div class="flex items-center justify-center gap-3">
        <span class="flex items-center gap-1">
          <kbd class="px-1 py-0.5 bg-gray-100 rounded text-xs font-mono">↑↓</kbd>
          이동
        </span>
        <span class="flex items-center gap-1">
          <kbd class="px-1 py-0.5 bg-gray-100 rounded text-xs font-mono">Enter</kbd>
          선택
        </span>
        <span class="flex items-center gap-1">
          <kbd class="px-1 py-0.5 bg-gray-100 rounded text-xs font-mono">Esc</kbd>
          닫기
        </span>
        <span class="flex items-center gap-1">
          <kbd class="px-1 py-0.5 bg-gray-100 rounded text-xs font-mono">클릭</kbd>
          외부닫기
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRAGDepartmentsStore } from '@/stores/ragDepartments'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  searchQuery: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['select', 'close', 'update:searchQuery'])

const ragDepartmentsStore = useRAGDepartmentsStore()
const searchInput = ref(null)
const scrollContainer = ref(null)
const itemRefs = ref([])
const selectedIndex = ref(0)
const hoveredIndex = ref(-1)

// 필터링된 부서 목록 (활성화된 것만)
const filteredDepartments = computed(() => {
  const allDepartments = ragDepartmentsStore.filteredDepartments(props.searchQuery)
  // 활성화된 부서만 필터링 (status가 없거나 'active'인 경우)
  return allDepartments.filter(dept => !dept.status || dept.status === 'active')
})

// 선택된 항목을 뷰포트에 맞게 스크롤
const scrollToSelected = () => {
  if (!scrollContainer.value || !itemRefs.value[selectedIndex.value]) return
  
  const container = scrollContainer.value
  const selectedItem = itemRefs.value[selectedIndex.value]
  
  if (!selectedItem) return
  
  const containerRect = container.getBoundingClientRect()
  const itemRect = selectedItem.getBoundingClientRect()
  
  // 아이템이 컨테이너 위에 있으면 스크롤 업
  if (itemRect.top < containerRect.top) {
    container.scrollTop -= (containerRect.top - itemRect.top)
  }
  // 아이템이 컨테이너 아래에 있으면 스크롤 다운
  else if (itemRect.bottom > containerRect.bottom) {
    container.scrollTop += (itemRect.bottom - containerRect.bottom)
  }
}

// 검색 입력창 키보드 이벤트 처리
const handleSearchKeydown = (event) => {
  switch (event.key) {
    case 'ArrowDown':
      event.preventDefault()
      event.stopPropagation()
      selectedIndex.value = Math.min(selectedIndex.value + 1, filteredDepartments.value.length - 1)
      hoveredIndex.value = selectedIndex.value
      scrollToSelected()
      break
    case 'ArrowUp':
      event.preventDefault()
      event.stopPropagation()
      selectedIndex.value = Math.max(selectedIndex.value - 1, 0)
      hoveredIndex.value = selectedIndex.value
      scrollToSelected()
      break
    case 'Enter':
      event.preventDefault()
      event.stopPropagation()
      console.log('MentionDropdown: Enter 키 처리됨', filteredDepartments.value[selectedIndex.value])
      if (filteredDepartments.value[selectedIndex.value]) {
        selectDepartment(filteredDepartments.value[selectedIndex.value])
      }
      return false // 이벤트 전파 완전 차단
    case 'Escape':
      event.preventDefault()
      event.stopPropagation()
      emit('close')
      return false
    case 'Tab':
      event.preventDefault()
      event.stopPropagation()
      if (filteredDepartments.value[selectedIndex.value]) {
        selectDepartment(filteredDepartments.value[selectedIndex.value])
      }
      return false
  }
}

// 부서 선택
const selectDepartment = (department) => {
  emit('select', department)
}

// 검색 입력 처리
const handleSearchInput = (event) => {
  emit('update:searchQuery', event.target.value)
}

// 검색어 변경 시 선택 인덱스 리셋
watch(() => props.searchQuery, () => {
  selectedIndex.value = 0
  hoveredIndex.value = -1
})

// 필터링된 부서 목록이 변경될 때 선택 인덱스 조정
watch(() => filteredDepartments.value.length, (newLength) => {
  if (selectedIndex.value >= newLength) {
    selectedIndex.value = Math.max(0, newLength - 1)
  }
})

// 외부 클릭 감지
const handleClickOutside = (event) => {
  // 드롭다운 내부 클릭이 아닌 경우에만 닫기
  if (!event.target.closest('.mention-dropdown')) {
    emit('close')
  }
}

// ESC 키로 닫기
const handleEscapeKey = (event) => {
  if (event.key === 'Escape' && props.show) {
    event.preventDefault()
    emit('close')
  }
}

// 드롭다운이 표시될 때 검색 입력창에 포커스
watch(() => props.show, async (newValue) => {
  if (newValue) {
    await nextTick()
    searchInput.value?.focus()
    // 약간의 지연 후 이벤트 리스너 추가 (드롭다운이 완전히 렌더링된 후)
    setTimeout(() => {
      document.addEventListener('click', handleClickOutside)
    }, 100)
  } else {
    // 드롭다운이 닫힐 때 이벤트 리스너 제거
    document.removeEventListener('click', handleClickOutside)
  }
})

onMounted(() => {
  if (props.show) {
    searchInput.value?.focus()
    document.addEventListener('click', handleClickOutside)
  }
})

// 컴포넌트 언마운트 시 이벤트 리스너 정리
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script> 
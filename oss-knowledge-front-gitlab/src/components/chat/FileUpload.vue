<template>
  <div>
    <!-- 업로드된 파일 목록 -->
    <div v-if="chatStore.uploadedFiles.length > 0" class="mb-3">
      <div class="max-w-xl lg:max-w-2xl xl:max-w-3xl mx-auto px-6">
      <div class="flex flex-wrap gap-2">
        <div
          v-for="(file, index) in chatStore.uploadedFiles"
          :key="index"
          class="inline-flex items-center gap-2 px-3 py-2 bg-white rounded-2xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
        >
          <span class="text-lg">{{ getFileIcon(getFileExtension(file.name)) }}</span>
          <div class="flex flex-col">
            <span class="text-sm font-medium text-gray-900">{{ file.name }}</span>
            <span class="text-xs text-gray-500">{{ formatFileSize(file.size) }}</span>
          </div>
          <button
            @click="chatStore.removeFile(index)"
            class="text-gray-400 hover:text-red-500 transition-colors p-1 rounded-full hover:bg-red-50"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        </div>
      </div>
    </div>

    <!-- 파일 입력 (숨김) -->
    <input
      ref="fileInput"
      type="file"
      multiple
      accept=".txt,.md,.py,.js,.ts,.json,.yaml,.yml,.sh,.bash,.java"
      @change="handleFileSelect"
      class="hidden"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useChatStore } from '@/stores/chat'
import { getFileIcon, formatFileSize } from '@/utils/fileHandler'

const chatStore = useChatStore()
const fileInput = ref(null)

// 파일 선택 트리거
const openFileDialog = () => {
  fileInput.value?.click()
}

// 파일 선택 처리
const handleFileSelect = (event) => {
  const files = Array.from(event.target.files)

  files.forEach(file => {
    chatStore.addFile(file)
  })

  // 입력 초기화
  event.target.value = ''
}

// 파일 확장자 추출
const getFileExtension = (filename) => {
  return filename.split('.').pop().toLowerCase()
}

// 외부에서 호출 가능하도록 expose
defineExpose({
  openFileDialog
})
</script>
<template>
  <MainLayout>
    <div class="h-full flex flex-col" style="background-color: var(--color-bg-primary)">
    <!-- 헤더 -->
    <div class="bg-white border-b px-6 py-4" style="border-color: var(--color-border-light)">
      <div class="max-w-6xl mx-auto">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-bold text-gray-900 mb-1">RAG 시스템 관리</h1>
            <p class="text-base text-gray-600">부서별 RAG 시스템을 생성, 수정, 삭제하고 성능을 모니터링하세요</p>
          </div>
          <button
            @click="showCreateModal = true"
            class="inline-flex items-center px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors duration-200 shadow-md hover:shadow-lg"
            style="min-width: 180px; border: 1px solid #2563eb;"
          >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
            <span class="text-sm">새 RAG 시스템 추가</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 메인 컨텐츠 -->
    <div class="flex-1 overflow-y-auto">
      <div class="max-w-6xl mx-auto p-6 space-y-6">
        <!-- 통계 카드 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="bg-white rounded-xl shadow-md border-0 p-4 hover:shadow-lg transition-shadow duration-200">
            <div class="flex items-center">
              <div class="w-10 h-10 rounded-lg flex items-center justify-center bg-blue-500">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
                </svg>
              </div>
              <div class="ml-3">
                <p class="text-xs font-medium text-gray-600">총 RAG 시스템</p>
                <p class="text-xl font-bold text-gray-900">{{ departments.length }}</p>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-xl shadow-md border-0 p-4 hover:shadow-lg transition-shadow duration-200">
            <div class="flex items-center">
              <div class="w-10 h-10 rounded-lg flex items-center justify-center bg-green-500">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
              <div class="ml-3">
                <p class="text-xs font-medium text-gray-600">활성 시스템</p>
                <p class="text-xl font-bold text-gray-900">{{ activeSystemsCount }}</p>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-xl shadow-md border-0 p-4 hover:shadow-lg transition-shadow duration-200">
            <div class="flex items-center">
              <div class="w-10 h-10 rounded-lg flex items-center justify-center bg-yellow-500">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
              </div>
              <div class="ml-3">
                <p class="text-xs font-medium text-gray-600">총 문서</p>
                <p class="text-xl font-bold text-gray-900">{{ totalDocuments }}</p>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-xl shadow-md border-0 p-4 hover:shadow-lg transition-shadow duration-200">
            <div class="flex items-center">
              <div class="w-10 h-10 rounded-lg flex items-center justify-center bg-blue-500">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                </svg>
              </div>
              <div class="ml-3">
                <p class="text-xs font-medium text-gray-600">이번 달 쿼리</p>
                <p class="text-xl font-bold text-gray-900">{{ monthlyQueries }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- RAG 시스템 목록 -->
        <div class="bg-white rounded-xl shadow-md border-0">
          <div class="p-6">
            <div class="text-center mb-6">
              <h2 class="text-2xl font-bold mb-2 text-gray-900">RAG 시스템 목록</h2>
              <p class="text-gray-600 text-sm">부서별 RAG 시스템을 관리하고 모니터링하세요</p>
            </div>
            
            <div class="flex items-center justify-between mb-6">
              <div class="flex items-center space-x-4">
                <div class="relative">
                  <input
                    v-model="searchQuery"
                    type="text"
                    placeholder="시스템 검색..."
                    class="pl-10 pr-4 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent border-gray-300"
                    style="min-width: 250px"
                  >
                  <svg class="w-4 h-4 absolute left-3 top-2.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                  </svg>
                </div>
              </div>
            </div>

            <!-- 로딩 상태 -->
            <div v-if="loading" class="flex justify-center items-center py-12">
              <div class="text-center">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p class="text-gray-600">RAG 부서 데이터를 불러오는 중...</p>
              </div>
            </div>

            <!-- 에러 상태 -->
            <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div class="flex items-center">
                <svg class="w-5 h-5 text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <p class="text-red-800 font-medium">데이터 로드 실패</p>
              </div>
              <p class="text-red-600 text-sm mt-1">{{ error }}</p>
              <button 
                @click="ragDepartmentsStore.fetchDepartments()"
                class="mt-2 text-sm text-red-600 hover:text-red-800 underline"
              >
                다시 시도
              </button>
            </div>

            <!-- 부서 목록 -->
            <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div
                v-for="dept in filteredDepartments"
                :key="dept.id"
                :class="[
                  'bg-white rounded-xl p-4 transition-all duration-200 hover:shadow-lg cursor-pointer border',
                  dept.status === 'inactive' 
                    ? 'border-red-200 bg-red-50' 
                    : 'border-gray-200'
                ]"
                @click="selectDepartment(dept)"
              >
                <div class="flex items-start justify-between mb-4">
                  <div class="flex items-center space-x-3">
                    <div 
                      :class="[
                        'text-3xl transition-colors duration-200',
                        dept.status === 'inactive' ? 'opacity-50 grayscale' : ''
                      ]"
                    >
                      {{ dept.icon }}
                    </div>
                    <div>
                      <h3 class="font-semibold mb-1 text-gray-900">{{ dept.name }}</h3>
                      <p class="text-sm text-gray-600">{{ dept.description }}</p>
                    </div>
                  </div>
                  <div class="flex items-center space-x-2">
                    <span
                      :class="[
                        'px-2 py-1 text-xs rounded-full font-medium',
                        dept.status === 'active' ? 'bg-green-100 text-green-800' :
                        dept.status === 'inactive' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      ]"
                    >
                      {{ getStatusText(dept.status) }}
                    </span>
                  </div>
                </div>

                <div class="space-y-2 mb-4">
                  <div class="flex items-center justify-between p-2 rounded-lg bg-blue-50">
                    <span class="text-xs font-medium text-gray-600">📄 문서 수</span>
                    <span class="font-bold text-sm text-blue-700">{{ getDepartmentDocumentCount(dept.id) }}개</span>
                  </div>
                  <div class="flex items-center justify-between p-2 rounded-lg bg-green-50">
                    <span class="text-xs font-medium text-gray-600">🔄 마지막 업데이트</span>
                    <span class="font-bold text-xs text-green-700">{{ formatDate(dept.lastUpdated) }}</span>
                  </div>
                  <div class="flex items-center justify-between p-2 rounded-lg bg-blue-50">
                    <span class="text-xs font-medium text-gray-600">⚡ 이번 달 쿼리</span>
                    <span class="font-bold text-sm text-blue-700">{{ dept.monthlyQueries || 0 }}회</span>
                  </div>
                </div>

                <div class="pt-3 border-t border-gray-200 flex items-center justify-between">
                  <div class="flex items-center space-x-1">
                    <button
                      @click.stop="editDepartment(dept)"
                      class="p-1.5 transition-colors duration-200 rounded hover:bg-blue-100 text-gray-400"
                      title="편집"
                    >
                      <svg class="w-4 h-4 hover:text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                      </svg>
                    </button>
                    <button
                      @click.stop="toggleDepartmentStatus(dept)"
                      :class="[
                        'p-1.5 transition-colors duration-200 rounded',
                        dept.status === 'active' 
                          ? 'hover:bg-yellow-100 text-yellow-500' 
                          : 'hover:bg-red-100 text-red-400'
                      ]"
                      :title="dept.status === 'active' ? '비활성화' : '활성화'"
                    >
                      <svg v-if="dept.status === 'active'" class="w-4 h-4 hover:text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9V6a4 4 0 118 0v3M5 9h14l1 12H4L5 9z"/>
                      </svg>
                      <svg v-else class="w-4 h-4 hover:text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z"/>
                      </svg>
                    </button>
                    <button
                      @click.stop="deleteDepartment(dept)"
                      class="p-1.5 transition-colors duration-200 rounded hover:bg-red-100 text-gray-400"
                      title="삭제"
                    >
                      <svg class="w-4 h-4 hover:text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                      </svg>
                    </button>
                  </div>
                  <div class="text-xs font-mono text-gray-400">
                    ID: {{ dept.id }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- RAG 시스템 생성/편집 모달 -->
    <RAGSystemModal
      :is-visible="showCreateModal || showEditModal"
      :department="editingDepartment"
      @close="closeModal"
      @save="saveDepartment"
    />

    <!-- RAG 시스템 상세 정보 모달 -->
    <RAGDetailModal
      :is-visible="showDetailModal"
      :department="selectedDepartment"
      @close="closeDetailModal"
    />
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRAGDepartmentsStore } from '@/stores/ragDepartments'
import { useDataUploadStore } from '@/stores/dataUpload'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { getQdrantCollectionInfoAPI, getCollectionNameForDepartment, listCollectionsAPI, getCollectionDocumentsAPI } from '@/services/embeddingApi'
import RAGSystemModal from '@/components/modals/RAGSystemModal.vue'
import RAGDetailModal from '@/components/modals/RAGDetailModal.vue'
import MainLayout from '@/components/layout/MainLayout.vue'

const ragDepartmentsStore = useRAGDepartmentsStore()
const dataUploadStore = useDataUploadStore()
const authStore = useAuthStore()
const router = useRouter()

// 반응형 상태
const searchQuery = ref('')
const showCreateModal = ref(false)
const showEditModal = ref(false)
const editingDepartment = ref(null)
const selectedDepartment = ref(null)
const showDetailModal = ref(false)
const departmentDocumentCounts = ref({}) // 부서별 문서 수 캐시

// 계산된 속성
const departments = computed(() => ragDepartmentsStore.departments)
const loading = computed(() => ragDepartmentsStore.loading)
const error = computed(() => ragDepartmentsStore.error)

const filteredDepartments = computed(() => {
  if (!searchQuery.value) return departments.value
  return departments.value.filter(dept => 
    dept.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    dept.description.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const activeSystemsCount = computed(() => 
  departments.value.filter(dept => dept.status === 'active').length
)

const totalDocuments = computed(() => {
  try {
    const deptTotal = departments.value.reduce((total, dept) => {
      const count = getDepartmentDocumentCount(dept.id)
      return total + count
    }, 0)
    const ossTotal = dataUploadStore.documents?.length || 0
    return deptTotal + ossTotal
  } catch (error) {
    console.error('문서 수 계산 중 오류:', error.message)
    return departments.value.length * 2 + 4 // 기본 더미 데이터 수
  }
})

const monthlyQueries = computed(() => {
  try {
    return departments.value.reduce((total, dept) => {
      return total + (dept.monthlyQueries || 0)
    }, 0)
  } catch (error) {
    console.error('월간 쿼리 수 계산 중 오류:', error.message)
    return 1200 // 기본 더미 데이터
  }
})

// 메서드
const loadDepartmentDocumentCounts = async () => {
  try {
    // 실제 Qdrant 컬렉션 목록을 가져옴
    const collectionsResponse = await listCollectionsAPI()
    const actualCollections = collectionsResponse.collections || []
    
    const counts = {}
    for (const dept of departments.value) {
      try {
        // 부서명을 사용해서 예상 컬렉션명 생성
        const expectedCollectionName = getCollectionNameForDepartment(dept.name)
        
        // 실제 컬렉션명과 매칭 시도
        let actualCollectionName = expectedCollectionName
        const matchingCollection = actualCollections.find(c => 
          c.name === expectedCollectionName || 
          c.name.toLowerCase().includes(dept.name.toLowerCase()) ||
          dept.name.toLowerCase().includes(c.name.toLowerCase())
        )
        
        if (matchingCollection) {
          actualCollectionName = matchingCollection.name
        }
        
        // 실제 문서 수를 가져오기 위해 documents API 사용
        const collectionDocuments = await getCollectionDocumentsAPI(actualCollectionName)
        counts[dept.id] = collectionDocuments.total_documents || 0
      } catch (error) {
        console.error(`부서 ${dept.name} 문서 수 로드 실패:`, error.message)
        counts[dept.id] = 0
      }
    }
    departmentDocumentCounts.value = counts
  } catch (error) {
    console.error('문서 수 로드 중 오류:', error.message)
  }
}

const getDepartmentDocumentCount = (departmentId) => {
  return departmentDocumentCounts.value[departmentId] || 0
}

const getStatusText = (status) => {
  const statusMap = {
    'active': '활성',
    'inactive': '비활성',
    'maintenance': '점검중'
  }
  return statusMap[status] || status
}

const formatDate = (dateStr) => {
  if (!dateStr) return '없음'
  const date = new Date(dateStr)
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const selectDepartment = (dept) => {
  selectedDepartment.value = dept
  showDetailModal.value = true
}

const editDepartment = (dept) => {
  editingDepartment.value = dept
  showEditModal.value = true
}

const deleteDepartment = async (dept) => {
  if (confirm(`"${dept.name}" RAG 시스템을 완전히 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없으며, PostgreSQL과 Qdrant에서 모두 삭제됩니다.`)) {
    try {
      await ragDepartmentsStore.deleteDepartment(dept.id)
      alert(`"${dept.name}" RAG 시스템이 삭제되었습니다.`)
      // 문서 수 다시 로드
      await loadDepartmentDocumentCounts()
    } catch (error) {
      alert(`삭제 중 오류가 발생했습니다: ` + error.message)
    }
  }
}

const toggleDepartmentStatus = async (dept) => {
  const newStatus = dept.status === 'active' ? 'inactive' : 'active'
  const action = newStatus === 'active' ? '활성화' : '비활성화'
  
  if (confirm(`"${dept.name}" RAG 시스템을 ${action}하시겠습니까?`)) {
    try {
      await ragDepartmentsStore.updateDepartmentStatus(dept.id, newStatus)
      alert(`"${dept.name}" RAG 시스템이 ${action}되었습니다.`)
    } catch (error) {
      alert(`${action} 중 오류가 발생했습니다: ` + error.message)
    }
  }
}

const saveDepartment = async (departmentData) => {
  try {
    if (showCreateModal.value) {
      await ragDepartmentsStore.createDepartment(departmentData)
      alert('새 RAG 시스템이 추가되었습니다.')
    } else {
      await ragDepartmentsStore.updateDepartment(editingDepartment.value.id, departmentData)
      alert('RAG 시스템이 수정되었습니다.')
    }
    
    closeModal()
  } catch (error) {
    alert('저장 중 오류가 발생했습니다: ' + error.message)
  }
}

const closeModal = () => {
  showCreateModal.value = false
  showEditModal.value = false
  editingDepartment.value = null
}

const closeDetailModal = () => {
  showDetailModal.value = false
  selectedDepartment.value = null
}

// 컴포넌트 마운트 시 데이터 로드
onMounted(async () => {
  // 인증 상태 확인
  if (!authStore.isLoggedIn) {
    router.push('/login')
    return
  }

  try {
    // RAG 부서 데이터 로드
    await ragDepartmentsStore.fetchDepartments()
    
    // 문서 통계를 위해 일반 문서 로드 (Qdrant 기반)
    dataUploadStore.fetchDocuments()
    
    // 부서별 문서 수 로드
    await loadDepartmentDocumentCounts()
  } catch (error) {
    // 백엔드 연결 실패 시 에러 무시하고 계속 진행
    console.log('백엔드 연결 실패, 로컬 데이터로 계속 진행:', error.message)
  }
})
</script>
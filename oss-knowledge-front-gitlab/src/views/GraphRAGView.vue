<template>
  <MainLayout>
    <div 
      class="h-full flex flex-col transition-all duration-300" 
      :class="{ 'fullscreen-mode': isFullscreen }"
      style="background-color: var(--color-bg-primary)"
    >
      <!-- 헤더 -->
    <div class="bg-white border-b px-6 py-4" style="border-color: var(--color-border-light)">
      <div class="max-w-7xl mx-auto">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-bold text-gray-900 mb-1">🧠 지식 그래프 관계 관리</h1>
            <p class="text-base text-gray-600">뇌구조처럼 연결된 지식 네트워크를 시각화하고 관리하세요</p>
          </div>
          <div class="flex items-center space-x-3">
            <button
              @click="toggleEditMode"
              :class="[
                'px-4 py-2 font-medium rounded-lg transition-colors duration-200',
                editMode 
                  ? 'bg-orange-600 text-white hover:bg-orange-700' 
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              ]"
            >
              {{ editMode ? '편집 모드 종료' : '관계 편집 모드' }}
            </button>
            <button
              @click="showAddNodeModal = true"
              class="inline-flex items-center px-4 py-2 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 transition-colors duration-200"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
              </svg>
              <span class="text-sm">새 노드 추가</span>
            </button>
            <button
              @click="toggleFullscreen"
              class="inline-flex items-center px-4 py-2 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 transition-colors duration-200"
            >
              <svg v-if="!isFullscreen" class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"/>
              </svg>
              <svg v-else class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 9V4.5M9 9H4.5M9 9L3.5 3.5M15 9v-4.5M15 9h4.5M15 9l5.5-5.5M9 15v4.5M9 15H4.5M9 15l-5.5 5.5M15 15v4.5M15 15h4.5M15 15l5.5 5.5"/>
              </svg>
              <span class="text-sm">{{ isFullscreen ? '전체화면 종료' : '전체화면' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 컨트롤 패널 -->
    <div class="bg-white border-b px-6 py-3" style="border-color: var(--color-border-light)">
      <div class="max-w-7xl mx-auto">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-4">
            <!-- 필터 옵션 -->
            <select v-model="selectedDepartment" class="px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="">전체 부서</option>
              <option v-for="dept in departments" :key="dept.id" :value="dept.id">
                {{ dept.name }}
              </option>
            </select>
            
            <!-- 관계 타입 필터 -->
            <select v-model="selectedRelationType" class="px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="">전체 관계</option>
              <option value="semantic">의미적 연관</option>
              <option value="dependency">의존성</option>
              <option value="reference">참조</option>
              <option value="hierarchical">계층적</option>
            </select>

            <!-- 검색 -->
            <div class="relative">
              <input
                v-model="searchQuery"
                type="text"
                placeholder="노드 검색..."
                class="pl-10 pr-4 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                style="min-width: 200px"
              >
              <svg class="w-4 h-4 absolute left-3 top-2.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
              </svg>
            </div>
          </div>

          <div class="flex items-center space-x-3">
            <!-- 줌 컨트롤 -->
            <div class="flex items-center space-x-2">
              <button @click="zoomOut" class="p-2 border rounded-lg hover:bg-gray-50" title="축소">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
              </button>
              <span class="text-sm text-gray-600 min-w-16 text-center">{{ Math.round(zoomLevel * 100) }}%</span>
              <button @click="zoomIn" class="p-2 border rounded-lg hover:bg-gray-50" title="확대">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
              </button>
              <button @click="resetZoom" class="p-2 border rounded-lg hover:bg-gray-50" title="리셋">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                </svg>
              </button>
              <button @click="fitToScreen" class="p-2 border rounded-lg hover:bg-gray-50" title="화면에 맞춤">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"/>
                </svg>
              </button>
            </div>

            <!-- 레이아웃 컨트롤 -->
            <GraphLayoutControls
              :nodes="filteredNodes"
              :edges="filteredEdges"
              :container-width="containerWidth"
              :container-height="containerHeight"
              @layout-change="applyLayoutChange"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 메인 그래프 영역 -->
    <div class="flex-1 relative overflow-hidden">
      <!-- 뇌구조 스타일 배경 -->
      <div class="absolute inset-0 opacity-5">
        <svg class="w-full h-full">
          <defs>
            <pattern id="brainPattern" x="0" y="0" width="100" height="100" patternUnits="userSpaceOnUse">
              <circle cx="50" cy="50" r="2" fill="#3b82f6" opacity="0.3"/>
              <circle cx="25" cy="25" r="1" fill="#8b5cf6" opacity="0.2"/>
              <circle cx="75" cy="75" r="1.5" fill="#06b6d4" opacity="0.2"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#brainPattern)"/>
        </svg>
      </div>

      <!-- 그래프 캔버스 -->
      <div 
        ref="graphContainer" 
        class="graph-container w-full h-full relative cursor-grab"
        :class="{ 'cursor-grabbing': isDragging }"
        @mousedown="startPan"
        @mousemove="pan"
        @mouseup="endPan"
        @wheel="handleWheel"
        @mouseenter="handleGraphMouseEnter"
        @mouseleave="handleGraphMouseLeave"
      >
        <!-- SVG 그래프 -->
        <svg 
          ref="graphSvg" 
          class="w-full h-full"
          :style="{ transform: `scale(${zoomLevel}) translate(${panX}px, ${panY}px)` }"
        >
          <!-- 관계선 (시냅스) -->
          <g class="edges">
            <GraphEdge
              v-for="edge in filteredEdges"
              :key="edge.id"
              :edge="edge"
              :source-node="getNodeById(edge.source)"
              :target-node="getNodeById(edge.target)"
              :is-selected="selectedEdge?.id === edge.id"
              :show-label="zoomLevel > 0.8"
              :show-strength-indicator="zoomLevel > 0.6"
              :show-type-icon="zoomLevel > 1.2"
              @click="selectEdge"
              @hover="handleEdgeHover"
            />
          </g>

          <!-- 노드 (뉴런) -->
          <g class="nodes">
            <GraphNode
              v-for="node in filteredNodes"
              :key="node.id"
              :node="node"
              :is-selected="selectedNode?.id === node.id"
              :edit-mode="editMode"
              :connection-count="getNodeConnectionCount(node.id)"
              @click="selectNode"
              @drag-start="handleNodeDragStart"
              @drag-move="handleNodeDragMove"
              @drag-end="handleNodeDragEnd"
            />
          </g>
        </svg>

        <!-- 편집 모드 오버레이 -->
        <div v-if="editMode" class="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-4 border">
          <h3 class="text-sm font-semibold mb-2">편집 모드</h3>
          <div class="text-xs text-gray-600 space-y-1">
            <p>• 노드 드래그: 위치 변경</p>
            <p>• 노드 클릭: 선택</p>
            <p>• 관계선 클릭: 관계 편집</p>
            <p>• 우클릭: 컨텍스트 메뉴</p>
          </div>
        </div>

    <!-- 오른쪽 상세 정보 패널 -->
    <GraphDetailPanel
      :is-visible="showDetailPanel"
      :node="selectedNode"
      :departments="departments"
      :related-nodes="getRelatedNodes(selectedNode?.id)"
      @close="closeDetailPanel"
      @select-node="selectNode"
      @edit-node="editNode"
      @add-connection="addConnection"
      @delete-node="deleteNode"
    />
      </div>
    </div>

    <!-- 통계 패널 -->
    <div class="bg-white border-t px-6 py-3" style="border-color: var(--color-border-light)">
      <div class="max-w-7xl mx-auto">
        <div class="flex items-center justify-between text-sm text-gray-600">
          <div class="flex items-center space-x-6">
            <span>총 노드: <strong class="text-gray-900">{{ filteredNodes.length }}</strong></span>
            <span>총 관계: <strong class="text-gray-900">{{ filteredEdges.length }}</strong></span>
            <span>활성 노드: <strong class="text-green-600">{{ activeNodesCount }}</strong></span>
          </div>
          <div class="flex items-center space-x-4">
            <span>네트워크 밀도: <strong class="text-gray-900">{{ networkDensity }}%</strong></span>
            <span>평균 연결: <strong class="text-gray-900">{{ averageConnections }}</strong></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 관계 편집 모달 -->
    <GraphRelationshipModal
      :is-visible="showRelationshipModal"
      :relationship="editingRelationship"
      :nodes="filteredNodes"
      @close="closeRelationshipModal"
      @save="saveRelationship"
    />

    <!-- 노드 추가 모달 -->
    <div v-if="showAddNodeModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-xl max-w-md w-full mx-4">
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-lg font-semibold text-gray-900">새 노드 추가</h3>
            <button @click="showAddNodeModal = false" class="text-gray-400 hover:text-gray-600">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <form @submit.prevent="addNewNode" class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-2 text-gray-700">노드 이름</label>
              <input
                v-model="newNodeData.label"
                type="text"
                required
                class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="예: WM 현장작업 매뉴얼"
              >
            </div>

            <div>
              <label class="block text-sm font-medium mb-2 text-gray-700">노드 타입</label>
              <select v-model="newNodeData.type" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="document">문서</option>
                <option value="chunk">청크</option>
                <option value="concept">개념</option>
                <option value="process">프로세스</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium mb-2 text-gray-700">부서</label>
              <select v-model="newNodeData.departmentId" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">부서 선택</option>
                <option v-for="dept in departments" :key="dept.id" :value="dept.id">
                  {{ dept.name }}
                </option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium mb-2 text-gray-700">아이콘</label>
              <div class="grid grid-cols-6 gap-2">
                <button
                  v-for="icon in nodeIcons"
                  :key="icon"
                  type="button"
                  @click="newNodeData.icon = icon"
                  :class="[
                    'p-2 text-lg border-2 rounded-lg transition-all duration-200',
                    newNodeData.icon === icon 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-200 hover:border-gray-300'
                  ]"
                >
                  {{ icon }}
                </button>
              </div>
            </div>

            <div class="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                @click="showAddNodeModal = false"
                class="px-4 py-2 text-sm font-medium border rounded-lg hover:bg-gray-50"
              >
                취소
              </button>
              <button
                type="submit"
                class="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                추가
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRAGDepartmentsStore } from '@/stores/ragDepartments'
import { useGraphRAGStore } from '@/stores/graphRAG'
import GraphRelationshipModal from '@/components/modals/GraphRelationshipModal.vue'
import GraphDetailPanel from '@/components/graph/GraphDetailPanel.vue'
import GraphNode from '@/components/graph/GraphNode.vue'
import GraphEdge from '@/components/graph/GraphEdge.vue'
import GraphLayoutControls from '@/components/graph/GraphLayoutControls.vue'
import MainLayout from '@/components/layout/MainLayout.vue'

const ragDepartmentsStore = useRAGDepartmentsStore()
const graphRAGStore = useGraphRAGStore()

// 반응형 상태
const showAddNodeModal = ref(false)
const showRelationshipModal = ref(false)
const showDetailPanel = ref(false)
const editingRelationship = ref(null)
const searchQuery = ref('')
const selectedDepartment = ref('')
const selectedRelationType = ref('')
const layoutType = ref('force')
const zoomLevel = ref(1)
const panX = ref(0)
const panY = ref(0)
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const draggedNode = ref(null)
const containerWidth = ref(800)
const containerHeight = ref(600)
const isFullscreen = ref(false)

// 새 노드 데이터
const newNodeData = ref({
  label: '',
  type: 'document',
  departmentId: '',
  icon: '📄'
})

// 사용 가능한 아이콘
const nodeIcons = ['📄', '📋', '📊', '🏭', '⚡', '🎓', '🔧', '💡', '📈', '🔍', '📞', '💬']

// 계산된 속성
const departments = computed(() => ragDepartmentsStore.departments)

const filteredNodes = computed(() => {
  return graphRAGStore.filteredNodes({
    departmentId: selectedDepartment.value,
    searchQuery: searchQuery.value
  })
})

const filteredEdges = computed(() => {
  return graphRAGStore.filteredEdges({
    relationType: selectedRelationType.value,
    nodeIds: filteredNodes.value.map(n => n.id)
  })
})

const activeNodesCount = computed(() => graphRAGStore.activeNodesCount)
const networkDensity = computed(() => graphRAGStore.networkDensity)
const averageConnections = computed(() => graphRAGStore.averageConnections)
const editMode = computed(() => graphRAGStore.editMode)
const selectedNode = computed(() => graphRAGStore.selectedNode)
const selectedEdge = computed(() => graphRAGStore.selectedEdge)

// 메서드
const getDepartmentName = (departmentId) => {
  const dept = departments.value.find(d => d.id === departmentId)
  return dept ? dept.name : '알 수 없음'
}

const getNodeConnectionCount = (nodeId) => {
  return graphRAGStore.getNodeConnectionCount(nodeId)
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

const getNodeRadius = (node) => {
  const baseRadius = 20
  const importanceMultiplier = {
    'high': 1.5,
    'medium': 1.2,
    'low': 1
  }
  return baseRadius * (importanceMultiplier[node.importance] || 1)
}

const getNodeColor = (node) => {
  const colors = {
    'document': '#3b82f6',
    'chunk': '#8b5cf6',
    'concept': '#06b6d4',
    'process': '#10b981'
  }
  return colors[node.type] || '#6b7280'
}

const getEdgeColor = (type) => {
  const colors = {
    'semantic': '#3b82f6',
    'dependency': '#f59e0b',
    'reference': '#8b5cf6',
    'hierarchical': '#10b981'
  }
  return colors[type] || '#6b7280'
}

const getEdgeWidth = (strength) => {
  return Math.max(1, strength * 3)
}

const getEdgePath = (edge) => {
  const sourceNode = filteredNodes.value.find(n => n.id === edge.source)
  const targetNode = filteredNodes.value.find(n => n.id === edge.target)
  
  if (!sourceNode || !targetNode) return ''

  const dx = targetNode.x - sourceNode.x
  const dy = targetNode.y - sourceNode.y
  const distance = Math.sqrt(dx * dx + dy * dy)
  
  // 곡선 경로 생성 (뇌의 시냅스처럼)
  const controlPointOffset = distance * 0.3
  const controlX = (sourceNode.x + targetNode.x) / 2 + (dy / distance) * controlPointOffset
  const controlY = (sourceNode.y + targetNode.y) / 2 - (dx / distance) * controlPointOffset
  
  return `M ${sourceNode.x} ${sourceNode.y} Q ${controlX} ${controlY} ${targetNode.x} ${targetNode.y}`
}

const selectNode = (node) => {
  graphRAGStore.selectNode(node)
  showDetailPanel.value = true
  // 연결된 관계선들 하이라이트
  highlightConnectedEdges(node.id)
}

const selectEdge = (edge) => {
  graphRAGStore.selectEdge(edge)
  showDetailPanel.value = false
}

const closeDetailPanel = () => {
  showDetailPanel.value = false
  graphRAGStore.clearSelection()
  // 연결선과 노드 하이라이트 해제
  clearEdgeHighlights()
  clearNodeHighlights()
  
  // 사이드바가 닫힐 때 그래프 컨테이너의 스크롤을 다시 활성화
  nextTick(() => {
    const graphContainer = document.querySelector('.graph-container')
    if (graphContainer) {
      graphContainer.style.overflow = ''
    }
    // 커서도 원래대로 복원
    document.body.style.cursor = ''
  })
}

// 연결된 관계선들 하이라이트
const highlightConnectedEdges = (nodeId) => {
  // 모든 관계선과 노드의 하이라이트 상태 초기화
  clearEdgeHighlights()
  clearNodeHighlights()
  
  // 선택된 노드와 연결된 관계선들 찾기
  const connectedEdges = filteredEdges.value.filter(edge => 
    edge.source === nodeId || edge.target === nodeId
  )
  
  // 연결된 관계선들에 하이라이트 클래스 추가
  connectedEdges.forEach(edge => {
    const edgeElement = document.querySelector(`[data-edge-id="${edge.id}"]`)
    if (edgeElement) {
      edgeElement.classList.add('edge-connected-highlight')
    }
    
    // 연결된 다른 노드들도 하이라이트
    const connectedNodeId = edge.source === nodeId ? edge.target : edge.source
    const connectedNodeElement = document.querySelector(`[data-node-id="${connectedNodeId}"]`)
    if (connectedNodeElement) {
      connectedNodeElement.classList.add('node-connected-highlight')
    }
  })
}

// 관계선 하이라이트 해제
const clearEdgeHighlights = () => {
  const highlightedEdges = document.querySelectorAll('.edge-connected-highlight')
  highlightedEdges.forEach(edge => {
    edge.classList.remove('edge-connected-highlight')
  })
}

// 연결된 노드 하이라이트 해제
const clearNodeHighlights = () => {
  const highlightedNodes = document.querySelectorAll('.node-connected-highlight')
  highlightedNodes.forEach(node => {
    node.classList.remove('node-connected-highlight')
  })
}

const getNodeById = (nodeId) => {
  return filteredNodes.value.find(n => n.id === nodeId)
}

const getRelatedNodes = (nodeId) => {
  if (!nodeId) return []
  
  const relatedEdges = filteredEdges.value.filter(edge => 
    edge.source === nodeId || edge.target === nodeId
  )
  
  return relatedEdges.map(edge => {
    const relatedNodeId = edge.source === nodeId ? edge.target : edge.source
    const relatedNode = getNodeById(relatedNodeId)
    return {
      ...relatedNode,
      relationType: edge.type,
      relationStrength: edge.strength
    }
  }).filter(Boolean)
}

const handleEdgeHover = (edge) => {
  // 엣지 호버 효과 처리
  console.log('Edge hovered:', edge)
}

const handleNodeDragStart = (data) => {
  draggedNode.value = data.node
  console.log('Node drag start:', data)
}

const handleNodeDragMove = (data) => {
  if (draggedNode.value) {
    // 노드 위치 업데이트
    graphRAGStore.updateNodePosition(data.node.id, data.newPos)
  }
}

const handleNodeDragEnd = (node) => {
  draggedNode.value = null
  console.log('Node drag end:', node)
}

const startNodeDrag = (node, event) => {
  if (!editMode.value) return
  
  event.preventDefault()
  // 드래그 로직 구현
}

const startPan = (event) => {
  if (event.target.tagName === 'svg' || event.target.tagName === 'rect') {
    isDragging.value = true
    dragStart.value = { x: event.clientX - panX.value, y: event.clientY - panY.value }
  }
}

const pan = (event) => {
  if (!isDragging.value) return
  
  panX.value = event.clientX - dragStart.value.x
  panY.value = event.clientY - dragStart.value.y
}

const endPan = () => {
  isDragging.value = false
}

const handleWheel = (event) => {
  // 사이드바가 열려있으면 휠 이벤트를 무시
  if (showDetailPanel.value) {
    return
  }
  
  event.preventDefault()
  const delta = event.deltaY > 0 ? 0.9 : 1.1
  const newZoom = Math.max(0.1, Math.min(3, zoomLevel.value * delta))
  
  // 마우스 위치를 기준으로 줌
  const rect = event.currentTarget.getBoundingClientRect()
  const mouseX = event.clientX - rect.left
  const mouseY = event.clientY - rect.top
  
  // 줌 중심점 계산
  const zoomCenterX = (mouseX - panX.value) / zoomLevel.value
  const zoomCenterY = (mouseY - panY.value) / zoomLevel.value
  
  // 새로운 팬 위치 계산
  panX.value = mouseX - zoomCenterX * newZoom
  panY.value = mouseY - zoomCenterY * newZoom
  
  zoomLevel.value = newZoom
}

const handleGraphMouseEnter = () => {
  // 그래프 영역에 마우스가 들어오면 커서를 그래프용으로 설정
  if (!showDetailPanel.value) {
    document.body.style.cursor = ''
  }
}

const handleGraphMouseLeave = () => {
  // 그래프 영역에서 마우스가 나가면 커서를 기본으로 설정
  document.body.style.cursor = 'default'
}

const zoomIn = () => {
  zoomLevel.value = Math.min(3, zoomLevel.value * 1.2)
}

const zoomOut = () => {
  zoomLevel.value = Math.max(0.1, zoomLevel.value * 0.8)
}

const resetZoom = () => {
  zoomLevel.value = 1
  panX.value = 0
  panY.value = 0
}

const fitToScreen = () => {
  if (filteredNodes.value.length === 0) return
  
  // 노드들의 경계 계산
  const minX = Math.min(...filteredNodes.value.map(n => n.x))
  const maxX = Math.max(...filteredNodes.value.map(n => n.x))
  const minY = Math.min(...filteredNodes.value.map(n => n.y))
  const maxY = Math.max(...filteredNodes.value.map(n => n.y))
  
  const width = maxX - minX
  const height = maxY - minY
  
  // 캔버스 크기 가져오기
  const container = document.querySelector('.graph-container')
  if (!container) return
  
  const containerWidth = container.clientWidth
  const containerHeight = container.clientHeight
  
  // 여백을 더 크게 설정하여 잘림 방지
  const padding = 150
  
  // 적절한 줌 레벨 계산 (여백 고려)
  const scaleX = (containerWidth - padding) / (width + padding)
  const scaleY = (containerHeight - padding) / (height + padding)
  const scale = Math.min(scaleX, scaleY, 1)
  
  zoomLevel.value = scale
  
  // 중앙 정렬을 위한 팬 계산
  const centerX = (minX + maxX) / 2
  const centerY = (minY + maxY) / 2
  
  panX.value = containerWidth / 2 - centerX * scale
  panY.value = containerHeight / 2 - centerY * scale
}

const applyLayoutChange = (newPositions) => {
  // 노드 위치 업데이트
  newPositions.forEach(pos => {
    graphRAGStore.updateNodePosition(pos.id, { x: pos.x, y: pos.y })
  })
  
  // 화면에 맞춤
  setTimeout(() => {
    fitToScreen()
  }, 100)
}

const updateContainerSize = () => {
  const container = document.querySelector('.graph-container')
  if (container) {
    containerWidth.value = container.clientWidth
    containerHeight.value = container.clientHeight
  }
}

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    // 전체화면 진입
    const element = document.documentElement
    if (element.requestFullscreen) {
      element.requestFullscreen()
    } else if (element.webkitRequestFullscreen) {
      element.webkitRequestFullscreen()
    } else if (element.msRequestFullscreen) {
      element.msRequestFullscreen()
    }
    isFullscreen.value = true
  } else {
    // 전체화면 종료
    if (document.exitFullscreen) {
      document.exitFullscreen()
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen()
    } else if (document.msExitFullscreen) {
      document.msExitFullscreen()
    }
    isFullscreen.value = false
  }
}

const toggleEditMode = () => {
  graphRAGStore.toggleEditMode()
}

const editNode = (node) => {
  // 노드 편집 로직
  console.log('편집할 노드:', node)
}

const addConnection = (node) => {
  editingRelationship.value = {
    source: node.id,
    target: '',
    type: '',
    label: '',
    strength: 0.5,
    description: '',
    directional: false,
    weight: 1,
    metadata: {
      source: '수동 입력',
      confidence: 0.8
    }
  }
  showRelationshipModal.value = true
}

const closeRelationshipModal = () => {
  showRelationshipModal.value = false
  editingRelationship.value = null
}

const editRelationship = (edge) => {
  editingRelationship.value = edge
  showRelationshipModal.value = true
}

const saveRelationship = async (relationshipData) => {
  try {
    if (editingRelationship.value?.id) {
      // 기존 관계 수정
      await graphRAGStore.updateEdge(editingRelationship.value.id, relationshipData)
    } else {
      // 새 관계 생성
      await graphRAGStore.createEdge(relationshipData)
    }
    closeRelationshipModal()
  } catch (error) {
    console.error('Failed to save relationship:', error)
    alert('관계 저장 중 오류가 발생했습니다: ' + error.message)
  }
}

const deleteRelationship = async (edge) => {
  if (confirm(`"${edge.label}" 관계를 삭제하시겠습니까?`)) {
    try {
      await graphRAGStore.deleteEdge(edge.id)
      graphRAGStore.clearSelection()
    } catch (error) {
      console.error('Failed to delete relationship:', error)
      alert('관계 삭제 중 오류가 발생했습니다: ' + error.message)
    }
  }
}

const deleteNode = async (node) => {
  if (confirm(`"${node.label}" 노드를 삭제하시겠습니까? 관련된 모든 연결도 함께 삭제됩니다.`)) {
    try {
      await graphRAGStore.deleteNode(node.id)
      closeDetailPanel()
    } catch (error) {
      console.error('Failed to delete node:', error)
      alert('노드 삭제 중 오류가 발생했습니다: ' + error.message)
    }
  }
}

const addNewNode = async () => {
  try {
    const newNode = {
      label: newNodeData.value.label,
      type: newNodeData.value.type,
      departmentId: newNodeData.value.departmentId,
      x: Math.random() * 400 + 100,
      y: Math.random() * 300 + 100,
      icon: newNodeData.value.icon,
      importance: 'medium',
      isActive: false,
      description: `${newNodeData.value.label} 관련 정보`
    }
    
    await graphRAGStore.createNode(newNode)
    showAddNodeModal.value = false
    
    // 폼 초기화
    newNodeData.value = {
      label: '',
      type: 'document',
      departmentId: '',
      icon: '📄'
    }
  } catch (error) {
    console.error('Failed to create node:', error)
    alert('노드 생성 중 오류가 발생했습니다: ' + error.message)
  }
}

// 컴포넌트 마운트
onMounted(async () => {
  // 초기 데이터 로드
  try {
    console.log('🧠 Graph RAG 데이터 로드 시작...')
    
    // 부서 데이터 로드
    try {
      await ragDepartmentsStore.fetchDepartments()
      console.log('✅ 부서 데이터 로드 완료')
    } catch (error) {
      console.warn('⚠️ 부서 데이터 로드 실패, 기본 데이터 사용:', error.message)
    }
    
    // Graph RAG 데이터 로드
    try {
      await graphRAGStore.initialize()
      console.log('✅ Graph RAG 데이터 로드 완료')
    } catch (error) {
      console.warn('⚠️ Graph RAG 데이터 로드 실패, 기본 데이터 사용:', error.message)
    }
    
    // 컨테이너 크기 업데이트
    updateContainerSize()
    
    // 윈도우 리사이즈 이벤트 리스너
    window.addEventListener('resize', updateContainerSize)
    
    // 전체화면 변경 이벤트 리스너
    document.addEventListener('fullscreenchange', () => {
      isFullscreen.value = !!document.fullscreenElement
      updateContainerSize()
    })
    
    console.log('🎉 Graph RAG 초기화 완료!')
  } catch (error) {
    console.error('❌ 데이터 로드 실패:', error.message)
  }
})
</script>

<style scoped>
/* 뇌구조 스타일 애니메이션 */
@keyframes neuron-pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

.animate-pulse {
  animation: neuron-pulse 2s ease-in-out infinite;
}

/* 드래그 앤 드롭 스타일 */
.cursor-grab {
  cursor: grab;
}

.cursor-grabbing {
  cursor: grabbing;
}

/* 관계선 호버 효과 - 더 부드럽게 */
.edges path {
  transition: stroke-width 0.2s ease, stroke-opacity 0.2s ease;
}

.edges path:hover {
  stroke-width: 3 !important;
  stroke-opacity: 0.9 !important;
}

/* 연결된 관계선 하이라이트 효과 */
.edge-connected-highlight path {
  stroke: #ef4444 !important;
  stroke-width: 4 !important;
  stroke-opacity: 1 !important;
  filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.6));
  animation: connected-edge-pulse 2s ease-in-out infinite;
}

/* 연결된 관계선 펄스 애니메이션 */
@keyframes connected-edge-pulse {
  0%, 100% {
    stroke-opacity: 1;
    filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.6));
  }
  50% {
    stroke-opacity: 0.8;
    filter: drop-shadow(0 0 12px rgba(239, 68, 68, 0.8));
  }
}

/* 노드 호버 효과 - 더 부드럽게 */
.nodes g:hover circle {
  stroke-width: 3;
  stroke: #f59e0b;
  transition: stroke-width 0.2s ease, stroke 0.2s ease;
}

/* 연결된 노드 하이라이트 효과 */
.node-connected-highlight circle {
  stroke: #f59e0b !important;
  stroke-width: 3 !important;
  filter: drop-shadow(0 0 6px rgba(245, 158, 11, 0.5));
}

/* 전체화면 모드 스타일 */
.fullscreen-mode {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  background: white;
}

.fullscreen-mode .bg-white {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
}

.fullscreen-mode .border-b {
  border-bottom: 1px solid rgba(229, 231, 235, 0.5);
}

/* 전체화면 모드에서 헤더 최소화 */
.fullscreen-mode .px-6 {
  padding-left: 1rem;
  padding-right: 1rem;
}

.fullscreen-mode .py-4 {
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
}

/* 전체화면 모드에서 컨트롤 패널 최소화 */
.fullscreen-mode .py-3 {
  padding-top: 0.25rem;
  padding-bottom: 0.25rem;
}

/* 전체화면 모드에서 통계 패널 숨김 */
.fullscreen-mode .border-t {
  display: none;
}
</style>

import { defineStore } from 'pinia'
import { 
  getGraphNodesAPI, 
  getGraphEdgesAPI, 
  createGraphNodeAPI, 
  updateGraphNodeAPI, 
  deleteGraphNodeAPI,
  createGraphEdgeAPI,
  updateGraphEdgeAPI,
  deleteGraphEdgeAPI,
  inferGraphRelationsAPI,
  analyzeGraphNetworkAPI,
  updateEdgeStrengthAPI,
  updateNodePositionAPI
} from '@/services/searchApi'

export const useGraphRAGStore = defineStore('graphRAG', {
  state: () => ({
    // 노드 데이터
    nodes: [],
    // 관계 데이터
    edges: [],
    // 선택된 노드/관계
    selectedNode: null,
    selectedEdge: null,
    // 편집 모드
    editMode: false,
    // 네트워크 분석 결과
    networkAnalysis: null,
    // 로딩 상태
    loading: {
      nodes: false,
      edges: false,
      analysis: false
    },
    // 에러 상태
    error: null
  }),

  getters: {
    // 필터링된 노드들
    filteredNodes: (state) => (filters = {}) => {
      let filtered = state.nodes

      if (filters.departmentId) {
        filtered = filtered.filter(node => node.departmentId === filters.departmentId)
      }

      if (filters.type) {
        filtered = filtered.filter(node => node.type === filters.type)
      }

      if (filters.searchQuery) {
        const query = filters.searchQuery.toLowerCase()
        filtered = filtered.filter(node => 
          node.label.toLowerCase().includes(query) ||
          node.description?.toLowerCase().includes(query)
        )
      }

      return filtered
    },

    // 필터링된 관계들
    filteredEdges: (state) => (filters = {}) => {
      let filtered = state.edges

      if (filters.relationType) {
        filtered = filtered.filter(edge => edge.type === filters.relationType)
      }

      if (filters.nodeIds) {
        const nodeIdSet = new Set(filters.nodeIds)
        filtered = filtered.filter(edge => 
          nodeIdSet.has(edge.source) && nodeIdSet.has(edge.target)
        )
      }

      return filtered
    },

    // 활성 노드 수
    activeNodesCount: (state) => {
      return state.nodes.filter(node => node.isActive).length
    },

    // 네트워크 밀도 계산
    networkDensity: (state) => {
      const n = state.nodes.length
      if (n < 2) return 0
      const maxEdges = n * (n - 1) / 2
      return Math.round((state.edges.length / maxEdges) * 100)
    },

    // 평균 연결 수
    averageConnections: (state) => {
      if (state.nodes.length === 0) return 0
      const totalConnections = state.nodes.reduce((sum, node) => {
        return sum + getNodeConnectionCount(state.edges, node.id)
      }, 0)
      return Math.round(totalConnections / state.nodes.length * 10) / 10
    },

    // 특정 노드의 연결 수
    getNodeConnectionCount: (state) => (nodeId) => {
      return state.edges.filter(edge => 
        edge.source === nodeId || edge.target === nodeId
      ).length
    },

    // 특정 노드의 연결된 노드들
    getConnectedNodes: (state) => (nodeId) => {
      const connectedNodeIds = new Set()
      state.edges.forEach(edge => {
        if (edge.source === nodeId) connectedNodeIds.add(edge.target)
        if (edge.target === nodeId) connectedNodeIds.add(edge.source)
      })
      return state.nodes.filter(node => connectedNodeIds.has(node.id))
    }
  },

  actions: {
    // 노드 관련 액션들
    async fetchNodes() {
      this.loading.nodes = true
      this.error = null
      
      // 개발 환경에서는 바로 더미 데이터 사용
      if (import.meta.env.DEV) {
        console.log('🔄 개발 환경에서 더미 노드 데이터 로드...')
        this.nodes = [
            // 중앙 허브 노드들 (뇌의 주요 영역)
            {
              id: 'node_wm',
              label: 'WM 현장작업',
              type: 'process',
              departmentId: 'dept1',
              x: 250,
              y: 200,
              icon: '🏭',
              importance: 'high',
              isActive: true,
              description: 'WM 현장 작업 프로세스'
            },
            {
              id: 'node_lean',
              label: 'LEAN 현장작업',
              type: 'process',
              departmentId: 'dept2',
              x: 450,
              y: 200,
              icon: '⚡',
              importance: 'high',
              isActive: true,
              description: 'LEAN 현장 작업 프로세스'
            },
            {
              id: 'node_quality',
              label: '품질관리',
              type: 'concept',
              departmentId: 'quality-dept',
              x: 350,
              y: 100,
              icon: '🎯',
              importance: 'high',
              isActive: true,
              description: '품질 관리 시스템'
            },
            
            // 문서 노드들 (뇌의 기억 저장소)
            {
              id: 'node_safety',
              label: '안전수칙',
              type: 'document',
              departmentId: 'safety-dept',
              x: 150,
              y: 300,
              icon: '🛡️',
              importance: 'medium',
              isActive: false,
              description: '현장 안전 수칙 매뉴얼'
            },
            {
              id: 'node_standards',
              label: '작업기준',
              type: 'document',
              departmentId: 'quality-dept',
              x: 550,
              y: 300,
              icon: '📋',
              importance: 'medium',
              isActive: false,
              description: '작업 표준 매뉴얼'
            },
            {
              id: 'node_training',
              label: '교육자료',
              type: 'document',
              departmentId: 'safety-dept',
              x: 200,
              y: 450,
              icon: '📚',
              importance: 'medium',
              isActive: false,
              description: '작업자 교육 자료'
            },
            
            // 세부 프로세스 노드들 (뇌의 세부 기능)
            {
              id: 'node_inspection',
              label: '검사절차',
              type: 'process',
              departmentId: 'quality-dept',
              x: 100,
              y: 150,
              icon: '🔍',
              importance: 'medium',
              isActive: true,
              description: '품질 검사 절차'
            },
            {
              id: 'node_maintenance',
              label: '정비관리',
              type: 'process',
              departmentId: 'maintenance-dept',
              x: 500,
              y: 150,
              icon: '🔧',
              importance: 'medium',
              isActive: true,
              description: '장비 정비 관리'
            },
            {
              id: 'node_reporting',
              label: '보고체계',
              type: 'concept',
              departmentId: 'reporting-dept',
              x: 350,
              y: 350,
              icon: '📊',
              importance: 'medium',
              isActive: true,
              description: '작업 보고 체계'
            },
            
            // 외부 연계 노드들 (뇌의 외부 연결)
            {
              id: 'node_supplier',
              label: '협력업체',
              type: 'concept',
              departmentId: 'external',
              x: 50,
              y: 400,
              icon: '🤝',
              importance: 'low',
              isActive: false,
              description: '협력업체 관리'
            },
            {
              id: 'node_customer',
              label: '고객요구',
              type: 'concept',
              departmentId: 'external',
              x: 650,
              y: 400,
              icon: '👥',
              importance: 'medium',
              isActive: true,
              description: '고객 요구사항'
            }
          ]
        console.log('✅ 더미 노드 데이터 로드 완료:', this.nodes.length, '개')
        this.loading.nodes = false
        return
      }
      
      // 프로덕션 환경에서만 API 호출
      try {
        const response = await getGraphNodesAPI()
        this.nodes = response.data || response
      } catch (error) {
        this.error = error.message
        console.error('Failed to fetch nodes:', error)
        throw error
      } finally {
        this.loading.nodes = false
      }
    },

    async createNode(nodeData) {
      try {
        const response = await createGraphNodeAPI(nodeData)
        this.nodes.push(response.data || response)
        return response
      } catch (error) {
        this.error = error.message
        throw error
      }
    },

    async updateNode(nodeId, nodeData) {
      try {
        const response = await updateGraphNodeAPI(nodeId, nodeData)
        const index = this.nodes.findIndex(node => node.id === nodeId)
        if (index !== -1) {
          this.nodes[index] = { ...this.nodes[index], ...response.data || response }
        }
        return response
      } catch (error) {
        this.error = error.message
        throw error
      }
    },

    async deleteNode(nodeId) {
      try {
        await deleteGraphNodeAPI(nodeId)
        this.nodes = this.nodes.filter(node => node.id !== nodeId)
        // 관련된 관계들도 삭제
        this.edges = this.edges.filter(edge => 
          edge.source !== nodeId && edge.target !== nodeId
        )
        // 선택된 노드가 삭제된 경우 선택 해제
        if (this.selectedNode?.id === nodeId) {
          this.selectedNode = null
        }
      } catch (error) {
        this.error = error.message
        throw error
      }
    },

    // 관계 관련 액션들
    async fetchEdges() {
      this.loading.edges = true
      this.error = null
      
      // 개발 환경에서는 바로 더미 데이터 사용
      if (import.meta.env.DEV) {
        console.log('🔄 개발 환경에서 더미 관계 데이터 로드...')
        this.edges = [
            // 핵심 연결 (뇌의 주요 신경망)
            {
              id: 'edge_wm_lean',
              source: 'node_wm',
              target: 'node_lean',
              type: 'semantic',
              strength: 0.9,
              label: '상호 연관',
              description: 'WM과 LEAN 작업 간의 강한 연관성',
              directional: false,
              weight: 5
            },
            {
              id: 'edge_wm_quality',
              source: 'node_wm',
              target: 'node_quality',
              type: 'dependency',
              strength: 0.8,
              label: '품질 의존',
              description: 'WM 작업이 품질관리에 의존',
              directional: true,
              weight: 4
            },
            {
              id: 'edge_lean_quality',
              source: 'node_lean',
              target: 'node_quality',
              type: 'dependency',
              strength: 0.8,
              label: '품질 의존',
              description: 'LEAN 작업이 품질관리에 의존',
              directional: true,
              weight: 4
            },
            
            // 문서 연결 (뇌의 기억 연결)
            {
              id: 'edge_wm_safety',
              source: 'node_wm',
              target: 'node_safety',
              type: 'reference',
              strength: 0.7,
              label: '안전 참조',
              description: 'WM 작업이 안전수칙을 참조',
              directional: true,
              weight: 3
            },
            {
              id: 'edge_lean_standards',
              source: 'node_lean',
              target: 'node_standards',
              type: 'reference',
              strength: 0.7,
              label: '기준 참조',
              description: 'LEAN 작업이 작업기준을 참조',
              directional: true,
              weight: 3
            },
            {
              id: 'edge_quality_training',
              source: 'node_quality',
              target: 'node_training',
              type: 'hierarchical',
              strength: 0.6,
              label: '교육 포함',
              description: '품질관리가 교육자료에 포함',
              directional: true,
              weight: 2
            },
            
            // 세부 프로세스 연결 (뇌의 세부 신경망)
            {
              id: 'edge_wm_inspection',
              source: 'node_wm',
              target: 'node_inspection',
              type: 'dependency',
              strength: 0.8,
              label: '검사 의존',
              description: 'WM 작업이 검사절차에 의존',
              directional: true,
              weight: 4
            },
            {
              id: 'edge_lean_maintenance',
              source: 'node_lean',
              target: 'node_maintenance',
              type: 'dependency',
              strength: 0.8,
              label: '정비 의존',
              description: 'LEAN 작업이 정비관리에 의존',
              directional: true,
              weight: 4
            },
            {
              id: 'edge_quality_reporting',
              source: 'node_quality',
              target: 'node_reporting',
              type: 'hierarchical',
              strength: 0.7,
              label: '보고 포함',
              description: '품질관리가 보고체계에 포함',
              directional: true,
              weight: 3
            },
            
            // 외부 연계 (뇌의 외부 연결)
            {
              id: 'edge_supplier_wm',
              source: 'node_supplier',
              target: 'node_wm',
              type: 'temporal',
              strength: 0.5,
              label: '협력 순서',
              description: '협력업체와 WM 작업의 시간적 순서',
              directional: true,
              weight: 2
            },
            {
              id: 'edge_customer_quality',
              source: 'node_customer',
              target: 'node_quality',
              type: 'causal',
              strength: 0.6,
              label: '요구 반영',
              description: '고객요구가 품질관리에 영향',
              directional: true,
              weight: 3
            },
            
            // 간접 연결 (뇌의 복잡한 신경망)
            {
              id: 'edge_safety_training',
              source: 'node_safety',
              target: 'node_training',
              type: 'hierarchical',
              strength: 0.5,
              label: '교육 포함',
              description: '안전수칙이 교육자료에 포함',
              directional: true,
              weight: 2
            },
            {
              id: 'edge_standards_training',
              source: 'node_standards',
              target: 'node_training',
              type: 'hierarchical',
              strength: 0.5,
              label: '교육 포함',
              description: '작업기준이 교육자료에 포함',
              directional: true,
              weight: 2
            },
            {
              id: 'edge_inspection_reporting',
              source: 'node_inspection',
              target: 'node_reporting',
              type: 'temporal',
              strength: 0.6,
              label: '보고 순서',
              description: '검사 후 보고하는 시간적 순서',
              directional: true,
              weight: 3
            },
            {
              id: 'edge_maintenance_reporting',
              source: 'node_maintenance',
              target: 'node_reporting',
              type: 'temporal',
              strength: 0.6,
              label: '보고 순서',
              description: '정비 후 보고하는 시간적 순서',
              directional: true,
              weight: 3
            }
          ]
        console.log('✅ 더미 관계 데이터 로드 완료:', this.edges.length, '개')
        this.loading.edges = false
        return
      }
      
      // 프로덕션 환경에서만 API 호출
      try {
        const response = await getGraphEdgesAPI()
        this.edges = response.data || response
      } catch (error) {
        this.error = error.message
        console.error('Failed to fetch edges:', error)
        throw error
      } finally {
        this.loading.edges = false
      }
    },

    async createEdge(edgeData) {
      try {
        const response = await createGraphEdgeAPI(edgeData)
        this.edges.push(response.data || response)
        return response
      } catch (error) {
        this.error = error.message
        throw error
      }
    },

    async updateEdge(edgeId, edgeData) {
      try {
        const response = await updateGraphEdgeAPI(edgeId, edgeData)
        const index = this.edges.findIndex(edge => edge.id === edgeId)
        if (index !== -1) {
          this.edges[index] = { ...this.edges[index], ...response.data || response }
        }
        return response
      } catch (error) {
        this.error = error.message
        throw error
      }
    },

    async deleteEdge(edgeId) {
      try {
        await deleteGraphEdgeAPI(edgeId)
        this.edges = this.edges.filter(edge => edge.id !== edgeId)
        // 선택된 관계가 삭제된 경우 선택 해제
        if (this.selectedEdge?.id === edgeId) {
          this.selectedEdge = null
        }
      } catch (error) {
        this.error = error.message
        throw error
      }
    },

    // 관계 강도 업데이트
    async updateEdgeStrength(edgeId, strength) {
      try {
        const response = await updateEdgeStrengthAPI(edgeId, strength)
        const index = this.edges.findIndex(edge => edge.id === edgeId)
        if (index !== -1) {
          this.edges[index].strength = strength
        }
        return response
      } catch (error) {
        this.error = error.message
        throw error
      }
    },

    // 노드 위치 업데이트 (드래그앤드롭)
    async updateNodePosition(nodeId, position) {
      try {
        // 개발 환경에서는 로컬 업데이트만
        if (import.meta.env.DEV) {
          const index = this.nodes.findIndex(node => node.id === nodeId)
          if (index !== -1) {
            this.nodes[index].x = position.x
            this.nodes[index].y = position.y
          }
          return { success: true }
        }
        
        // 프로덕션 환경에서만 API 호출
        const response = await updateNodePositionAPI(nodeId, position.x, position.y)
        const index = this.nodes.findIndex(node => node.id === nodeId)
        if (index !== -1) {
          this.nodes[index].x = position.x
          this.nodes[index].y = position.y
        }
        return response
      } catch (error) {
        this.error = error.message
        throw error
      }
    },

    // 자동 관계 추론
    async inferRelations(nodeId) {
      try {
        const response = await inferGraphRelationsAPI(nodeId)
        // 추론된 관계들을 기존 관계에 추가
        const newEdges = response.data || response
        newEdges.forEach(edge => {
          if (!this.edges.find(existingEdge => 
            existingEdge.source === edge.source && existingEdge.target === edge.target
          )) {
            this.edges.push(edge)
          }
        })
        return response
      } catch (error) {
        this.error = error.message
        throw error
      }
    },

    // 네트워크 분석
    async analyzeNetwork() {
      this.loading.analysis = true
      this.error = null
      
      // 개발 환경에서는 바로 더미 데이터 사용
      if (import.meta.env.DEV) {
        console.log('🔄 개발 환경에서 더미 네트워크 분석 데이터 생성...')
        this.networkAnalysis = {
            density: this.networkDensity,
            averageConnections: this.averageConnections,
            centralNodes: this.nodes.filter(node => 
              this.getNodeConnectionCount(node.id) > 2
            ).map(node => ({
              id: node.id,
              label: node.label,
              connections: this.getNodeConnectionCount(node.id)
            })),
            isolatedNodes: this.nodes.filter(node => 
              this.getNodeConnectionCount(node.id) === 0
            ).map(node => ({
              id: node.id,
              label: node.label
            })),
            clusters: [
              {
                id: 'cluster1',
                name: '현장작업 클러스터',
                nodes: ['node1', 'node2'],
                strength: 0.8
              },
              {
                id: 'cluster2',
                name: '문서 클러스터',
                nodes: ['node3', 'node4'],
                strength: 0.6
              }
            ]
          }
        console.log('✅ 더미 네트워크 분석 데이터 생성 완료')
        this.loading.analysis = false
        return
      }
      
      // 프로덕션 환경에서만 API 호출
      try {
        const response = await analyzeGraphNetworkAPI()
        this.networkAnalysis = response.data || response
        return response
      } catch (error) {
        this.error = error.message
        console.error('Failed to analyze network:', error)
        throw error
      } finally {
        this.loading.analysis = false
      }
    },

    // 선택 관리
    selectNode(node) {
      this.selectedNode = node
      this.selectedEdge = null
    },

    selectEdge(edge) {
      this.selectedEdge = edge
      this.selectedNode = null
    },

    clearSelection() {
      this.selectedNode = null
      this.selectedEdge = null
    },

    // 편집 모드 토글
    toggleEditMode() {
      this.editMode = !this.editMode
      if (!this.editMode) {
        this.clearSelection()
      }
    },

    // 초기 데이터 로드
    async initialize() {
      console.log('🔄 Graph RAG 초기화 시작...')
      try {
        await Promise.all([
          this.fetchNodes(),
          this.fetchEdges(),
          this.analyzeNetwork()
        ])
        console.log('✅ Graph RAG 초기화 완료')
      } catch (error) {
        console.error('❌ Graph RAG 초기화 실패:', error.message)
        throw error
      }
    },

    // 에러 클리어
    clearError() {
      this.error = null
    }
  }
})

// 헬퍼 함수들
function getNodeConnectionCount(edges, nodeId) {
  return edges.filter(edge => 
    edge.source === nodeId || edge.target === nodeId
  ).length
}

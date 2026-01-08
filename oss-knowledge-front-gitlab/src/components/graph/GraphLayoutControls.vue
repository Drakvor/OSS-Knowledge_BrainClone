<template>
  <div class="layout-controls">
    <div class="flex items-center gap-2">
      <label class="text-sm font-medium text-gray-700">레이아웃:</label>
      <select 
        v-model="selectedLayout" 
        @change="applyLayout"
        class="px-3 py-1 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="force">자유 배치</option>
        <option value="circular">원형 배치</option>
        <option value="hierarchical">계층 배치</option>
        <option value="grid">격자 배치</option>
        <option value="tree">트리 배치</option>
      </select>
      
      <button 
        @click="applyLayout"
        class="px-3 py-1 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
        :disabled="isAnimating"
      >
        {{ isAnimating ? '적용 중...' : '적용' }}
      </button>
      
      <button 
        @click="resetLayout"
        class="px-3 py-1 bg-gray-600 text-white text-sm rounded-lg hover:bg-gray-700 transition-colors"
      >
        리셋
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  nodes: {
    type: Array,
    required: true
  },
  edges: {
    type: Array,
    required: true
  },
  containerWidth: {
    type: Number,
    default: 800
  },
  containerHeight: {
    type: Number,
    default: 600
  }
})

const emit = defineEmits(['layout-change'])

const selectedLayout = ref('force')
const isAnimating = ref(false)

// 레이아웃 적용
const applyLayout = async () => {
  if (isAnimating.value) return
  
  isAnimating.value = true
  
  try {
    const newPositions = await calculateLayout(selectedLayout.value)
    emit('layout-change', newPositions)
    
    // 애니메이션 완료 대기
    setTimeout(() => {
      isAnimating.value = false
    }, 1000)
  } catch (error) {
    console.error('Layout calculation failed:', error)
    isAnimating.value = false
  }
}

// 레이아웃 리셋
const resetLayout = () => {
  const randomPositions = props.nodes.map(node => ({
    id: node.id,
    x: Math.random() * props.containerWidth,
    y: Math.random() * props.containerHeight
  }))
  
  emit('layout-change', randomPositions)
}

// 레이아웃 계산
const calculateLayout = async (layoutType) => {
  switch (layoutType) {
    case 'force':
      return await calculateForceLayout()
    case 'circular':
      return await calculateCircularLayout()
    case 'hierarchical':
      return await calculateHierarchicalLayout()
    case 'grid':
      return await calculateGridLayout()
    case 'tree':
      return await calculateTreeLayout()
    default:
      return await calculateForceLayout()
  }
}

// Force-directed 레이아웃
const calculateForceLayout = async () => {
  const nodes = [...props.nodes]
  const edges = [...props.edges]
  
  // 초기 위치 설정
  nodes.forEach(node => {
    if (node.x === undefined || node.y === undefined) {
      node.x = Math.random() * props.containerWidth
      node.y = Math.random() * props.containerHeight
    }
  })
  
  // Force simulation parameters
  const iterations = 100
  const k = Math.sqrt((props.containerWidth * props.containerHeight) / nodes.length)
  const temperature = Math.min(props.containerWidth, props.containerHeight) / 10
  
  for (let i = 0; i < iterations; i++) {
    const forces = new Map()
    
    // Repulsion forces
    for (let j = 0; j < nodes.length; j++) {
      for (let k = j + 1; k < nodes.length; k++) {
        const node1 = nodes[j]
        const node2 = nodes[k]
        
        const dx = node1.x - node2.x
        const dy = node1.y - node2.y
        const distance = Math.sqrt(dx * dx + dy * dy) || 1
        
        const force = (k * k) / distance
        const fx = (dx / distance) * force
        const fy = (dy / distance) * force
        
        if (!forces.has(node1.id)) forces.set(node1.id, { x: 0, y: 0 })
        if (!forces.has(node2.id)) forces.set(node2.id, { x: 0, y: 0 })
        
        forces.get(node1.id).x += fx
        forces.get(node1.id).y += fy
        forces.get(node2.id).x -= fx
        forces.get(node2.id).y -= fy
      }
    }
    
    // Attraction forces
    edges.forEach(edge => {
      const sourceNode = nodes.find(n => n.id === edge.source)
      const targetNode = nodes.find(n => n.id === edge.target)
      
      if (!sourceNode || !targetNode) return
      
      const dx = targetNode.x - sourceNode.x
      const dy = targetNode.y - sourceNode.y
      const distance = Math.sqrt(dx * dx + dy * dy) || 1
      
      const force = (distance * distance) / k
      const fx = (dx / distance) * force
      const fy = (dy / distance) * force
      
      if (!forces.has(sourceNode.id)) forces.set(sourceNode.id, { x: 0, y: 0 })
      if (!forces.has(targetNode.id)) forces.set(targetNode.id, { x: 0, y: 0 })
      
      forces.get(sourceNode.id).x += fx
      forces.get(sourceNode.id).y += fy
      forces.get(targetNode.id).x -= fx
      forces.get(targetNode.id).y -= fy
    })
    
    // Apply forces
    const coolingFactor = 1 - (i / iterations)
    nodes.forEach(node => {
      const force = forces.get(node.id) || { x: 0, y: 0 }
      
      node.x += force.x * coolingFactor
      node.y += force.y * coolingFactor
      
      // Keep nodes within bounds (더 큰 여백 적용)
      node.x = Math.max(100, Math.min(props.containerWidth - 100, node.x))
      node.y = Math.max(100, Math.min(props.containerHeight - 100, node.y))
    })
  }
  
  return nodes.map(node => ({ id: node.id, x: node.x, y: node.y }))
}

// 원형 레이아웃
const calculateCircularLayout = async () => {
  const nodes = [...props.nodes]
  const centerX = props.containerWidth / 2
  const centerY = props.containerHeight / 2
  // 여백을 고려하여 반지름을 더 작게 설정
  const radius = Math.min(props.containerWidth, props.containerHeight) / 3.5
  
  return nodes.map((node, index) => {
    const angle = (2 * Math.PI * index) / nodes.length
    return {
      id: node.id,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle)
    }
  })
}

// 계층 레이아웃
const calculateHierarchicalLayout = async () => {
  const nodes = [...props.nodes]
  const edges = [...props.edges]
  
  // 노드 레벨 계산 (BFS)
  const levels = new Map()
  const visited = new Set()
  const queue = []
  
  // 시작점 찾기 (연결이 적은 노드)
  const nodeConnections = new Map()
  nodes.forEach(node => nodeConnections.set(node.id, 0))
  edges.forEach(edge => {
    nodeConnections.set(edge.source, nodeConnections.get(edge.source) + 1)
    nodeConnections.set(edge.target, nodeConnections.get(edge.target) + 1)
  })
  
  const startNode = nodes.reduce((min, node) => 
    nodeConnections.get(node.id) < nodeConnections.get(min.id) ? node : min
  )
  
  queue.push({ node: startNode, level: 0 })
  levels.set(startNode.id, 0)
  visited.add(startNode.id)
  
  while (queue.length > 0) {
    const { node, level } = queue.shift()
    
    edges.forEach(edge => {
      const neighborId = edge.source === node.id ? edge.target : edge.source
      if (!visited.has(neighborId)) {
        visited.add(neighborId)
        levels.set(neighborId, level + 1)
        const neighborNode = nodes.find(n => n.id === neighborId)
        if (neighborNode) {
          queue.push({ node: neighborNode, level: level + 1 })
        }
      }
    })
  }
  
  // 레벨별로 배치 (여백 고려)
  const maxLevel = Math.max(...levels.values())
  const padding = 100
  const availableHeight = props.containerHeight - (padding * 2)
  const availableWidth = props.containerWidth - (padding * 2)
  const levelHeight = availableHeight / (maxLevel + 1)
  
  return nodes.map(node => {
    const level = levels.get(node.id) || 0
    const nodesInLevel = nodes.filter(n => levels.get(n.id) === level)
    const nodeIndex = nodesInLevel.findIndex(n => n.id === node.id)
    const levelWidth = availableWidth / (nodesInLevel.length + 1)
    
    return {
      id: node.id,
      x: padding + levelWidth * (nodeIndex + 1),
      y: padding + levelHeight * (level + 1)
    }
  })
}

// 격자 레이아웃
const calculateGridLayout = async () => {
  const nodes = [...props.nodes]
  const cols = Math.ceil(Math.sqrt(nodes.length))
  const rows = Math.ceil(nodes.length / cols)
  
  // 여백 고려
  const padding = 100
  const availableWidth = props.containerWidth - (padding * 2)
  const availableHeight = props.containerHeight - (padding * 2)
  
  const cellWidth = availableWidth / cols
  const cellHeight = availableHeight / rows
  
  return nodes.map((node, index) => {
    const row = Math.floor(index / cols)
    const col = index % cols
    
    return {
      id: node.id,
      x: padding + col * cellWidth + cellWidth / 2,
      y: padding + row * cellHeight + cellHeight / 2
    }
  })
}

// 트리 레이아웃
const calculateTreeLayout = async () => {
  const nodes = [...props.nodes]
  const edges = [...props.edges]
  
  // 트리 구조 생성
  const tree = new Map()
  const children = new Map()
  
  nodes.forEach(node => {
    tree.set(node.id, node)
    children.set(node.id, [])
  })
  
  edges.forEach(edge => {
    children.get(edge.source).push(edge.target)
  })
  
  // 루트 노드 찾기
  const hasParent = new Set()
  edges.forEach(edge => hasParent.add(edge.target))
  const rootId = nodes.find(node => !hasParent.has(node.id))?.id || nodes[0].id
  
  // 트리 순회로 위치 계산 (여백 고려)
  const positions = new Map()
  const padding = 100
  const availableWidth = props.containerWidth - (padding * 2)
  const availableHeight = props.containerHeight - (padding * 2)
  const levelWidth = availableWidth / 4
  const levelHeight = availableHeight / 6
  
  const traverse = (nodeId, level, offset) => {
    const nodeChildren = children.get(nodeId) || []
    const childCount = nodeChildren.length
    
    positions.set(nodeId, {
      x: padding + offset * levelWidth + levelWidth / 2,
      y: padding + level * levelHeight + levelHeight / 2
    })
    
    if (childCount > 0) {
      const childOffset = offset - childCount / 2
      nodeChildren.forEach((childId, index) => {
        traverse(childId, level + 1, childOffset + index)
      })
    }
  }
  
  traverse(rootId, 0, 2)
  
  return nodes.map(node => {
    const pos = positions.get(node.id)
    return {
      id: node.id,
      x: pos.x,
      y: pos.y
    }
  })
}

// 레이아웃 타입 변경 감지
watch(selectedLayout, () => {
  applyLayout()
})
</script>

<style scoped>
.layout-controls {
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 0.5rem;
  backdrop-filter: blur(10px);
}
</style>

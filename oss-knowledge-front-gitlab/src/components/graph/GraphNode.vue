<template>
  <g
    :transform="`translate(${node.x}, ${node.y})`"
    class="node-group cursor-pointer"
    :class="{
      'node-selected': isSelected,
      'node-active': node.isActive,
      'node-hover': isHovered
    }"
    :data-node-id="node.id"
    @click="handleClick"
    @mouseenter="isHovered = true"
    @mouseleave="isHovered = false"
    @mousedown="startDrag"
  >
    <!-- 외부 글로우 효과 (활성 상태) -->
    <circle
      v-if="node.isActive"
      :r="radius + 8"
      fill="none"
      :stroke="getNodeColor(node.type)"
      stroke-width="2"
      stroke-opacity="0.3"
      class="animate-pulse"
    />
    
    <!-- 노드 배경 (그라데이션) -->
    <defs>
      <radialGradient :id="`nodeGradient-${node.id}`" cx="30%" cy="30%">
        <stop offset="0%" :stop-color="getNodeColor(node.type)" stop-opacity="1"/>
        <stop offset="100%" :stop-color="getNodeColor(node.type)" stop-opacity="0.8"/>
      </radialGradient>
      
      <!-- 선택 상태 그라데이션 -->
      <radialGradient :id="`nodeGradientSelected-${node.id}`" cx="30%" cy="30%">
        <stop offset="0%" stop-color="#ffffff" stop-opacity="1"/>
        <stop offset="100%" :stop-color="getNodeColor(node.type)" stop-opacity="0.9"/>
      </radialGradient>
    </defs>

    <!-- 메인 노드 원 -->
    <circle
      :r="radius"
      :fill="isSelected ? `url(#nodeGradientSelected-${node.id})` : `url(#nodeGradient-${node.id})`"
      :stroke="getNodeStrokeColor()"
      :stroke-width="getNodeStrokeWidth()"
      class="node-circle"
    />
    
    <!-- 노드 아이콘 -->
    <text
      :y="node.icon ? '4' : '0'"
      text-anchor="middle"
      class="text-white text-sm font-bold pointer-events-none select-none"
      :class="{
        'drop-shadow-sm': true,
        'animate-bounce': node.isActive
      }"
    >
      {{ node.icon || getDefaultIcon(node.type) }}
    </text>
    
    <!-- 중요도 표시 (작은 점) -->
    <circle
      v-if="node.importance === 'high'"
      :cx="radius - 6"
      :cy="-radius + 6"
      r="3"
      fill="#ef4444"
      stroke="white"
      stroke-width="1"
    />
    
    <!-- 노드 라벨 배경 -->
    <rect
      :x="-labelWidth / 2"
      :y="radius + 8"
      :width="labelWidth"
      :height="20"
      :fill="getLabelBackgroundColor()"
      :stroke="getLabelStrokeColor()"
      stroke-width="1"
      rx="10"
      class="node-label-bg"
    />
    
    <!-- 노드 라벨 -->
    <text
      :y="radius + 22"
      text-anchor="middle"
      class="text-xs font-medium pointer-events-none select-none node-label-text"
      :fill="getLabelTextColor()"
    >
      {{ node.label }}
    </text>
    
    <!-- 연결 수 표시 (우상단) -->
    <circle
      v-if="connectionCount > 0"
      :cx="radius - 4"
      :cy="-radius + 4"
      r="8"
      fill="#3b82f6"
      stroke="white"
      stroke-width="2"
    />
    <text
      v-if="connectionCount > 0"
      :x="radius - 4"
      :y="-radius + 7"
      text-anchor="middle"
      class="text-xs font-bold text-white pointer-events-none select-none"
    >
      {{ connectionCount > 99 ? '99+' : connectionCount }}
    </text>
    
    <!-- 상태 표시 (좌하단) -->
    <circle
      v-if="node.isActive"
      :cx="-radius + 6"
      :cy="radius - 6"
      r="4"
      fill="#10b981"
      stroke="white"
      stroke-width="1"
      class="animate-pulse"
    />
    
    <!-- 편집 모드 표시 -->
    <circle
      v-if="editMode && isSelected"
      :cx="radius - 6"
      :cy="radius - 6"
      r="4"
      fill="#f59e0b"
      stroke="white"
      stroke-width="1"
    />
  </g>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  node: {
    type: Object,
    required: true
  },
  isSelected: {
    type: Boolean,
    default: false
  },
  editMode: {
    type: Boolean,
    default: false
  },
  connectionCount: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['click', 'drag-start', 'drag-move', 'drag-end'])

const isHovered = ref(false)
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })

// 노드 반지름 계산
const radius = computed(() => {
  const baseRadius = 24
  const importanceMultiplier = {
    'high': 1.4,
    'medium': 1.2,
    'low': 1.0
  }
  return baseRadius * (importanceMultiplier[props.node.importance] || 1.2)
})

// 라벨 너비 계산
const labelWidth = computed(() => {
  return Math.max(60, props.node.label.length * 7 + 16)
})

// 노드 색상
const getNodeColor = (type) => {
  const colors = {
    'document': '#3b82f6',
    'chunk': '#8b5cf6', 
    'concept': '#06b6d4',
    'process': '#10b981',
    'department': '#f59e0b',
    'user': '#ef4444'
  }
  return colors[type] || '#6b7280'
}

// 기본 아이콘
const getDefaultIcon = (type) => {
  const icons = {
    'document': '📄',
    'chunk': '📋',
    'concept': '💡',
    'process': '⚙️',
    'department': '🏢',
    'user': '👤'
  }
  return icons[type] || '📄'
}

// 노드 테두리 색상
const getNodeStrokeColor = () => {
  if (props.isSelected) return '#ef4444'
  if (props.isHovered) return '#f59e0b'
  if (props.node.isActive) return '#10b981'
  return '#ffffff'
}

// 노드 테두리 두께
const getNodeStrokeWidth = () => {
  if (props.isSelected) return 3
  if (props.isHovered) return 2.5
  return 2
}

// 라벨 배경 색상
const getLabelBackgroundColor = () => {
  if (props.isSelected) return '#fef2f2'
  if (props.isHovered) return '#fffbeb'
  return '#ffffff'
}

// 라벨 테두리 색상
const getLabelStrokeColor = () => {
  if (props.isSelected) return '#ef4444'
  if (props.isHovered) return '#f59e0b'
  return '#e5e7eb'
}

// 라벨 텍스트 색상
const getLabelTextColor = () => {
  if (props.isSelected) return '#dc2626'
  if (props.isHovered) return '#d97706'
  return '#374151'
}

// 클릭 핸들러
const handleClick = (event) => {
  event.stopPropagation()
  emit('click', props.node)
}

// 드래그 시작
const startDrag = (event) => {
  if (!props.editMode) return
  
  event.preventDefault()
  isDragging.value = true
  dragStart.value = {
    x: event.clientX - props.node.x,
    y: event.clientY - props.node.y
  }
  
  emit('drag-start', { node: props.node, startPos: dragStart.value })
  
  // 전역 이벤트 리스너 추가
  document.addEventListener('mousemove', handleDragMove)
  document.addEventListener('mouseup', handleDragEnd)
}

// 드래그 이동
const handleDragMove = (event) => {
  if (!isDragging.value) return
  
  const newX = event.clientX - dragStart.value.x
  const newY = event.clientY - dragStart.value.y
  
  emit('drag-move', { 
    node: props.node, 
    newPos: { x: newX, y: newY } 
  })
}

// 드래그 종료
const handleDragEnd = () => {
  if (!isDragging.value) return
  
  isDragging.value = false
  emit('drag-end', props.node)
  
  // 전역 이벤트 리스너 제거
  document.removeEventListener('mousemove', handleDragMove)
  document.removeEventListener('mouseup', handleDragEnd)
}
</script>

<style scoped>
.node-group {
  /* 호버 시에만 부드러운 전환 효과 적용 */
  transition: filter 0.3s ease, stroke-width 0.2s ease;
  /* transform 전환은 제거하여 춤추는 현상 방지 */
}

.node-group:hover {
  /* 스케일링 대신 글로우 효과만 사용 */
  filter: drop-shadow(0 0 8px rgba(245, 158, 11, 0.4));
}

.node-selected {
  filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.3));
}

.node-active {
  filter: drop-shadow(0 0 12px rgba(16, 185, 129, 0.4));
}

.node-hover {
  filter: drop-shadow(0 0 6px rgba(245, 158, 11, 0.3));
}

/* 애니메이션 - 더 부드럽게 수정 */
@keyframes pulse-glow {
  0%, 100% {
    opacity: 0.3;
  }
  50% {
    opacity: 0.6;
  }
}

.animate-pulse {
  animation: pulse-glow 2s ease-in-out infinite;
}

/* 바운스 애니메이션을 더 미묘하게 수정 */
@keyframes bounce-subtle {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-1px);
  }
}

.animate-bounce {
  animation: bounce-subtle 1.5s ease-in-out infinite;
}

/* 드래그 중 스타일 */
.node-group:active {
  cursor: grabbing;
}

/* 선택 불가능한 텍스트 */
.select-none {
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

/* 호버 시 노드 원의 안정적인 전환 */
.node-circle {
  transition: stroke-width 0.2s ease, stroke 0.2s ease;
}

/* 호버 시 라벨의 부드러운 전환 */
.node-label-bg {
  transition: fill 0.2s ease, stroke 0.2s ease;
}

.node-label-text {
  transition: fill 0.2s ease;
}

/* 호버 시 전체 노드 그룹의 안정적인 효과 */
.node-group:hover .node-circle {
  stroke-width: 3;
}

.node-group:hover .node-label-bg {
  fill: #fffbeb;
  stroke: #f59e0b;
}

.node-group:hover .node-label-text {
  fill: #d97706;
}

/* 연결된 노드 하이라이트 효과 */
.node-connected-highlight .node-circle {
  stroke: #f59e0b !important;
  stroke-width: 3 !important;
  filter: drop-shadow(0 0 6px rgba(245, 158, 11, 0.5));
}

.node-connected-highlight .node-label-bg {
  fill: #fffbeb !important;
  stroke: #f59e0b !important;
  stroke-width: 2 !important;
}

.node-connected-highlight .node-label-text {
  fill: #d97706 !important;
}
</style>

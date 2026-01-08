<template>
  <g class="edge-group" :data-edge-id="edge.id">
    <!-- 연결선 정의 -->
    <defs>
      <!-- 화살표 마커들 -->
      <marker
        :id="`arrow-${edge.id}`"
        markerWidth="10"
        markerHeight="10"
        refX="9"
        refY="3"
        orient="auto"
        markerUnits="strokeWidth"
      >
        <path
          :d="getArrowPath()"
          :fill="getEdgeColor(edge.type)"
          :stroke="getEdgeColor(edge.type)"
          stroke-width="1"
        />
      </marker>
      
      <!-- 점선 패턴 -->
      <pattern
        :id="`dashPattern-${edge.id}`"
        patternUnits="userSpaceOnUse"
        width="8"
        height="2"
      >
        <rect width="4" height="2" :fill="getEdgeColor(edge.type)" />
      </pattern>
      
      <!-- 그라데이션 -->
      <linearGradient
        :id="`edgeGradient-${edge.id}`"
        x1="0%"
        y1="0%"
        x2="100%"
        y2="0%"
      >
        <stop offset="0%" :stop-color="getEdgeColor(edge.type)" stop-opacity="0.8" />
        <stop offset="50%" :stop-color="getEdgeColor(edge.type)" stop-opacity="1" />
        <stop offset="100%" :stop-color="getEdgeColor(edge.type)" stop-opacity="0.8" />
      </linearGradient>
    </defs>

    <!-- 메인 연결선 -->
    <path
      :d="getEdgePath()"
      :stroke="getEdgeStroke()"
      :stroke-width="getEdgeWidth()"
      :stroke-opacity="getEdgeOpacity()"
      :stroke-dasharray="getDashArray()"
      :marker-end="edge.directional ? `url(#arrow-${edge.id})` : ''"
      fill="none"
      class="edge-path"
      :class="{
        'edge-hover': isHovered,
        'edge-selected': isSelected,
        'edge-active': edge.isActive
      }"
      @click="handleClick"
      @mouseenter="isHovered = true"
      @mouseleave="isHovered = false"
    />
    
    <!-- 연결선 라벨 배경 -->
    <rect
      v-if="edge.label && showLabel"
      :x="labelPosition.x - labelWidth / 2"
      :y="labelPosition.y - 8"
      :width="labelWidth"
      :height="16"
      :fill="getLabelBackgroundColor()"
      :stroke="getEdgeColor(edge.type)"
      stroke-width="1"
      rx="8"
      class="edge-label-bg"
    />
    
    <!-- 연결선 라벨 -->
    <text
      v-if="edge.label && showLabel"
      :x="labelPosition.x"
      :y="labelPosition.y + 4"
      text-anchor="middle"
      class="text-xs font-medium pointer-events-none select-none"
      :fill="getLabelTextColor()"
    >
      {{ edge.label }}
    </text>
    
    <!-- 관계 강도 표시 (작은 원) -->
    <circle
      v-if="showStrengthIndicator"
      :cx="strengthPosition.x"
      :cy="strengthPosition.y"
      :r="getStrengthRadius()"
      :fill="getEdgeColor(edge.type)"
      :stroke="getLabelBackgroundColor()"
      stroke-width="2"
      class="edge-strength-indicator"
    />
    
    <!-- 관계 타입 아이콘 -->
    <text
      v-if="showTypeIcon"
      :x="typeIconPosition.x"
      :y="typeIconPosition.y + 4"
      text-anchor="middle"
      class="text-xs pointer-events-none select-none"
    >
      {{ getTypeIcon(edge.type) }}
    </text>
    
    <!-- 애니메이션 효과 (활성 상태) -->
    <path
      v-if="edge.isActive"
      :d="getEdgePath()"
      :stroke="getEdgeColor(edge.type)"
      :stroke-width="getEdgeWidth() + 2"
      stroke-opacity="0.3"
      fill="none"
      class="animate-pulse"
    />
  </g>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  edge: {
    type: Object,
    required: true
  },
  sourceNode: {
    type: Object,
    required: true
  },
  targetNode: {
    type: Object,
    required: true
  },
  isSelected: {
    type: Boolean,
    default: false
  },
  showLabel: {
    type: Boolean,
    default: true
  },
  showStrengthIndicator: {
    type: Boolean,
    default: true
  },
  showTypeIcon: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click', 'hover'])

const isHovered = ref(false)

// 연결선 색상
const getEdgeColor = (type) => {
  const colors = {
    'semantic': '#3b82f6',      // 파란색 - 의미적 연관
    'dependency': '#f59e0b',    // 주황색 - 의존성
    'reference': '#8b5cf6',     // 보라색 - 참조
    'hierarchical': '#10b981',   // 초록색 - 계층적
    'temporal': '#06b6d4',      // 청록색 - 시간적
    'causal': '#ef4444',        // 빨간색 - 인과관계
    'similarity': '#84cc16',    // 라임색 - 유사성
    'containment': '#f97316'    // 오렌지색 - 포함관계
  }
  return colors[type] || '#6b7280'
}

// 연결선 스타일
const getEdgeStroke = () => {
  if (props.isSelected) return '#ef4444'
  if (isHovered.value) return '#f59e0b'
  return `url(#edgeGradient-${props.edge.id})`
}

// 연결선 두께
const getEdgeWidth = () => {
  const baseWidth = 2
  const strengthMultiplier = props.edge.strength || 0.5
  const hoverMultiplier = isHovered.value ? 1.5 : 1
  const selectedMultiplier = props.isSelected ? 2 : 1
  
  return Math.max(1, baseWidth * strengthMultiplier * hoverMultiplier * selectedMultiplier)
}

// 연결선 투명도
const getEdgeOpacity = () => {
  if (props.isSelected) return 1
  if (isHovered.value) return 0.9
  if (props.edge.isActive) return 0.8
  return 0.6
}

// 점선 패턴
const getDashArray = () => {
  const patterns = {
    'semantic': '5,5',           // 점선
    'dependency': '0',          // 실선
    'reference': '10,5',         // 긴 점선
    'hierarchical': '0',         // 실선
    'temporal': '2,3',           // 짧은 점선
    'causal': '0',               // 실선
    'similarity': '8,4,2,4',     // 복합 점선
    'containment': '0'           // 실선
  }
  return patterns[props.edge.type] || '0'
}

// 연결선 경로 생성
const getEdgePath = () => {
  const dx = props.targetNode.x - props.sourceNode.x
  const dy = props.targetNode.y - props.sourceNode.y
  const distance = Math.sqrt(dx * dx + dy * dy)
  
  // 노드 반지름 고려
  const sourceRadius = 24
  const targetRadius = 24
  
  // 시작점과 끝점 계산
  const startX = props.sourceNode.x + (dx / distance) * sourceRadius
  const startY = props.sourceNode.y + (dy / distance) * sourceRadius
  const endX = props.targetNode.x - (dx / distance) * targetRadius
  const endY = props.targetNode.y - (dy / distance) * targetRadius
  
  // 곡선 제어점 계산
  const controlOffset = distance * 0.3
  const controlX = (startX + endX) / 2 + (dy / distance) * controlOffset
  const controlY = (startY + endY) / 2 - (dx / distance) * controlOffset
  
  return `M ${startX} ${startY} Q ${controlX} ${controlY} ${endX} ${endY}`
}

// 화살표 경로
const getArrowPath = () => {
  return 'M0,0 L0,6 L9,3 z'
}

// 라벨 위치 계산
const labelPosition = computed(() => {
  const midX = (props.sourceNode.x + props.targetNode.x) / 2
  const midY = (props.sourceNode.y + props.targetNode.y) / 2
  
  // 곡선의 중간점으로 조정
  const dx = props.targetNode.x - props.sourceNode.x
  const dy = props.targetNode.y - props.sourceNode.y
  const distance = Math.sqrt(dx * dx + dy * dy)
  const controlOffset = distance * 0.15
  
  return {
    x: midX + (dy / distance) * controlOffset,
    y: midY - (dx / distance) * controlOffset
  }
})

// 라벨 너비 계산
const labelWidth = computed(() => {
  return Math.max(40, (props.edge.label?.length || 0) * 6 + 16)
})

// 강도 표시 위치
const strengthPosition = computed(() => {
  const midX = (props.sourceNode.x + props.targetNode.x) / 2
  const midY = (props.sourceNode.y + props.targetNode.y) / 2
  
  return {
    x: midX,
    y: midY + 15
  }
})

// 타입 아이콘 위치
const typeIconPosition = computed(() => {
  const midX = (props.sourceNode.x + props.targetNode.x) / 2
  const midY = (props.sourceNode.y + props.targetNode.y) / 2
  
  return {
    x: midX,
    y: midY - 15
  }
})

// 강도 반지름
const getStrengthRadius = () => {
  const strength = props.edge.strength || 0.5
  return Math.max(3, strength * 6)
}

// 타입 아이콘
const getTypeIcon = (type) => {
  const icons = {
    'semantic': '🔗',
    'dependency': '⬇️',
    'reference': '📖',
    'hierarchical': '📊',
    'temporal': '⏰',
    'causal': '⚡',
    'similarity': '🔄',
    'containment': '📦'
  }
  return icons[type] || '🔗'
}

// 라벨 배경 색상
const getLabelBackgroundColor = () => {
  if (props.isSelected) return '#fef2f2'
  if (isHovered.value) return '#fffbeb'
  return '#ffffff'
}

// 라벨 텍스트 색상
const getLabelTextColor = () => {
  if (props.isSelected) return '#dc2626'
  if (isHovered.value) return '#d97706'
  return '#374151'
}

// 클릭 핸들러
const handleClick = (event) => {
  event.stopPropagation()
  emit('click', props.edge)
}
</script>

<style scoped>
.edge-group {
  /* 전체 그룹의 전환 효과 최소화 */
  transition: filter 0.3s ease;
}

.edge-path {
  cursor: pointer;
  /* 연결선의 부드러운 전환 효과 */
  transition: stroke-width 0.2s ease, stroke-opacity 0.2s ease, filter 0.2s ease;
}

.edge-path:hover {
  filter: drop-shadow(0 0 3px rgba(0, 0, 0, 0.15));
}

.edge-hover {
  filter: drop-shadow(0 0 4px rgba(245, 158, 11, 0.3));
}

.edge-selected {
  filter: drop-shadow(0 0 6px rgba(239, 68, 68, 0.4));
}

.edge-active {
  filter: drop-shadow(0 0 8px rgba(16, 185, 129, 0.5));
}

/* 연결된 관계선 하이라이트 효과 */
.edge-connected-highlight .edge-path {
  stroke: #ef4444 !important;
  stroke-width: 4 !important;
  stroke-opacity: 1 !important;
  filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.6));
  animation: connected-pulse 2s ease-in-out infinite;
}

.edge-connected-highlight .edge-label-bg {
  fill: #fef2f2 !important;
  stroke: #ef4444 !important;
  stroke-width: 2 !important;
}

.edge-connected-highlight .edge-strength-indicator {
  fill: #ef4444 !important;
  stroke: #ffffff !important;
  stroke-width: 3 !important;
}

/* 라벨과 인디케이터의 부드러운 전환 */
.edge-label-bg {
  transition: fill 0.2s ease, stroke 0.2s ease;
}

.edge-strength-indicator {
  transition: fill 0.2s ease, stroke 0.2s ease;
}

/* 애니메이션 - 더 부드럽게 */
@keyframes pulse-flow {
  0%, 100% {
    stroke-dashoffset: 0;
  }
  50% {
    stroke-dashoffset: 15;
  }
}

.animate-pulse {
  animation: pulse-flow 2.5s ease-in-out infinite;
}

/* 연결된 관계선 펄스 애니메이션 */
@keyframes connected-pulse {
  0%, 100% {
    stroke-opacity: 1;
    filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.6));
  }
  50% {
    stroke-opacity: 0.8;
    filter: drop-shadow(0 0 12px rgba(239, 68, 68, 0.8));
  }
}

/* 선택 불가능한 텍스트 */
.select-none {
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}
</style>

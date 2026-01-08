<template>
  <span
    :class="[
      'inline-flex items-center gap-1 px-2 py-1 rounded-md text-sm font-medium cursor-pointer transition-colors duration-150',
      colorClasses[department.color] || colorClasses.blue
    ]"
    @click="$emit('click', department)"
  >
    <span class="text-xs">{{ department.icon }}</span>
    <span>{{ department.name }}</span>
    <button
      v-if="removable"
      @click.stop="$emit('remove', department)"
      class="ml-1 hover:bg-black hover:bg-opacity-10 rounded-full p-0.5 transition-colors duration-150"
    >
      <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  department: {
    type: Object,
    required: true
  },
  removable: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click', 'remove'])

// 색상 클래스 매핑
const colorClasses = {
  blue: 'bg-blue-100 text-blue-800 hover:bg-blue-200',
  green: 'bg-green-100 text-green-800 hover:bg-green-200',
  purple: 'bg-purple-100 text-purple-800 hover:bg-purple-200',
  orange: 'bg-orange-100 text-orange-800 hover:bg-orange-200',
  indigo: 'bg-indigo-100 text-indigo-800 hover:bg-indigo-200',
  red: 'bg-red-100 text-red-800 hover:bg-red-200',
  gray: 'bg-gray-100 text-gray-800 hover:bg-gray-200'
}
</script> 
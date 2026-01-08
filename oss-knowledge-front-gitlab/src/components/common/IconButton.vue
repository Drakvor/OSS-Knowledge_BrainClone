<template>
    <button
        :class="[
            'p-2 rounded-lg transition-colors duration-200',
            variant === 'ghost' && 'hover:bg-claude-hover',
            variant === 'primary' && 'bg-blue-500 text-white hover:bg-blue-600',
            variant === 'secondary' &&
                'bg-claude-sidebar hover:bg-claude-hover',
            disabled && 'opacity-50 cursor-not-allowed',
        ]"
        :disabled="disabled"
        @click="$emit('click')"
    >
        <slot />
    </button>
</template>

<script setup>
defineProps({
    variant: {
        type: String,
        default: "ghost",
        validator: (value) => ["ghost", "primary", "secondary"].includes(value),
    },
    disabled: {
        type: Boolean,
        default: false,
    },
});

defineEmits(["click"]);
</script>

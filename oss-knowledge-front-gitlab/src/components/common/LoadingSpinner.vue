<template>
    <div class="flex items-center justify-center p-4">
        <div class="relative">
            <div
                class="w-8 h-8 border-4 border-claude-border rounded-full animate-spin border-t-blue-500"
            ></div>
            <div
                v-if="message"
                class="absolute -bottom-6 left-1/2 transform -translate-x-1/2 whitespace-nowrap text-sm text-claude-muted"
            >
                {{ message }}
            </div>
        </div>
    </div>
</template>

<script setup>
defineProps({
    message: {
        type: String,
        default: "",
    },
});
</script>

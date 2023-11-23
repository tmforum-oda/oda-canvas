<template>
    <svg aria-hidden="true" class="svg-icon" :class="props.class" :width="props.size" :height="props.size">
        <use :xlink:href="symbolId" :fill="props.color" />
    </svg>
</template>
  
<script setup>
import { computed } from 'vue'
const props = defineProps({
    prefix: {
        type: String,
        default: 'icon'
    },
    name: {
        type: String,
        required: true
    },
    color: {
        type: String,
        default: '#333'
    },
    size: {
        type: String,
        default: '16'
    },
    class: {
        type: String,
        default: ''
    }
})

const symbolId = computed(() => `#${props.prefix}-${props.name}`)
</script>
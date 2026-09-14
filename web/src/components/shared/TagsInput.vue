<script setup>
import { computed } from 'vue'

const props = defineProps({ modelValue: { type: Array, default: () => [] }, placeholder: { type: String, default: 'tags, comma separated' } })
const emit = defineEmits(['update:modelValue'])
const text = computed(() => (props.modelValue || []).join(', '))

function onInput(e) {
  const tags = e.target.value
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean)
  emit('update:modelValue', [...new Set(tags)])
}
</script>

<template>
  <input type="text" :value="text" :placeholder="placeholder" @change="onInput" />
</template>

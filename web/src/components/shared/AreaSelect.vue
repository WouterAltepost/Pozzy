<script setup>
import { onMounted } from 'vue'
import { useAreasStore } from '../../stores/areas'

defineProps({ modelValue: { type: String, default: '' }, allowEmpty: { type: Boolean, default: true } })
const emit = defineEmits(['update:modelValue'])
const areas = useAreasStore()
onMounted(() => areas.load())
</script>

<template>
  <select :value="modelValue || ''" @change="emit('update:modelValue', $event.target.value || null)">
    <option v-if="allowEmpty" value="">No area</option>
    <option v-for="a in areas.items" :key="a.id" :value="a.id">{{ a.name }}</option>
  </select>
</template>

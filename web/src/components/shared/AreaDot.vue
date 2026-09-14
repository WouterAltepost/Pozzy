<script setup>
import { useAreasStore } from '../../stores/areas'

defineProps({ areaId: { type: String, default: null }, label: { type: Boolean, default: false } })
const areas = useAreasStore()
</script>

<template>
  <span v-if="areaId" class="area-dot" :title="areas.name(areaId)">
    <span class="dot" :style="{ background: areas.color(areaId) }"></span>
    <span v-if="label">{{ areas.name(areaId) }}</span>
  </span>
</template>

<style scoped>
.area-dot { display: inline-flex; align-items: center; gap: 0.3rem; font-size: 0.8rem; color: #6b7280; }
.dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
</style>

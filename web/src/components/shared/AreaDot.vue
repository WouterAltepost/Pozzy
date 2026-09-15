<script setup>
// The one area indicator. Colour is data from the areas table, never restyled.
import { useAreasStore } from '../../stores/areas'

defineProps({ areaId: { type: String, default: null }, label: { type: Boolean, default: false } })
const areas = useAreasStore()
</script>

<template>
  <span v-if="areaId" class="area-dot" :title="areas.name(areaId)">
    <span class="dot" :style="{ background: areas.color(areaId) }" aria-hidden="true"></span>
    <span v-if="label">{{ areas.name(areaId) }}</span>
    <span v-else class="visually-hidden">{{ areas.name(areaId) }}</span>
  </span>
</template>

<style scoped>
.area-dot { display: inline-flex; align-items: center; gap: 6px; font-size: var(--fs-sm); color: var(--ink-3); white-space: nowrap; }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; flex: none; }
</style>

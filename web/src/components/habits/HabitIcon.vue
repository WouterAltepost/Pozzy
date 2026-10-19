<script setup>
// The habit's symbol on a small tile tinted with its area colour (data colour, never restyled).
import { computed } from 'vue'
import { iconFor } from '../../lib/habits'

const props = defineProps({ tracker: { type: Object, required: true }, size: { type: Number, default: 40 }, done: { type: Boolean, default: false } })
const icon = computed(() => iconFor(props.tracker))
const color = computed(() => props.tracker.area_color || 'var(--ink-3)')
</script>

<template>
  <span class="tile" :class="{ done }" :style="{ '--c': color, width: size + 'px', height: size + 'px' }" aria-hidden="true">
    <component :is="icon" :size="Math.round(size * 0.5)" weight="regular" />
  </span>
</template>

<style scoped>
.tile {
  flex: none;
  display: inline-grid;
  place-items: center;
  border-radius: 30%;
  color: var(--c);
  background: color-mix(in srgb, var(--c) 13%, var(--surface));
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--c) 16%, transparent);
  transition: background-color var(--dur-ui) ease, color var(--dur-ui) ease;
}
.tile.done { background: var(--c); color: #fff; box-shadow: inset 0 1px 0 rgb(255 255 255 / 0.25); }
</style>

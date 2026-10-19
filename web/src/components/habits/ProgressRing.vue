<script setup>
// A ring that fills with the day's progress. Turns green when everything due is done.
import { computed } from 'vue'

const props = defineProps({
  value: { type: Number, default: 0 },
  total: { type: Number, default: 0 },
  size: { type: Number, default: 64 },
  stroke: { type: Number, default: 6 },
  label: { type: Boolean, default: true },
})
const r = computed(() => (props.size - props.stroke) / 2)
const c = computed(() => 2 * Math.PI * r.value)
const fraction = computed(() => (props.total ? Math.min(1, props.value / props.total) : 0))
const full = computed(() => props.total > 0 && props.value >= props.total)
</script>

<template>
  <span class="ring" :class="{ full }" :style="{ width: size + 'px', height: size + 'px' }" role="img" :aria-label="`${value} of ${total} done`">
    <svg :viewBox="`0 0 ${size} ${size}`" :width="size" :height="size">
      <circle class="track" :cx="size / 2" :cy="size / 2" :r="r" :stroke-width="stroke" fill="none" />
      <circle class="fill" :cx="size / 2" :cy="size / 2" :r="r" :stroke-width="stroke" fill="none" stroke-linecap="round" :stroke-dasharray="c" :stroke-dashoffset="c * (1 - fraction)" :transform="`rotate(-90 ${size / 2} ${size / 2})`" />
    </svg>
    <span v-if="label" class="txt num"><slot>{{ value }}<span class="of">/{{ total }}</span></slot></span>
  </span>
</template>

<style scoped>
.ring { position: relative; display: inline-grid; place-items: center; flex: none; }
.ring svg { position: absolute; inset: 0; }
.track { stroke: var(--surface-3); }
.fill { stroke: var(--brand); transition: stroke-dashoffset 600ms var(--ease-spring), stroke var(--dur-ui) ease; }
.full .fill { stroke: var(--ok); }
.txt { position: relative; font-size: calc(var(--fs-base) * 1.05); font-weight: 650; letter-spacing: -0.02em; color: var(--ink); }
.of { color: var(--ink-4); font-weight: 500; }
</style>

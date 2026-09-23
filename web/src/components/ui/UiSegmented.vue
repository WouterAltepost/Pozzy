<script setup>
// Segmented control: options [{ value, label }]. v-model the value. The selected pill is one
// element that springs to the chosen segment, so a change reads as the same object moving.
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { createSpring, reducedMotion } from '../../lib/spring'

const props = defineProps({ modelValue: { type: [String, Number], required: true }, options: { type: Array, required: true } })
const emit = defineEmits(['update:modelValue'])

const root = ref(null)
const thumb = ref({ x: 0, w: 0, ready: false })
const sx = createSpring({ value: 0, damping: 1, response: 0.3, onUpdate: (v) => (thumb.value.x = v) })
const sw = createSpring({ value: 0, damping: 1, response: 0.3, onUpdate: (v) => (thumb.value.w = v) })

function measure(animate = true) {
  const el = root.value?.querySelector('.seg-item.active')
  if (!el) return
  const x = el.offsetLeft
  const w = el.offsetWidth
  if (!thumb.value.ready || !animate || reducedMotion()) {
    sx.jump(x)
    sw.jump(w)
    thumb.value.ready = true
  } else {
    sx.set(x)
    sw.set(w)
  }
}
let observer = null
onMounted(() => {
  measure(false)
  observer = new ResizeObserver(() => measure(false))
  observer.observe(root.value)
})
onBeforeUnmount(() => {
  observer?.disconnect()
  sx.stop()
  sw.stop()
})
watch(() => [props.modelValue, props.options], () => nextTick(() => measure(true)), { deep: true })
</script>

<template>
  <div ref="root" class="seg" role="tablist">
    <span v-if="thumb.ready" class="thumb" :style="{ transform: `translate3d(${thumb.x}px, 0, 0)`, width: thumb.w + 'px' }" aria-hidden="true"></span>
    <button
      v-for="o in options"
      :key="o.value"
      type="button"
      role="tab"
      class="seg-item"
      :class="{ active: o.value === modelValue }"
      :aria-selected="o.value === modelValue"
      @click="emit('update:modelValue', o.value)"
    >
      {{ o.label }}
    </button>
  </div>
</template>

<style scoped>
.seg { position: relative; display: inline-flex; padding: 2px; gap: 0; background: var(--surface-2); border-radius: 9px; isolation: isolate; }
.thumb { position: absolute; top: 2px; bottom: 2px; left: 0; border-radius: 7px; background: var(--surface); box-shadow: 0 3px 8px rgb(0 0 0 / 0.12), 0 3px 1px rgb(0 0 0 / 0.04); z-index: 0; will-change: transform, width; }
:root[data-theme="dark"] .thumb { background: #636366; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .thumb { background: #636366; } }
.seg-item {
  position: relative;
  z-index: 1;
  height: 28px;
  padding: 0 12px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: var(--ink);
  font-size: var(--fs-md);
  font-weight: 500;
  touch-action: manipulation;
  transition: color var(--dur-hover) ease, transform var(--dur-press) var(--ease-out);
}
.seg-item:active { transform: scale(0.96); }
.seg-item.active { color: var(--ink); font-weight: 600; }
@media (hover: hover) and (pointer: fine) { .seg-item:not(.active):hover { color: var(--ink); } }
</style>

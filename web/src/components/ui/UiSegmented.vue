<script setup>
// Segmented control: options [{ value, label }]. v-model the value. The selected pill is one
// element that springs to the chosen segment, so a change reads as the same object moving.
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { createSpring, reducedMotion } from '../../lib/spring'
import { tick } from '../../lib/haptics'

const props = defineProps({ modelValue: { type: [String, Number], required: true }, options: { type: Array, required: true } })
const emit = defineEmits(['update:modelValue'])

const root = ref(null)
function pick(value) {
  if (value !== props.modelValue) tick()
  emit('update:modelValue', value)
}
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
      @click="pick(o.value)"
    >
      {{ o.label }}
    </button>
  </div>
</template>

<style scoped>
.seg { position: relative; display: inline-flex; padding: 3px; gap: 0; background: var(--surface-2); border-radius: var(--r-pill); box-shadow: var(--inset); isolation: isolate; }
.thumb { position: absolute; top: 3px; bottom: 3px; left: 0; border-radius: var(--r-pill); background: var(--surface); box-shadow: inset 0 1px 0 var(--edge), 0 1px 2px rgb(14 17 32 / 0.08), 0 4px 10px -4px rgb(14 17 32 / 0.16); z-index: 0; will-change: transform, width; }
.seg-item {
  position: relative;
  z-index: 1;
  height: 28px;
  padding: 0 14px;
  border: 0;
  border-radius: var(--r-pill);
  background: transparent;
  color: var(--ink-3);
  font-size: var(--fs-md);
  font-weight: 500;
  touch-action: manipulation;
  transition: color var(--dur-hover) ease, transform var(--dur-press) var(--ease-out);
}
.seg-item:active { transform: scale(0.96); }
.seg-item.active { color: var(--ink); font-weight: 600; }
@media (hover: hover) and (pointer: fine) { .seg-item:not(.active):hover { color: var(--ink); } }
/* iOS segmented control: a grey rounded track, a white thumb with a soft shadow, 13pt labels. */
@media (max-width: 1023px) {
  .seg { padding: 2px; border-radius: 9px; background: var(--surface-2); box-shadow: none; }
  .thumb { top: 2px; bottom: 2px; border-radius: 7px; background: #fff; box-shadow: 0 3px 8px rgb(0 0 0 / 0.12), 0 3px 1px rgb(0 0 0 / 0.04); }
  :root[data-theme='dark'] .thumb { background: #636366; }
  .seg-item { height: 28px; padding: 0 12px; border-radius: 7px; font-size: 0.8125rem; font-weight: 500; color: var(--ink); }
  .seg-item.active { font-weight: 600; }
  .seg-item:active { transform: none; opacity: 0.6; }
}
@media (max-width: 1023px) and (prefers-color-scheme: dark) { :root:not([data-theme='light']) .thumb { background: #636366; } }
</style>

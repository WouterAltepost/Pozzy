<script setup>
// Segmented control: options [{ value, label }]. v-model the value.
defineProps({ modelValue: { type: [String, Number], required: true }, options: { type: Array, required: true } })
const emit = defineEmits(['update:modelValue'])
</script>

<template>
  <div class="seg" role="tablist">
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
.seg { display: inline-flex; padding: 3px; gap: 2px; background: var(--surface-2); border-radius: var(--r-md); }
.seg-item {
  height: 28px;
  padding: 0 12px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--ink-2);
  font-size: var(--fs-md);
  font-weight: 500;
  transition: background-color var(--dur-hover) ease, color var(--dur-hover) ease, box-shadow var(--dur-hover) ease;
}
.seg-item.active { background: var(--surface); color: var(--ink); box-shadow: var(--shadow-1); }
@media (hover: hover) and (pointer: fine) { .seg-item:not(.active):hover { color: var(--ink); } }
</style>

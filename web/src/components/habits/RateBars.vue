<script setup>
// Small vertical bars for a rate per bucket (month, weekday). Empty buckets show a dash.
defineProps({ items: { type: Array, default: () => [] }, color: { type: String, default: '' } })
</script>

<template>
  <div class="bars" :style="{ '--c': color || 'var(--brand)' }">
    <div v-for="it in items" :key="it.key" class="b" :title="it.rate === null ? `${it.label}: nothing due` : `${it.label}: ${Math.round(it.rate * 100)}% (${it.met} of ${it.counted})`">
      <span class="val num">{{ it.rate === null ? '' : Math.round(it.rate * 100) }}</span>
      <span class="track"><span class="fill" :style="{ height: (it.rate || 0) * 100 + '%' }"></span></span>
      <span class="lbl">{{ it.label }}</span>
    </div>
  </div>
</template>

<style scoped>
.bars { display: grid; grid-auto-flow: column; grid-auto-columns: minmax(0, 1fr); gap: 6px; align-items: end; }
.b { display: flex; flex-direction: column; align-items: center; gap: 4px; min-width: 0; }
.val { font-size: 10px; color: var(--ink-3); height: 13px; }
.track { position: relative; width: 100%; max-width: 28px; height: 96px; border-radius: 6px; background: var(--surface-2); box-shadow: var(--inset); overflow: hidden; }
.fill { position: absolute; left: 0; right: 0; bottom: 0; background: var(--c); border-radius: 6px 6px 0 0; transition: height 600ms var(--ease-spring); }
.lbl { font-size: var(--fs-xs); color: var(--ink-3); white-space: nowrap; }
</style>

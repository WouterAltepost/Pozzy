<script setup>
defineProps({ title: { type: String, required: true } })
</script>

<template>
  <header class="page-header">
    <div class="title-row">
      <h1>{{ title }}</h1>
      <span v-if="$slots.meta" class="meta"><slot name="meta" /></span>
    </div>
    <div v-if="$slots.default" class="toolbar"><slot /></div>
  </header>
</template>

<style scoped>
.page-header { display: flex; align-items: center; justify-content: space-between; gap: var(--sp-3) var(--sp-4); flex-wrap: wrap; margin-bottom: var(--sp-4); }
.title-row { display: flex; align-items: baseline; gap: var(--sp-3); min-width: 0; }
.meta { font-size: var(--fs-sm); color: var(--ink-3); font-variant-numeric: tabular-nums; }
.toolbar { display: flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap; }
</style>

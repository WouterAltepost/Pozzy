<script setup>
import { CATEGORIES, PRIORITIES } from '../../api/mail'
import AreaSelect from '../shared/AreaSelect.vue'

const props = defineProps({ filters: { type: Object, required: true }, accounts: { type: Array, default: () => [] } })
const emit = defineEmits(['change', 'reset'])
const change = () => emit('change')
</script>

<template>
  <div class="filters">
    <input v-model="props.filters.q" type="search" placeholder="Search from, subject, summary" @change="change" />
    <select v-model="props.filters.account_id" @change="change">
      <option value="">All accounts</option>
      <option v-for="a in accounts" :key="a.id" :value="a.id">{{ a.label }}</option>
    </select>
    <select v-model="props.filters.category" @change="change">
      <option value="">All categories</option>
      <option v-for="c in CATEGORIES" :key="c" :value="c">{{ c }}</option>
    </select>
    <AreaSelect v-model="props.filters.area_id" @update:model-value="change" />
    <select v-model="props.filters.priority" @change="change">
      <option value="">Any priority</option>
      <option v-for="[value, label] in PRIORITIES" :key="value" :value="String(value)">{{ label }}</option>
    </select>
    <select v-model="props.filters.needs_reply" @change="change">
      <option value="">Reply: any</option>
      <option value="1">Needs reply</option>
      <option value="0">No reply needed</option>
    </select>
    <select v-model="props.filters.handled" @change="change">
      <option value="0">Unhandled</option>
      <option value="1">Handled</option>
      <option value="all">All</option>
    </select>
    <button type="button" class="link" @click="emit('reset')">Reset</button>
  </div>
</template>

<style scoped>
.filters { display: flex; flex-wrap: wrap; gap: 0.4rem; align-items: center; }
.filters input, .filters select, .filters :deep(select) { font: inherit; font-size: 0.85rem; padding: 0.3rem; border: 1px solid #d1d5db; border-radius: 4px; }
.filters input { min-width: 200px; flex: 1; }
.link { border: none; background: none; color: #2563eb; padding: 0.2rem 0.4rem; font-size: 0.85rem; }
</style>

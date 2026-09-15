<script setup>
import { accountName } from '../../lib/mail'
import { CATEGORIES, PRIORITIES } from '../../api/mail'
import AreaSelect from '../shared/AreaSelect.vue'

const props = defineProps({ filters: { type: Object, required: true }, accounts: { type: Array, default: () => [] } })
const emit = defineEmits(['change', 'reset'])
const change = () => emit('change')
</script>

<template>
  <div class="filters">
    <input v-model="props.filters.q" type="search" placeholder="Search from, subject, summary" aria-label="Search mail" class="search" @change="change" />
    <select v-model="props.filters.account_id" aria-label="Account" @change="change">
      <option value="">All accounts</option>
      <option v-for="a in accounts" :key="a.id" :value="a.id">{{ accountName(a) }} ({{ a.label }})</option>
    </select>
    <select v-model="props.filters.category" aria-label="Category" @change="change">
      <option value="">All categories</option>
      <option v-for="c in CATEGORIES" :key="c" :value="c">{{ c }}</option>
    </select>
    <AreaSelect v-model="props.filters.area_id" aria-label="Area" @update:model-value="change" />
    <select v-model="props.filters.priority" aria-label="Priority" @change="change">
      <option value="">Any priority</option>
      <option v-for="[value, label] in PRIORITIES" :key="value" :value="String(value)">{{ label }}</option>
    </select>
    <select v-model="props.filters.needs_reply" aria-label="Reply" @change="change">
      <option value="">Reply: any</option>
      <option value="1">Needs reply</option>
      <option value="0">No reply needed</option>
    </select>
    <select v-model="props.filters.handled" aria-label="Handled" @change="change">
      <option value="0">Unhandled</option>
      <option value="1">Handled</option>
      <option value="all">All</option>
    </select>
    <button type="button" class="link-btn" @click="emit('reset')">Reset</button>
  </div>
</template>

<style scoped>
.filters { display: flex; flex-wrap: wrap; gap: var(--sp-2); align-items: center; }
.filters select { height: var(--control-h-sm); padding-left: 10px; font-size: var(--fs-md); border-radius: var(--r-pill); }
.filters :deep(select) { height: var(--control-h-sm); padding-left: 10px; font-size: var(--fs-md); border-radius: var(--r-pill); }
.search { flex: 1 1 200px; min-width: 180px; height: var(--control-h-sm); border-radius: var(--r-pill); font-size: var(--fs-md); }
</style>

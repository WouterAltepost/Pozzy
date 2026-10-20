<script setup>
import { accountName } from '../../lib/mail'
import { CATEGORIES, PRIORITIES } from '../../api/mail'
import AreaSelect from '../shared/AreaSelect.vue'

// `ios`: the filter sheet on the phone. Grouped rows with the label on the left and the menu on
// the right, like a Settings form; the handled mode and the search live on the page itself.
const props = defineProps({ filters: { type: Object, required: true }, accounts: { type: Array, default: () => [] }, ios: { type: Boolean, default: false } })
const emit = defineEmits(['change', 'reset'])
const change = () => emit('change')
</script>

<template>
  <div v-if="ios" class="iform">
    <div class="grp">
      <label class="frow">
        <span class="flabel">Account</span>
        <select v-model="props.filters.account_id" @change="change">
          <option value="">All</option>
          <option v-for="a in accounts" :key="a.id" :value="a.id">{{ a.label || accountName(a) }}</option>
        </select>
      </label>
      <label class="frow">
        <span class="flabel">Category</span>
        <select v-model="props.filters.category" class="cap" @change="change">
          <option value="">All</option>
          <option v-for="c in CATEGORIES" :key="c" :value="c">{{ c }}</option>
        </select>
      </label>
      <label class="frow">
        <span class="flabel">Area</span>
        <AreaSelect v-model="props.filters.area_id" @update:model-value="change" />
      </label>
    </div>
    <div class="grp">
      <label class="frow">
        <span class="flabel">Priority</span>
        <select v-model="props.filters.priority" @change="change">
          <option value="">Any</option>
          <option v-for="[value, label] in PRIORITIES" :key="value" :value="String(value)">{{ label }}</option>
        </select>
      </label>
      <label class="frow">
        <span class="flabel">Reply</span>
        <select v-model="props.filters.needs_reply" @change="change">
          <option value="">Any</option>
          <option value="1">Needs reply</option>
          <option value="0">No reply needed</option>
        </select>
      </label>
    </div>
    <div class="grp">
      <button type="button" class="frow reset pressable" @click="emit('reset')">Reset filters</button>
    </div>
  </div>
  <div v-else class="filters">
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

/* Grouped form rows in the sheet: label left, the value as a quiet menu on the right. */
.iform { display: flex; flex-direction: column; gap: var(--sp-6); }
.grp { background: var(--surface-2); border-radius: var(--r-lg); overflow: hidden; }
.frow { position: relative; display: flex; align-items: center; gap: var(--sp-3); width: 100%; min-height: 44px; padding: 0 16px; border: 0; border-radius: 0; background: none; color: var(--ink); font: inherit; font-size: 1.0625rem; text-align: left; }
.frow + .frow::before { content: ''; position: absolute; top: 0; left: 16px; right: 0; height: 0.5px; background: var(--line-2); }
.flabel { flex: 1; min-width: 0; }
.frow select, .frow :deep(select) { flex: none; width: auto; max-width: 60%; height: 44px; padding: 0 22px 0 8px; border: 0; background-color: transparent; box-shadow: none; color: var(--ink-3); font-size: 1.0625rem; text-align: right; text-align-last: right; background-position: right 2px center; }
select.cap { text-transform: capitalize; }
.reset { justify-content: center; color: var(--danger); }
</style>

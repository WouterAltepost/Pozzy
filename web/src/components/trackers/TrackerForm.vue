<script setup>
import { reactive, watch } from 'vue'
import AreaSelect from '../shared/AreaSelect.vue'

const props = defineProps({ tracker: { type: Object, default: null } })
const emit = defineEmits(['save', 'cancel'])
const form = reactive({ name: '', type: 'daily_bool', area_id: null, target_value: null, target_period: 'day', unit: '', active: true })

watch(
  () => props.tracker,
  (t) => Object.assign(form, { name: '', type: 'daily_bool', area_id: null, target_value: null, target_period: 'day', unit: '', active: true }, t || {}),
  { immediate: true },
)

function submit() {
  emit('save', {
    name: form.name,
    type: form.type,
    area_id: form.area_id || null,
    target_value: form.target_value || null,
    target_period: form.target_period,
    unit: form.unit || null,
    active: form.active,
  })
}
</script>

<template>
  <form class="tracker-form" @submit.prevent="submit">
    <input v-model="form.name" type="text" placeholder="Name" required maxlength="100" />
    <select v-model="form.type">
      <option value="daily_bool">daily yes/no</option>
      <option value="weekly_count">weekly count</option>
      <option value="numeric">numeric</option>
      <option value="duration">duration (minutes)</option>
    </select>
    <AreaSelect v-model="form.area_id" />
    <template v-if="form.type !== 'daily_bool'">
      <input v-model.number="form.target_value" type="number" step="any" min="0" placeholder="target" />
      <select v-if="form.type !== 'weekly_count'" v-model="form.target_period">
        <option value="day">per day</option>
        <option value="week">per week</option>
      </select>
      <input v-if="form.type === 'numeric'" v-model="form.unit" type="text" placeholder="unit" maxlength="20" />
    </template>
    <label v-if="tracker" class="check"><input v-model="form.active" type="checkbox" /> active</label>
    <button type="submit">{{ tracker ? 'Save' : 'Add' }}</button>
    <button type="button" @click="emit('cancel')">Cancel</button>
  </form>
</template>

<style scoped>
.tracker-form { display: flex; flex-wrap: wrap; gap: 0.4rem; align-items: center; }
.tracker-form input, .tracker-form select { font: inherit; padding: 0.35rem; border: 1px solid #d1d5db; border-radius: 4px; }
.tracker-form input[type='text'] { min-width: 140px; }
.tracker-form input[type='number'] { width: 90px; }
.check { display: flex; align-items: center; gap: 0.3rem; font-size: 0.85rem; }
</style>

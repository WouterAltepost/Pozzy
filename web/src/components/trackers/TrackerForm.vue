<script setup>
import { reactive, watch } from 'vue'
import AreaSelect from '../shared/AreaSelect.vue'
import UiButton from '../ui/UiButton.vue'
import UiField from '../ui/UiField.vue'

const props = defineProps({ tracker: { type: Object, default: null }, busy: { type: Boolean, default: false } })
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
    <UiField label="Name" class="grow"><input v-model="form.name" type="text" required maxlength="100" /></UiField>
    <UiField label="Type">
      <select v-model="form.type">
        <option value="daily_bool">daily yes/no</option>
        <option value="weekly_count">weekly count</option>
        <option value="numeric">numeric</option>
        <option value="duration">duration (minutes)</option>
      </select>
    </UiField>
    <UiField label="Area"><AreaSelect v-model="form.area_id" /></UiField>
    <template v-if="form.type !== 'daily_bool'">
      <UiField label="Target"><input v-model.number="form.target_value" type="number" step="any" min="0" class="narrow" /></UiField>
      <UiField v-if="form.type !== 'weekly_count'" label="Per">
        <select v-model="form.target_period">
          <option value="day">day</option>
          <option value="week">week</option>
        </select>
      </UiField>
      <UiField v-if="form.type === 'numeric'" label="Unit"><input v-model="form.unit" type="text" maxlength="20" class="narrow" /></UiField>
    </template>
    <label v-if="tracker" class="check"><input v-model="form.active" type="checkbox" /> Active</label>
    <div class="actions">
      <UiButton type="submit" variant="primary" :loading="busy">{{ tracker ? 'Save' : 'Add tracker' }}</UiButton>
      <UiButton :disabled="busy" @click="emit('cancel')">Cancel</UiButton>
    </div>
  </form>
</template>

<style scoped>
.tracker-form { display: flex; flex-wrap: wrap; gap: var(--sp-3); align-items: end; }
.grow { flex: 1 1 180px; }
.narrow { width: 96px; }
.check { display: flex; align-items: center; gap: 6px; height: var(--control-h); font-size: var(--fs-base); }
.actions { display: flex; gap: var(--sp-2); }
</style>

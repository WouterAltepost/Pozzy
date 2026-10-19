<script setup>
// Create or edit a habit: name and icon, what kind of check-in it takes, when it is due, its
// goal, area and an optional reminder time. A popup on the desktop, a sheet on the phone.
import { computed, reactive, ref, watch } from 'vue'
import AreaSelect from '../shared/AreaSelect.vue'
import UiButton from '../ui/UiButton.vue'
import UiField from '../ui/UiField.vue'
import UiModal from '../ui/UiModal.vue'
import UiSegmented from '../ui/UiSegmented.vue'
import { ICONS, WEEKDAYS } from '../../lib/habits'

const props = defineProps({ open: { type: Boolean, default: false }, tracker: { type: Object, default: null }, busy: { type: Boolean, default: false }, error: { type: String, default: '' } })
const emit = defineEmits(['save', 'close'])

const blank = () => ({ name: '', icon: 'check', type: 'daily_bool', area_id: null, target_value: null, target_period: 'day', unit: '', active: true, schedule: 'daily', schedule_days: 0b0011111, schedule_n: 2, reminder_time: '' })
const form = reactive(blank())
const localError = ref('')

watch(
  () => [props.open, props.tracker],
  () => {
    if (!props.open) return
    const t = props.tracker
    Object.assign(form, blank(), t ? { ...t, icon: t.icon || 'check', unit: t.unit || '', reminder_time: t.reminder_time || '', schedule: t.schedule || 'daily', schedule_days: t.schedule_days || 0b0011111, schedule_n: t.schedule_n || 2 } : {})
    localError.value = ''
  },
  { immediate: true },
)

const kinds = [
  { value: 'daily_bool', label: 'Yes/no' },
  { value: 'weekly_count', label: 'Per week' },
  { value: 'numeric', label: 'Number' },
  { value: 'duration', label: 'Minutes' },
]
const schedules = [
  { value: 'daily', label: 'Every day' },
  { value: 'weekdays', label: 'Set days' },
  { value: 'every_n_days', label: 'Every N days' },
]
const periods = [
  { value: 'day', label: 'Per day' },
  { value: 'week', label: 'Per week' },
]
// Week habits are judged on the week total, so they have no day schedule.
const daySchedule = computed(() => form.type === 'daily_bool' || ((form.type === 'numeric' || form.type === 'duration') && form.target_period === 'day'))
const iconNames = Object.keys(ICONS)

watch(() => form.type, (type) => {
  if (type === 'weekly_count') form.target_period = 'week'
  if (type === 'daily_bool') form.target_period = 'day'
  if (type === 'weekly_count' && !form.target_value) form.target_value = 3
})

function toggleDay(i) {
  form.schedule_days ^= 1 << i
}

function submit() {
  localError.value = ''
  if (daySchedule.value && form.schedule === 'weekdays' && !form.schedule_days) {
    localError.value = 'Pick at least one day.'
    return
  }
  const body = {
    name: form.name,
    icon: form.icon,
    type: form.type,
    area_id: form.area_id || null,
    target_value: form.type === 'daily_bool' ? null : form.target_value || null,
    target_period: form.target_period,
    unit: form.type === 'numeric' ? form.unit || null : form.type === 'duration' ? 'min' : null,
    reminder_time: form.reminder_time || null,
    schedule: daySchedule.value ? form.schedule : 'daily',
  }
  if (body.schedule === 'weekdays') body.schedule_days = form.schedule_days
  if (body.schedule === 'every_n_days') body.schedule_n = Math.max(2, Number(form.schedule_n) || 2)
  if (props.tracker) body.active = form.active
  emit('save', body)
}
</script>

<template>
  <UiModal :open="open" :title="tracker ? 'Edit habit' : 'New habit'" size="md" @close="emit('close')">
    <form class="editor" @submit.prevent="submit">
      <UiField label="Name"><input v-model="form.name" type="text" required maxlength="100" placeholder="Creatine, gym, read 20 pages" /></UiField>

      <fieldset>
        <legend class="label">Icon</legend>
        <div class="icons">
          <button v-for="name in iconNames" :key="name" type="button" class="ic" :class="{ on: form.icon === name }" :aria-label="name" :aria-pressed="form.icon === name" @click="form.icon = name">
            <component :is="ICONS[name]" :size="20" />
          </button>
        </div>
      </fieldset>

      <fieldset>
        <legend class="label">Check-in</legend>
        <UiSegmented v-model="form.type" :options="kinds" />
      </fieldset>

      <div v-if="form.type !== 'daily_bool'" class="grid">
        <UiField :label="form.type === 'weekly_count' ? 'Times per week' : 'Goal'">
          <input v-model.number="form.target_value" type="number" step="any" min="0" inputmode="decimal" :placeholder="form.type === 'weekly_count' ? '3' : 'optional'" />
        </UiField>
        <UiField v-if="form.type === 'numeric'" label="Unit"><input v-model="form.unit" type="text" maxlength="20" placeholder="kg, pages, glasses" /></UiField>
        <fieldset v-if="form.type !== 'weekly_count'" class="span">
          <legend class="label">Goal counts</legend>
          <UiSegmented v-model="form.target_period" :options="periods" />
        </fieldset>
      </div>

      <fieldset v-if="daySchedule">
        <legend class="label">Due</legend>
        <UiSegmented v-model="form.schedule" :options="schedules" />
        <div v-if="form.schedule === 'weekdays'" class="days" role="group" aria-label="Days">
          <button v-for="(d, i) in WEEKDAYS" :key="d" type="button" class="day" :class="{ on: (form.schedule_days >> i) & 1 }" :aria-pressed="Boolean((form.schedule_days >> i) & 1)" @click="toggleDay(i)">{{ d }}</button>
        </div>
        <div v-if="form.schedule === 'every_n_days'" class="every">
          <span>Every</span>
          <input v-model.number="form.schedule_n" type="number" min="2" max="60" class="n" aria-label="Number of days" />
          <span>days, counted from the last time you did it</span>
        </div>
        <p class="muted small hint">Days it is not due never break the streak.</p>
      </fieldset>

      <div class="grid">
        <UiField label="Area"><AreaSelect v-model="form.area_id" /></UiField>
        <UiField label="Reminder" hint="A push notification if it is still open. Turn notifications on in Settings.">
          <input v-model="form.reminder_time" type="time" />
        </UiField>
      </div>

      <label v-if="tracker" class="check"><input v-model="form.active" type="checkbox" /> Active</label>
      <p v-if="localError || error" class="error">{{ localError || error }}</p>

      <div class="actions">
        <UiButton :disabled="busy" @click="emit('close')">Cancel</UiButton>
        <UiButton type="submit" variant="primary" :loading="busy">{{ tracker ? 'Save' : 'Add habit' }}</UiButton>
      </div>
    </form>
  </UiModal>
</template>

<style scoped>
.editor { display: flex; flex-direction: column; gap: var(--sp-5); }
.editor :deep(.seg) { display: flex; width: 100%; }
.editor :deep(.seg-item) { flex: 1; white-space: nowrap; padding-left: 6px; padding-right: 6px; }
.label { font-size: var(--fs-xs); font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink-3); padding: 0; margin-bottom: 8px; }
.icons { display: grid; grid-template-columns: repeat(auto-fill, minmax(40px, 1fr)); gap: 6px; }
.ic { height: 40px; border: 1px solid var(--line); border-radius: var(--r-md); background: var(--surface); color: var(--ink-2); display: inline-grid; place-items: center; transition: background-color var(--dur-hover) ease, color var(--dur-hover) ease, border-color var(--dur-hover) ease; }
.ic.on { background: var(--brand-soft); color: var(--brand); border-color: color-mix(in srgb, var(--brand) 40%, transparent); }
@media (hover: hover) and (pointer: fine) { .ic:not(.on):hover { background: var(--surface-2); color: var(--ink); } }
.grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--sp-4); }
.grid .span { grid-column: 1 / -1; }
@media (max-width: 480px) { .grid { grid-template-columns: minmax(0, 1fr); } }
.days { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 6px; margin-top: var(--sp-3); }
.day { height: 38px; border: 1px solid var(--line-2); border-radius: var(--r-md); background: var(--surface); color: var(--ink-2); font-size: var(--fs-sm); font-weight: 600; }
.day.on { background: var(--ink); color: var(--on-ink); border-color: var(--ink); }
.every { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin-top: var(--sp-3); font-size: var(--fs-md); color: var(--ink-2); }
.every .n { width: 72px; }
.hint { margin: 8px 0 0; }
.check { display: flex; align-items: center; gap: 8px; font-size: var(--fs-base); }
.actions { display: flex; justify-content: flex-end; gap: var(--sp-2); }
</style>

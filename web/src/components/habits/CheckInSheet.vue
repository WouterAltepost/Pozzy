<script setup>
// Check-in for one habit on one day: done, not done or skipped, the exact value for counts and
// numbers, and a note. Replaces the old window.prompt. Saving writes value, status and note in
// one call; Clear removes the day's entry.
import { computed, reactive, watch } from 'vue'
import { PhArrowRight, PhMinus, PhPlus } from '@phosphor-icons/vue'
import UiButton from '../ui/UiButton.vue'
import UiField from '../ui/UiField.vue'
import UiModal from '../ui/UiModal.vue'
import UiSegmented from '../ui/UiSegmented.vue'
import HabitIcon from './HabitIcon.vue'
import { formatDay } from '../../lib/dates'
import { cellOf, fmt, isBool, isCount, scheduleLabel, targetLabel, unitOf } from '../../lib/habits'

const props = defineProps({
  open: { type: Boolean, default: false },
  tracker: { type: Object, default: null },
  day: { type: String, default: '' },
  busy: { type: Boolean, default: false },
})
const emit = defineEmits(['save', 'clear', 'close'])

const form = reactive({ status: 'none', value: null, note: '' })
const cell = computed(() => (props.tracker ? cellOf(props.tracker, props.day) : null))
const bool = computed(() => isBool(props.tracker))
const step = computed(() => {
  const t = props.tracker
  if (!t || isCount(t)) return 1
  return t.type === 'duration' ? 5 : 1
})

watch(
  () => [props.open, props.tracker?.id, props.day],
  () => {
    if (!props.open || !props.tracker) return
    const c = cell.value
    form.note = c?.note || ''
    if (c?.status === 'skipped') form.status = 'skipped'
    else if (c?.value || !bool.value) form.status = 'done' // a value habit opens on Log, the number field ready
    else form.status = 'none'
    form.value = c?.status === 'skipped' ? null : c?.value ?? null
  },
  { immediate: true },
)

const options = computed(() =>
  bool.value
    ? [{ value: 'done', label: 'Done' }, { value: 'none', label: 'Not done' }, { value: 'skipped', label: 'Skip' }]
    : [{ value: 'done', label: 'Log' }, { value: 'skipped', label: 'Skip' }],
)

function bump(dir) {
  const next = Math.max(0, Math.round(((Number(form.value) || 0) + dir * step.value) * 100) / 100)
  form.value = next
}

const title = computed(() => props.tracker?.name || '')
const dayLabel = computed(() => formatDay(props.day))
const hasEntry = computed(() => Boolean(cell.value && (cell.value.value !== null || cell.value.status)))

function save() {
  const note = form.note.trim()
  if (form.status === 'skipped') return emit('save', { status: 'skipped', value: 0, note })
  if (bool.value) {
    if (form.status === 'none') {
      // Not done with a note keeps the note on a 0 entry; without one the day is cleared.
      return note ? emit('save', { status: 'done', value: 0, note }) : emit('clear')
    }
    return emit('save', { status: 'done', value: 1, note })
  }
  const value = Number(form.value)
  if (!form.value && form.value !== 0) return note ? emit('save', { status: 'done', value: 0, note }) : emit('clear')
  if (Number.isNaN(value) || value < 0) return
  emit('save', { status: 'done', value, note })
}
</script>

<template>
  <UiModal :open="open" :title="title" size="sm" @close="emit('close')">
    <form v-if="tracker" class="checkin" @submit.prevent="save">
      <div class="head">
        <HabitIcon :tracker="tracker" :size="44" :done="form.status === 'done' && (bool ? true : Boolean(form.value))" />
        <div class="head-text">
          <span class="eyebrow">{{ dayLabel }}</span>
          <span class="muted small">{{ scheduleLabel(tracker) }}<template v-if="targetLabel(tracker)"> · {{ targetLabel(tracker) }}</template></span>
        </div>
      </div>

      <UiSegmented v-model="form.status" :options="options" />

      <div v-if="!bool && form.status === 'done'" class="stepper">
        <button type="button" class="step" aria-label="Less" @click="bump(-1)"><PhMinus weight="bold" /></button>
        <label class="value">
          <input v-model.number="form.value" type="number" inputmode="decimal" min="0" step="any" :aria-label="`${tracker.name} value`" placeholder="0" />
          <span class="unit">{{ isCount(tracker) ? 'times' : unitOf(tracker) }}</span>
        </label>
        <button type="button" class="step" aria-label="More" @click="bump(1)"><PhPlus weight="bold" /></button>
      </div>
      <p v-if="!bool && form.status === 'done' && tracker.target_value" class="muted small target">Goal {{ fmt(tracker.target_value) }} {{ isCount(tracker) ? '' : unitOf(tracker) }} per {{ tracker.target_period }}</p>
      <p v-if="form.status === 'skipped'" class="muted small">A skipped day does not count and does not break the streak. Use it for illness, travel or a planned rest day.</p>

      <UiField label="Note">
        <textarea v-model="form.note" rows="2" maxlength="2000" placeholder="How did it go?"></textarea>
      </UiField>

      <div class="actions">
        <RouterLink :to="{ name: 'habit', params: { id: tracker.id } }" class="stats-link" @click="emit('close')">Stats <PhArrowRight /></RouterLink>
        <span class="spacer"></span>
        <UiButton v-if="hasEntry" variant="ghost" :disabled="busy" @click="emit('clear')">Clear</UiButton>
        <UiButton type="submit" variant="primary" :loading="busy">Save</UiButton>
      </div>
    </form>
  </UiModal>
</template>

<style scoped>
.checkin { display: flex; flex-direction: column; gap: var(--sp-4); }
.checkin :deep(.seg) { display: flex; width: 100%; }
.checkin :deep(.seg-item) { flex: 1; white-space: nowrap; }
.head { display: flex; align-items: center; gap: var(--sp-3); }
.head-text { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.stepper { display: flex; align-items: center; justify-content: center; gap: var(--sp-4); padding: var(--sp-2) 0; }
.step { width: 48px; height: 48px; border-radius: 50%; border: 1px solid var(--line-2); background: var(--surface); color: var(--ink); display: inline-grid; place-items: center; box-shadow: inset 0 1px 0 var(--edge), 0 1px 2px rgb(14 17 32 / 0.06); transition: transform var(--dur-press) var(--ease-out); }
.step:active { transform: scale(0.92); }
.step :deep(svg) { width: 18px; height: 18px; }
.value { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.value input { width: 120px; height: 56px; text-align: center; font-size: var(--fs-3xl); font-weight: 600; letter-spacing: -0.02em; font-variant-numeric: tabular-nums; border: 0; box-shadow: none; background: transparent; -moz-appearance: textfield; }
.value input::-webkit-outer-spin-button, .value input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
.value input:focus-visible { box-shadow: 0 0 0 3px var(--brand-soft); border-radius: var(--r-md); }
.unit { font-size: var(--fs-sm); color: var(--ink-3); }
.target { text-align: center; margin-top: calc(var(--sp-2) * -1); }
.actions { display: flex; align-items: center; gap: var(--sp-2); }
.stats-link { display: inline-flex; align-items: center; gap: 4px; font-size: var(--fs-md); font-weight: 500; }
.stats-link :deep(svg) { width: 14px; height: 14px; }
</style>

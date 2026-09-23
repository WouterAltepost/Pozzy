<script setup>
// Small popover next to a selected slot: title, day, times, calendar, Create. "More" hands
// the same values to the full form in the side panel. Positioned by the parent inside the grid.
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { PhX } from '@phosphor-icons/vue'
import UiButton from '../ui/UiButton.vue'
import UiField from '../ui/UiField.vue'

const props = defineProps({
  defaults: { type: Object, required: true }, // { day, hour, minute, endHour, endMinute, anchor }
  calendars: { type: Array, default: () => [] },
  defaultCalendarUrl: { type: String, default: '' },
  saving: { type: Boolean, default: false },
  error: { type: String, default: '' },
})
const emit = defineEmits(['save', 'more', 'close'])

const root = ref(null)
const titleInput = ref(null)
const form = reactive({ title: '', day: '', startTime: '', endTime: '', calendar_url: '' })

function pad(n) {
  return String(n).padStart(2, '0')
}
function reset() {
  const d = props.defaults
  form.title = ''
  form.day = d.day
  form.startTime = `${pad(d.hour ?? 9)}:${pad(d.minute ?? 0)}`
  const end = d.endHour != null ? d.endHour * 60 + (d.endMinute ?? 0) : (d.hour ?? 9) * 60 + (d.minute ?? 0) + 60
  form.endTime = `${pad(Math.min(23, Math.floor(end / 60)))}:${pad(end % 60)}`
  form.calendar_url = props.defaultCalendarUrl
}
watch(() => props.defaults, reset, { immediate: true })

// Place beside the selection: to the right of the column when there is room, else to the left,
// and never below the bottom of the grid.
const WIDTH = 340
const popHeight = ref(250)
const style = computed(() => {
  const a = props.defaults.anchor
  if (!a) return { left: '8px', top: '8px' }
  const fitsRight = a.right + 8 + WIDTH <= a.gridWidth
  const left = fitsRight ? a.right + 8 : Math.max(4, a.left - 8 - WIDTH)
  const maxTop = Math.max(4, (a.gridHeight || Infinity) - popHeight.value - 8)
  return { left: `${left}px`, top: `${Math.min(Math.max(4, a.top - 8), maxTop)}px`, width: `${WIDTH}px` }
})

// The popover grows out of the slot: origin on the side that faces it.
const origin = computed(() => {
  const a = props.defaults.anchor
  if (!a) return 'top left'
  return a.right + 8 + WIDTH <= a.gridWidth ? 'top left' : 'top right'
})

function iso(day, time) {
  const [y, m, d] = day.split('-').map(Number)
  const [hh, mm] = time.split(':').map(Number)
  return new Date(y, m - 1, d, hh, mm).toISOString()
}
function submit() {
  if (!form.title.trim()) return
  const body = { title: form.title.trim(), all_day: false, start: iso(form.day, form.startTime), end: iso(form.day, form.endTime) }
  if (form.calendar_url) body.calendar_url = form.calendar_url
  emit('save', body)
}
function more() {
  const [sh, sm] = form.startTime.split(':').map(Number)
  const [eh, em] = form.endTime.split(':').map(Number)
  emit('more', { day: form.day, hour: sh, minute: sm, endHour: eh, endMinute: em, title: form.title })
}

function onDocPointer(e) {
  if (root.value && !root.value.contains(e.target)) emit('close')
}
function onKey(e) {
  if (e.key === 'Escape') emit('close')
}
onMounted(() => {
  // Defer so the pointerup that opened us does not close us.
  setTimeout(() => document.addEventListener('pointerdown', onDocPointer), 0)
  document.addEventListener('keydown', onKey)
  titleInput.value?.focus({ preventScroll: true })
  if (root.value) popHeight.value = root.value.offsetHeight
})
onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onDocPointer)
  document.removeEventListener('keydown', onKey)
})
</script>

<template>
  <form ref="root" class="pop" :style="[style, { transformOrigin: origin }]" role="dialog" aria-label="New event" @submit.prevent="submit">
    <div class="head">
      <strong>New event</strong>
      <button type="button" class="icon-btn" aria-label="Close" @click="emit('close')"><PhX :size="16" /></button>
    </div>
    <fieldset :disabled="saving" class="fields">
      <input ref="titleInput" v-model="form.title" type="text" placeholder="Title" required maxlength="500" aria-label="Title" />
      <div class="row">
        <input v-model="form.day" type="date" required aria-label="Day" />
        <input v-model="form.startTime" type="time" required aria-label="Start" />
        <span class="muted">to</span>
        <input v-model="form.endTime" type="time" required aria-label="End" />
      </div>
      <UiField v-if="calendars.length > 1" label="Calendar">
        <select v-model="form.calendar_url">
          <option v-for="c in calendars" :key="c.url" :value="c.url">{{ c.name }}</option>
        </select>
      </UiField>
    </fieldset>
    <p v-if="error" class="error">{{ error }}</p>
    <div class="actions">
      <UiButton type="submit" variant="primary" size="sm" :loading="saving">Create</UiButton>
      <button type="button" class="link-btn" @click="more">More options</button>
    </div>
  </form>
</template>

<style scoped>
.pop {
  position: absolute;
  z-index: var(--z-sticky);
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  padding: var(--sp-3);
  background: color-mix(in srgb, var(--surface) 88%, transparent);
  -webkit-backdrop-filter: blur(20px) saturate(150%);
  backdrop-filter: blur(20px) saturate(150%);
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-3);
  font-size: var(--fs-md);
  transform-origin: top left;
}
@media (prefers-reduced-transparency: reduce) { .pop { background: var(--surface); -webkit-backdrop-filter: none; backdrop-filter: none; } }
.head { display: flex; align-items: center; justify-content: space-between; }
.fields { display: flex; flex-direction: column; gap: var(--sp-2); border: 0; padding: 0; margin: 0; min-width: 0; }
.fields input[type='text'] { width: 100%; }
.row { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr) auto minmax(0, 1fr); gap: 6px; align-items: center; }
.row input { min-width: 0; width: 100%; padding-left: 6px; padding-right: 4px; }
.actions { display: flex; align-items: center; gap: var(--sp-3); }
</style>

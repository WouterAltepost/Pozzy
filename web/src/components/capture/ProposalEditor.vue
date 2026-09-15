<script setup>
import { onMounted, reactive, watch } from 'vue'
import { useAreasStore } from '../../stores/areas'
import UiBadge from '../ui/UiBadge.vue'
import UiButton from '../ui/UiButton.vue'
import UiField from '../ui/UiField.vue'

const props = defineProps({ proposal: { type: Object, default: null } })
const emit = defineEmits(['confirm', 'discard'])
const areas = useAreasStore()
onMounted(() => areas.load())

const TYPES = ['task', 'event', 'goal', 'note', 'tracker']
const form = reactive({ type: 'task', fields: {} })

const DEFAULTS = {
  task: { title: '', description: '', area: null, tags: [], urgent: false, important: false, due_date: null, estimated_minutes: null },
  event: { title: '', start: '', end: '', area: null, description: '' },
  goal: { title: '', area: null, target_value: null, week: 'this' },
  note: { title: '', body: '', area: null, tags: [] },
  tracker: { tracker: '', date: null, value: 1, note: '' },
}

function reset() {
  const p = props.proposal
  form.type = p?.type || 'task'
  form.fields = { ...DEFAULTS[form.type], ...(p?.fields || {}) }
  if (form.type === 'event') {
    form.fields.start = toLocalInput(form.fields.start)
    form.fields.end = toLocalInput(form.fields.end)
  }
  form.fields.tagsText = (form.fields.tags || []).join(', ')
}

function switchType(t) {
  form.type = t
  const title = form.fields.title || form.fields.tracker || ''
  form.fields = { ...DEFAULTS[t], title, tagsText: '' }
}

// ISO with offset -> value for <input type="datetime-local"> (local wall time).
function toLocalInput(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function fromLocalInput(v) {
  if (!v) return null
  return new Date(v).toISOString()
}

function submit() {
  const f = { ...form.fields }
  if ('tagsText' in f) {
    f.tags = f.tagsText.split(',').map((t) => t.trim()).filter(Boolean)
    delete f.tagsText
  }
  for (const k of Object.keys(f)) if (f[k] === '') f[k] = null
  if (form.type === 'event') {
    f.start = fromLocalInput(form.fields.start)
    f.end = fromLocalInput(form.fields.end)
  }
  if (form.type === 'task' && f.estimated_minutes != null) f.estimated_minutes = Number(f.estimated_minutes)
  if (form.type === 'goal' && f.target_value != null) f.target_value = Number(f.target_value)
  if (form.type === 'tracker') f.value = Number(f.value ?? 1)
  emit('confirm', { type: form.type, fields: f })
}

watch(() => props.proposal, reset, { immediate: true })
</script>

<template>
  <form class="proposal" @submit.prevent="submit">
    <div class="types" role="radiogroup" aria-label="Type">
      <label v-for="t in TYPES" :key="t" class="type" :class="{ on: form.type === t }">
        <input type="radio" name="capture-type" :value="t" :checked="form.type === t" @change="switchType(t)" />
        {{ t }}
      </label>
      <UiBadge v-if="proposal?.reason" tone="neutral" class="reason" :title="proposal.reason">{{ proposal.source === 'claude' ? 'Claude' : 'Rules' }}</UiBadge>
      <span v-if="proposal?.reason" class="muted small reason-text">{{ proposal.reason }}</span>
    </div>

    <template v-if="form.type === 'tracker'">
      <UiField label="Tracker"><input v-model="form.fields.tracker" type="text" required /></UiField>
      <div class="row">
        <UiField label="Date"><input v-model="form.fields.date" type="date" /></UiField>
        <UiField label="Value"><input v-model="form.fields.value" type="number" step="any" class="narrow" /></UiField>
        <UiField label="Note" class="grow"><input v-model="form.fields.note" type="text" /></UiField>
      </div>
    </template>
    <template v-else>
      <UiField label="Title"><input v-model="form.fields.title" type="text" required maxlength="200" /></UiField>
      <div class="row">
        <UiField label="Area">
          <select v-model="form.fields.area">
            <option :value="null">No area</option>
            <option v-for="a in areas.items" :key="a.id" :value="a.name">{{ a.name }}</option>
          </select>
        </UiField>
        <template v-if="form.type === 'task'">
          <UiField label="Due"><input v-model="form.fields.due_date" type="date" /></UiField>
          <UiField label="Minutes"><input v-model="form.fields.estimated_minutes" type="number" min="1" class="narrow" /></UiField>
          <label class="check"><input v-model="form.fields.urgent" type="checkbox" /> Urgent</label>
          <label class="check"><input v-model="form.fields.important" type="checkbox" /> Important</label>
        </template>
        <template v-if="form.type === 'event'">
          <UiField label="Start"><input v-model="form.fields.start" type="datetime-local" required /></UiField>
          <UiField label="End"><input v-model="form.fields.end" type="datetime-local" /></UiField>
        </template>
        <template v-if="form.type === 'goal'">
          <UiField label="Target"><input v-model="form.fields.target_value" type="number" step="any" min="0" class="narrow" /></UiField>
          <UiField label="Week"><select v-model="form.fields.week"><option value="this">this week</option><option value="next">next week</option></select></UiField>
        </template>
      </div>
      <UiField v-if="form.type === 'task' || form.type === 'note'" label="Tags" hint="Comma separated"><input v-model="form.fields.tagsText" type="text" /></UiField>
      <UiField v-if="form.type === 'note'" label="Body" hint="Markdown"><textarea v-model="form.fields.body" rows="4"></textarea></UiField>
      <UiField v-else-if="form.type !== 'goal'" label="Description"><textarea v-model="form.fields.description" rows="2"></textarea></UiField>
    </template>

    <div class="actions">
      <UiButton type="submit" variant="primary">Confirm</UiButton>
      <UiButton variant="danger" class="push" @click="emit('discard')">Discard</UiButton>
    </div>
  </form>
</template>

<style scoped>
.proposal { display: flex; flex-direction: column; gap: var(--sp-3); }
.types { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.type { display: inline-flex; align-items: center; height: 28px; padding: 0 12px; border: 1px solid var(--line-2); border-radius: var(--r-pill); font-size: var(--fs-md); font-weight: 500; color: var(--ink-2); cursor: pointer; text-transform: capitalize; transition: background-color var(--dur-hover) ease, color var(--dur-hover) ease, border-color var(--dur-hover) ease; }
.type.on { background: var(--ink); color: var(--on-ink); border-color: var(--ink); }
.type input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.type:has(input:focus-visible) { outline: 2px solid var(--brand); outline-offset: 2px; }
.reason { margin-left: var(--sp-2); }
.reason-text { flex-basis: 100%; }
.row { display: flex; flex-wrap: wrap; gap: var(--sp-3); align-items: end; }
.grow { flex: 1 1 140px; }
.narrow { width: 90px; }
.check { display: flex; align-items: center; gap: 6px; height: var(--control-h); }
.actions { display: flex; gap: var(--sp-2); }
.push { margin-left: auto; }
</style>

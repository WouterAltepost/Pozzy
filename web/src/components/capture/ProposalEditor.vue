<script setup>
import { onMounted, reactive, watch } from 'vue'
import { useAreasStore } from '../../stores/areas'

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
    <div class="row types">
      <label v-for="t in TYPES" :key="t" :class="{ on: form.type === t }"><input type="radio" :value="t" :checked="form.type === t" @change="switchType(t)" /> {{ t }}</label>
      <span v-if="proposal?.reason" class="muted small">{{ proposal.source === 'claude' ? 'Claude' : 'Rules' }}: {{ proposal.reason }}</span>
    </div>

    <template v-if="form.type === 'tracker'">
      <input v-model="form.fields.tracker" type="text" placeholder="Tracker name" required />
      <div class="row">
        <input v-model="form.fields.date" type="date" />
        <input v-model="form.fields.value" type="number" step="any" placeholder="Value" />
        <input v-model="form.fields.note" type="text" placeholder="Note" />
      </div>
    </template>
    <template v-else>
      <input v-model="form.fields.title" type="text" placeholder="Title" required maxlength="200" />
      <div class="row">
        <select v-model="form.fields.area">
          <option :value="null">No area</option>
          <option v-for="a in areas.items" :key="a.id" :value="a.name">{{ a.name }}</option>
        </select>
        <template v-if="form.type === 'task'">
          <input v-model="form.fields.due_date" type="date" title="Due date" />
          <input v-model="form.fields.estimated_minutes" type="number" min="1" placeholder="min" class="narrow" />
          <label class="check"><input v-model="form.fields.urgent" type="checkbox" /> urgent</label>
          <label class="check"><input v-model="form.fields.important" type="checkbox" /> important</label>
        </template>
        <template v-if="form.type === 'event'">
          <input v-model="form.fields.start" type="datetime-local" required />
          <input v-model="form.fields.end" type="datetime-local" />
        </template>
        <template v-if="form.type === 'goal'">
          <input v-model="form.fields.target_value" type="number" step="any" min="0" placeholder="target" class="narrow" />
          <select v-model="form.fields.week"><option value="this">this week</option><option value="next">next week</option></select>
        </template>
      </div>
      <input v-if="form.type === 'task' || form.type === 'note'" v-model="form.fields.tagsText" type="text" placeholder="tags, comma separated" />
      <textarea v-if="form.type === 'note'" v-model="form.fields.body" rows="4" placeholder="Body (markdown)"></textarea>
      <textarea v-else-if="form.type !== 'goal'" v-model="form.fields.description" rows="2" placeholder="Description"></textarea>
    </template>

    <div class="row actions">
      <button type="submit">Confirm</button>
      <button type="button" class="danger" @click="emit('discard')">Discard</button>
    </div>
  </form>
</template>

<style scoped>
.proposal { display: flex; flex-direction: column; gap: 0.45rem; }
.row { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }
.types label { font-size: 0.85rem; padding: 0.1rem 0.4rem; border: 1px solid #e5e7eb; border-radius: 3px; cursor: pointer; }
.types label.on { border-color: #2563eb; background: #eff6ff; }
.types input { display: none; }
.small { font-size: 0.78rem; }
input[type='text'], input[type='date'], input[type='datetime-local'], input[type='number'], select, textarea { font: inherit; padding: 0.35rem; border: 1px solid #d1d5db; border-radius: 4px; }
input[type='text'], textarea { width: 100%; }
.narrow { width: 5rem; }
.check { display: flex; align-items: center; gap: 0.3rem; font-size: 0.85rem; }
.danger { color: #b91c1c; }
</style>

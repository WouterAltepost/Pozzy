<script setup>
import { onMounted, reactive, watch } from 'vue'
import { useAreasStore } from '../../stores/areas'
import UiBadge from '../ui/UiBadge.vue'
import UiButton from '../ui/UiButton.vue'
import UiField from '../ui/UiField.vue'
import UiSegmented from '../ui/UiSegmented.vue'

// `ios`: the phone layout in the capture sheet. The type is a segmented control and the fields
// are grouped form rows (label left, value right), like a new event in Calendar.
const props = defineProps({ proposal: { type: Object, default: null }, busy: { type: Boolean, default: false }, ios: { type: Boolean, default: false } })
const emit = defineEmits(['confirm', 'discard'])
const areas = useAreasStore()
onMounted(() => areas.load())

const TYPES = ['task', 'event', 'goal', 'note', 'tracker']
const TYPE_OPTIONS = TYPES.map((t) => ({ value: t, label: t[0].toUpperCase() + t.slice(1) }))
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
  <form v-if="ios" class="iprop" @submit.prevent="submit">
    <UiSegmented :model-value="form.type" :options="TYPE_OPTIONS" class="iseg" @update:model-value="(t) => t !== form.type && switchType(t)" />
    <p v-if="proposal?.reason" class="ireason">{{ proposal.source === 'claude' ? 'Claude' : 'Rules' }}: {{ proposal.reason }}</p>

    <div v-if="form.type === 'tracker'" class="grp">
      <label class="frow"><span class="flabel">Tracker</span><input v-model="form.fields.tracker" type="text" class="fval" required /></label>
      <label class="frow"><span class="flabel">Date</span><input v-model="form.fields.date" type="date" class="fval" /></label>
      <label class="frow"><span class="flabel">Value</span><input v-model="form.fields.value" type="number" step="any" inputmode="decimal" class="fval" /></label>
      <label class="frow"><span class="flabel">Note</span><input v-model="form.fields.note" type="text" class="fval" placeholder="None" /></label>
    </div>
    <template v-else>
      <div class="grp">
        <label class="frow"><input v-model="form.fields.title" type="text" class="fin" placeholder="Title" aria-label="Title" required maxlength="200" /></label>
        <label class="frow">
          <span class="flabel">Area</span>
          <select v-model="form.fields.area" class="fval">
            <option :value="null">None</option>
            <option v-for="a in areas.items" :key="a.id" :value="a.name">{{ a.name }}</option>
          </select>
        </label>
      </div>
      <div v-if="form.type === 'task'" class="grp">
        <label class="frow"><span class="flabel">Due</span><input v-model="form.fields.due_date" type="date" class="fval" /></label>
        <label class="frow"><span class="flabel">Minutes</span><input v-model="form.fields.estimated_minutes" type="number" min="1" inputmode="numeric" class="fval" placeholder="None" /></label>
        <label class="frow"><span class="flabel">Urgent</span><input v-model="form.fields.urgent" type="checkbox" role="switch" /></label>
        <label class="frow"><span class="flabel">Important</span><input v-model="form.fields.important" type="checkbox" role="switch" /></label>
      </div>
      <div v-if="form.type === 'event'" class="grp">
        <label class="frow"><span class="flabel">Starts</span><input v-model="form.fields.start" type="datetime-local" class="fval" required /></label>
        <label class="frow"><span class="flabel">Ends</span><input v-model="form.fields.end" type="datetime-local" class="fval" /></label>
      </div>
      <div v-if="form.type === 'goal'" class="grp">
        <label class="frow"><span class="flabel">Target</span><input v-model="form.fields.target_value" type="number" step="any" min="0" inputmode="decimal" class="fval" placeholder="None" /></label>
        <label class="frow">
          <span class="flabel">Week</span>
          <select v-model="form.fields.week" class="fval"><option value="this">This week</option><option value="next">Next week</option></select>
        </label>
      </div>
      <div v-if="form.type === 'task' || form.type === 'note'" class="grp">
        <label class="frow"><span class="flabel">Tags</span><input v-model="form.fields.tagsText" type="text" class="fval" placeholder="Comma separated" /></label>
      </div>
      <div v-if="form.type === 'note'" class="grp"><textarea v-model="form.fields.body" rows="5" class="farea" placeholder="Body (markdown)" aria-label="Body"></textarea></div>
      <div v-else-if="form.type !== 'goal'" class="grp"><textarea v-model="form.fields.description" rows="3" class="farea" placeholder="Description" aria-label="Description"></textarea></div>
    </template>

    <UiButton type="submit" variant="primary" block :loading="busy" class="iconfirm">Confirm</UiButton>
    <button type="button" class="idiscard" :disabled="busy" @click="emit('discard')">Discard</button>
  </form>
  <form v-else class="proposal" @submit.prevent="submit">
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
      <UiButton type="submit" variant="primary" :loading="busy">Confirm</UiButton>
      <UiButton variant="danger" class="push" :disabled="busy" @click="emit('discard')">Discard</UiButton>
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
/* Phone: grouped form rows in the sheet. */
.iprop { display: flex; flex-direction: column; gap: var(--sp-4); }
.iseg { display: flex; width: 100%; }
.iseg :deep(.seg-item) { flex: 1; padding-left: 0; padding-right: 0; }
.ireason { margin: calc(var(--sp-2) * -1) 4px 0; font-size: var(--fs-sm); color: var(--ink-3); }
.grp { background: var(--surface-2); border-radius: var(--r-lg); overflow: hidden; }
.frow { position: relative; display: flex; align-items: center; gap: var(--sp-3); min-height: 44px; padding: 0 16px; font-size: 1.0625rem; }
.frow + .frow::before { content: ''; position: absolute; top: 0; left: 16px; right: 0; height: 0.5px; background: var(--line-2); }
.flabel { flex: 1 0 auto; }
.frow .fin, .frow .fval, .grp .farea { border: 0; background-color: transparent; box-shadow: none; }
.frow .fin { flex: 1; min-width: 0; height: 44px; padding: 0; }
.frow .fval { flex: 1 1 0; min-width: 0; height: 44px; padding: 0; color: var(--ink-3); text-align: right; text-align-last: right; }
.frow select.fval { padding-right: 22px; background-position: right 2px center; }
.frow input[type='date'].fval, .frow input[type='datetime-local'].fval { color: var(--brand); }
.grp .farea { display: block; width: 100%; padding: 11px 16px; resize: vertical; line-height: 1.4; }
.frow .fin:focus-visible, .frow .fval:focus-visible, .grp .farea:focus-visible { box-shadow: none; }
.iconfirm { height: 50px; font-size: 1.0625rem; margin-top: var(--sp-2); }
.idiscard { height: 44px; border: 0; background: none; box-shadow: none; color: var(--danger); font: inherit; font-size: 1.0625rem; }
.idiscard:disabled { opacity: 0.5; }
</style>

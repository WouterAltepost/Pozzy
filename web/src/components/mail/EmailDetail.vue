<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { PhArrowSquareOut, PhCaretRight, PhPaperclip } from '@phosphor-icons/vue'
import { CATEGORIES, PRIORITIES } from '../../api/mail'
import { formatDateTime } from '../../lib/dates'
import { tick } from '../../lib/haptics'
import { accountName } from '../../lib/mail'
import AreaSelect from '../shared/AreaSelect.vue'
import UiBadge from '../ui/UiBadge.vue'
import UiButton from '../ui/UiButton.vue'
import UiField from '../ui/UiField.vue'
import PriorityBadge from './PriorityBadge.vue'

// `ios`: the phone layout inside the sheet. The message reads first (sender, subject, summary,
// text), then the actions and the classification as grouped rows, the way a Mail message
// leads into its toolbar and a Settings form follows.
const props = defineProps({ email: { type: Object, required: true }, busy: { type: Boolean, default: false }, pending: { type: String, default: '' }, ios: { type: Boolean, default: false } })
const emit = defineEmits(['close', 'update', 'task', 'reclassify'])

const overrides = reactive({ priority: '', category: '', area_id: '' })
const taskDue = ref('')
const message = ref('')

watch(
  () => props.email,
  (e) => {
    overrides.priority = e?.overrides?.priority ? String(e.overrides.priority) : ''
    overrides.category = e?.overrides?.category || ''
    overrides.area_id = e?.overrides?.area_id || ''
    message.value = ''
  },
  { immediate: true },
)

const hasOverride = computed(() => overrides.priority || overrides.category || overrides.area_id)
const sender = computed(() => props.email.from_name || props.email.from_email)
const initials = computed(() => {
  const words = (props.email.from_name || props.email.from_email || '?').replace(/[^\p{L}\p{N}\s]/gu, ' ').trim().split(/\s+/)
  return ((words[0]?.[0] || '?') + (words.length > 1 ? words[words.length - 1][0] : '')).toUpperCase()
})

function saveOverrides() {
  emit('update', {
    priority_override: overrides.priority ? Number(overrides.priority) : null,
    category_override: overrides.category || null,
    area_override_id: overrides.area_id || null,
  })
}

function clearOverrides() {
  overrides.priority = ''
  overrides.category = ''
  overrides.area_id = ''
  saveOverrides()
}

function createTask() {
  emit('task', taskDue.value ? { due_date: taskDue.value } : {})
}

function toggleHandled() {
  tick()
  emit('update', { handled: !props.email.handled })
}
</script>

<template>
  <div v-if="ios" class="idetail">
    <div class="ihead">
      <span class="avatar" aria-hidden="true">{{ initials }}</span>
      <div class="who">
        <div class="wl1"><strong class="truncate">{{ sender }}</strong><span class="when num">{{ formatDateTime(email.date) }}</span></div>
        <div v-if="email.from_name" class="addr truncate">{{ email.from_email }}</div>
        <div class="addr truncate">To {{ accountName(email.account) }}</div>
      </div>
    </div>
    <h2 class="isubject">{{ email.subject || '(no subject)' }}</h2>
    <div class="ibadges">
      <PriorityBadge :priority="email.priority" />
      <span class="tag">{{ email.category }}</span>
      <UiBadge v-if="email.needs_reply" tone="info">needs reply</UiBadge>
      <span v-if="email.has_attachments" class="tag att" title="Attachments are not downloaded"><PhPaperclip aria-hidden="true" />attachment</span>
    </div>
    <p v-if="email.summary" class="isummary">{{ email.summary }}</p>
    <div class="itext">{{ email.snippet || '(no text)' }}</div>
    <p class="foot">First 2 KB of the message. Attachments and full bodies are not stored.<template v-if="email.classifier"> Classified by {{ email.classifier }}.</template></p>

    <div class="grp">
      <a v-if="email.gmail_url" :href="email.gmail_url" target="_blank" rel="noopener" class="frow tint pressable"><span class="flabel">Open in Gmail</span><PhArrowSquareOut class="ficon" aria-hidden="true" /></a>
      <label class="frow">
        <span class="flabel">Handled</span>
        <input type="checkbox" role="switch" :checked="email.handled" :disabled="busy" @change="toggleHandled" />
      </label>
      <button type="button" class="frow tint pressable" :disabled="busy" @click="emit('reclassify')"><span class="flabel">{{ pending === 'reclassify' ? 'Reclassifying…' : 'Reclassify' }}</span></button>
    </div>

    <p class="ghead">Task</p>
    <div class="grp">
      <RouterLink v-if="email.task_id" :to="{ name: 'tasks' }" class="frow pressable"><span class="flabel">A task exists for this email</span><PhCaretRight class="chev" weight="bold" aria-hidden="true" /></RouterLink>
      <template v-else>
        <label class="frow">
          <span class="flabel">Due</span>
          <input v-model="taskDue" type="date" class="fval" />
        </label>
        <button type="button" class="frow tint pressable" :disabled="busy" @click="createTask"><span class="flabel">{{ pending === 'task' ? 'Creating…' : 'Create task from email' }}</span></button>
      </template>
    </div>

    <p class="ghead">Classification</p>
    <div class="grp">
      <label class="frow">
        <span class="flabel">Priority</span>
        <select v-model="overrides.priority" class="fval">
          <option value="">Auto ({{ email.raw?.priority ?? 3 }})</option>
          <option v-for="[value, label] in PRIORITIES" :key="value" :value="String(value)">{{ label }}</option>
        </select>
      </label>
      <label class="frow">
        <span class="flabel">Category</span>
        <select v-model="overrides.category" class="fval cap">
          <option value="">Auto ({{ email.raw?.category || 'other' }})</option>
          <option v-for="c in CATEGORIES" :key="c" :value="c">{{ c }}</option>
        </select>
      </label>
      <label class="frow">
        <span class="flabel">Area</span>
        <AreaSelect v-model="overrides.area_id" class="fval" />
      </label>
      <button type="button" class="frow tint pressable" :disabled="busy" @click="saveOverrides"><span class="flabel">{{ pending === 'update' ? 'Saving…' : 'Save classification' }}</span></button>
      <button v-if="hasOverride" type="button" class="frow danger pressable" :disabled="busy" @click="clearOverrides"><span class="flabel">Clear overrides</span></button>
    </div>
    <p class="gfoot">Overrides are kept when the email is classified again.</p>
  </div>

  <div v-else class="detail">
    <div class="card-head">
      <div class="badges">
        <UiBadge :color="email.account?.color || ''">{{ accountName(email.account) }}</UiBadge>
        <span v-if="email.account?.label" class="tag">{{ email.account.label }}</span>
        <PriorityBadge :priority="email.priority" />
        <span class="tag">{{ email.category }}</span>
        <UiBadge v-if="email.needs_reply" tone="info">needs reply</UiBadge>
      </div>
      <span class="meta"><button type="button" class="link-btn" @click="emit('close')">Close</button></span>
    </div>

    <h2 class="subject">{{ email.subject }}</h2>
    <p class="from">
      <strong>{{ email.from_name || email.from_email }}</strong>
      <span v-if="email.from_name" class="muted small">{{ email.from_email }}</span>
      <span class="muted small num">{{ formatDateTime(email.date) }}</span>
      <span v-if="email.has_attachments" class="muted small" title="Attachments are not downloaded">has attachments</span>
      <span v-if="email.classifier" class="muted small">classified by {{ email.classifier }}</span>
    </p>
    <p v-if="email.summary" class="summary">{{ email.summary }}</p>

    <pre class="snippet">{{ email.snippet || '(no text)' }}</pre>
    <p class="muted xs">First 2 KB of the message. Attachments and full bodies are not stored.</p>

    <div class="actions">
      <a v-if="email.gmail_url" :href="email.gmail_url" target="_blank" rel="noopener" class="ext">Open in Gmail</a>
      <UiButton :disabled="busy" :loading="pending === 'update'" @click="emit('update', { handled: !email.handled })">{{ email.handled ? 'Mark unhandled' : 'Mark handled' }}</UiButton>
      <UiButton variant="ghost" :disabled="busy" :loading="pending === 'reclassify'" @click="emit('reclassify')">Reclassify</UiButton>
    </div>

    <div class="block">
      <h3>Create task</h3>
      <p v-if="email.task_id" class="muted small">A task exists for this email. <RouterLink :to="{ name: 'tasks' }">Open tasks</RouterLink></p>
      <div v-else class="row">
        <UiField label="Due"><input v-model="taskDue" type="date" /></UiField>
        <UiButton :disabled="busy" :loading="pending === 'task'" @click="createTask">Create task from email</UiButton>
      </div>
    </div>

    <div class="block">
      <h3>Override classification</h3>
      <div class="row">
        <UiField label="Priority">
          <select v-model="overrides.priority">
            <option value="">auto ({{ email.raw?.priority ?? 3 }})</option>
            <option v-for="[value, label] in PRIORITIES" :key="value" :value="String(value)">{{ label }}</option>
          </select>
        </UiField>
        <UiField label="Category">
          <select v-model="overrides.category">
            <option value="">auto ({{ email.raw?.category || 'other' }})</option>
            <option v-for="c in CATEGORIES" :key="c" :value="c">{{ c }}</option>
          </select>
        </UiField>
        <UiField label="Area"><AreaSelect v-model="overrides.area_id" /></UiField>
        <UiButton :disabled="busy" @click="saveOverrides">Save</UiButton>
        <button v-if="hasOverride" type="button" class="link-btn" :disabled="busy" @click="clearOverrides">Clear</button>
      </div>
      <p class="muted xs">Overrides are kept when the email is classified again.</p>
    </div>
    <p v-if="message" class="muted small">{{ message }}</p>
  </div>
</template>

<style scoped>
.detail { display: flex; flex-direction: column; gap: var(--sp-3); }
.badges { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.subject { font-size: var(--fs-xl); }
.from { display: flex; flex-wrap: wrap; gap: var(--sp-2); align-items: baseline; }
.summary { background: var(--surface-2); border-radius: var(--r-md); padding: var(--sp-2) var(--sp-3); font-size: var(--fs-base); }
.snippet { white-space: pre-wrap; word-break: break-word; max-height: 320px; overflow: auto; font-size: var(--fs-md); margin: 0; }
.actions { display: flex; flex-wrap: wrap; gap: var(--sp-2); align-items: center; }
.ext { display: inline-flex; align-items: center; height: var(--control-h); padding: 0 var(--sp-3); border: 1px solid var(--line-2); border-radius: var(--r-md); background: var(--surface); color: var(--ink); text-decoration: none; font-weight: 500; transition: background-color var(--dur-hover) ease; }
@media (hover: hover) and (pointer: fine) { .ext:hover { background: var(--surface-2); } }
.block { border-top: 1px solid var(--line); padding-top: var(--sp-3); }
.block h3 { font-size: var(--fs-base); margin-bottom: var(--sp-2); }
.row { display: flex; flex-wrap: wrap; gap: var(--sp-2); align-items: end; }

/* Phone: the message, then grouped rows. */
.idetail { display: flex; flex-direction: column; }
.ihead { display: flex; align-items: flex-start; gap: 12px; }
.avatar { flex: none; display: grid; place-items: center; width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(180deg, #A5A9B3, #858993); color: #fff; font-size: 0.9375rem; font-weight: 600; letter-spacing: 0.02em; }
.who { flex: 1; min-width: 0; }
.wl1 { display: flex; align-items: baseline; gap: var(--sp-2); }
.wl1 strong { flex: 1; min-width: 0; font-size: 1.0625rem; font-weight: 600; }
.when { flex: none; font-size: var(--fs-sm); color: var(--ink-3); }
.addr { font-size: var(--fs-md); color: var(--ink-3); }
.isubject { margin: var(--sp-4) 0 var(--sp-2); font-size: 1.375rem; font-weight: 700; line-height: 1.25; letter-spacing: normal; }
.ibadges { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.ibadges .tag { text-transform: capitalize; }
.att { display: inline-flex; align-items: center; gap: 3px; }
.att svg { width: 12px; height: 12px; }
.isummary { margin-top: var(--sp-4); padding: 12px 14px; border-radius: var(--r-lg); background: var(--surface-2); font-size: 0.9375rem; line-height: 1.45; color: var(--ink-2); }
.itext { margin-top: var(--sp-4); padding-top: var(--sp-4); border-top: 0.5px solid var(--line); white-space: pre-wrap; word-break: break-word; font-size: 1.0625rem; line-height: 1.47; }
.foot { margin-top: var(--sp-3); font-size: var(--fs-xs); color: var(--ink-3); }
.grp { margin-top: var(--sp-6); background: var(--surface-2); border-radius: var(--r-lg); overflow: hidden; }
.ghead { margin: var(--sp-6) 16px -18px; font-size: var(--fs-sm); text-transform: uppercase; color: var(--ink-3); }
.gfoot { margin: 6px 16px 0; font-size: var(--fs-sm); color: var(--ink-3); }
.frow { position: relative; display: flex; align-items: center; gap: var(--sp-3); width: 100%; min-height: 44px; padding: 0 16px; border: 0; border-radius: 0; background: none; box-shadow: none; color: var(--ink); font: inherit; font-size: 1.0625rem; text-align: left; text-decoration: none; }
.frow:hover { text-decoration: none; }
.frow + .frow::before { content: ''; position: absolute; top: 0; left: 16px; right: 0; height: 0.5px; background: var(--line-2); }
.frow:disabled { opacity: 0.5; }
.flabel { flex: 1; min-width: 0; }
.tint { color: var(--brand); }
.danger { color: var(--danger); }
.ficon { width: 20px; height: 20px; color: var(--brand); flex: none; }
.chev { width: 13px; height: 13px; color: var(--ink-4); flex: none; }
.fval, .frow :deep(select.fval) { flex: none; width: auto; max-width: 58%; height: 44px; padding: 0 22px 0 8px; border: 0; background-color: transparent; box-shadow: none; color: var(--ink-3); font-size: 1.0625rem; text-align: right; text-align-last: right; background-position: right 2px center; }
.fval.cap { text-transform: capitalize; }
input.fval { padding: 0; color: var(--brand); text-transform: none; }
</style>

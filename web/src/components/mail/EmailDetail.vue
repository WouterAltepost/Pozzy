<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { CATEGORIES, PRIORITIES } from '../../api/mail'
import { formatDateTime } from '../../lib/dates'
import { accountName } from '../../lib/mail'
import AreaSelect from '../shared/AreaSelect.vue'
import UiBadge from '../ui/UiBadge.vue'
import UiButton from '../ui/UiButton.vue'
import UiField from '../ui/UiField.vue'
import PriorityBadge from './PriorityBadge.vue'

const props = defineProps({ email: { type: Object, required: true }, busy: { type: Boolean, default: false }, pending: { type: String, default: '' } })
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
</script>

<template>
  <div class="detail">
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
</style>

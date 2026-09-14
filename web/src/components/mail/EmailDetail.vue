<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { CATEGORIES, PRIORITIES } from '../../api/mail'
import { formatDateTime } from '../../lib/dates'
import AreaSelect from '../shared/AreaSelect.vue'
import PriorityBadge from './PriorityBadge.vue'

const props = defineProps({ email: { type: Object, required: true }, busy: { type: Boolean, default: false } })
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
  <section class="card detail">
    <div class="head">
      <div class="badges">
        <span class="account" :style="{ background: email.account?.color || '#9ca3af' }">{{ email.account?.label }}</span>
        <PriorityBadge :priority="email.priority" />
        <span class="category">{{ email.category }}</span>
        <span v-if="email.needs_reply" class="needs-reply">needs reply</span>
        <span v-if="email.classifier" class="muted small">classified by {{ email.classifier }}</span>
      </div>
      <button type="button" class="link" @click="emit('close')">Close</button>
    </div>

    <h2>{{ email.subject }}</h2>
    <p class="meta">
      <strong>{{ email.from_name || email.from_email }}</strong>
      <span v-if="email.from_name" class="muted">&lt;{{ email.from_email }}&gt;</span>
      <span class="muted">{{ formatDateTime(email.date) }}</span>
      <span v-if="email.has_attachments" class="muted" title="Attachments are not downloaded">has attachments</span>
    </p>
    <p v-if="email.summary" class="summary">{{ email.summary }}</p>

    <pre class="snippet">{{ email.snippet || '(no text)' }}</pre>
    <p class="muted small">First 2 KB of the message. Attachments and full bodies are not stored.</p>

    <div class="actions">
      <a v-if="email.gmail_url" :href="email.gmail_url" target="_blank" rel="noopener">Open in Gmail</a>
      <button type="button" :disabled="busy" @click="emit('update', { handled: !email.handled })">
        {{ email.handled ? 'Mark unhandled' : 'Mark handled' }}
      </button>
      <button type="button" :disabled="busy" @click="emit('reclassify')">Reclassify</button>
    </div>

    <div class="block">
      <h3>Create task</h3>
      <div v-if="email.task_id" class="muted small">
        A task exists for this email. <RouterLink :to="{ name: 'tasks' }">Open tasks</RouterLink>
      </div>
      <div v-else class="row">
        <label class="small">Due <input v-model="taskDue" type="date" /></label>
        <button type="button" :disabled="busy" @click="createTask">Create task from email</button>
      </div>
    </div>

    <div class="block">
      <h3>Override classification</h3>
      <div class="row">
        <select v-model="overrides.priority">
          <option value="">Priority: auto ({{ email.raw?.priority ?? 3 }})</option>
          <option v-for="[value, label] in PRIORITIES" :key="value" :value="String(value)">{{ label }}</option>
        </select>
        <select v-model="overrides.category">
          <option value="">Category: auto ({{ email.raw?.category || 'other' }})</option>
          <option v-for="c in CATEGORIES" :key="c" :value="c">{{ c }}</option>
        </select>
        <AreaSelect v-model="overrides.area_id" />
        <button type="button" :disabled="busy" @click="saveOverrides">Save</button>
        <button v-if="hasOverride" type="button" class="link" :disabled="busy" @click="clearOverrides">Clear</button>
      </div>
      <p class="muted small">Overrides are kept when the email is classified again.</p>
    </div>
    <p v-if="message" class="muted small">{{ message }}</p>
  </section>
</template>

<style scoped>
.detail { position: sticky; top: 1rem; }
.head { display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; }
.badges { display: flex; flex-wrap: wrap; align-items: center; gap: 0.4rem; font-size: 0.78rem; }
.account { color: #fff; padding: 0.05rem 0.4rem; border-radius: 3px; font-weight: 600; }
.category { background: #f3f4f6; padding: 0 0.3rem; border-radius: 3px; }
.needs-reply { background: #dbeafe; color: #1d4ed8; padding: 0 0.3rem; border-radius: 3px; font-weight: 600; }
h2 { font-size: 1.05rem; margin: 0.5rem 0 0.25rem; }
h3 { font-size: 0.85rem; margin: 0 0 0.3rem; color: #374151; }
.meta { display: flex; flex-wrap: wrap; gap: 0.5rem; font-size: 0.85rem; margin: 0 0 0.5rem; }
.summary { font-size: 0.9rem; background: #f9fafb; border-left: 3px solid #d1d5db; padding: 0.3rem 0.6rem; margin: 0 0 0.5rem; }
.snippet { white-space: pre-wrap; word-break: break-word; max-height: 320px; overflow: auto; font-size: 0.85rem; margin: 0; }
.actions { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; margin: 0.5rem 0; }
.actions a { font-size: 0.9rem; }
.block { border-top: 1px solid #e5e7eb; padding-top: 0.6rem; margin-top: 0.6rem; }
.row { display: flex; flex-wrap: wrap; gap: 0.4rem; align-items: center; }
.row select, .row :deep(select), .row input { font: inherit; font-size: 0.85rem; padding: 0.3rem; border: 1px solid #d1d5db; border-radius: 4px; }
.small { font-size: 0.8rem; }
.link { border: none; background: none; color: #2563eb; padding: 0.2rem 0.4rem; }
</style>

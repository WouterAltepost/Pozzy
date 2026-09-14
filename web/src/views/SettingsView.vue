<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { formatDateTime } from '../lib/dates'
import { useAreasStore } from '../stores/areas'
import { useSettingsStore } from '../stores/settings'

import CalendarAccounts from '../components/settings/CalendarAccounts.vue'
import MailAccounts from '../components/settings/MailAccounts.vue'

const store = useSettingsStore()
const areas = useAreasStore()
const saved = ref('')
const form = reactive({ working_days: [], start: '08:00', end: '18:00', timezone: 'Europe/Amsterdam', briefing_time: '07:00', hour_targets: {}, ai_enabled: {}, deadline_urgent_days: 3, default_task_minutes: 60, slot_lookahead_days: 7, three_dos_count: 3 })

const DAYS = [
  [1, 'Mon'], [2, 'Tue'], [3, 'Wed'], [4, 'Thu'], [5, 'Fri'], [6, 'Sat'], [7, 'Sun'],
]
const AI_FEATURES = [
  ['mail_classify', 'Email classification (Haiku)'],
  ['briefing', 'Daily briefing'],
  ['scheduling', 'Slot ranking'],
  ['three_dos', 'Three do suggestions'],
  ['capture', 'Quick capture parsing'],
  ['weekly_review', 'Weekly reflection'],
]

const ready = computed(() => store.values && areas.loaded)

onMounted(async () => {
  await Promise.all([store.load(), areas.load(), store.loadJobRuns()])
  if (!store.values) return
  const v = store.values
  form.working_days = [...(v.working_window?.days || [1, 2, 3, 4, 5])]
  form.start = v.working_window?.start || '08:00'
  form.end = v.working_window?.end || '18:00'
  form.timezone = v.timezone || 'Europe/Amsterdam'
  form.briefing_time = v.briefing_time || '07:00'
  form.deadline_urgent_days = v.deadline_urgent_days ?? 3
  form.default_task_minutes = v.default_task_minutes ?? 60
  form.slot_lookahead_days = v.slot_lookahead_days ?? 7
  form.three_dos_count = v.three_dos_count ?? 3
  form.ai_enabled = { ...(store.defaults?.ai_enabled || {}), ...(v.ai_enabled || {}) }
  form.hour_targets = {}
  for (const a of areas.items) form.hour_targets[a.name] = v.hour_targets?.[a.name] ? Math.round((v.hour_targets[a.name] / 60) * 10) / 10 : null
})

async function save() {
  saved.value = ''
  const hour_targets = {}
  for (const [name, hours] of Object.entries(form.hour_targets)) if (hours) hour_targets[name] = Math.round(Number(hours) * 60)
  try {
    await store.save({
      working_window: { days: [...form.working_days].sort(), start: form.start, end: form.end },
      timezone: form.timezone,
      briefing_time: form.briefing_time,
      hour_targets,
      ai_enabled: form.ai_enabled,
      deadline_urgent_days: Number(form.deadline_urgent_days),
      default_task_minutes: Number(form.default_task_minutes),
      slot_lookahead_days: Number(form.slot_lookahead_days),
      three_dos_count: Number(form.three_dos_count),
    })
    saved.value = 'Saved.'
  } catch {
    // store.error is shown
  }
}
</script>

<template>
  <div class="settings">
    <h1>Settings</h1>
    <p v-if="store.error" class="error">{{ store.error }}</p>
    <p v-if="!ready && !store.error" class="muted">Loading...</p>

    <form v-if="ready" @submit.prevent="save">
      <section class="card">
        <h2>Working window</h2>
        <div class="days">
          <label v-for="[n, name] in DAYS" :key="n"><input v-model="form.working_days" type="checkbox" :value="n" /> {{ name }}</label>
        </div>
        <div class="row">
          <label>Start <input v-model="form.start" type="time" /></label>
          <label>End <input v-model="form.end" type="time" /></label>
          <label>Timezone <input v-model="form.timezone" type="text" /></label>
          <label>Briefing time <input v-model="form.briefing_time" type="time" /></label>
        </div>
      </section>

      <section class="card">
        <h2>Hour targets per week</h2>
        <div class="row">
          <label v-for="a in areas.items" :key="a.id"><span class="dot" :style="{ background: a.color }"></span>{{ a.name }} <input v-model.number="form.hour_targets[a.name]" type="number" min="0" step="0.5" placeholder="hours" /></label>
        </div>
      </section>

      <section class="card">
        <h2>Tasks and planning</h2>
        <div class="row">
          <label>Urgent when due within (days) <input v-model.number="form.deadline_urgent_days" type="number" min="0" max="30" /></label>
          <label>Default task length (min) <input v-model.number="form.default_task_minutes" type="number" min="5" max="480" step="5" /></label>
          <label>Slot lookahead (days) <input v-model.number="form.slot_lookahead_days" type="number" min="1" max="30" /></label>
          <label>Do's per day <input v-model.number="form.three_dos_count" type="number" min="1" max="10" /></label>
        </div>
      </section>

      <section class="card">
        <h2>AI kill switches</h2>
        <p class="muted small">Off means the feature uses its deterministic fallback and makes no Anthropic call.</p>
        <div class="days">
          <label v-for="[key, label] in AI_FEATURES" :key="key"><input v-model="form.ai_enabled[key]" type="checkbox" /> {{ label }}</label>
        </div>
      </section>

      <div class="actions">
        <button type="submit" :disabled="store.saving">Save settings</button>
        <span class="ok">{{ saved }}</span>
      </div>
    </form>

    <section class="card">
      <h2>Integrations</h2>
      <CalendarAccounts />
      <MailAccounts />
    </section>

    <section class="card">
      <div class="row head">
        <h2>Background jobs</h2>
        <button type="button" @click="store.loadJobRuns()">Refresh</button>
      </div>
      <p v-if="!store.jobRuns.length" class="muted">No job runs recorded yet.</p>
      <table v-else class="jobs">
        <thead><tr><th>Job</th><th>Started</th><th>Result</th><th>Message</th></tr></thead>
        <tbody>
          <tr v-for="r in store.jobRuns" :key="r.id">
            <td>{{ r.name }}</td>
            <td class="muted">{{ formatDateTime(r.started_at) }}</td>
            <td><span :class="r.ok === false ? 'error' : r.ok ? 'ok' : 'muted'">{{ r.ok === null ? 'running' : r.ok ? 'ok' : 'failed' }}</span></td>
            <td class="msg">{{ r.message }}</td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<style scoped>
h1 { font-size: 1.3rem; }
h2 { font-size: 1rem; margin: 0 0 0.5rem; }
.row { display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: flex-end; }
.row.head { align-items: center; justify-content: space-between; }
.row label { display: flex; flex-direction: column; gap: 0.2rem; font-size: 0.85rem; color: #4b5563; }
.row input { font: inherit; padding: 0.35rem; border: 1px solid #d1d5db; border-radius: 4px; width: 140px; }
.days { display: flex; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 0.5rem; font-size: 0.9rem; }
.days label { display: flex; align-items: center; gap: 0.3rem; }
.dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 0.3rem; }
.small { font-size: 0.8rem; }
.actions { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; }
.jobs { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.jobs th { text-align: left; font-weight: 500; color: #6b7280; padding: 0.2rem 0.4rem; }
.jobs td { padding: 0.25rem 0.4rem; border-top: 1px solid #f3f4f6; vertical-align: top; }
.msg { word-break: break-word; }
</style>

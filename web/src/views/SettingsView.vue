<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import PageHeader from '../components/ui/PageHeader.vue'
import UiBadge from '../components/ui/UiBadge.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiField from '../components/ui/UiField.vue'
import UiLoadGate from '../components/ui/UiLoadGate.vue'
import { useToast } from '../composables/useToast'
import { formatDateTime } from '../lib/dates'
import { useAreasStore } from '../stores/areas'
import { useSettingsStore } from '../stores/settings'

import CalendarAccounts from '../components/settings/CalendarAccounts.vue'
import MailAccounts from '../components/settings/MailAccounts.vue'

const store = useSettingsStore()
const areas = useAreasStore()
const toast = useToast()
const form = reactive({ working_days: [], start: '08:00', end: '18:00', timezone: 'Europe/Amsterdam', briefing_time: '07:00', hour_targets: {}, ai_enabled: {}, deadline_urgent_days: 3, default_task_minutes: 60, slot_lookahead_days: 7, three_dos_count: 3, ai_rules: '', ai_context: '' })

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
const allJobs = ref(false)
const jobRows = computed(() => (allJobs.value ? store.jobRuns : store.jobRuns.slice(0, 8)))

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
  form.ai_rules = (v.ai_rules || []).join('\n')
  form.ai_context = v.ai_context || ''
  form.hour_targets = {}
  for (const a of areas.items) form.hour_targets[a.name] = v.hour_targets?.[a.name] ? Math.round((v.hour_targets[a.name] / 60) * 10) / 10 : null
})

async function save() {
  const hour_targets = {}
  for (const [name, hours] of Object.entries(form.hour_targets)) if (hours) hour_targets[name] = Math.round(Number(hours) * 60)
  try {
    await store.save({
      working_window: { days: [...form.working_days].sort(), start: form.start, end: form.end },
      timezone: form.timezone,
      briefing_time: form.briefing_time,
      hour_targets,
      ai_enabled: form.ai_enabled,
      ai_rules: form.ai_rules.split('\n').map((r) => r.trim()).filter(Boolean),
      ai_context: form.ai_context.trim(),
      deadline_urgent_days: Number(form.deadline_urgent_days),
      default_task_minutes: Number(form.default_task_minutes),
      slot_lookahead_days: Number(form.slot_lookahead_days),
      three_dos_count: Number(form.three_dos_count),
    })
    toast.success('Settings saved.')
  } catch {
    // store.error is shown
  }
}
</script>

<template>
  <div class="settings">
    <PageHeader title="Settings" />
    <p v-if="store.error" class="error">{{ store.error }}</p>
    <UiLoadGate :ready="Boolean(ready) || Boolean(store.error)" label="Loading settings">

    <form v-if="ready" @submit.prevent="save">
      <section class="card">
        <div class="card-head"><h2>Working window</h2></div>
        <div class="days">
          <label v-for="[n, name] in DAYS" :key="n" class="check"><input v-model="form.working_days" type="checkbox" :value="n" /> {{ name }}</label>
        </div>
        <div class="fields">
          <UiField label="Start"><input v-model="form.start" type="time" /></UiField>
          <UiField label="End"><input v-model="form.end" type="time" /></UiField>
          <UiField label="Timezone"><input v-model="form.timezone" type="text" /></UiField>
          <UiField label="Briefing time"><input v-model="form.briefing_time" type="time" /></UiField>
        </div>
      </section>

      <section class="card">
        <div class="card-head"><h2>Hour targets per week</h2></div>
        <div class="fields">
          <UiField v-for="a in areas.items" :key="a.id" :label="a.name">
            <span class="with-dot"><span class="dot" :style="{ background: a.color }" aria-hidden="true"></span><input v-model.number="form.hour_targets[a.name]" type="number" min="0" step="0.5" placeholder="hours" /></span>
          </UiField>
        </div>
      </section>

      <section class="card">
        <div class="card-head"><h2>Tasks and planning</h2></div>
        <div class="fields">
          <UiField label="Urgent when due within (days)"><input v-model.number="form.deadline_urgent_days" type="number" min="0" max="30" /></UiField>
          <UiField label="Default task length (min)"><input v-model.number="form.default_task_minutes" type="number" min="5" max="480" step="5" /></UiField>
          <UiField label="Slot lookahead (days)"><input v-model.number="form.slot_lookahead_days" type="number" min="1" max="30" /></UiField>
          <UiField label="Do's per day"><input v-model.number="form.three_dos_count" type="number" min="1" max="10" /></UiField>
        </div>
      </section>

      <section class="card">
        <div class="card-head"><h2>Rules for Pozzy</h2><span class="meta">Read by every AI feature: planning, briefing, do suggestions, capture, the review</span></div>
        <UiField label="Rules, one per line" hint="Plain sentences. They outrank the feature instructions; when a rule makes a suggestion impossible, Pozzy leaves it out and says why.">
          <textarea v-model="form.ai_rules" rows="6" placeholder="Never plan anything before 09:00; I add early things myself.&#10;My commute to school takes 45 minutes, so nothing right before a class on campus.&#10;Keep Sunday free of work."></textarea>
        </UiField>
        <UiField label="About you" hint="Standing context Pozzy should know: where you are, how you work, what matters this period.">
          <textarea v-model="form.ai_context" rows="3" placeholder="Student in Amsterdam, building Pozzy on the side. Classes are on campus, training on Tuesday and Thursday evenings."></textarea>
        </UiField>
      </section>

      <section class="card">
        <div class="card-head"><h2>AI kill switches</h2><span class="meta">Off means the deterministic fallback, no Anthropic call</span></div>
        <div class="days">
          <label v-for="[key, label] in AI_FEATURES" :key="key" class="check"><input v-model="form.ai_enabled[key]" type="checkbox" /> {{ label }}</label>
        </div>
      </section>

      <div class="actions">
        <UiButton type="submit" variant="primary" :loading="store.saving">Save settings</UiButton>
      </div>
    </form>

    <section class="card">
      <div class="card-head"><h2>Integrations</h2></div>
      <CalendarAccounts />
      <MailAccounts />
    </section>

    <section class="card">
      <div class="card-head">
        <h2>Background jobs</h2>
        <span class="meta"><button type="button" class="link-btn" @click="store.loadJobRuns()">Refresh</button></span>
      </div>
      <p v-if="!store.jobRuns.length" class="muted">No job runs recorded yet.</p>
      <div v-else class="table-wrap">
        <table class="ui jobs">
          <thead><tr><th>Job</th><th>Started</th><th>Result</th><th>Message</th></tr></thead>
          <tbody>
            <tr v-for="r in jobRows" :key="r.id">
              <td class="jname">{{ r.name }}</td>
              <td class="muted num nowrap">{{ formatDateTime(r.started_at) }}</td>
              <td><UiBadge :tone="r.ok === false ? 'danger' : r.ok ? 'ok' : 'neutral'">{{ r.ok === null ? 'running' : r.ok ? 'ok' : 'failed' }}</UiBadge></td>
              <td class="msg">{{ r.message }}</td>
            </tr>
          </tbody>
        </table>
        <button v-if="store.jobRuns.length > 8" type="button" class="link-btn more" @click="allJobs = !allJobs">{{ allJobs ? 'Show fewer' : `Show all ${store.jobRuns.length}` }}</button>
      </div>
    </section>
    </UiLoadGate>
  </div>
</template>

<style scoped>
.more { margin-top: var(--sp-2); }
.settings { max-width: 760px; }
.fields { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: var(--sp-3); }
.days { display: flex; flex-wrap: wrap; gap: var(--sp-2) var(--sp-4); margin-bottom: var(--sp-3); }
.check { display: flex; align-items: center; gap: 6px; font-size: var(--fs-base); }
.with-dot { display: flex; align-items: center; gap: 8px; width: 100%; }
.dot { width: 8px; height: 8px; border-radius: 50%; flex: none; }
.actions { display: flex; align-items: center; gap: var(--sp-3); margin-bottom: var(--sp-5); }
.jname { font-weight: 500; white-space: nowrap; }
.nowrap { white-space: nowrap; }
.msg { word-break: break-word; font-size: var(--fs-sm); color: var(--ink-2); }
@media (max-width: 699px) { .fields { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-3); } .fields :deep(.field) { min-width: 0; } }
</style>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import PullToRefresh from '../components/ios/PullToRefresh.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import UiBadge from '../components/ui/UiBadge.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiField from '../components/ui/UiField.vue'
import UiLoadGate from '../components/ui/UiLoadGate.vue'
import { useMediaQuery } from '../composables/useMediaQuery'
import { useToast } from '../composables/useToast'
import { formatDateTime } from '../lib/dates'
import { tick } from '../lib/haptics'
import { useAreasStore } from '../stores/areas'
import { useSettingsStore } from '../stores/settings'

import CalendarAccounts from '../components/settings/CalendarAccounts.vue'
import MailAccounts from '../components/settings/MailAccounts.vue'
import HabitReminders from '../components/settings/HabitReminders.vue'

const store = useSettingsStore()
const areas = useAreasStore()
const toast = useToast()
// Phone: the iOS Settings app. Sections are a footnote header over a plate of 44pt rows (label
// left, value or control right), Save moves into the navigation bar, jobs become rows.
const phone = useMediaQuery('(max-width: 1023px)')
const route = useRoute()
const form = reactive({ working_days: [], start: '08:00', end: '18:00', timezone: 'Europe/Amsterdam', briefing_time: '07:00', hour_targets: {}, ai_enabled: {}, deadline_urgent_days: 3, default_task_minutes: 60, slot_lookahead_days: 7, three_dos_count: 3, plan_buffer_minutes: 0, ai_rules: '', ai_context: '' })

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
  form.plan_buffer_minutes = v.plan_buffer_minutes ?? 0
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
      plan_buffer_minutes: Number(form.plan_buffer_minutes) || 0,
    })
    toast.success('Settings saved.')
  } catch {
    // store.error is shown
  }
}
</script>

<template>
  <PullToRefresh :action="() => store.loadJobRuns()">
  <div class="settings">
    <PageHeader title="Settings" />
    <Teleport v-if="phone && ready && route.name === 'settings'" defer to="#nav-trailing">
      <button type="submit" form="settings-form" class="nav-save" :disabled="store.saving">{{ store.saving ? 'Saving…' : 'Save' }}</button>
    </Teleport>
    <p v-if="store.error" class="error">{{ store.error }}</p>
    <UiLoadGate :ready="Boolean(ready) || Boolean(store.error)" label="Loading settings">

    <HabitReminders v-if="ready" />
    <form v-if="ready" id="settings-form" @submit.prevent="save">
      <section class="card grp">
        <div class="card-head"><h2>Working window</h2></div>
        <div class="days week">
          <label v-for="[n, name] in DAYS" :key="n" class="check"><input v-model="form.working_days" type="checkbox" :value="n" @change="tick()" /> {{ name }}</label>
        </div>
        <div class="fields">
          <UiField label="Start"><input v-model="form.start" type="time" /></UiField>
          <UiField label="End"><input v-model="form.end" type="time" /></UiField>
          <UiField label="Timezone"><input v-model="form.timezone" type="text" /></UiField>
          <UiField label="Briefing time"><input v-model="form.briefing_time" type="time" /></UiField>
        </div>
      </section>

      <section class="card grp">
        <div class="card-head"><h2>Hour targets per week</h2></div>
        <div class="fields">
          <UiField v-for="a in areas.items" :key="a.id" :label="a.name">
            <span class="with-dot"><span class="dot" :style="{ background: a.color }" aria-hidden="true"></span><input v-model.number="form.hour_targets[a.name]" type="number" min="0" step="0.5" placeholder="hours" /></span>
          </UiField>
        </div>
        <p v-if="phone" class="foot">Hours per week. Leave empty for no target.</p>
      </section>

      <section class="card grp">
        <div class="card-head"><h2>Tasks and planning</h2></div>
        <div class="fields">
          <UiField label="Urgent when due within (days)"><input v-model.number="form.deadline_urgent_days" type="number" min="0" max="30" /></UiField>
          <UiField label="Default task length (min)"><input v-model.number="form.default_task_minutes" type="number" min="5" max="480" step="5" /></UiField>
          <UiField label="Slot lookahead (days)"><input v-model.number="form.slot_lookahead_days" type="number" min="1" max="30" /></UiField>
          <UiField label="Buffer around events (min)" hint="Kept free before and after every calendar event when Pozzy plans or suggests a slot"><input v-model.number="form.plan_buffer_minutes" type="number" min="0" max="240" step="5" /></UiField>
          <UiField label="Do's per day"><input v-model.number="form.three_dos_count" type="number" min="1" max="10" /></UiField>
        </div>
        <p v-if="phone" class="foot">The buffer is kept free before and after every calendar event when Pozzy plans or suggests a slot.</p>
      </section>

      <section class="card grp notes">
        <div class="card-head"><h2>Rules for Pozzy</h2><span class="meta">Read by every AI feature: planning, briefing, do suggestions, capture, the review</span></div>
        <UiField :label="phone ? 'Rules for Pozzy' : 'Rules, one per line'" :hint="phone ? 'One per line, read by every AI feature. They outrank the feature instructions; when a rule makes a suggestion impossible, Pozzy leaves it out and says why.' : 'Plain sentences. They outrank the feature instructions; when a rule makes a suggestion impossible, Pozzy leaves it out and says why.'">
          <textarea v-model="form.ai_rules" rows="6" placeholder="Never plan anything before 09:00; I add early things myself.&#10;My commute to school takes 45 minutes, so nothing right before a class on campus.&#10;Keep Sunday free of work."></textarea>
        </UiField>
        <UiField label="About you" hint="Standing context Pozzy should know: where you are, how you work, what matters this period.">
          <textarea v-model="form.ai_context" rows="3" placeholder="Student in Amsterdam, building Pozzy on the side. Classes are on campus, training on Tuesday and Thursday evenings."></textarea>
        </UiField>
      </section>

      <section class="card grp">
        <div class="card-head"><h2>AI kill switches</h2><span class="meta">Off means the deterministic fallback, no Anthropic call</span></div>
        <div class="days switches">
          <label v-for="[key, label] in AI_FEATURES" :key="key" class="check"><input v-model="form.ai_enabled[key]" type="checkbox" role="switch" @change="tick()" /> {{ label }}</label>
        </div>
        <p v-if="phone" class="foot">Off means the deterministic fallback, no Anthropic call.</p>
      </section>

      <div class="actions">
        <UiButton type="submit" variant="primary" :loading="store.saving">Save settings</UiButton>
      </div>
    </form>

    <section class="card grp integrations">
      <div class="card-head"><h2>Integrations</h2></div>
      <CalendarAccounts />
      <MailAccounts />
    </section>

    <section class="card grp">
      <div class="card-head">
        <h2>Background jobs</h2>
        <span class="meta"><button type="button" class="link-btn" @click="store.loadJobRuns()">Refresh</button></span>
      </div>
      <p v-if="!store.jobRuns.length" class="muted empty">No job runs recorded yet.</p>
      <ul v-else-if="phone" class="jobs-list">
        <li v-for="r in jobRows" :key="r.id" class="job">
          <span class="job-main">
            <span class="job-name">{{ r.name }}</span>
            <span class="job-when num">{{ formatDateTime(r.started_at) }}</span>
            <span v-if="r.message" class="job-msg">{{ r.message }}</span>
          </span>
          <span class="job-state" :class="r.ok === false ? 'bad' : r.ok ? 'good' : ''">{{ r.ok === null ? 'Running' : r.ok ? 'OK' : 'Failed' }}</span>
        </li>
        <li v-if="store.jobRuns.length > 8"><button type="button" class="job-more" @click="allJobs = !allJobs">{{ allJobs ? 'Show fewer' : `Show all ${store.jobRuns.length}` }}</button></li>
      </ul>
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
  </PullToRefresh>
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

/* iOS layer. Each card turns into an inset grouped section: its title becomes the footnote
   header over the plate, fields become rows with the label on the left and a compact value on
   the right (time and number as the grey pill of a compact picker), hints move under the plate. */
@media (max-width: 1023px) {
  .settings { max-width: 680px; margin: 0 auto; }
  .grp { background: none; padding: 0; border-radius: 0; margin-bottom: var(--sp-8); }
  .grp > .card-head { margin: 0 16px 6px; }
  .grp > .card-head h2 { font-size: 0.8125rem; font-weight: 400; text-transform: uppercase; color: var(--ink-3); }
  .grp > .card-head .meta { display: none; }
  .foot, .empty { margin: 6px 16px 0; font-size: 0.8125rem; line-height: 1.4; color: var(--ink-3); }
  .empty { margin: 0; padding: 12px 16px; background: var(--surface); border-radius: var(--r-lg); font-size: 1.0625rem; }

  .fields { display: block; background: var(--surface); border-radius: var(--r-lg); overflow: hidden; }
  .fields :deep(.field) { position: relative; flex-direction: row; align-items: center; gap: 12px; min-height: 44px; padding: 6px 16px; }
  .fields :deep(.field + .field)::before { content: ''; position: absolute; top: 0; left: 16px; right: 0; height: 0.5px; background: var(--line-2); }
  .fields :deep(.field-label) { flex: 1; min-width: 0; font-size: 1.0625rem; font-weight: 400; letter-spacing: 0; text-transform: none; color: var(--ink); line-height: 1.3; }
  .fields :deep(.field-control) { flex: none; justify-content: flex-end; }
  .fields :deep(.field-hint) { display: none; }
  .fields :deep(input[type='time']), .fields :deep(input[type='number']) { width: auto; min-width: 76px; max-width: 110px; height: 34px; padding: 0 11px; border-radius: 8px; text-align: center; font-variant-numeric: tabular-nums; }
  .fields :deep(input[type='text']) { width: 190px; height: 34px; padding: 0; background: transparent; text-align: right; color: var(--ink-3); }
  .fields :deep(input[type='text']:focus-visible) { box-shadow: none; color: var(--ink); }
  /* Area targets: the area's dot sits before its name, as in a Settings row with a symbol. */
  .fields :deep(.field:has(.with-dot)) { padding-left: 38px; }
  .with-dot { width: auto; }
  .with-dot .dot { position: absolute; left: 16px; top: 50%; width: 12px; height: 12px; margin-top: -6px; }

  /* Working days: a row of round day toggles on top of the window's plate. */
  .week { display: flex; justify-content: space-between; gap: 4px; margin: 0; padding: 12px 16px; background: var(--surface); border-radius: var(--r-lg) var(--r-lg) 0 0; }
  .week + .fields { position: relative; border-radius: 0 0 var(--r-lg) var(--r-lg); }
  .week + .fields::before { content: ''; position: absolute; top: 0; left: 16px; right: 0; height: 0.5px; background: var(--line-2); }
  .week .check { position: relative; justify-content: center; width: 40px; height: 40px; border-radius: 50%; background: var(--surface-2); color: var(--ink); font-size: 0.8125rem; font-weight: 600; gap: 0; }
  .week .check input { position: absolute; opacity: 0; pointer-events: none; }
  .week .check:has(input:checked) { background: var(--brand); color: #fff; }
  .week .check:has(input:focus-visible) { outline: 2px solid var(--brand); outline-offset: 2px; }

  /* Kill switches: label left, iOS switch right. */
  .switches { display: block; margin: 0; background: var(--surface); border-radius: var(--r-lg); overflow: hidden; }
  .switches .check { position: relative; flex-direction: row-reverse; justify-content: space-between; gap: 12px; min-height: 44px; padding: 6px 16px; font-size: 1.0625rem; }
  .switches .check + .check::before { content: ''; position: absolute; top: 0; left: 16px; right: 0; height: 0.5px; background: var(--line-2); }

  /* Rules and context: each field is its own header, plate and footer. */
  .notes > .card-head { display: none; }
  .notes :deep(.field) { gap: 0; margin-bottom: var(--sp-8); }
  .notes :deep(.field:last-child) { margin-bottom: 0; }
  .notes :deep(.field-label) { margin: 0 16px 6px; font-size: 0.8125rem; font-weight: 400; letter-spacing: 0; color: var(--ink-3); }
  .notes :deep(.field-control) { background: var(--surface); border-radius: var(--r-lg); overflow: hidden; }
  .notes :deep(textarea) { background: transparent; border-radius: 0; padding: 11px 16px; line-height: 1.4; resize: none; }
  .notes :deep(textarea:focus-visible) { box-shadow: none; }
  .notes :deep(.field-hint) { margin: 6px 16px 0; font-size: 0.8125rem; line-height: 1.4; }

  /* Save lives in the navigation bar on the phone. */
  .actions { display: none; }
  .nav-save { height: 44px; padding: 0 10px; border: 0; background: none; color: var(--brand); font: inherit; font-size: 1.0625rem; font-weight: 600; }
  .nav-save:active { opacity: 0.4; }
  .nav-save:disabled { color: var(--ink-4); }

  .integrations > .card-head { display: none; }
  .grp > .card-head:has(.link-btn) .meta { display: inline; }
  .grp > .card-head:has(.link-btn) h2 { white-space: nowrap; }
  .card-head .link-btn { font-size: 0.8125rem; text-transform: none; min-height: 0; }

  .jobs-list { background: var(--surface); border-radius: var(--r-lg); overflow: hidden; }
  .jobs-list > li { position: relative; }
  .jobs-list > li + li::before { content: ''; position: absolute; top: 0; left: 16px; right: 0; height: 0.5px; background: var(--line-2); }
  .job { display: flex; align-items: center; gap: 12px; min-height: 44px; padding: 10px 16px; }
  .job-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }
  .job-name { font-size: 1.0625rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .job-when { font-size: 0.9375rem; color: var(--ink-3); }
  .job-msg { font-size: 0.8125rem; color: var(--ink-3); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; word-break: break-word; }
  .job-state { flex: none; font-size: 0.9375rem; color: var(--ink-3); }
  .job-state.good { color: var(--ok); }
  .job-state.bad { color: var(--danger); }
  .job-more { width: 100%; height: 44px; padding: 0 16px; border: 0; background: none; color: var(--brand); font: inherit; font-size: 1.0625rem; text-align: left; }
  .job-more:active { background: var(--surface-3); }
}
</style>

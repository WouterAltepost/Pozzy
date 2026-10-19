<script setup>
// Habits: every habit's week at a glance, plus managing them. A tap on a cell checks a yes/no
// or count habit with Undo in the toast; value cells, a long press or a right-click open the
// check-in sheet. Days a habit is not due are dimmed, skipped days show a slash. The name opens
// the habit's stats page. Reorder moves a habit within its area.
import { computed, ref } from 'vue'
import { PhArrowDown, PhArrowUp, PhFlame, PhPlus, PhSparkle } from '@phosphor-icons/vue'
import CheckInSheet from '../components/habits/CheckInSheet.vue'
import HabitEditor from '../components/habits/HabitEditor.vue'
import HabitIcon from '../components/habits/HabitIcon.vue'
import TrackerSeriesChart from '../components/trackers/TrackerSeriesChart.vue'
import WeekNav from '../components/shared/WeekNav.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiConfirm from '../components/ui/UiConfirm.vue'
import UiEmpty from '../components/ui/UiEmpty.vue'
import UiLoadGate from '../components/ui/UiLoadGate.vue'
import { useLongPress } from '../composables/useLongPress'
import { useMediaQuery } from '../composables/useMediaQuery'
import { useReady } from '../composables/useReady'
import { useToast } from '../composables/useToast'
import { formatDay, shortDay, today as todayFn } from '../lib/dates'
import { WEEKDAY_LETTERS, dayState, fmt, isBool, isCount, isWeekly, scheduleLabel, targetLabel } from '../lib/habits'
import { useTrackersStore } from '../stores/trackers'

const store = useTrackersStore()
const toast = useToast()
const error = ref('')
const today = todayFn()
const phone = useMediaQuery('(max-width: 699px)')
const reordering = ref(false)

const ready = useReady(() => store.load())

function describe(t, d, value, status) {
  const day = d === today ? 'today' : formatDay(d)
  if (status === 'skipped') return `${t.name} skipped ${day}`
  if (isBool(t)) return `${t.name} ${value ? 'done' : 'not done'} ${day}`
  if (value === null || value === undefined) return `${t.name} cleared ${day}`
  return `${t.name} ${day}: ${fmt(value)}${t.unit ? ' ' + t.unit : ''}`
}
async function write(t, date, fn) {
  error.value = ''
  try {
    const { previous, value, status } = await fn()
    toast.undo(describe(t, date, value, status), async () => {
      try {
        await store.revert(t.id, date, previous)
      } catch (err) {
        toast.error(err.message)
      }
    })
  } catch (err) {
    error.value = err.message
  }
}

const press = useLongPress(({ t, d }) => openSheet(t, d.date))
function cellTap(t, d) {
  if (press.consumed()) return
  if (d.date > today) return
  if (isBool(t) || isCount(t)) write(t, d.date, () => store.tick(t.id, d.date))
  else openSheet(t, d.date)
}
function cellPress(t, d) {
  return d.date > today ? {} : press.handlers({ t, d })
}
function cellClass(t, d) {
  return `s-${dayState(t, d, today)}`
}
function cellText(t, d) {
  if (d.date > today || d.status === 'skipped') return ''
  if (isBool(t)) return ''
  return d.value ? fmt(d.value) : ''
}
function cellLabel(t, d) {
  const state = dayState(t, d, today)
  return `${t.name} ${shortDay(d.date)}: ${state === 'off' ? 'not due' : state}${d.value && !isBool(t) ? ' ' + fmt(d.value) : ''}${d.note ? ', note: ' + d.note : ''}`
}

// Check-in sheet
const sheet = ref(null) // { id, date }
const sheetBusy = ref(false)
const sheetTracker = computed(() => (sheet.value ? store.byId(sheet.value.id) : null))
function openSheet(t, date) {
  sheet.value = { id: t.id, date }
}
async function saveSheet(body) {
  const t = sheetTracker.value
  const date = sheet.value.date
  sheetBusy.value = true
  try {
    await write(t, date, () => store.setEntry(t.id, date, body.value, body.note, body.status))
    sheet.value = null
  } finally {
    sheetBusy.value = false
  }
}
async function clearSheet() {
  const t = sheetTracker.value
  const date = sheet.value.date
  sheetBusy.value = true
  try {
    await write(t, date, () => store.clearEntry(t.id, date))
    sheet.value = null
  } finally {
    sheetBusy.value = false
  }
}

// Create and edit
const editing = ref(null) // null | 'new' | tracker
const saving = ref(false)
const editError = ref('')
async function save(body) {
  saving.value = true
  editError.value = ''
  try {
    if (editing.value === 'new') await store.create(body)
    else await store.update(editing.value.id, body)
    editing.value = null
  } catch (err) {
    editError.value = err.message
  } finally {
    saving.value = false
  }
}
function openEditor(t) {
  editError.value = ''
  editing.value = t
}

async function archive(t) {
  error.value = ''
  try {
    await store.update(t.id, { active: !t.active })
    toast.success(t.active ? `${t.name} archived` : `${t.name} restored`)
  } catch (err) {
    error.value = err.message
  }
}

const deleting = ref(null)
const deleteBusy = ref(false)
async function confirmDelete() {
  deleteBusy.value = true
  try {
    await store.remove(deleting.value.id)
    deleting.value = null
  } catch (err) {
    error.value = err.message
  } finally {
    deleteBusy.value = false
  }
}

// Move a habit one place up or down among the habits of its own area.
async function move(t, dir) {
  const group = store.grouped.find((g) => g.trackers.some((x) => x.id === t.id))?.trackers || []
  const i = group.findIndex((x) => x.id === t.id)
  const other = group[i + dir]
  if (!other) return
  const ids = store.trackers.map((x) => x.id)
  const a = ids.indexOf(t.id)
  const b = ids.indexOf(other.id)
  ;[ids[a], ids[b]] = [ids[b], ids[a]]
  try {
    await store.reorder(ids)
  } catch (err) {
    error.value = err.message
    await store.load()
  }
}

const days = computed(() => store.week?.trackers[0]?.days.map((d) => d.date) || [])
</script>

<template>
  <div class="habits">
    <PageHeader v-if="!phone" title="Habits" eyebrow="Week view">
      <WeekNav :week-start="store.weekStart" @change="store.setWeek($event)" />
      <label class="check"><input v-model="store.includeInactive" type="checkbox" @change="store.load()" /> Archived</label>
      <UiButton v-if="store.trackers.length > 1" :variant="reordering ? 'primary' : 'secondary'" @click="reordering = !reordering">{{ reordering ? 'Done' : 'Reorder' }}</UiButton>
      <UiButton variant="primary" @click="openEditor('new')"><PhPlus />New habit</UiButton>
    </PageHeader>
    <div v-else class="phead">
      <h1>Habits</h1>
      <UiButton variant="primary" size="sm" @click="openEditor('new')"><PhPlus />New</UiButton>
    </div>
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>

    <UiLoadGate :ready="ready" label="Loading habits">
      <section v-if="!store.trackers.length" class="card">
        <UiEmpty title="No habits yet" hint="Creatine, gym three times a week, sleep hours, reading on weekdays: anything you want to keep up.">
          <template #icon><PhSparkle /></template>
          <template #action><UiButton variant="primary" @click="openEditor('new')">New habit</UiButton></template>
        </UiEmpty>
      </section>

      <!-- Phone: one block per habit, the name above its seven days. -->
      <template v-if="phone && store.trackers.length">
        <section class="card">
          <div class="card-head">
            <h2>This week</h2>
            <span class="meta"><WeekNav :week-start="store.weekStart" compact @change="store.setWeek($event)" /></span>
          </div>
          <div class="letters" aria-hidden="true"><span v-for="(l, i) in WEEKDAY_LETTERS" :key="i" :class="{ now: days[i] === today }">{{ l }}</span></div>
          <div v-for="t in store.trackers" :key="t.id" class="prow" :class="{ inactive: !t.active }">
            <RouterLink :to="{ name: 'habit', params: { id: t.id } }" class="pname">
              <HabitIcon :tracker="t" :size="28" />
              <span class="truncate">{{ t.name }}</span>
              <span v-if="t.streak > 1" class="streak num"><PhFlame weight="fill" />{{ t.streak }}</span>
            </RouterLink>
            <span class="cells">
              <button v-for="d in t.days" :key="d.date" type="button" class="cell" :class="[cellClass(t, d), { today: d.date === today }]" :aria-label="cellLabel(t, d)" :disabled="d.date > today" v-bind="cellPress(t, d)" @click="cellTap(t, d)">{{ cellText(t, d) }}</button>
            </span>
          </div>
        </section>
        <label class="check pcheck"><input v-model="store.includeInactive" type="checkbox" @change="store.load()" /> Show archived habits</label>
      </template>

      <!-- Desktop: a table per area. -->
      <section v-for="group in store.grouped" v-else :key="group.area" class="card group">
        <div class="card-head">
          <h2><span class="dot" :style="{ background: group.color }" aria-hidden="true"></span>{{ group.area }}</h2>
        </div>
        <div class="table-wrap">
          <table class="ui grid">
            <thead>
              <tr>
                <th class="name"></th>
                <th v-for="d in days" :key="d" class="day" :class="{ today: d === today }">{{ shortDay(d) }}</th>
                <th class="num">week</th>
                <th class="num">streak</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(t, i) in group.trackers" :key="t.id" :class="{ inactive: !t.active }">
                <td class="name">
                  <RouterLink :to="{ name: 'habit', params: { id: t.id } }" class="tname">
                    <HabitIcon :tracker="t" :size="30" />
                    <span class="tname-text">
                      <span class="truncate">{{ t.name }}</span>
                      <span class="muted xs">{{ scheduleLabel(t) }}<template v-if="targetLabel(t) && !isWeekly(t)"> · {{ targetLabel(t) }}</template><template v-if="t.reminder_time"> · {{ t.reminder_time }}</template></span>
                    </span>
                  </RouterLink>
                </td>
                <td v-for="d in t.days" :key="d.date" class="c">
                  <button type="button" class="cell" :class="[cellClass(t, d), { today: d.date === today, wide: !isBool(t) && !isCount(t) }]" :title="d.note || ''" :aria-label="cellLabel(t, d)" :disabled="d.date > today" v-bind="cellPress(t, d)" @click="cellTap(t, d)">{{ cellText(t, d) }}</button>
                </td>
                <td class="num">
                  <span v-if="isWeekly(t)">{{ fmt(t.week_total) }}<span v-if="t.target_value" class="muted"> / {{ fmt(t.target_value) }}</span></span>
                  <span v-else-if="t.completion !== null">{{ Math.round(t.completion * 100) }}%</span>
                  <span v-else class="muted">-</span>
                </td>
                <td class="num"><span class="streak"><PhFlame v-if="t.streak" weight="fill" />{{ t.streak }}</span></td>
                <td class="actions">
                  <template v-if="reordering">
                    <button type="button" class="icon-btn" :disabled="i === 0" :aria-label="`Move ${t.name} up`" @click="move(t, -1)"><PhArrowUp /></button>
                    <button type="button" class="icon-btn" :disabled="i === group.trackers.length - 1" :aria-label="`Move ${t.name} down`" @click="move(t, 1)"><PhArrowDown /></button>
                  </template>
                  <template v-else>
                    <button type="button" class="link-btn" @click="openEditor(t)">edit</button>
                    <button type="button" class="link-btn" @click="archive(t)">{{ t.active ? 'archive' : 'restore' }}</button>
                    <button type="button" class="link-btn danger" @click="deleting = t">delete</button>
                  </template>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <div v-if="store.trackers.length" class="legend muted xs">
        <span><i class="sw s-done"></i>done</span><span><i class="sw s-part"></i>partly</span><span><i class="sw s-skipped"></i>skipped</span><span><i class="sw s-off"></i>not due</span>
        <span v-if="!phone">Click to check, right-click for value, note or skip</span>
        <span v-else>Tap to check, hold for value, note or skip</span>
      </div>

      <TrackerSeriesChart v-if="store.trackers.length" :refresh-key="store.version" />
    </UiLoadGate>

    <CheckInSheet :open="Boolean(sheetTracker)" :tracker="sheetTracker" :day="sheet?.date || ''" :busy="sheetBusy" @save="saveSheet" @clear="clearSheet" @close="sheet = null" />
    <HabitEditor :open="Boolean(editing)" :tracker="editing === 'new' ? null : editing" :busy="saving" :error="editError" @save="save" @close="editing = null" />
    <UiConfirm :open="Boolean(deleting)" title="Delete habit?" :message="deleting ? `${deleting.name} and every check-in it has will be gone. Archive keeps the history instead.` : ''" confirm-label="Delete" danger :busy="deleteBusy" @confirm="confirmDelete" @cancel="deleting = null" />
  </div>
</template>

<style scoped>
.phead { display: flex; align-items: center; justify-content: space-between; gap: var(--sp-2); margin-bottom: var(--sp-4); }
.check { display: flex; align-items: center; gap: 6px; font-size: var(--fs-md); white-space: nowrap; }
.pcheck { margin: 0 4px var(--sp-5); color: var(--ink-3); }
.card-head h2 { display: flex; align-items: center; gap: 8px; }
.dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }

/* Cells: one vocabulary for the grid and the phone rows. */
.cell { width: 34px; height: 32px; padding: 0; border-radius: var(--r-md); border: 1px solid var(--line); background: var(--surface); color: var(--ink-2); font-size: var(--fs-sm); font-weight: 600; display: inline-flex; align-items: center; justify-content: center; font-variant-numeric: tabular-nums; touch-action: manipulation; -webkit-touch-callout: none; user-select: none; -webkit-user-select: none; transition: background-color var(--dur-hover) ease, border-color var(--dur-hover) ease, color var(--dur-hover) ease, transform var(--dur-press) var(--ease-out); }
.cell.wide { width: 46px; }
.cell:active:not(:disabled) { transform: scale(0.92); }
.cell:disabled { opacity: 0.35; }
.cell.today { border-color: var(--brand); }
.s-done { background: var(--ok); border-color: var(--ok); color: #fff; }
.s-part { background: var(--warn-soft); border-color: transparent; color: var(--warn); }
.s-skipped { background: repeating-linear-gradient(135deg, var(--surface-2) 0 4px, var(--surface-3) 4px 6px); border-color: transparent; }
.s-off { background: transparent; border-style: dashed; border-color: var(--line); }
.s-done.today { box-shadow: 0 0 0 2px var(--surface), 0 0 0 3px var(--brand); }
@media (hover: hover) and (pointer: fine) { .cell:not(:disabled):not(.s-done):hover { border-color: var(--ink-4); } }

.grid th.day { text-align: center; }
.grid th.today { color: var(--brand); }
.grid td { text-align: center; padding: 6px 3px; }
.grid td.name { text-align: left; min-width: 200px; max-width: 280px; padding-left: 0; }
.tname { display: flex; align-items: center; gap: 10px; color: var(--ink); text-decoration: none; min-width: 0; }
.tname:hover { text-decoration: none; }
.tname-text { display: flex; flex-direction: column; min-width: 0; line-height: 1.3; }
.tname-text .truncate { font-weight: 600; }
@media (hover: hover) and (pointer: fine) { .tname:hover .truncate { color: var(--brand); } }
.streak { display: inline-flex; align-items: center; gap: 3px; color: var(--warn); font-weight: 600; }
.streak :deep(svg) { width: 13px; height: 13px; }
tr.inactive, .prow.inactive { opacity: 0.5; }
.actions { white-space: nowrap; text-align: right; }
.actions .link-btn { margin-left: var(--sp-2); }
.link-btn.danger { color: var(--danger); }

/* Phone rows */
.letters, .prow .cells { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 4px; }
.letters { font-size: var(--fs-xs); font-weight: 600; color: var(--ink-3); text-align: center; margin-bottom: 4px; }
.letters .now { color: var(--brand); }
.prow { padding: 10px 0; border-top: 1px solid var(--line); }
.pname { display: flex; align-items: center; gap: 10px; min-width: 0; color: var(--ink); font-weight: 600; margin-bottom: 8px; text-decoration: none; }
.pname .streak { margin-left: auto; }
.prow .cell { width: 100%; height: 36px; }

.legend { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 16px; margin: calc(var(--sp-2) * -1) 4px var(--sp-6); }
.legend span { display: inline-flex; align-items: center; gap: 6px; }
.sw { display: inline-block; width: 12px; height: 12px; border-radius: 4px; border: 1px solid var(--line); }
</style>

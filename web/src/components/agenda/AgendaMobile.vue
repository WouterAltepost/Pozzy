<script setup>
// Phone agenda (design: Pozzy Phone, Agenda). Week: a compact grid, 30px per hour from 07:00,
// tap a day to open it. Day: a seven-day strip and a list of the day's events with the now line;
// swipe the list to change day. Planner suggestions show as dashed blocks and dashed rows.
import { computed, ref } from 'vue'
import { PhCaretLeft, PhCaretRight, PhCheck, PhPlus, PhSparkle, PhX } from '@phosphor-icons/vue'
import { formatDay, formatTime, mondayOf, shortDay, today, weekDays } from '../../lib/dates'
import { useCalendarStore } from '../../stores/calendar'
import UiBadge from '../ui/UiBadge.vue'
import UiEmpty from '../ui/UiEmpty.vue'
import UiSegmented from '../ui/UiSegmented.vue'

const props = defineProps({ suggestions: { type: Array, default: () => [] }, planning: { type: Boolean, default: false } })
const emit = defineEmits(['select-event', 'create', 'plan', 'accept', 'deny'])
const store = useCalendarStore()

const H0 = 7
const H1 = 23
const HOUR_PX = 30
const VIEWS = [
  { value: 'week', label: 'Week' },
  { value: 'day', label: 'Day' },
]
const view = computed({ get: () => store.view, set: (v) => store.setView(v) })
const week = computed(() => weekDays(mondayOf(store.anchor)))
const hours = Array.from({ length: H1 - H0 }, (_, i) => H0 + i)
const gridH = (H1 - H0) * HOUR_PX

function dayBounds(day) {
  const [y, m, d] = day.split('-').map(Number)
  return [new Date(y, m - 1, d), new Date(y, m - 1, d + 1)]
}
function kindOf(item) {
  if (item.kind === 'task') return 'task'
  if (item.recurrence_id) return 'recurring'
  if (item.task_id) return 'linked'
  return 'event'
}
// Everything on a day: events, scheduled tasks and suggestions, clipped to 07:00 to 23:00.
function itemsFor(day) {
  const [ds, de] = dayBounds(day)
  const out = []
  const push = (item, kind, extra = {}) => {
    const s = new Date(item.start)
    const e = new Date(item.end)
    if (e <= ds || s >= de) return
    const from = Math.max((s - ds) / 60000, H0 * 60)
    const to = Math.min((e - ds) / 60000, H1 * 60)
    if (to <= from) return
    out.push({ item, kind, from, to, top: ((from - H0 * 60) / 60) * HOUR_PX, height: Math.max(((to - from) / 60) * HOUR_PX - 2, 16), ...extra })
  }
  const linked = new Set(store.events.filter((e) => e.task_id).map((e) => String(e.task_id)))
  for (const e of store.events) if (!e.all_day) push(e, kindOf(e))
  for (const t of store.tasks) if (t.scheduled_start && t.scheduled_end && !linked.has(String(t.id))) push({ ...t, start: t.scheduled_start, end: t.scheduled_end, kind: 'task' }, 'task')
  for (const sg of props.suggestions) push(sg, 'suggest', { suggestion: sg })
  return out.sort((a, b) => a.from - b.from)
}
const columns = computed(() => week.value.map((day) => ({ day, isToday: day === today(), items: itemsFor(day) })))
const dayItems = computed(() => itemsFor(store.anchor))
const nowMinutes = computed(() => {
  const n = new Date()
  return n.getHours() * 60 + n.getMinutes()
})
const nowTop = computed(() => ((nowMinutes.value - H0 * 60) / 60) * HOUR_PX)
const nowVisible = computed(() => nowMinutes.value >= H0 * 60 && nowMinutes.value <= H1 * 60)
const nowIndex = computed(() => (store.anchor === today() ? dayItems.value.findIndex((i) => i.from > nowMinutes.value) : -1))
const count = computed(() => {
  if (store.view === 'week') return `${store.events.length} ${store.events.length === 1 ? 'event' : 'events'} this week`
  const n = dayItems.value.filter((i) => i.kind !== 'suggest').length
  return `${n} ${n === 1 ? 'event' : 'events'}`
})
const synced = computed(() => (store.account?.last_synced_at ? `synced ${formatTime(store.account.last_synced_at)}` : store.account ? 'not synced' : 'no calendar'))

function openDay(day) {
  store.anchor = day
  store.setView('day')
}
function pickDay(day) {
  store.setAnchor(day)
}
function stepWeek(n) {
  store.setAnchor(week.value[0] === undefined ? today() : addDaysLocal(week.value[0], 7 * n))
}
function addDaysLocal(day, n) {
  const [y, m, d] = day.split('-').map(Number)
  const x = new Date(y, m - 1, d + n)
  return `${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, '0')}-${String(x.getDate()).padStart(2, '0')}`
}
let sx = null
function swipeStart(e) {
  sx = e.clientX
}
function swipeEnd(e) {
  if (sx === null) return
  const dx = e.clientX - sx
  sx = null
  if (dx < -40) store.step(1)
  else if (dx > 40) store.step(-1)
}
function dayNum(day) {
  return Number(day.slice(8))
}
function wd(day) {
  return shortDay(day).slice(0, 3)
}
</script>

<template>
  <div class="magenda">
    <div class="head">
      <div>
        <h1>Agenda</h1>
        <span class="muted small">{{ store.view === 'week' ? 'Week of ' + formatDay(week[0]) : formatDay(store.anchor) }}</span>
      </div>
      <UiSegmented v-model="view" :options="VIEWS" />
    </div>
    <div class="status">
      <button type="button" class="icon-btn" aria-label="Previous week" @click="stepWeek(-1)"><PhCaretLeft /></button>
      <button type="button" class="icon-btn" aria-label="Next week" @click="stepWeek(1)"><PhCaretRight /></button>
      <button type="button" class="sync" :disabled="!store.account || store.syncing" @click="store.sync()">
        <UiBadge :tone="store.account?.last_sync_error ? 'danger' : store.account ? 'ok' : 'neutral'" dot>{{ store.syncing ? 'syncing' : synced }}</UiBadge>
      </button>
      <span class="muted small">iCloud</span>
      <span class="spacer"></span>
      <span class="muted small num">{{ count }}</span>
      <button type="button" class="icon-btn" title="Plan the week" aria-label="Plan the week" :disabled="planning" @click="emit('plan')"><PhSparkle weight="fill" /></button>
      <button type="button" class="icon-btn" aria-label="New event" @click="emit('create', { day: store.anchor })"><PhPlus weight="bold" /></button>
    </div>

    <template v-if="store.view === 'week'">
      <div class="mini">
        <div class="corner"></div>
        <button v-for="c in columns" :key="c.day" type="button" class="dhead" :class="{ today: c.isToday }" @click="openDay(c.day)">
          <span class="wd">{{ wd(c.day) }}</span><span class="dn num">{{ dayNum(c.day) }}</span>
        </button>
        <div class="gutter" :style="{ height: gridH + 'px' }">
          <span v-for="h in hours" :key="h" class="hl num" :style="{ top: (h - H0) * HOUR_PX + 'px' }">{{ String(h).padStart(2, '0') }}</span>
        </div>
        <div v-for="c in columns" :key="'c' + c.day" class="col" :class="{ today: c.isToday }" :style="{ height: gridH + 'px' }" @click="openDay(c.day)">
          <span v-for="h in hours" :key="h" class="line" :style="{ top: (h - H0) * HOUR_PX + 'px' }"></span>
          <span v-if="c.isToday && nowVisible" class="now" :style="{ top: nowTop + 'px' }"></span>
          <span v-for="it in c.items" :key="(it.item.id || it.item.title) + it.from" class="blk" :class="it.kind" :style="{ top: it.top + 'px', height: it.height + 'px' }" @click.stop="it.kind === 'suggest' ? openDay(c.day) : it.kind === 'task' ? null : emit('select-event', it.item)">
            <span class="bt num">{{ formatTime(it.item.start) }}</span>
            <span class="bn">{{ it.item.title }}</span>
          </span>
        </div>
      </div>
      <p class="hint muted small">Tap a day to open it</p>
    </template>

    <template v-else>
      <div class="strip">
        <button v-for="day in week" :key="day" type="button" class="dbtn" :class="{ active: day === store.anchor, today: day === today() }" :aria-pressed="day === store.anchor" @click="pickDay(day)">
          <span class="wd">{{ wd(day) }}</span><span class="dn num">{{ dayNum(day) }}</span>
        </button>
      </div>
      <section class="card daylist" @pointerdown="swipeStart" @pointerup="swipeEnd">
        <div v-if="!dayItems.length" class="empty-wrap">
          <UiEmpty compact title="No events" hint="Nothing on the calendar mirror for this day." />
        </div>
        <ul v-else>
          <li v-for="(it, i) in dayItems" :key="(it.item.id || it.item.title) + it.from" :class="{ first: i === 0 }">
            <div v-if="i === nowIndex" class="nowrow"><span class="dot"></span><span class="rule"></span><span class="t num">{{ String(Math.floor(nowMinutes / 60)).padStart(2, '0') }}:{{ String(nowMinutes % 60).padStart(2, '0') }}</span></div>
            <div class="row" :class="it.kind" @click="it.kind === 'event' || it.kind === 'linked' || it.kind === 'recurring' ? emit('select-event', it.item) : null">
              <span class="times num"><span class="s">{{ formatTime(it.item.start) }}</span><span class="e">{{ formatTime(it.item.end) }}</span></span>
              <span class="bar"></span>
              <span class="body">
                <span class="title">{{ it.item.title }}</span>
                <span class="meta">
                  <span v-if="it.item.location" class="muted small truncate">{{ it.item.location }}</span>
                  <UiBadge v-if="it.kind === 'task'" tone="ok">task</UiBadge>
                  <UiBadge v-if="it.kind === 'linked'" tone="ok">linked</UiBadge>
                  <UiBadge v-if="it.kind === 'recurring'" tone="neutral">recurring</UiBadge>
                  <span v-if="it.kind === 'suggest'" class="muted small truncate">{{ it.suggestion.reason }}</span>
                </span>
              </span>
              <span v-if="it.kind === 'suggest'" class="sactions">
                <button type="button" class="s-btn ok" :aria-label="'Accept: ' + it.item.title" @click.stop="emit('accept', it.suggestion)"><PhCheck weight="bold" /></button>
                <button type="button" class="s-btn no" :aria-label="'Deny: ' + it.item.title" @click.stop="emit('deny', it.suggestion)"><PhX weight="bold" /></button>
              </span>
            </div>
          </li>
          <li v-if="nowIndex === -1 && store.anchor === today() && dayItems.length" class="tail"><div class="nowrow"><span class="dot"></span><span class="rule"></span><span class="t num">{{ String(Math.floor(nowMinutes / 60)).padStart(2, '0') }}:{{ String(nowMinutes % 60).padStart(2, '0') }}</span></div></li>
        </ul>
      </section>
      <p class="hint muted small">Swipe the list to change day</p>
    </template>
  </div>
</template>

<style scoped>
.magenda { display: flex; flex-direction: column; gap: var(--sp-4); }
.head { display: flex; align-items: center; justify-content: space-between; gap: var(--sp-2); }
.head h1 { font-size: var(--fs-2xl); }
.status { display: flex; align-items: center; gap: 8px; font-size: var(--fs-sm); color: var(--ink-3); }
.sync { border: 0; background: none; padding: 0; }
.spacer { flex: 1; }
.mini { display: grid; grid-template-columns: 30px repeat(7, minmax(0, 1fr)); background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-lg); overflow: hidden; font-size: var(--fs-xs); }
.corner { border-bottom: 1px solid var(--line); }
.dhead { border: 0; border-left: 1px solid var(--line); border-bottom: 1px solid var(--line); padding: 6px 0; background: transparent; color: var(--ink-2); display: flex; flex-direction: column; align-items: center; line-height: 1.3; }
.dhead.today { background: var(--brand-soft); color: var(--brand); }
.dhead .wd { font-size: 10px; letter-spacing: 0.02em; font-weight: 500; }
.dhead .dn { font-size: 13px; font-weight: 600; }
.gutter { position: relative; }
.hl { position: absolute; right: 4px; font-size: 10px; color: var(--ink-3); transform: translateY(-50%); }
.col { position: relative; border-left: 1px solid var(--line); }
.col.today { background: color-mix(in srgb, var(--brand-soft) 35%, transparent); }
.line { position: absolute; left: 0; right: 0; border-top: 1px solid var(--line); opacity: 0.7; pointer-events: none; }
.now { position: absolute; left: 0; right: 0; border-top: 2px solid var(--brand); z-index: 3; pointer-events: none; }
.now::before { content: ''; position: absolute; left: -1px; top: -4px; width: 6px; height: 6px; border-radius: 50%; background: var(--brand); }
.blk { --accent: var(--info); position: absolute; left: 2px; right: 2px; border-radius: 4px; overflow: hidden; background: var(--info-soft); border: 1px solid color-mix(in srgb, var(--accent) 35%, transparent); border-left: 3px solid var(--accent); padding: 2px 3px; z-index: 2; display: flex; flex-direction: column; line-height: 1.2; }
.blk.recurring { --accent: var(--ink-3); background: var(--surface-2); }
.blk.linked { --accent: var(--ok); background: var(--ok-soft); }
.blk.task { --accent: var(--ok); background: var(--surface); border-style: dashed; }
.blk.suggest { --accent: var(--ok); background: color-mix(in srgb, var(--ok) 10%, var(--surface)); border-style: dashed; border-width: 1.5px; }
.blk.suggest.event { --accent: var(--info); }
.bt { font-size: 9px; color: var(--accent); font-weight: 500; }
.bn { font-size: 10px; font-weight: 500; color: var(--ink); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.hint { text-align: center; margin: 0; }
.strip { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 4px; }
.dbtn { height: 52px; border: 0; border-radius: var(--r-md); background: var(--surface); color: var(--ink-2); box-shadow: 0 0 0 1px var(--line) inset; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; transition: background-color var(--dur-hover) ease, color var(--dur-hover) ease, transform var(--dur-press) var(--ease-out); }
.dbtn:active { transform: scale(0.96); }
.dbtn.today { background: var(--brand-soft); color: var(--brand); }
.dbtn.active { background: var(--ink); color: var(--on-ink); box-shadow: none; }
.dbtn .wd { font-size: var(--fs-xs); letter-spacing: 0.02em; font-weight: 500; }
.dbtn .dn { font-size: var(--fs-lg); font-weight: 600; }
.daylist { padding: 4px 16px; margin: 0; touch-action: pan-y; user-select: none; }
.empty-wrap { padding: 12px 0; }
.daylist li { border-top: 1px solid var(--line); }
.daylist li.first { border-top: 0; }
.daylist li.tail { border-top: 0; padding-bottom: 8px; }
.nowrow { display: flex; align-items: center; gap: 8px; height: 0; position: relative; z-index: 1; }
.nowrow .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--brand); flex: none; margin-left: -4px; }
.nowrow .rule { flex: 1; border-top: 2px solid var(--brand); }
.nowrow .t { font-size: var(--fs-xs); color: var(--brand); font-weight: 500; }
.row { display: flex; gap: 12px; padding: 12px 0; align-items: flex-start; }
.times { color: var(--ink-3); font-size: var(--fs-sm); width: 40px; flex: none; display: flex; flex-direction: column; line-height: 1.5; }
.times .s { color: var(--ink); }
.bar { --accent: var(--info); width: 3px; border-radius: 2px; background: var(--accent); align-self: stretch; flex: none; }
.row.recurring .bar { --accent: var(--ink-3); }
.row.linked .bar, .row.task .bar, .row.suggest .bar { --accent: var(--ok); }
.row.suggest { border: 1.5px dashed var(--ok); border-radius: var(--r-md); padding: 8px 8px; margin: 6px 0; background: color-mix(in srgb, var(--ok) 8%, var(--surface)); }
.body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.title { font-size: var(--fs-base); font-weight: 500; line-height: 1.35; }
.meta { display: flex; gap: 8px; align-items: center; min-width: 0; }
.sactions { display: inline-flex; gap: 4px; align-self: center; }
.s-btn { width: 28px; height: 28px; border-radius: 50%; border: 0; display: inline-flex; align-items: center; justify-content: center; padding: 0; }
.s-btn.ok { background: var(--ok); color: #fff; }
.s-btn.no { background: var(--surface-3); color: var(--ink-2); }
</style>

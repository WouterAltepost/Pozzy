<script setup>
// Phone agenda (design: Pozzy Phone, Agenda). Week: a compact grid, 30px per hour from 07:00,
// tap a day to open it. Day: a seven-day strip and a list of the day's events with the now line;
// swipe the list to change day. Planner suggestions show as dashed blocks and dashed rows.
// iOS layer: it reads like Calendar's day list. Large title, the week strip with today's number
// in the tint, one inset grouped plate per day with a coloured bar per event; Plan and New event
// sit in the nav bar (AgendaView). A long press on a row opens its context menu.
import { computed, ref } from 'vue'
import { PhArrowSquareOut, PhCaretLeft, PhCaretRight, PhCheck, PhPencilSimple, PhTrash, PhX } from '@phosphor-icons/vue'
import { useContextMenu } from '../../composables/useContextMenu'
import { useDrag } from '../../composables/useDrag'
import { useLongPress } from '../../composables/useLongPress'
import { createSpring, project, reducedMotion } from '../../lib/spring'
import { formatDay, formatTime, mondayOf, shortDay, today, weekDays } from '../../lib/dates'
import { useCalendarStore } from '../../stores/calendar'
import UiEmpty from '../ui/UiEmpty.vue'
import UiSegmented from '../ui/UiSegmented.vue'

const props = defineProps({ suggestions: { type: Array, default: () => [] }, planning: { type: Boolean, default: false }, deciding: { type: Object, default: () => ({}) } })
const emit = defineEmits(['select-event', 'create', 'plan', 'accept', 'deny', 'delete-event'])
const store = useCalendarStore()
const menu = useContextMenu()

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
  if (store.view === 'week') return `${store.events.length} ${store.events.length === 1 ? 'event' : 'events'}`
  const n = dayItems.value.filter((i) => i.kind !== 'suggest').length
  return `${n} ${n === 1 ? 'event' : 'events'}`
})
const synced = computed(() => (store.account?.last_synced_at ? `Synced ${formatTime(store.account.last_synced_at)}` : store.account ? 'Not synced' : 'No calendar'))
const syncTone = computed(() => (store.account?.last_sync_error ? 'danger' : store.account ? 'ok' : 'neutral'))
const dayTitle = computed(() => (store.anchor === today() ? 'Today' : new Date(`${store.anchor}T12:00:00`).toLocaleDateString('en-GB', { weekday: 'long' })))
const opens = (it) => it.kind === 'event' || it.kind === 'linked' || it.kind === 'recurring'
function metaOf(it) {
  const out = []
  if (it.item.location) out.push(it.item.location)
  if (it.kind === 'task') out.push('Scheduled task')
  if (it.kind === 'linked') out.push('Linked task')
  if (it.kind === 'recurring') out.push('Recurring')
  if (it.kind === 'suggest' && it.suggestion.reason) out.push(it.suggestion.reason)
  return out.join(' \u00B7 ')
}

// Long press: the row's actions, the same ones a tap and the sheet offer, in one place.
const press = useLongPress((it, evt) => {
  // The timer fires after the event has finished dispatching, so its currentTarget is gone;
  // the composable kept the row for us (a right-click arrives live and still has it).
  const el = press.target() || evt?.currentTarget
  if (it.kind === 'suggest') {
    return menu.open(el, [
      { label: 'Accept', icon: PhCheck, action: () => emit('accept', it.suggestion) },
      { label: 'Deny', icon: PhX, danger: true, action: () => emit('deny', it.suggestion) },
    ])
  }
  if (!opens(it)) return
  if (it.kind === 'recurring') return menu.open(el, [{ label: 'Open', icon: PhArrowSquareOut, action: () => emit('select-event', it.item) }])
  menu.open(el, [
    { label: 'Edit', icon: PhPencilSimple, action: () => emit('select-event', it.item) },
    { label: 'Delete', icon: PhTrash, danger: true, action: () => emit('delete-event', it.item) },
  ])
})
function tapRow(it) {
  if (press.consumed() || swipe.wasDrag()) return
  if (opens(it)) emit('select-event', it.item)
}

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
// Day swipe: the list tracks the finger 1:1. On release the flick is projected forward; past a
// third of the width (or a fast flick) the list leaves at the finger's speed, the day changes,
// and the new day's list arrives from the other side carrying the same velocity.
const listEl = ref(null)
const listX = ref(0)
let pendingStep = 0
const listSpring = createSpring({
  value: 0,
  damping: 1,
  response: 0.34,
  onUpdate: (v) => (listX.value = v),
  onRest: () => {
    if (!pendingStep) return
    const dir = pendingStep
    pendingStep = 0
    store.step(dir)
    const w = listEl.value?.offsetWidth || 360
    listSpring.jump(dir * w * 0.5)
    listSpring.set(0, { velocity: -dir * Math.max(600, Math.abs(listSpring.velocity)) })
  },
})
let startX = 0
const swipe = useDrag({
  axis: 'x',
  onStart: () => {
    startX = pendingStep ? 0 : listSpring.value
    pendingStep = 0
    listSpring.stop()
  },
  onMove: ({ dx }) => listSpring.jump(startX + dx),
  onEnd: ({ vx }) => {
    const w = listEl.value?.offsetWidth || 360
    if (reducedMotion()) {
      const dir = Math.abs(vx) > 250 ? (vx < 0 ? 1 : -1) : Math.abs(listSpring.value) > w / 3 ? (listSpring.value < 0 ? 1 : -1) : 0
      listSpring.jump(0)
      if (dir) store.step(dir)
      return
    }
    const rest = listSpring.value + project(vx)
    const dir = Math.abs(vx) > 250 ? (vx < 0 ? 1 : -1) : Math.abs(rest) > w / 3 ? (rest < 0 ? 1 : -1) : 0
    if (dir) {
      pendingStep = dir
      listSpring.set(-dir * w, { velocity: vx, response: 0.3 })
    } else {
      listSpring.set(0, { velocity: vx, response: 0.34 })
    }
  },
})
const listStyle = computed(() => ({ transform: `translate3d(${listX.value}px, 0, 0)`, opacity: listEl.value ? Math.max(0.2, 1 - Math.abs(listX.value) / (listEl.value.offsetWidth || 360)) : 1 }))
function dayNum(day) {
  return Number(day.slice(8))
}
function wd(day) {
  return shortDay(day).slice(0, 3)
}
// The strip shows one letter per day, as Calendar does.
function letter(day) {
  return shortDay(day).slice(0, 1)
}
</script>

<template>
  <div class="magenda">
    <div class="head">
      <h1>Agenda</h1>
      <span class="sub">{{ store.view === 'week' ? 'Week of ' + formatDay(week[0]) : formatDay(store.anchor) }}</span>
    </div>
    <UiSegmented v-model="view" :options="VIEWS" class="views" />
    <div class="status">
      <button type="button" class="icon-btn" aria-label="Previous week" @click="stepWeek(-1)"><PhCaretLeft /></button>
      <span class="mid">
        <button type="button" class="sync" :class="syncTone" :disabled="!store.account || store.syncing" @click="store.sync()">
          <span class="dot" aria-hidden="true"></span>{{ store.syncing ? 'Syncing' : synced }}
        </button>
        <template v-if="store.view === 'week'">
          <span class="sep" aria-hidden="true">&middot;</span>
          <span class="num">{{ count }}</span>
        </template>
      </span>
      <button type="button" class="icon-btn" aria-label="Next week" @click="stepWeek(1)"><PhCaretRight /></button>
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
      <p class="hint">Tap a day to open it</p>
    </template>

    <template v-else>
      <div class="strip">
        <button v-for="day in week" :key="day" type="button" class="dbtn" :class="{ active: day === store.anchor, today: day === today() }" :aria-pressed="day === store.anchor" :aria-label="formatDay(day)" @click="pickDay(day)">
          <span class="wd">{{ letter(day) }}</span><span class="dn num">{{ dayNum(day) }}</span>
        </button>
      </div>
      <section ref="listEl" class="card daylist" v-bind="swipe.handlers" @dragstart.prevent>
        <div class="daybody" :style="listStyle">
        <header class="dayhead">
          <h2>{{ dayTitle }}</h2>
          <span class="num">{{ count }}</span>
        </header>
        <div v-if="!dayItems.length" class="empty-wrap">
          <UiEmpty compact title="No events" hint="Nothing on the calendar mirror for this day." />
        </div>
        <ul v-else>
          <li v-for="(it, i) in dayItems" :key="(it.item.id || it.item.title) + it.from" :class="{ first: i === 0 }">
            <div v-if="i === nowIndex" class="nowrow"><span class="dot"></span><span class="rule"></span><span class="t num">{{ String(Math.floor(nowMinutes / 60)).padStart(2, '0') }}:{{ String(nowMinutes % 60).padStart(2, '0') }}</span></div>
            <div class="row" :class="[it.kind, { opens: opens(it) }]" v-bind="press.handlers(it)" @click="tapRow(it)">
              <span class="times num"><span class="s">{{ formatTime(it.item.start) }}</span><span class="e">{{ formatTime(it.item.end) }}</span></span>
              <span class="ebar"></span>
              <span class="body">
                <span class="title">{{ it.item.title }}</span>
                <span v-if="metaOf(it)" class="meta">{{ metaOf(it) }}</span>
              </span>
              <span v-if="it.kind === 'suggest'" class="sactions">
                <button type="button" class="s-btn ok" :aria-label="'Accept: ' + it.item.title" :disabled="deciding[it.suggestion.id]" :aria-busy="deciding[it.suggestion.id] || undefined" @click.stop="emit('accept', it.suggestion)"><span v-if="deciding[it.suggestion.id]" class="spin" aria-hidden="true"></span><PhCheck v-else weight="bold" /></button>
                <button type="button" class="s-btn no" :aria-label="'Deny: ' + it.item.title" :disabled="deciding[it.suggestion.id]" @click.stop="emit('deny', it.suggestion)"><PhX weight="bold" /></button>
              </span>
              <PhCaretRight v-else-if="opens(it)" class="chev" aria-hidden="true" />
            </div>
          </li>
          <li v-if="nowIndex === -1 && store.anchor === today() && dayItems.length" class="tail"><div class="nowrow"><span class="dot"></span><span class="rule"></span><span class="t num">{{ String(Math.floor(nowMinutes / 60)).padStart(2, '0') }}:{{ String(nowMinutes % 60).padStart(2, '0') }}</span></div></li>
        </ul>
        </div>
      </section>
      <p class="hint">Swipe the list to change day</p>
    </template>
  </div>
</template>

<style scoped>
/* This component only renders on the phone (AgendaView, under 700px), so it is all iOS layer. */
.magenda { display: flex; flex-direction: column; gap: var(--sp-3); }
.head { display: flex; flex-direction: column; gap: 0; margin-top: 4px; }
.sub { font-size: 0.9375rem; color: var(--ink-3); }
.views { display: flex; width: 100%; }
.views :deep(.seg-item) { flex: 1; }
/* One tidy row: week back and forward at the ends, the sync state and the count between. */
.status { display: flex; align-items: center; gap: 4px; margin: -4px -8px 0; font-size: 0.8125rem; color: var(--ink-3); }
.status .icon-btn { width: 44px; height: 36px; flex: none; }
.mid { flex: 1; min-width: 0; display: flex; align-items: center; justify-content: center; gap: 6px; white-space: nowrap; }
.mid .num { overflow: hidden; text-overflow: ellipsis; }
.sep { color: var(--ink-4); }
.sync { display: inline-flex; align-items: center; gap: 6px; min-height: 36px; padding: 0; border: 0; background: none; color: var(--ink-3); font: inherit; }
.sync:disabled { opacity: 1; }
.sync .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--ink-4); }
.sync.ok .dot { background: var(--ok); }
.sync.danger { color: var(--danger); }
.sync.danger .dot { background: var(--danger); }
.mini { display: grid; grid-template-columns: 30px repeat(7, minmax(0, 1fr)); background: var(--surface); border-radius: var(--r-lg); overflow: hidden; font-size: var(--fs-xs); }
.corner { border-bottom: 0.5px solid var(--line-2); }
.dhead { border: 0; border-left: 0.5px solid var(--line); border-bottom: 0.5px solid var(--line-2); padding: 6px 0; background: transparent; color: var(--ink); display: flex; flex-direction: column; align-items: center; gap: 2px; line-height: 1.2; }
.dhead .wd { font-size: 11px; color: var(--ink-3); }
.dhead .dn { display: grid; place-items: center; width: 26px; height: 26px; border-radius: 50%; font-size: 15px; font-weight: 500; }
.dhead.today .wd { color: var(--brand); }
.dhead.today .dn { background: var(--brand); color: #fff; font-weight: 600; }
.gutter { position: relative; }
.hl { position: absolute; right: 4px; font-size: 10px; color: var(--ink-3); transform: translateY(-50%); }
.col { position: relative; border-left: 0.5px solid var(--line); }
.col.today { background: color-mix(in srgb, var(--brand) 5%, transparent); }
.line { position: absolute; left: 0; right: 0; border-top: 0.5px solid var(--line); pointer-events: none; }
.now { position: absolute; left: 0; right: 0; border-top: 2px solid var(--brand); z-index: 3; pointer-events: none; }
.now::before { content: ''; position: absolute; left: -1px; top: -4px; width: 6px; height: 6px; border-radius: 50%; background: var(--brand); }
/* Calendar's blocks: a tint of the calendar colour with a solid bar on the leading edge. */
.blk { --accent: var(--info); position: absolute; left: 1px; right: 1px; border-radius: 4px; overflow: hidden; background: color-mix(in srgb, var(--accent) 18%, var(--surface)); border-left: 3px solid var(--accent); padding: 2px 3px; z-index: 2; display: flex; flex-direction: column; line-height: 1.2; }
.blk.recurring { --accent: #8E8E93; }
.blk.linked { --accent: var(--ok); }
.blk.task { --accent: var(--ok); background: var(--surface); border: 1px dashed var(--accent); border-left: 3px solid var(--accent); }
.blk.suggest { --accent: var(--ok); background: color-mix(in srgb, var(--ok) 10%, var(--surface)); border: 1.5px dashed var(--accent); }
.blk.suggest.event { --accent: var(--info); }
.bt { font-size: 9px; color: var(--accent); font-weight: 600; }
.bn { font-size: 10px; font-weight: 500; color: var(--ink); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.hint { text-align: center; margin: 0; font-size: 0.8125rem; color: var(--ink-3); }
/* The week strip: a letter over the number, the chosen day in a filled circle (tint when it
   is today), today's number in the tint otherwise. */
.strip { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); }
.dbtn { height: 56px; padding: 0; border: 0; background: transparent; color: var(--ink); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; }
.dbtn .wd { font-size: 0.6875rem; font-weight: 500; color: var(--ink-3); }
.dbtn .dn { display: grid; place-items: center; width: 34px; height: 34px; border-radius: 50%; font-size: 1.25rem; font-weight: 400; transition: background-color 200ms ease, color 200ms ease; }
.dbtn:active .dn { background: var(--surface-2); }
.dbtn.today .dn { color: var(--brand); font-weight: 600; }
.dbtn.active .dn { background: var(--ink); color: var(--bg); font-weight: 600; }
.dbtn.active.today .dn { background: var(--brand); color: #fff; }
.daylist { padding: 0; margin: 0; touch-action: pan-y; user-select: none; -webkit-user-select: none; overflow: hidden; }
.daybody { will-change: transform; }
.dayhead { display: flex; align-items: baseline; justify-content: space-between; gap: var(--sp-2); padding: 12px 16px 4px; }
.dayhead h2 { font-size: 1.0625rem; font-weight: 600; }
.dayhead .num { font-size: 0.9375rem; color: var(--ink-3); }
.empty-wrap { padding: 4px 16px 12px; }
.daylist ul { padding-bottom: 4px; }
.daylist li { position: relative; }
.daylist li + li:not(.tail)::before { content: ''; position: absolute; top: 0; left: 16px; right: 0; border-top: 0.5px solid var(--line-2); }
.daylist li.tail { padding: 0 16px 8px; }
.nowrow { display: flex; align-items: center; gap: 8px; height: 0; position: relative; z-index: 1; margin: 0 16px 0 12px; }
.daylist li.tail .nowrow { margin: 0; }
.nowrow .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--brand); flex: none; }
.nowrow .rule { flex: 1; border-top: 2px solid var(--brand); }
.nowrow .t { font-size: 0.75rem; color: var(--brand); font-weight: 600; }
.row { display: flex; gap: 10px; min-height: 44px; padding: 10px 16px; align-items: stretch; }
.times { color: var(--ink-3); font-size: 0.9375rem; width: 44px; flex: none; display: flex; flex-direction: column; line-height: 20px; }
.times .e { font-size: 0.8125rem; }
/* Not .bar: that is the global progress bar class, which would flatten this to 4px tall. */
.ebar { --accent: var(--info); width: 4px; border-radius: 2px; background: var(--accent); flex: none; }
.row.recurring .ebar { --accent: #8E8E93; }
.row.linked .ebar, .row.task .ebar, .row.suggest .ebar { --accent: var(--ok); }
.row.suggest { margin: 6px 12px; padding: 8px; border: 1.5px dashed var(--ok); border-radius: var(--r-md); background: color-mix(in srgb, var(--ok) 8%, var(--surface)); }
.body { flex: 1; min-width: 0; display: flex; flex-direction: column; justify-content: center; gap: 1px; }
.title { font-size: 1.0625rem; line-height: 22px; }
.meta { font-size: 0.9375rem; line-height: 20px; color: var(--ink-3); overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.chev { width: 14px; height: 14px; flex: none; align-self: center; color: var(--ink-4); }
.sactions { display: inline-flex; gap: 6px; align-self: center; }
.s-btn { width: 30px; height: 30px; border-radius: 50%; border: 0; display: inline-flex; align-items: center; justify-content: center; padding: 0; }
.s-btn.ok { background: var(--ok); color: #fff; }
.s-btn.no { background: var(--surface-2); color: var(--ink-2); }
.spin { display: inline-block; width: 14px; height: 14px; border-radius: 50%; border: 2px solid currentColor; border-right-color: transparent; animation: spin 700ms linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .spin { animation: none; border-right-color: currentColor; opacity: 0.5; } }
</style>

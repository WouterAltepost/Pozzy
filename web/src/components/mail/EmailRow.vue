<script setup>
// One email in the list. Desktop: the dense row with badges and a handled checkbox. Phone
// (`ios`): an iOS Mail cell inside the grouped plate: sender bold, time on the right, subject,
// one line of summary, a dot on the left for what needs attention. Swipe right marks it
// handled, swipe left makes a task, a long press opens the context menu. The view owns the
// writes; this only says what was asked.
import { computed, ref } from 'vue'
import { PhArrowCounterClockwise, PhArrowSquareOut, PhCaretRight, PhCheck, PhCheckSquare, PhEnvelopeOpen } from '@phosphor-icons/vue'
import { formatDateTime } from '../../lib/dates'
import { accountName } from '../../lib/mail'
import AreaDot from '../shared/AreaDot.vue'
import SwipeRow from '../ios/SwipeRow.vue'
import UiBadge from '../ui/UiBadge.vue'
import PriorityBadge from './PriorityBadge.vue'
import { useContextMenu } from '../../composables/useContextMenu'
import { useLongPress } from '../../composables/useLongPress'

const props = defineProps({ email: { type: Object, required: true }, active: { type: Boolean, default: false }, ios: { type: Boolean, default: false } })
const emit = defineEmits(['open', 'handled', 'task'])
const menu = useContextMenu()
const cell = ref(null)

// iOS Mail dates: the time today, "Yesterday", the weekday within a week, else the date.
const when = computed(() => {
  const d = new Date(props.email.date)
  if (Number.isNaN(d.getTime())) return ''
  const now = new Date()
  const startOf = (x) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime()
  const days = Math.round((startOf(now) - startOf(d)) / 86400000)
  if (days <= 0) return d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
  if (days === 1) return 'Yesterday'
  if (days < 7) return d.toLocaleDateString('en-GB', { weekday: 'long' })
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'numeric', year: '2-digit' })
})
const preview = computed(() => {
  const e = props.email
  if (e.summary && e.summary !== e.subject) return e.summary
  return (e.snippet || '').split('\n').find((l) => l.trim()) || ''
})
// The dot says why a row wants attention: urgent red, important orange, a reply owed blue.
const dot = computed(() => {
  const e = props.email
  if (e.handled) return null
  if (e.priority === 1) return { tone: 'p1', label: 'Urgent' }
  if (e.priority === 2) return { tone: 'p2', label: 'Important' }
  if (e.needs_reply) return { tone: 'reply', label: 'Needs a reply' }
  return null
})

const leading = computed(() => [
  props.email.handled
    ? { label: 'Unhandle', icon: PhArrowCounterClockwise, color: '#8E8E93', action: () => emit('handled', props.email, false) }
    : { label: 'Handled', icon: PhCheck, color: 'var(--ok)', action: () => emit('handled', props.email, true) },
])
const trailing = computed(() => [{ label: 'Task', icon: PhCheckSquare, color: 'var(--warn)', action: () => emit('task', props.email) }])

const press = useLongPress(() => {
  const e = props.email
  menu.open(cell.value, [
    { label: 'Open', icon: PhEnvelopeOpen, action: () => emit('open', e) },
    e.handled
      ? { label: 'Mark unhandled', icon: PhArrowCounterClockwise, action: () => emit('handled', e, false) }
      : { label: 'Mark handled', icon: PhCheck, action: () => emit('handled', e, true) },
    { label: e.task_id ? 'Task exists' : 'Create task', icon: PhCheckSquare, action: () => emit('task', e) },
    e.gmail_url ? { label: 'Open in Gmail', icon: PhArrowSquareOut, action: () => window.open(e.gmail_url, '_blank', 'noopener') } : null,
  ])
})
function tap() {
  if (press.consumed()) return
  emit('open', props.email)
}
</script>

<template>
  <li v-if="ios" class="cell-li">
    <SwipeRow :leading="leading" :trailing="trailing">
      <button ref="cell" type="button" class="cell pressable" :class="{ handled: email.handled }" v-bind="press.handlers()" @click="tap">
        <span class="dot" :class="dot?.tone" :title="dot?.label" aria-hidden="true"></span>
        <span class="cbody">
          <span class="l1">
            <span class="sender truncate">{{ email.from_name || email.from_email }}</span>
            <span class="when num">{{ when }}</span>
            <PhCaretRight class="chev" weight="bold" aria-hidden="true" />
          </span>
          <span class="l2">
            <span class="subj truncate">{{ email.subject || '(no subject)' }}</span>
            <span v-if="email.account?.label" class="c-acct" :style="{ color: email.account?.color || 'var(--ink-3)' }">{{ email.account.label }}</span>
          </span>
          <span v-if="preview" class="l3">{{ preview }}</span>
          <span v-if="dot" class="visually-hidden">{{ dot.label }}</span>
        </span>
      </button>
    </SwipeRow>
  </li>
  <li v-else class="row" :class="{ active, handled: email.handled, reply: email.needs_reply }">
    <span class="account" :style="{ background: email.account?.color || 'var(--ink-3)' }" :title="accountName(email.account)"></span>
    <button type="button" class="open" @click="emit('open', email)">
      <span class="line1">
        <PriorityBadge :priority="email.priority" />
        <span class="acct truncate" :style="{ color: email.account?.color || 'var(--ink-2)' }">{{ accountName(email.account) }}</span>
        <span v-if="email.account?.label" class="tag">{{ email.account.label }}</span>
        <span class="from truncate">{{ email.from_name || email.from_email }}</span>
        <span class="tag">{{ email.category }}</span>
        <UiBadge v-if="email.needs_reply" tone="info">reply</UiBadge>
        <AreaDot :area-id="email.area_id" />
        <span class="date muted xs num">{{ formatDateTime(email.date) }}</span>
      </span>
      <span class="subject truncate">{{ email.subject }}</span>
      <span v-if="email.summary && email.summary !== email.subject" class="summary truncate">{{ email.summary }}</span>
    </button>
    <input
      type="checkbox"
      class="tick"
      :checked="email.handled"
      title="Mark handled"
      :aria-label="'Mark handled: ' + email.subject"
      @change="emit('handled', email, $event.target.checked)"
    />
  </li>
</template>

<style scoped>
.row { display: flex; align-items: stretch; gap: var(--sp-2); padding: 6px var(--sp-3) 6px 6px; background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-md); transition: border-color var(--dur-hover) ease, box-shadow var(--dur-hover) ease, opacity var(--dur-hover) ease; }
.row.active { border-color: var(--ink); box-shadow: 0 0 0 1px var(--ink) inset; }
.row.handled { opacity: 0.6; }
@media (hover: hover) and (pointer: fine) { .row:not(.active):hover { border-color: var(--line-2); box-shadow: var(--shadow-1); } }
.account { width: 3px; border-radius: 2px; flex: none; }
.open { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; text-align: left; padding: 2px 4px; border: 0; background: none; color: inherit; font: inherit; cursor: pointer; border-radius: var(--r-sm); }
.line1 { display: flex; align-items: center; gap: 6px; min-width: 0; }
.acct { font-size: var(--fs-xs); font-weight: 600; letter-spacing: 0.01em; max-width: 30%; }
.from { color: var(--ink); font-weight: 500; font-size: var(--fs-md); max-width: 36%; }
.date { margin-left: auto; white-space: nowrap; }
.subject { font-size: var(--fs-base); }
.summary { font-size: var(--fs-sm); color: var(--ink-3); }
.tick { align-self: center; }

/* iOS Mail cell. The separator starts at the text, past the dot column. */
.cell-li { position: relative; }
.cell-li + .cell-li::before { content: ''; position: absolute; z-index: 2; top: 0; left: 28px; right: 0; height: 0.5px; background: var(--line); pointer-events: none; }
.cell { display: flex; align-items: flex-start; width: 100%; padding: 10px 16px 11px 0; border: 0; border-radius: 0; background: none; box-shadow: none; color: var(--ink); font: inherit; text-align: left; }
.dot { flex: none; width: 10px; height: 10px; margin: 6px 9px 0; border-radius: 50%; }
.dot.p1 { background: var(--danger); }
.dot.p2 { background: var(--warn); }
.dot.reply { background: var(--brand); }
.cbody { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.l1, .l2 { display: flex; align-items: baseline; gap: 6px; min-width: 0; }
.sender { flex: 1; min-width: 0; font-size: 1.0625rem; font-weight: 600; line-height: 1.3; }
.when { flex: none; font-size: 0.9375rem; color: var(--ink-3); }
.chev { flex: none; width: 12px; height: 12px; color: var(--ink-4); align-self: center; }
.subj { flex: 1; min-width: 0; font-size: 0.9375rem; line-height: 1.35; }
.c-acct { flex: none; max-width: 40%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 0.75rem; font-weight: 600; letter-spacing: 0; }
.l3 { font-size: 0.9375rem; line-height: 1.35; color: var(--ink-3); display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; overflow: hidden; }
.cell.handled .sender { font-weight: 500; }
@media (min-resolution: 2dppx) { .cell-li + .cell-li::before { height: 1px; transform: scaleY(0.5); transform-origin: top; } }
@media (max-width: 699px) {
  .row { padding: 8px 10px 8px 6px; }
  .line1 .tag, .line1 :deep(.area-dot) { display: none; }
  .from { max-width: 46%; }
  .subject { font-size: var(--fs-md); }
  .summary { display: none; }
}
</style>

<script setup>
import { formatDateTime } from '../../lib/dates'
import AreaDot from '../shared/AreaDot.vue'
import UiBadge from '../ui/UiBadge.vue'
import PriorityBadge from './PriorityBadge.vue'

defineProps({ email: { type: Object, required: true }, active: { type: Boolean, default: false } })
const emit = defineEmits(['open', 'handled'])
</script>

<template>
  <li class="row" :class="{ active, handled: email.handled, reply: email.needs_reply }">
    <span class="account" :style="{ background: email.account?.color || 'var(--ink-3)' }" :title="email.account?.label"></span>
    <button type="button" class="open" @click="emit('open', email)">
      <span class="line1">
        <PriorityBadge :priority="email.priority" />
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
.from { color: var(--ink); font-weight: 500; font-size: var(--fs-md); max-width: 40%; }
.date { margin-left: auto; white-space: nowrap; }
.subject { font-size: var(--fs-base); }
.summary { font-size: var(--fs-sm); color: var(--ink-3); }
.tick { align-self: center; }
</style>

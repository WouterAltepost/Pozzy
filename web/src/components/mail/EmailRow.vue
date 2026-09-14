<script setup>
import { formatDateTime } from '../../lib/dates'
import AreaDot from '../shared/AreaDot.vue'
import PriorityBadge from './PriorityBadge.vue'

defineProps({ email: { type: Object, required: true }, active: { type: Boolean, default: false } })
const emit = defineEmits(['open', 'handled'])
</script>

<template>
  <li class="row" :class="{ active, handled: email.handled, reply: email.needs_reply }" @click="emit('open', email)">
    <span class="account" :style="{ background: email.account?.color || '#9ca3af' }" :title="email.account?.label"></span>
    <PriorityBadge :priority="email.priority" />
    <div class="main">
      <div class="line1">
        <span class="from">{{ email.from_name || email.from_email }}</span>
        <span class="category">{{ email.category }}</span>
        <span v-if="email.needs_reply" class="needs-reply">reply</span>
        <AreaDot :area-id="email.area_id" />
        <span class="date">{{ formatDateTime(email.date) }}</span>
      </div>
      <div class="subject">{{ email.subject }}</div>
      <div v-if="email.summary && email.summary !== email.subject" class="summary">{{ email.summary }}</div>
    </div>
    <input
      type="checkbox"
      :checked="email.handled"
      title="Mark handled"
      @click.stop
      @change="emit('handled', email, $event.target.checked)"
    />
  </li>
</template>

<style scoped>
.row { display: flex; align-items: flex-start; gap: 0.5rem; padding: 0.45rem 0.6rem; background: #fff; border: 1px solid #e5e7eb; border-radius: 4px; cursor: pointer; }
.row.active { border-color: #2563eb; }
.row.handled { opacity: 0.6; }
.account { width: 6px; align-self: stretch; border-radius: 3px; flex: none; }
.main { flex: 1; min-width: 0; }
.line1 { display: flex; flex-wrap: wrap; align-items: center; gap: 0.4rem; font-size: 0.78rem; color: #6b7280; }
.from { color: #1f2937; font-weight: 600; }
.category { background: #f3f4f6; padding: 0 0.3rem; border-radius: 3px; }
.needs-reply { background: #dbeafe; color: #1d4ed8; padding: 0 0.3rem; border-radius: 3px; font-weight: 600; }
.date { margin-left: auto; white-space: nowrap; }
.subject { font-size: 0.92rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.summary { font-size: 0.8rem; color: #6b7280; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
input[type='checkbox'] { margin-top: 0.3rem; }
</style>

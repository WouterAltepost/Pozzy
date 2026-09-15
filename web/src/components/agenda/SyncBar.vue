<script setup>
import { computed } from 'vue'
import { formatDateTime } from '../../lib/dates'
import { useCalendarStore } from '../../stores/calendar'
import UiBadge from '../ui/UiBadge.vue'
import UiButton from '../ui/UiButton.vue'

const store = useCalendarStore()
const status = computed(() => {
  const a = store.account
  if (!a) return 'No calendar account configured'
  if (!a.enabled) return 'Calendar sync disabled in Settings'
  return a.last_synced_at ? `Synced ${formatDateTime(a.last_synced_at)}` : 'Not synced yet'
})
</script>

<template>
  <div class="syncbar">
    <span class="muted small num">{{ status }}</span>
    <UiBadge v-if="store.account?.last_sync_error" tone="danger" :title="store.account.last_sync_error">sync error</UiBadge>
    <UiButton size="sm" :loading="store.syncing" :disabled="!store.account" @click="store.sync()">Sync now</UiButton>
    <span v-if="store.syncMessage" class="muted small msg truncate">{{ store.syncMessage }}</span>
  </div>
</template>

<style scoped>
.syncbar { display: flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap; }
.msg { max-width: 420px; }
</style>

<script setup>
import { computed } from 'vue'
import { formatDateTime } from '../../lib/dates'
import { useCalendarStore } from '../../stores/calendar'

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
    <span class="muted">{{ status }}</span>
    <span v-if="store.account?.last_sync_error" class="error" :title="store.account.last_sync_error">sync error</span>
    <button type="button" :disabled="store.syncing || !store.account" @click="store.sync()">{{ store.syncing ? 'Syncing...' : 'Sync now' }}</button>
    <span v-if="store.syncMessage" class="muted msg">{{ store.syncMessage }}</span>
  </div>
</template>

<style scoped>
.syncbar { display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; font-size: 0.85rem; }
.msg { max-width: 420px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>

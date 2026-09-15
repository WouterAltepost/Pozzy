<script setup>
import { computed, onMounted, ref } from 'vue'
import { formatDateTime } from '../../lib/dates'
import { useCalendarStore } from '../../stores/calendar'
import UiButton from '../ui/UiButton.vue'
import UiField from '../ui/UiField.vue'

// Mounted inside SettingsView's Integrations card. Self-contained:
// loads the account, lets Wouter pick which calendars sync and where Pozzy writes.
const store = useCalendarStore()
const selected = ref([])
const writeUrl = ref('')
const enabled = ref(true)
const busy = ref(false)
const message = ref('')

const account = computed(() => store.account)
const calendars = computed(() => account.value?.known_calendars || [])

function fill() {
  if (!account.value) return
  selected.value = [...account.value.calendar_urls]
  writeUrl.value = account.value.write_calendar_url || ''
  enabled.value = account.value.enabled
}

onMounted(async () => {
  await store.loadAccount()
  fill()
})

async function discover() {
  busy.value = true
  message.value = ''
  try {
    const list = await store.discover()
    fill()
    message.value = `Found ${list.length} calendars.`
  } catch {
    // store.accountError is shown
  } finally {
    busy.value = false
  }
}

async function save() {
  busy.value = true
  message.value = ''
  try {
    if (writeUrl.value && !selected.value.includes(writeUrl.value)) selected.value.push(writeUrl.value)
    await store.saveAccount({ calendar_urls: selected.value, write_calendar_url: writeUrl.value || null, enabled: enabled.value })
    fill()
    message.value = 'Saved. The next sync applies the selection.'
  } catch {
    // store.accountError is shown
  } finally {
    busy.value = false
  }
}

async function syncNow() {
  busy.value = true
  message.value = ''
  await store.sync()
  fill()
  message.value = store.syncMessage
  busy.value = false
}
</script>

<template>
  <div class="integration">
    <h3>iCloud calendar</h3>
    <p v-if="store.accountError" class="error">{{ store.accountError }}</p>
    <p v-if="!account" class="muted small">Not configured. Set ICLOUD_USERNAME and ICLOUD_APP_PASSWORD in the environment and restart the API.</p>
    <template v-else>
      <p class="small">
        <strong>{{ account.name }}</strong> <span class="muted">{{ account.username }}</span><br />
        <span class="muted num">{{ account.last_synced_at ? 'Last synced ' + formatDateTime(account.last_synced_at) : 'Never synced' }}</span>
        <span v-if="account.last_sync_error" class="error"> {{ account.last_sync_error }}</span>
      </p>
      <label class="check"><input v-model="enabled" type="checkbox" /> Sync enabled</label>
      <p v-if="!calendars.length" class="muted small">No calendars discovered yet.</p>
      <div v-else class="list">
        <label v-for="c in calendars" :key="c.url" class="check">
          <input v-model="selected" type="checkbox" :value="c.url" /> {{ c.name }}
        </label>
      </div>
      <UiField v-if="calendars.length" label="Pozzy writes new events to" class="write">
        <select v-model="writeUrl">
          <option v-for="c in calendars" :key="c.url" :value="c.url">{{ c.name }}</option>
        </select>
      </UiField>
      <div class="actions">
        <UiButton :loading="busy" @click="discover">{{ calendars.length ? 'Refresh calendar list' : 'Discover calendars' }}</UiButton>
        <UiButton variant="primary" :disabled="busy || !calendars.length" @click="save">Save calendars</UiButton>
        <UiButton :disabled="busy" @click="syncNow">Sync now</UiButton>
        <span class="muted small">{{ message }}</span>
      </div>
    </template>
  </div>
</template>

<style scoped>
.integration { display: flex; flex-direction: column; gap: var(--sp-2); padding-bottom: var(--sp-4); }
h3 { font-size: var(--fs-base); }
.check { display: flex; align-items: center; gap: 6px; font-size: var(--fs-md); }
.list { display: flex; flex-wrap: wrap; gap: var(--sp-2) var(--sp-4); }
.write { max-width: 320px; }
.actions { display: flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap; margin-top: var(--sp-1); }
</style>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useMediaQuery } from '../../composables/useMediaQuery'
import { formatDateTime } from '../../lib/dates'
import { tick } from '../../lib/haptics'
import { useCalendarStore } from '../../stores/calendar'
import { useSettingsStore } from '../../stores/settings'
import AreaSelect from '../shared/AreaSelect.vue'
import UiButton from '../ui/UiButton.vue'
import UiField from '../ui/UiField.vue'

// Mounted inside SettingsView's Integrations card. Self-contained:
// loads the account, lets Wouter pick which calendars sync and where Pozzy writes.
const store = useCalendarStore()
const settings = useSettingsStore()
const selected = ref([])
const calendarAreas = ref({}) // calendar url -> area id, for the hours suggestions
const writeUrl = ref('')
const enabled = ref(true)
const busy = ref(false)
const message = ref('')
// Phone: iOS Settings sections (account, calendars as switches, area and write target as
// pop-up rows, actions as tint rows).
const phone = useMediaQuery('(max-width: 1023px)')

const account = computed(() => store.account)
const calendars = computed(() => account.value?.known_calendars || [])
const selectedCalendars = computed(() => calendars.value.filter((c) => selected.value.includes(c.url)))

function fill() {
  if (!account.value) return
  selected.value = [...account.value.calendar_urls]
  writeUrl.value = account.value.write_calendar_url || ''
  enabled.value = account.value.enabled
}

onMounted(async () => {
  await Promise.all([store.loadAccount(), settings.values ? Promise.resolve() : settings.load()])
  fill()
  calendarAreas.value = { ...(settings.values?.calendar_areas || {}) }
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
    const calendar_areas = {}
    for (const [url, areaId] of Object.entries(calendarAreas.value)) if (areaId && selected.value.includes(url)) calendar_areas[url] = areaId
    await settings.save({ calendar_areas })
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
  <div v-if="phone" class="ios">
    <section class="ios-sec">
      <h2 class="ios-head">iCloud calendar</h2>
      <div class="ios-plate">
        <template v-if="account">
          <div class="ios-row"><span class="lbl">{{ account.name }}</span><span class="val truncate">{{ account.username }}</span></div>
          <label class="ios-row"><span class="lbl">Sync</span><input v-model="enabled" type="checkbox" role="switch" @change="tick()" /></label>
          <div class="ios-row"><span class="lbl">Last synced</span><span class="val num">{{ account.last_synced_at ? formatDateTime(account.last_synced_at) : 'Never' }}</span></div>
        </template>
        <div v-else class="ios-row"><span class="lbl">Not configured</span></div>
      </div>
      <p v-if="store.accountError" class="ios-foot err">{{ store.accountError }}</p>
      <p v-if="account?.last_sync_error" class="ios-foot err">{{ account.last_sync_error }}</p>
      <p v-if="!account" class="ios-foot">Set ICLOUD_USERNAME and ICLOUD_APP_PASSWORD in the environment and restart the API.</p>
    </section>
    <template v-if="account">
      <section class="ios-sec">
        <h2 class="ios-head">Calendars</h2>
        <div class="ios-plate">
          <label v-for="c in calendars" :key="c.url" class="ios-row"><span class="lbl truncate">{{ c.name }}</span><input v-model="selected" type="checkbox" role="switch" :value="c.url" @change="tick()" /></label>
          <div v-if="!calendars.length" class="ios-row"><span class="lbl muted">No calendars discovered yet</span></div>
          <label v-if="calendars.length" class="ios-row">
            <span class="lbl">New events go to</span>
            <select v-model="writeUrl" class="pick"><option v-for="c in calendars" :key="c.url" :value="c.url">{{ c.name }}</option></select>
          </label>
        </div>
      </section>
      <section v-if="selectedCalendars.length" class="ios-sec">
        <h2 class="ios-head">Area per calendar</h2>
        <div class="ios-plate">
          <label v-for="c in selectedCalendars" :key="c.url" class="ios-row">
            <span class="lbl truncate">{{ c.name }}</span>
            <AreaSelect v-model="calendarAreas[c.url]" class="pick" :aria-label="'Area for ' + c.name" />
          </label>
        </div>
        <p class="ios-foot">Hours from a calendar's events count for this area in the suggestions on the Hours page.</p>
      </section>
      <section class="ios-sec">
        <div class="ios-plate">
          <button type="button" class="ios-row act" :disabled="busy || !calendars.length" @click="save">Save calendars</button>
          <button type="button" class="ios-row act" :disabled="busy" @click="discover">{{ calendars.length ? 'Refresh calendar list' : 'Discover calendars' }}</button>
          <button type="button" class="ios-row act" :disabled="busy" @click="syncNow">Sync now</button>
        </div>
        <p v-if="message" class="ios-foot">{{ message }}</p>
      </section>
    </template>
  </div>
  <div v-else class="integration">
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
      <div v-if="selectedCalendars.length" class="areas">
        <span class="muted small">Hours from a calendar's events count for this area (used by the suggestions on the Hours page):</span>
        <div v-for="c in selectedCalendars" :key="c.url" class="arow">
          <span class="cname truncate">{{ c.name }}</span>
          <AreaSelect v-model="calendarAreas[c.url]" :aria-label="'Area for ' + c.name" />
        </div>
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
.areas { display: flex; flex-direction: column; gap: 6px; margin-top: var(--sp-1); }
.arow { display: grid; grid-template-columns: minmax(0, 160px) 180px; gap: var(--sp-2); align-items: center; }
.cname { font-size: var(--fs-md); }
.actions { display: flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap; margin-top: var(--sp-1); }

/* Phone: inset grouped sections, as in the iOS Settings app. */
@media (max-width: 1023px) {
  .ios-sec { margin-bottom: var(--sp-8); }
  .ios-head { margin: 0 16px 6px; font-size: 0.8125rem; font-weight: 400; text-transform: uppercase; color: var(--ink-3); }
  .ios-plate { background: var(--surface); border-radius: var(--r-lg); overflow: hidden; }
  .ios-row { position: relative; display: flex; align-items: center; gap: 12px; width: 100%; min-height: 44px; padding: 6px 16px; border: 0; background: none; color: var(--ink); font: inherit; font-size: 1.0625rem; text-align: left; }
  .ios-row + .ios-row::before { content: ''; position: absolute; top: 0; left: 16px; right: 0; height: 0.5px; background: var(--line-2); }
  .lbl { flex: 1; min-width: 0; }
  .val { max-width: 60%; color: var(--ink-3); }
  .act { color: var(--brand); }
  .act:active:not(:disabled) { background: var(--surface-3); }
  .act:disabled { color: var(--ink-4); }
  .ios-foot { margin: 6px 16px 0; font-size: 0.8125rem; line-height: 1.4; color: var(--ink-3); }
  .ios-foot.err { color: var(--danger); }
  /* A pop-up button: the value in grey with the up and down chevron, no field around it. */
  .pick { flex: none; width: auto; max-width: 55%; height: 32px; padding: 0 20px 0 0; background: transparent url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 256 256' fill='none' stroke='%238E8E93' stroke-width='22' stroke-linecap='round' stroke-linejoin='round'><polyline points='80 96 128 48 176 96'/><polyline points='80 160 128 208 176 160'/></svg>") right center / 13px no-repeat; color: var(--ink-3); text-align: right; text-align-last: right; }
  .pick:focus-visible { box-shadow: none; color: var(--ink); }
}
</style>

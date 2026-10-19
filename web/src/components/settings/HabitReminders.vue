<script setup>
// Habit reminders: turn push on for this device, send a test, and the master switch. Each habit
// sets its own reminder time in its editor. Honest about why push may not work here.
import { computed, onMounted, ref } from 'vue'
import { pushConfig, sendTestPush } from '../../api/push'
import { useToast } from '../../composables/useToast'
import { currentSubscription, disablePush, enablePush, isIos, isStandalone, pushSupported } from '../../lib/push'
import { useSettingsStore } from '../../stores/settings'
import UiBadge from '../ui/UiBadge.vue'
import UiButton from '../ui/UiButton.vue'

const settings = useSettingsStore()
const toast = useToast()
const config = ref(null)
const subscribed = ref(false)
const busy = ref('')
const error = ref('')
const supported = pushSupported()
const iosBrowser = isIos() && !isStandalone()
const permission = ref(supported ? Notification.permission : 'unsupported')
const enabled = computed(() => settings.values?.habit_reminders !== false)

async function refresh() {
  try {
    config.value = await pushConfig()
    subscribed.value = Boolean(await currentSubscription())
  } catch (err) {
    error.value = err.message
  }
}
onMounted(refresh)

async function run(name, fn) {
  busy.value = name
  error.value = ''
  try {
    await fn()
  } catch (err) {
    error.value = err.message
  } finally {
    busy.value = ''
    if (supported) permission.value = Notification.permission
    await refresh()
  }
}
const turnOn = () => run('on', async () => {
  await enablePush()
  toast.success('Notifications on for this device')
})
const turnOff = () => run('off', disablePush)
const test = () => run('test', async () => {
  const res = await sendTestPush()
  toast.success(res.sent ? `Test sent to ${res.sent} device${res.sent === 1 ? '' : 's'}` : 'No device accepted the test')
})
const toggle = () => run('switch', () => settings.save({ habit_reminders: !enabled.value }))

const status = computed(() => {
  if (!supported) return { tone: 'neutral', text: 'Not supported here' }
  if (permission.value === 'denied') return { tone: 'danger', text: 'Blocked' }
  if (subscribed.value) return { tone: 'ok', text: 'On for this device' }
  return { tone: 'neutral', text: 'Off for this device' }
})
</script>

<template>
  <section class="card">
    <div class="card-head">
      <h2>Habit reminders</h2>
      <span class="meta"><UiBadge :tone="status.tone">{{ status.text }}</UiBadge></span>
    </div>
    <p class="muted small">A push notification at the reminder time of each habit, only when it is due and still open. Set the time in a habit's editor.</p>
    <p v-if="iosBrowser" class="note small">On iPhone, notifications only work from the installed app: Share, Add to Home Screen, then open Pozzy from the home screen and turn them on here.</p>
    <p v-else-if="config && !config.configured" class="note small">The server has no VAPID keys yet, so nothing can be sent. Add VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY and VAPID_SUBJECT to the api service.</p>
    <p v-if="error" class="error">{{ error }}</p>
    <div class="row actions">
      <UiButton v-if="!subscribed" variant="primary" :loading="busy === 'on'" :disabled="!supported || iosBrowser || permission === 'denied' || !config?.configured" @click="turnOn">Turn on for this device</UiButton>
      <UiButton v-else :loading="busy === 'off'" @click="turnOff">Turn off for this device</UiButton>
      <UiButton :loading="busy === 'test'" :disabled="!config?.subscriptions || !config?.configured" @click="test">Send a test</UiButton>
      <span class="spacer"></span>
      <label class="check"><input type="checkbox" :checked="enabled" :disabled="busy === 'switch'" @change="toggle" /> Reminders on</label>
    </div>
    <p v-if="config" class="muted xs">{{ config.subscriptions }} device{{ config.subscriptions === 1 ? '' : 's' }} subscribed</p>
  </section>
</template>

<style scoped>
.note { padding: var(--sp-3); border-radius: var(--r-md); background: var(--warn-soft); color: var(--ink-2); }
.actions { margin: var(--sp-4) 0 var(--sp-2); }
.check { display: flex; align-items: center; gap: 6px; font-size: var(--fs-md); }
</style>

<script setup>
// Habit reminders: turn push on for this device, send a test, and the master switch. Each habit
// sets its own reminder time in its editor. Honest about why push may not work here.
import { computed, onMounted, ref } from 'vue'
import { pushConfig, sendTestPush } from '../../api/push'
import { useToast } from '../../composables/useToast'
import { currentSubscription, disablePush, enablePush, isIos, isStandalone, pushSupported } from '../../lib/push'
import { tick } from '../../lib/haptics'
import { useMediaQuery } from '../../composables/useMediaQuery'
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
const toggle = () => {
  tick()
  return run('switch', () => settings.save({ habit_reminders: !enabled.value }))
}
// The phone reads as an iOS Settings section: switch and status as rows, the actions as tint
// rows, the explanation as the footer under the plate.
const phone = useMediaQuery('(max-width: 1023px)')
const canTurnOn = computed(() => supported && !iosBrowser && permission.value !== 'denied' && Boolean(config.value?.configured))
const canTest = computed(() => Boolean(config.value?.subscriptions && config.value?.configured))

const status = computed(() => {
  if (!supported) return { tone: 'neutral', text: 'Not supported here' }
  if (permission.value === 'denied') return { tone: 'danger', text: 'Blocked' }
  if (subscribed.value) return { tone: 'ok', text: 'On for this device' }
  return { tone: 'neutral', text: 'Off for this device' }
})
</script>

<template>
  <section v-if="phone" class="ios-sec">
    <h2 class="ios-head">Habit reminders</h2>
    <div class="ios-plate">
      <label class="ios-row">
        <span class="lbl">Reminders</span>
        <input type="checkbox" role="switch" :checked="enabled" :disabled="busy === 'switch'" @change="toggle" />
      </label>
      <div class="ios-row">
        <span class="lbl">This device</span>
        <span class="val" :class="status.tone">{{ status.text.replace(' for this device', '') }}</span>
      </div>
      <button v-if="!subscribed" type="button" class="ios-row act" :disabled="!canTurnOn || busy === 'on'" @click="turnOn">{{ busy === 'on' ? 'Turning on…' : 'Turn on for this device' }}</button>
      <button v-else type="button" class="ios-row act" :disabled="busy === 'off'" @click="turnOff">{{ busy === 'off' ? 'Turning off…' : 'Turn off for this device' }}</button>
      <button type="button" class="ios-row act" :disabled="!canTest || busy === 'test'" @click="test">{{ busy === 'test' ? 'Sending…' : 'Send a test' }}</button>
    </div>
    <p v-if="error" class="ios-foot err">{{ error }}</p>
    <p v-if="iosBrowser" class="ios-foot warn">Notifications only work from the installed app: Share, Add to Home Screen, then open Pozzy from the home screen and turn them on here.</p>
    <p v-else-if="config && !config.configured" class="ios-foot warn">The server has no VAPID keys yet, so nothing can be sent. Add VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY and VAPID_SUBJECT to the api service.</p>
    <p class="ios-foot">A push notification at the reminder time of each habit, only when it is due and still open. Set the time in a habit's editor.<template v-if="config"><br />{{ config.subscriptions }} device{{ config.subscriptions === 1 ? '' : 's' }} subscribed.</template></p>
  </section>
  <section v-else class="card">
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

/* Phone: an inset grouped section (header, plate of 44pt rows, footer), the iOS Settings look. */
@media (max-width: 1023px) {
  .ios-sec { margin-bottom: var(--sp-8); }
  .ios-head { margin: 0 16px 6px; font-size: 0.8125rem; font-weight: 400; text-transform: uppercase; color: var(--ink-3); }
  .ios-plate { background: var(--surface); border-radius: var(--r-lg); overflow: hidden; }
  .ios-row { position: relative; display: flex; align-items: center; gap: 12px; width: 100%; min-height: 44px; padding: 6px 16px; border: 0; background: none; color: var(--ink); font: inherit; font-size: 1.0625rem; text-align: left; }
  .ios-row + .ios-row::before { content: ''; position: absolute; top: 0; left: 16px; right: 0; height: 0.5px; background: var(--line-2); }
  .lbl { flex: 1; min-width: 0; }
  .val { color: var(--ink-3); }
  .val.ok { color: var(--ok); }
  .val.danger { color: var(--danger); }
  .act { color: var(--brand); }
  .act:active:not(:disabled) { background: var(--surface-3); }
  .act:disabled { color: var(--ink-4); }
  .ios-foot { margin: 6px 16px 0; font-size: 0.8125rem; line-height: 1.4; color: var(--ink-3); }
  .ios-foot.warn { color: var(--warn); }
  .ios-foot.err { color: var(--danger); }
}
</style>

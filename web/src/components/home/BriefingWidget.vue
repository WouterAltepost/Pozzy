<script setup>
import { computed, onMounted, ref } from 'vue'
import { getBriefing, regenerateBriefing } from '../../api/ai'
import { formatDateTime } from '../../lib/dates'

const data = ref(null)
const failed = ref(false)
const loaded = ref(false)
const busy = ref(false)
const error = ref('')

const paragraphs = computed(() => (data.value?.text || '').split(/\n{2,}/).map((p) => p.trim()).filter(Boolean))

async function load() {
  try {
    data.value = await getBriefing()
    failed.value = false
  } catch {
    failed.value = true
  } finally {
    loaded.value = true
  }
}

async function regenerate() {
  busy.value = true
  error.value = ''
  try {
    data.value = await regenerateBriefing()
  } catch (err) {
    error.value = err.message
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>

<template>
  <section v-if="!failed && loaded" class="card widget">
    <h2>
      Briefing
      <span class="muted small">
        <template v-if="data">{{ data.source === 'claude' ? 'Claude' : 'Rules' }} · {{ formatDateTime(data.generated_at) }} ·</template>
        <button type="button" class="link" :disabled="busy" @click="regenerate">{{ busy ? 'Working' : data ? 'Regenerate' : 'Generate' }}</button>
      </span>
    </h2>
    <p v-if="error" class="error">{{ error }}</p>
    <template v-if="data">
      <p v-for="(p, i) in paragraphs" :key="i">{{ p }}</p>
    </template>
    <p v-else class="muted">No briefing for today yet. It is generated at the time set in Settings, or on demand.</p>
  </section>
</template>

<style scoped>
h2 { font-size: 1rem; margin: 0 0 0.5rem; display: flex; justify-content: space-between; align-items: baseline; gap: 0.5rem; }
.small { font-size: 0.78rem; font-weight: normal; }
p { margin: 0 0 0.6rem; font-size: 0.92rem; line-height: 1.45; }
p:last-child { margin-bottom: 0; }
.link { border: none; background: none; padding: 0; color: #2563eb; font-size: 0.78rem; cursor: pointer; }
</style>

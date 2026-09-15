<script setup>
import { computed, onMounted, ref } from 'vue'
import { getBriefing, regenerateBriefing } from '../../api/ai'
import { formatDateTime } from '../../lib/dates'
import UiButton from '../ui/UiButton.vue'

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
    <div class="card-head">
      <h2>Briefing</h2>
      <span class="meta">
        <template v-if="data">{{ data.source === 'claude' ? 'Claude' : 'Rules' }}, {{ formatDateTime(data.generated_at) }}</template>
        <UiButton size="sm" variant="ghost" :loading="busy" @click="regenerate">{{ data ? 'Regenerate' : 'Generate' }}</UiButton>
      </span>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
    <div v-if="data" class="prose">
      <p v-for="(p, i) in paragraphs" :key="i">{{ p }}</p>
    </div>
    <p v-else class="muted">No briefing for today yet. It is generated at the time set in Settings, or on demand.</p>
  </section>
</template>

<style scoped>
.meta { display: inline-flex; align-items: center; gap: var(--sp-2); }
.prose { max-width: 68ch; }
.prose p { font-size: var(--fs-base); line-height: 1.6; margin-bottom: var(--sp-3); }
.prose p:last-child { margin-bottom: 0; }
</style>

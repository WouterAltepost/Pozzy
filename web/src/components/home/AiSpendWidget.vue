<script setup>
import { useWidgetLink } from '../../composables/useWidgetLink'
import { computed, onMounted, ref } from 'vue'
import { getSpend } from '../../api/ai'

const data = ref(null)
const failed = ref(false)
const open = ref(false)

const usd = (v) => '$' + Number(v || 0).toFixed(2)
const budgetPct = computed(() => (data.value?.budget_usd ? Math.min(100, Math.round((data.value.month.cost / data.value.budget_usd) * 100)) : null))
const maxDay = computed(() => Math.max(0.0001, ...(data.value?.last_7_days || []).map((d) => d.cost)))

async function load() {
  try {
    data.value = await getSpend()
    failed.value = false
  } catch {
    failed.value = true
  }
}

onMounted(load)
const link = useWidgetLink('settings')
</script>

<template>
  <section v-if="!failed && data" class="card widget clickable" tabindex="0" role="link" :aria-label="'Open settings'" @click="link.onClick" @keydown="link.onKey">
    <div class="card-head">
      <h2>AI spend</h2>
      <span class="meta num">{{ usd(data.month.cost) }} this month<template v-if="data.budget_usd"> of {{ usd(data.budget_usd) }}</template>, {{ usd(data.today_cost) }} today</span>
    </div>
    <div v-if="budgetPct !== null" class="bar"><div class="fill" :class="{ warn: budgetPct >= 80 }" :style="{ width: budgetPct + '%' }"></div></div>
    <div class="days" role="img" :aria-label="'Spend over the last 7 days'">
      <div v-for="d in data.last_7_days" :key="d.date" class="day" :title="d.date + ': ' + usd(d.cost) + ', ' + d.calls + ' calls'">
        <div class="col" :style="{ height: Math.max(2, Math.round((d.cost / maxDay) * 28)) + 'px' }"></div>
        <span class="muted xs num">{{ d.date.slice(8) }}</span>
      </div>
    </div>
    <ul class="features">
      <li v-for="f in data.month.by_feature.slice(0, 5)" :key="f.feature">
        <span>{{ f.feature }}</span>
        <span class="muted small num">{{ f.calls }} calls<template v-if="f.failed">, {{ f.failed }} failed</template></span>
        <span class="num">{{ usd(f.cost) }}</span>
      </li>
      <li v-if="!data.month.by_feature.length" class="muted">No AI calls this month.</li>
    </ul>
    <button v-if="data.recent.length" type="button" class="link-btn" @click="open = !open">{{ open ? 'Hide' : 'Show' }} recent calls</button>
    <ul v-if="open" class="recent">
      <li v-for="r in data.recent" :key="r.id" :class="{ bad: !r.ok }">
        <span>{{ r.feature }}</span><span class="muted small num">{{ r.model }}, {{ r.input_tokens }}/{{ r.output_tokens }} tok</span><span class="num">{{ usd(r.cost) }}</span>
        <div v-if="r.error" class="muted xs err">{{ r.error }}</div>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.bar { margin-bottom: var(--sp-3); }
.days { display: flex; gap: var(--sp-2); align-items: flex-end; margin-bottom: var(--sp-3); }
.day { display: flex; flex-direction: column; align-items: center; gap: 3px; flex: 1; }
.col { width: 100%; max-width: 28px; background: var(--ink-3); border-radius: 2px 2px 0 0; opacity: 0.7; }
.features li, .recent li { display: grid; grid-template-columns: 1fr auto auto; gap: var(--sp-3); font-size: var(--fs-md); padding: 4px 0; border-top: 1px solid var(--line); }
.features li:first-child { border-top: 0; }
.recent { margin-top: var(--sp-2); }
.recent li.bad { color: var(--danger); }
.err { grid-column: 1 / -1; }
.link-btn { margin-top: var(--sp-2); }
</style>

<script setup>
// A year of one habit: 53 week columns, Monday on top. Done days take the habit's area colour,
// a value habit shades by how close the day came to its goal; missed due days are a plain well,
// days off the schedule are empty, skipped days are striped. Scrolls to the current week.
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { WEEKDAY_LETTERS, fmt } from '../../lib/habits'
import { formatDay } from '../../lib/dates'

const props = defineProps({
  cells: { type: Array, default: () => [] },
  color: { type: String, default: '' },
  target: { type: Number, default: null },
  bool: { type: Boolean, default: true },
  unit: { type: String, default: '' },
})
const scroller = ref(null)

const weeks = computed(() => {
  const out = []
  for (let i = 0; i < props.cells.length; i += 7) out.push(props.cells.slice(i, i + 7))
  return out
})
const months = computed(() =>
  weeks.value.map((w, i) => {
    const first = w[0]?.date
    const prev = weeks.value[i - 1]?.[0]?.date
    if (!first || (prev && prev.slice(5, 7) === first.slice(5, 7))) return ''
    return new Date(first + 'T12:00:00').toLocaleDateString('en-GB', { month: 'short' })
  }),
)

function kind(c) {
  if (c.future || c.before_start) return 'none'
  if (c.status === 'skipped') return 'skip'
  if (c.met) return 'hit'
  if (c.value) return 'part'
  if (c.due === false) return 'off'
  return 'miss'
}
function level(c) {
  if (props.bool || !props.target || !c.value) return 1
  return Math.max(0.35, Math.min(1, c.value / props.target))
}
function title(c) {
  const k = kind(c)
  const day = formatDay(c.date)
  if (k === 'none') return day
  if (k === 'skip') return `${day}: skipped`
  if (k === 'off') return `${day}: not due`
  if (props.bool) return `${day}: ${k === 'hit' ? 'done' : 'missed'}`
  return `${day}: ${c.value ? fmt(c.value) + (props.unit ? ' ' + props.unit : '') : 'nothing'}`
}

function toEnd() {
  if (scroller.value) scroller.value.scrollLeft = scroller.value.scrollWidth
}
onMounted(() => nextTick(toEnd))
watch(() => props.cells.length, () => nextTick(toEnd))
</script>

<template>
  <div class="heat" :style="{ '--c': color || 'var(--ok)' }">
    <div class="letters" aria-hidden="true"><span v-for="(l, i) in WEEKDAY_LETTERS" :key="i">{{ i % 2 === 0 ? l : '' }}</span></div>
    <div ref="scroller" class="scroll">
      <div class="months" aria-hidden="true"><span v-for="(m, i) in months" :key="i">{{ m }}</span></div>
      <div class="cols" role="img" :aria-label="`Check-ins over the last year`">
        <div v-for="(w, i) in weeks" :key="i" class="col">
          <span v-for="c in w" :key="c.date" class="sq" :class="kind(c)" :style="kind(c) === 'hit' || kind(c) === 'part' ? { '--l': level(c) } : undefined" :title="title(c)"></span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.heat { --sq: 12px; --gap: 3px; display: flex; gap: 6px; }
.letters { display: grid; grid-template-rows: repeat(7, var(--sq)); gap: var(--gap); padding-top: 18px; font-size: 9px; font-weight: 600; color: var(--ink-4); line-height: var(--sq); }
.scroll { overflow-x: auto; flex: 1; min-width: 0; padding-bottom: 4px; scrollbar-width: thin; }
.months { display: grid; grid-auto-flow: column; grid-auto-columns: var(--sq); gap: var(--gap); height: 14px; margin-bottom: 4px; font-size: 10px; color: var(--ink-3); white-space: nowrap; }
.months span { overflow: visible; }
.cols { display: grid; grid-auto-flow: column; grid-auto-columns: var(--sq); gap: var(--gap); width: max-content; }
.col { display: grid; grid-template-rows: repeat(7, var(--sq)); gap: var(--gap); }
.sq { width: var(--sq); height: var(--sq); border-radius: 3px; background: var(--surface-2); }
.sq.none { background: transparent; }
.sq.off { background: transparent; box-shadow: inset 0 0 0 1px var(--line); }
.sq.miss { background: var(--surface-3); }
.sq.hit { background: color-mix(in srgb, var(--c) calc(var(--l, 1) * 100%), var(--surface-2)); }
.sq.part { background: color-mix(in srgb, var(--c) calc(var(--l, 0.4) * 60%), var(--surface-2)); }
.sq.skip { background: repeating-linear-gradient(135deg, var(--surface-2) 0 2px, var(--surface-3) 2px 4px); }
@media (min-width: 1100px) { .heat { --sq: 13px; } }
</style>

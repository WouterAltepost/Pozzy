<script setup>
// The trailing link in a widget's header. Desktop keeps the widget's own link text; the phone
// shows the iOS summary link instead, the same "Show all" with a chevron on every plate.
import { PhCaretRight } from '@phosphor-icons/vue'
import { useMediaQuery } from '../../composables/useMediaQuery'

defineOptions({ inheritAttrs: false })
defineProps({ to: { type: String, required: true }, label: { type: String, default: 'Show all' } })
const phone = useMediaQuery('(max-width: 1023px)')
</script>

<template>
  <RouterLink v-if="phone" :to="{ name: to }" class="show-all">{{ label }}<PhCaretRight weight="bold" class="chev" aria-hidden="true" /></RouterLink>
  <RouterLink v-else :to="{ name: to }" v-bind="$attrs"><slot /></RouterLink>
</template>

<style scoped>
.show-all { display: inline-flex; align-items: center; gap: 3px; min-height: 32px; color: var(--brand); font-size: 0.9375rem; white-space: nowrap; text-decoration: none; }
.show-all:active { opacity: 0.4; }
.chev { width: 12px; height: 12px; }
</style>

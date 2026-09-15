<script setup>
defineProps({
  title: { type: String, default: '' },
  as: { type: String, default: 'section' },
  flush: { type: Boolean, default: false },
})
</script>

<template>
  <component :is="as" class="card ui-card" :class="{ flush }">
    <div v-if="title || $slots.meta" class="card-head">
      <h2 v-if="title">{{ title }}</h2>
      <span v-if="$slots.meta" class="meta"><slot name="meta" /></span>
    </div>
    <slot />
  </component>
</template>

<style scoped>
.ui-card.flush { padding: 0; }
.ui-card.flush > .card-head { padding: var(--sp-4) var(--sp-4) 0; }
@media (min-width: 900px) { .ui-card.flush > .card-head { padding: var(--sp-5) var(--sp-5) 0; } }
</style>

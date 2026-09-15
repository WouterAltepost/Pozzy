import { onBeforeUnmount, onMounted, ref } from 'vue'

// Reactive media query for presentation switches (side panel vs sheet). Never drives data logic.
export function useMediaQuery(query) {
  const matches = ref(typeof window !== 'undefined' ? window.matchMedia(query).matches : false)
  let mql = null
  const update = (e) => (matches.value = e.matches)
  onMounted(() => {
    mql = window.matchMedia(query)
    matches.value = mql.matches
    mql.addEventListener('change', update)
  })
  onBeforeUnmount(() => mql?.removeEventListener('change', update))
  return matches
}

import { reactive } from 'vue'

// One toast at a time, 4 seconds. Presentation only: replaces inline "Saved." strings.
export const toastState = reactive({ current: null })
let timer = null

export function useToast() {
  function show(text, tone = 'neutral', ms = 4000) {
    clearTimeout(timer)
    toastState.current = { text, tone }
    timer = setTimeout(() => (toastState.current = null), ms)
  }
  return { show, success: (t) => show(t, 'neutral'), error: (t) => show(t, 'danger') }
}

import { reactive } from 'vue'

// One toast at a time, 4 seconds. Presentation only: replaces inline "Saved." strings.
// `action` ({ label, run }) adds a button, used for "Undo" after quick taps.
export const toastState = reactive({ current: null })
let timer = null

export function useToast() {
  function dismiss() {
    clearTimeout(timer)
    toastState.current = null
  }
  function show(text, tone = 'neutral', ms = 4000, action = null) {
    clearTimeout(timer)
    toastState.current = { text, tone, action }
    timer = setTimeout(dismiss, ms)
  }
  return {
    show,
    dismiss,
    success: (t) => show(t, 'neutral'),
    error: (t) => show(t, 'danger'),
    // Undo toast: the button runs `run` once and closes the toast. Stays a little longer.
    undo: (text, run, ms = 6000) => show(text, 'neutral', ms, { label: 'Undo', run }),
  }
}

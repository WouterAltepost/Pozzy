import { computed, inject, onMounted, provide, ref } from 'vue'

// Page readiness for UiLoadGate.
// useReady(fn): run the page's initial loads on mount, ready once they settle (success or failure).
export function useReady(fn, timeoutMs = 8000) {
  const ready = ref(false)
  onMounted(async () => {
    const guard = setTimeout(() => (ready.value = true), timeoutMs)
    try {
      await fn()
    } catch {
      // Errors are shown by the page itself; the gate still opens.
    } finally {
      clearTimeout(guard)
      ready.value = true
    }
  })
  return ready
}

// useLoadGateHost(): a page whose children each fetch their own data (the homepage widgets).
// Children call useLoadTask() during setup and settle it when their first fetch ends.
const KEY = Symbol('loadGate')

export function useLoadGateHost(timeoutMs = 8000) {
  const pending = ref(0)
  const mounted = ref(false)
  const timedOut = ref(false)
  provide(KEY, {
    register() {
      pending.value += 1
      let settled = false
      return () => {
        if (settled) return
        settled = true
        pending.value = Math.max(0, pending.value - 1)
      }
    },
  })
  onMounted(() => {
    mounted.value = true
    setTimeout(() => (timedOut.value = true), timeoutMs)
  })
  return computed(() => timedOut.value || (mounted.value && pending.value === 0))
}

export function useLoadTask() {
  const host = inject(KEY, null)
  return host ? host.register() : () => {}
}

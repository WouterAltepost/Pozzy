import { computed, ref } from 'vue'

// Theme preference: 'system' (default), 'light' or 'dark'. Presentation only, stored per device.
const KEY = 'pozzy.theme'
const LIGHT = '#F4F5F9'
const DARK = '#1C1E22'
const preference = ref('system')

function read() {
  try {
    const v = localStorage.getItem(KEY)
    return v === 'light' || v === 'dark' ? v : 'system'
  } catch {
    return 'system'
  }
}

function systemDark() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

export function applyTheme(value = read()) {
  preference.value = value
  const root = document.documentElement
  if (value === 'system') root.removeAttribute('data-theme')
  else root.setAttribute('data-theme', value)
  const dark = value === 'dark' || (value === 'system' && systemDark())
  for (const meta of document.querySelectorAll('meta[name="theme-color"]')) meta.setAttribute('content', dark ? DARK : LIGHT)
}

export function useTheme() {
  const isDark = computed(() => preference.value === 'dark' || (preference.value === 'system' && systemDark()))
  let switching = null
  function set(value) {
    try {
      if (value === 'system') localStorage.removeItem(KEY)
      else localStorage.setItem(KEY, value)
    } catch {}
    // A short colour transition on everything, so dark to light is a fade, not a flash.
    const root = document.documentElement
    root.classList.add('theme-switching')
    clearTimeout(switching)
    switching = setTimeout(() => root.classList.remove('theme-switching'), 320)
    applyTheme(value)
  }
  // The button flips to the opposite of what is on screen now, so it always does the obvious thing.
  function toggle() {
    set(isDark.value ? 'light' : 'dark')
  }
  return { preference, isDark, set, toggle }
}

if (typeof window !== 'undefined') {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => applyTheme(preference.value))
}

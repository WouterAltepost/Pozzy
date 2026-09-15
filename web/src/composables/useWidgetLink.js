import { useRouter } from 'vue-router'

// Clicking anywhere on a homepage widget opens its page, unless the click landed on a control.
const INTERACTIVE = 'a, button, input, select, textarea, label, [role="button"], summary'

export function useWidgetLink(routeName) {
  const router = useRouter()
  function onClick(event) {
    if (event.target.closest(INTERACTIVE)) return
    if (window.getSelection && String(window.getSelection()).length) return
    router.push({ name: routeName })
  }
  function onKey(event) {
    if (event.key === 'Enter' && event.target === event.currentTarget) router.push({ name: routeName })
  }
  return { onClick, onKey }
}

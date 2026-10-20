// One iOS context menu for the whole app (rendered by components/ios/IosContextMenu.vue in App).
//   const menu = useContextMenu()
//   menu.open(element, [{ label: 'Skip', icon: PhSkipForward, action: () => ... }, { label: 'Delete', danger: true, action }])
// The element is lifted above a blurred page and the menu opens next to it.
import { reactive } from 'vue'
import { bump } from '../lib/haptics'

export const contextMenuState = reactive({ open: false, anchor: null, rect: null, items: [], title: '' })

export function useContextMenu() {
  return {
    open(anchor, items, title = '') {
      if (!anchor) return
      bump()
      contextMenuState.anchor = anchor
      contextMenuState.rect = anchor.getBoundingClientRect()
      contextMenuState.items = items.filter(Boolean)
      contextMenuState.title = title
      contextMenuState.open = true
    },
    close() {
      contextMenuState.open = false
    },
  }
}

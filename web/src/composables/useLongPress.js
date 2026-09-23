// Long press (500 ms) on touch and mouse. Returns pointer handlers to spread on an element
// and a guard for its click handler: `if (longPress.consumed()) return` skips the click
// that the browser fires after a press that already opened something.
export function useLongPress(onLongPress, ms = 500) {
  let timer = null
  let fired = false
  let target = null

  function cancel() {
    clearTimeout(timer)
    timer = null
  }
  function down(payload, evt) {
    fired = false
    target = evt?.currentTarget || null
    cancel()
    timer = setTimeout(() => {
      fired = true
      timer = null
      onLongPress(payload, evt)
    }, ms)
  }
  function consumed() {
    const was = fired
    fired = false
    return was
  }
  const handlers = (payload) => ({
    onPointerdown: (evt) => down(payload, evt),
    onPointerup: cancel,
    onPointerleave: cancel,
    onPointercancel: cancel,
    onContextmenu: (evt) => {
      // Right-click on desktop and the long-press menu on iOS both land here.
      evt.preventDefault()
      cancel()
      fired = true
      onLongPress(payload, evt)
    },
  })
  return { handlers, consumed, target: () => target }
}

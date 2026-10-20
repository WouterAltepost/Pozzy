// Haptic feedback, fired on the same event as the visual so cause and feedback line up.
// Android PWAs vibrate. iOS has no web vibration API, but since iOS 18 Safari plays the system
// haptic when a native switch (<input type="checkbox" switch>) toggles, including one toggled
// through its label from script during a user gesture. A hidden label does that here. Older
// iOS and desktops do nothing.
let label = null

function hiddenSwitch() {
  if (label?.isConnected) return label
  const input = document.createElement('input')
  input.type = 'checkbox'
  input.setAttribute('switch', '')
  input.setAttribute('aria-hidden', 'true')
  input.tabIndex = -1
  label = document.createElement('label')
  label.setAttribute('aria-hidden', 'true')
  label.style.cssText = 'position:fixed;width:1px;height:1px;overflow:hidden;opacity:0;pointer-events:none;left:-10px;top:-10px'
  label.appendChild(input)
  document.body.appendChild(label)
  return label
}

function pulse(ms) {
  try {
    if (navigator.vibrate) {
      navigator.vibrate(ms)
      return
    }
    hiddenSwitch().click()
  } catch {
    // feedback is a nicety; never let it throw
  }
}

// A light tick: a habit checked, a swipe action committed, a switch flipped.
export function tick() {
  pulse(8)
}

// A firmer bump: a long press opening a context menu, pull to refresh crossing its threshold.
export function bump() {
  pulse(14)
}

// Success: two quick ticks (all habits done for the day).
export function success() {
  pulse(8)
  setTimeout(() => pulse(8), 90)
}

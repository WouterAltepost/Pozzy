// One short tick for a commit (a habit ticked, a sheet snapped shut). Android PWAs vibrate;
// iOS ignores the call. Fired on the same event as the visual so cause and feedback line up.
export function tick() {
  try {
    navigator.vibrate?.(8)
  } catch {}
}

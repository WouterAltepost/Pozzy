// The iOS card stack behind a sheet on the phone: while a sheet is up, the app shell is pinned
// at its scroll position and shrinks back on black (CSS in style.css, html.sheet-open).
// --sheet-p follows the sheet's position, so dragging the sheet down brings the page back up
// with the finger. Counted, so a sheet opened from a sheet does not drop the stack early.
let count = 0
let saved = 0

export function presentSheet() {
  if (count++ > 0) return
  saved = window.scrollY
  const root = document.documentElement
  root.style.setProperty('--sheet-scroll', `${-saved}px`)
  root.style.setProperty('--sheet-p', '0')
  root.classList.add('sheet-open')
}

export function sheetProgress(p) {
  document.documentElement.style.setProperty('--sheet-p', String(Math.max(0, Math.min(1, p))))
}

export function dismissSheet() {
  if (count === 0 || --count > 0) return
  const root = document.documentElement
  root.classList.remove('sheet-open')
  root.style.removeProperty('--sheet-p')
  root.style.removeProperty('--sheet-scroll')
  window.scrollTo(0, saved)
}

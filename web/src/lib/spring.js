// Spring animation in Apple's two parameters: damping ratio (1 = no overshoot, 0.8 = a little
// bounce) and response (seconds to reach the target, roughly). A spring has no fixed duration;
// it can be retargeted at any frame and starts from its current value and velocity, which is
// what makes a gesture interruptible. Runs on requestAnimationFrame, integrates in seconds.

export function reducedMotion() {
  return typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
}

export function createSpring({ value = 0, damping = 1, response = 0.35, onUpdate, onRest, restDelta = 0.1, restSpeed = 5 } = {}) {
  const s = { value, target: value, velocity: 0, damping, response, running: false }
  let raf = 0
  let last = 0

  function frame(now) {
    const dt = Math.min(0.064, Math.max(0.001, (now - last) / 1000))
    last = now
    const omega = (2 * Math.PI) / s.response
    const k = omega * omega
    const c = 2 * s.damping * omega
    // Semi-implicit Euler in a few sub-steps keeps stiff springs stable at low frame rates.
    const steps = 4
    const h = dt / steps
    for (let i = 0; i < steps; i++) {
      const a = -k * (s.value - s.target) - c * s.velocity
      s.velocity += a * h
      s.value += s.velocity * h
    }
    if (Math.abs(s.velocity) < restSpeed && Math.abs(s.value - s.target) < restDelta) {
      s.value = s.target
      s.velocity = 0
      s.running = false
      onUpdate?.(s.value)
      onRest?.(s.value)
      return
    }
    onUpdate?.(s.value)
    raf = requestAnimationFrame(frame)
  }

  return {
    get value() {
      return s.value
    },
    get velocity() {
      return s.velocity
    },
    get running() {
      return s.running
    },
    // Move to `target` from wherever the value is now. `velocity` (units per second) hands the
    // gesture's release speed to the spring so there is no seam between drag and animation.
    set(target, { velocity, damping, response } = {}) {
      s.target = target
      if (velocity !== undefined) s.velocity = velocity
      if (damping !== undefined) s.damping = damping
      if (response !== undefined) s.response = response
      if (reducedMotion()) {
        this.jump(target)
        onRest?.(s.value)
        return
      }
      if (!s.running) {
        s.running = true
        last = performance.now()
        cancelAnimationFrame(raf)
        raf = requestAnimationFrame(frame)
      }
    },
    // Follow the finger: no animation, the value is the pointer's.
    jump(value) {
      cancelAnimationFrame(raf)
      s.running = false
      s.value = value
      s.target = value
      s.velocity = 0
      onUpdate?.(value)
    },
    stop() {
      cancelAnimationFrame(raf)
      s.running = false
    },
  }
}

// Where a flick would come to rest on its own (Apple's scroll deceleration), in the same units
// as the velocity, per second. 0.998 feels like a scroll view; 0.99 stops sooner.
export function project(velocity, decelerationRate = 0.998) {
  return ((velocity / 1000) * decelerationRate) / (1 - decelerationRate)
}

// Resistance past a boundary: the further past it, the less the element follows.
export function rubberband(overshoot, dimension, constant = 0.55) {
  return (overshoot * dimension * constant) / (dimension + constant * Math.abs(overshoot))
}

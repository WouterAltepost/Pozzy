/* @ds-bundle: {"format":4,"namespace":"PozzyDesignSystem_379c1d","components":[{"name":"AreaDot","sourcePath":"components/core/AreaDot.jsx"},{"name":"Badge","sourcePath":"components/core/Badge.jsx"},{"name":"PriorityBadge","sourcePath":"components/core/Badge.jsx"},{"name":"Tag","sourcePath":"components/core/Badge.jsx"},{"name":"Button","sourcePath":"components/core/Button.jsx"},{"name":"Card","sourcePath":"components/core/Card.jsx"},{"name":"Inset","sourcePath":"components/core/Card.jsx"},{"name":"Field","sourcePath":"components/core/Field.jsx"},{"name":"Icon","sourcePath":"components/core/Icon.jsx"},{"name":"IconButton","sourcePath":"components/core/IconButton.jsx"},{"name":"PageHeader","sourcePath":"components/core/PageHeader.jsx"},{"name":"ProgressBar","sourcePath":"components/core/ProgressBar.jsx"},{"name":"Segmented","sourcePath":"components/core/Segmented.jsx"},{"name":"WeekNav","sourcePath":"components/core/WeekNav.jsx"},{"name":"Empty","sourcePath":"components/feedback/Empty.jsx"},{"name":"Sheet","sourcePath":"components/feedback/Sheet.jsx"},{"name":"Skeleton","sourcePath":"components/feedback/Skeleton.jsx"},{"name":"Toast","sourcePath":"components/feedback/Toast.jsx"},{"name":"EmailRow","sourcePath":"components/product/EmailRow.jsx"},{"name":"ListRow","sourcePath":"components/product/ListRow.jsx"},{"name":"TaskCard","sourcePath":"components/product/TaskCard.jsx"},{"name":"QUADRANTS","sourcePath":"components/product/TaskCard.jsx"},{"name":"Quadrant","sourcePath":"components/product/TaskCard.jsx"},{"name":"TrackerChip","sourcePath":"components/product/TrackerChip.jsx"},{"name":"CaptureBar","sourcePath":"components/shell/CaptureBar.jsx"},{"name":"NAV","sourcePath":"components/shell/NavRail.jsx"},{"name":"NavItem","sourcePath":"components/shell/NavRail.jsx"},{"name":"NavRail","sourcePath":"components/shell/NavRail.jsx"},{"name":"TopBar","sourcePath":"components/shell/TopBar.jsx"}],"sourceHashes":{"components/core/AreaDot.jsx":"8a295bf3266c","components/core/Badge.jsx":"c4944b253cdf","components/core/Button.jsx":"6681605c857b","components/core/Card.jsx":"92b40f7fb6f5","components/core/Field.jsx":"741cc90218da","components/core/Icon.jsx":"d9b9ede60ed1","components/core/IconButton.jsx":"6d2e9fdd60f0","components/core/PageHeader.jsx":"6998576ce560","components/core/ProgressBar.jsx":"234fb8425f5b","components/core/Segmented.jsx":"bbd37af2c9f2","components/core/WeekNav.jsx":"4713901a35a3","components/feedback/Empty.jsx":"267c118cbbe9","components/feedback/Sheet.jsx":"bc08febfe526","components/feedback/Skeleton.jsx":"93eeba9d19a2","components/feedback/Toast.jsx":"fc00004c3a38","components/product/EmailRow.jsx":"2aa39280376b","components/product/ListRow.jsx":"08054400f45a","components/product/TaskCard.jsx":"8262f2cf7735","components/product/TrackerChip.jsx":"8397a90b7aa6","components/shell/CaptureBar.jsx":"c481e7ec713f","components/shell/NavRail.jsx":"4f4cd4f3fcce","components/shell/TopBar.jsx":"7c38e43bf54e","ui_kits/pozzy/AgendaScreen.jsx":"221f7f6715d2","ui_kits/pozzy/Data.jsx":"7e429a070b27","ui_kits/pozzy/HomeScreen.jsx":"ad3c01769d0d","ui_kits/pozzy/LoginScreen.jsx":"5bc77c0deb24","ui_kits/pozzy/MailScreen.jsx":"d1f62bd63826","ui_kits/pozzy/TasksScreen.jsx":"17c107c8d694"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.PozzyDesignSystem_379c1d = window.PozzyDesignSystem_379c1d || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/core/AreaDot.jsx
try { (() => {
// The one area indicator. Colour is data from the areas table, never restyled.
function AreaDot({
  color,
  name,
  label = false
}) {
  if (!color) return null;
  return /*#__PURE__*/React.createElement("span", {
    title: name,
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      fontSize: 'var(--fs-sm)',
      color: 'var(--ink-3)',
      whiteSpace: 'nowrap'
    }
  }, /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    style: {
      width: 8,
      height: 8,
      borderRadius: '50%',
      background: color,
      flex: 'none'
    }
  }), label ? name : /*#__PURE__*/React.createElement("span", {
    style: {
      position: 'absolute',
      width: 1,
      height: 1,
      overflow: 'hidden',
      clip: 'rect(0 0 0 0)'
    }
  }, name));
}
Object.assign(__ds_scope, { AreaDot });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/AreaDot.jsx", error: String((e && e.message) || e) }); }

// components/core/Badge.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const TONES = {
  neutral: ['var(--surface-2)', 'var(--ink-2)'],
  brand: ['var(--brand-soft)', 'var(--brand)'],
  ok: ['var(--ok-soft)', 'var(--ok)'],
  warn: ['var(--warn-soft)', 'var(--warn)'],
  danger: ['var(--danger-soft)', 'var(--danger)'],
  info: ['var(--info-soft)', 'var(--info)']
};
function Badge({
  tone = 'neutral',
  color,
  dot = false,
  children,
  style,
  ...rest
}) {
  const [bg, fg] = color ? ['color-mix(in srgb, ' + color + ' 14%, transparent)', 'color-mix(in srgb, ' + color + ' 78%, var(--ink))'] : TONES[tone] || TONES.neutral;
  return /*#__PURE__*/React.createElement("span", _extends({
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 5,
      height: 20,
      padding: '0 7px',
      borderRadius: 'var(--r-sm)',
      fontSize: 'var(--fs-xs)',
      fontWeight: 500,
      letterSpacing: '0.02em',
      lineHeight: 1,
      whiteSpace: 'nowrap',
      background: bg,
      color: fg,
      fontVariantNumeric: 'tabular-nums',
      ...style
    }
  }, rest), dot && /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    style: {
      width: 7,
      height: 7,
      borderRadius: '50%',
      background: 'currentColor'
    }
  }), children);
}
const P = {
  1: ['P1', 'danger', 'Urgent'],
  2: ['P2', 'warn', 'Important'],
  3: ['P3', 'info', 'Normal'],
  4: ['P4', 'neutral', 'Low or noise']
};
function PriorityBadge({
  priority = 3
}) {
  const [label, tone, title] = P[priority] || P[3];
  return /*#__PURE__*/React.createElement(Badge, {
    tone: tone,
    title: title
  }, label);
}
function Tag({
  children
}) {
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      height: 20,
      padding: '0 var(--sp-2)',
      borderRadius: 'var(--r-sm)',
      background: 'var(--surface-2)',
      color: 'var(--ink-2)',
      fontSize: 'var(--fs-xs)',
      letterSpacing: '0.02em',
      whiteSpace: 'nowrap'
    }
  }, children);
}
Object.assign(__ds_scope, { Badge, PriorityBadge, Tag });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Badge.jsx", error: String((e && e.message) || e) }); }

// components/core/Button.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
if (typeof document !== 'undefined' && !document.getElementById('pz-btn')) {
  const s = document.createElement('style');
  s.id = 'pz-btn';
  s.textContent = ".pz-btn{position:relative;display:inline-flex;align-items:center;justify-content:center;gap:6px;height:var(--control-h);padding:0 var(--sp-3);border-radius:var(--r-md);border:1px solid transparent;font-weight:500;font-size:var(--fs-base);line-height:1;white-space:nowrap;cursor:pointer;font-family:inherit;transition:background-color var(--dur-hover) ease,border-color var(--dur-hover) ease,color var(--dur-hover) ease,transform var(--dur-press) var(--ease-out)}.pz-btn:active:not(:disabled){transform:scale(0.97)}.pz-btn:disabled{opacity:.55;cursor:default}.pz-btn-block{width:100%}.pz-btn-sm{height:var(--control-h-sm);padding:0 10px;font-size:var(--fs-md)}.pz-btn-primary{background:var(--ink);color:var(--on-ink);border-color:var(--ink)}.pz-btn-secondary{background:var(--surface);color:var(--ink);border-color:var(--line-2)}.pz-btn-ghost{background:transparent;color:var(--ink-2)}.pz-btn-danger{background:var(--danger-soft);color:var(--danger)}.pz-btn-link{background:none;color:var(--ink-2);padding:0;height:auto;border:0;text-decoration:underline;text-underline-offset:3px;text-decoration-thickness:1px;font-weight:400;border-radius:2px}.pz-btn-link:active:not(:disabled){transform:none}@media(hover:hover) and (pointer:fine){.pz-btn-primary:hover:not(:disabled){background:var(--ink-2);border-color:var(--ink-2)}.pz-btn-secondary:hover:not(:disabled){background:var(--surface-2)}.pz-btn-ghost:hover:not(:disabled){background:var(--surface-2);color:var(--ink)}.pz-btn-danger:hover:not(:disabled){background:color-mix(in srgb,var(--danger) 22%,var(--danger-soft))}.pz-btn-link:hover:not(:disabled){color:var(--ink)}}.pz-btn .pz-label{display:inline-flex;align-items:center;gap:6px}.pz-btn.is-loading .pz-label{opacity:0}.pz-spin{position:absolute;width:14px;height:14px;border-radius:50%;border:2px solid currentColor;border-right-color:transparent;animation:pz-spin 700ms linear infinite}@keyframes pz-spin{to{transform:rotate(360deg)}}";
  document.head.appendChild(s);
}
function Button({
  variant = 'secondary',
  size = 'md',
  loading = false,
  disabled = false,
  block = false,
  type = 'button',
  children,
  className = '',
  ...rest
}) {
  const cls = ['pz-btn', 'pz-btn-' + variant, 'pz-btn-' + size, loading && 'is-loading', block && 'pz-btn-block', className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("button", _extends({
    type: type,
    className: cls,
    disabled: disabled || loading,
    "aria-busy": loading || undefined
  }, rest), loading && /*#__PURE__*/React.createElement("span", {
    className: "pz-spin",
    "aria-hidden": "true"
  }), /*#__PURE__*/React.createElement("span", {
    className: "pz-label"
  }, children));
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Button.jsx", error: String((e && e.message) || e) }); }

// components/core/Card.jsx
try { (() => {
function Card({
  title,
  meta,
  flush = false,
  as = 'section',
  children,
  style,
  ...rest
}) {
  const pad = 'var(--sp-5)';
  return React.createElement(as, {
    style: {
      background: 'var(--surface)',
      border: '1px solid var(--line)',
      borderRadius: 'var(--r-lg)',
      boxShadow: 'var(--shadow-1)',
      padding: flush ? 0 : pad,
      ...style
    },
    ...rest
  }, (title || meta) && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'baseline',
      justifyContent: 'space-between',
      gap: 'var(--sp-3)',
      marginBottom: flush ? 0 : 'var(--sp-3)',
      padding: flush ? pad + ' ' + pad + ' 0' : 0
    }
  }, title && /*#__PURE__*/React.createElement("h2", {
    style: {
      margin: 0,
      fontSize: 'var(--fs-lg)',
      fontWeight: 600,
      lineHeight: 1.25,
      letterSpacing: '-0.01em'
    }
  }, title), meta && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 'var(--fs-sm)',
      color: 'var(--ink-3)',
      fontVariantNumeric: 'tabular-nums'
    }
  }, meta)), children);
}
function Inset({
  children,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--surface-2)',
      borderRadius: 'var(--r-md)',
      padding: 'var(--sp-3)',
      ...style
    }
  }, children);
}
Object.assign(__ds_scope, { Card, Inset });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Card.jsx", error: String((e && e.message) || e) }); }

// components/core/Field.jsx
try { (() => {
function Field({
  label,
  hint,
  error,
  inline = false,
  children
}) {
  return /*#__PURE__*/React.createElement("label", {
    style: {
      display: 'flex',
      flexDirection: inline ? 'row' : 'column',
      alignItems: inline ? 'center' : undefined,
      gap: inline ? 'var(--sp-2)' : 4,
      minWidth: 0
    }
  }, label && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 'var(--fs-xs)',
      letterSpacing: '0.02em',
      fontWeight: 500,
      color: 'var(--ink-2)'
    }
  }, label), /*#__PURE__*/React.createElement("span", {
    className: error ? 'pz-field-invalid' : '',
    style: {
      display: 'flex',
      minWidth: 0
    }
  }, children), error ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 'var(--fs-sm)',
      color: 'var(--danger)'
    }
  }, error) : hint ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 'var(--fs-sm)',
      color: 'var(--ink-3)'
    }
  }, hint) : null);
}
if (typeof document !== 'undefined' && !document.getElementById('pz-field')) {
  const s = document.createElement('style');
  s.id = 'pz-field';
  s.textContent = ".pz-field-invalid input,.pz-field-invalid select,.pz-field-invalid textarea{border-color:var(--danger)!important}label>span>input,label>span>select,label>span>textarea{width:100%}";
  document.head.appendChild(s);
}
Object.assign(__ds_scope, { Field });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Field.jsx", error: String((e && e.message) || e) }); }

// components/core/Icon.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
// Phosphor icon by name (regular weight by default). Intentional addition: wraps the CDN icon font @phosphor-icons/web.
function Icon({
  name,
  size = 16,
  weight = 'regular',
  style,
  ...rest
}) {
  const cls = weight === 'regular' ? 'ph' : 'ph-' + weight;
  return /*#__PURE__*/React.createElement("i", _extends({
    className: cls + ' ph-' + name,
    "aria-hidden": "true",
    style: {
      fontSize: size,
      width: size,
      height: size,
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      lineHeight: 1,
      flex: 'none',
      ...style
    }
  }, rest));
}
Object.assign(__ds_scope, { Icon });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Icon.jsx", error: String((e && e.message) || e) }); }

// components/core/IconButton.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
if (typeof document !== 'undefined' && !document.getElementById('pz-iconbtn')) {
  const s = document.createElement('style');
  s.id = 'pz-iconbtn';
  s.textContent = ".pz-iconbtn{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border:0;border-radius:var(--r-md);background:transparent;color:var(--ink-3);cursor:pointer;transition:background-color var(--dur-hover) ease,color var(--dur-hover) ease,transform var(--dur-press) var(--ease-out)}.pz-iconbtn:active{transform:scale(0.94)}@media(hover:hover) and (pointer:fine){.pz-iconbtn:hover{background:var(--surface-2);color:var(--ink)}}";
  document.head.appendChild(s);
}
function IconButton({
  icon,
  label,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("button", _extends({
    type: "button",
    className: "pz-iconbtn",
    "aria-label": label,
    title: label
  }, rest), /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: icon,
    size: 16
  }));
}
Object.assign(__ds_scope, { IconButton });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/IconButton.jsx", error: String((e && e.message) || e) }); }

// components/core/PageHeader.jsx
try { (() => {
function PageHeader({
  title,
  meta,
  children
}) {
  return /*#__PURE__*/React.createElement("header", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 'var(--sp-3) var(--sp-4)',
      flexWrap: 'wrap',
      marginBottom: 'var(--sp-5)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'baseline',
      gap: 'var(--sp-3)',
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("h1", {
    style: {
      margin: 0,
      fontSize: 'var(--fs-2xl)',
      fontWeight: 600,
      lineHeight: 1.25,
      letterSpacing: '-0.01em'
    }
  }, title), meta && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 'var(--fs-sm)',
      color: 'var(--ink-3)',
      fontVariantNumeric: 'tabular-nums'
    }
  }, meta)), children && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--sp-2)',
      flexWrap: 'wrap'
    }
  }, children));
}
Object.assign(__ds_scope, { PageHeader });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/PageHeader.jsx", error: String((e && e.message) || e) }); }

// components/core/ProgressBar.jsx
try { (() => {
function ProgressBar({
  value = 0,
  max = 100,
  tone = 'ink',
  style
}) {
  const pct = Math.min(100, Math.round(value / (max || 1) * 100));
  const fill = tone === 'ok' || pct >= 100 && tone === 'auto' ? 'var(--ok)' : tone === 'warn' ? 'var(--warn)' : 'var(--ink)';
  return /*#__PURE__*/React.createElement("div", {
    role: "progressbar",
    "aria-valuenow": value,
    "aria-valuemax": max,
    style: {
      height: 6,
      background: 'var(--surface-3)',
      borderRadius: 3,
      overflow: 'hidden',
      ...style
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      height: '100%',
      width: pct + '%',
      background: fill,
      borderRadius: 3
    }
  }));
}
Object.assign(__ds_scope, { ProgressBar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/ProgressBar.jsx", error: String((e && e.message) || e) }); }

// components/core/Segmented.jsx
try { (() => {
function Segmented({
  value,
  options,
  onChange
}) {
  return /*#__PURE__*/React.createElement("div", {
    role: "tablist",
    style: {
      display: 'inline-flex',
      padding: 3,
      gap: 2,
      background: 'var(--surface-2)',
      borderRadius: 'var(--r-md)'
    }
  }, options.map(o => {
    const active = o.value === value;
    return /*#__PURE__*/React.createElement("button", {
      key: o.value,
      type: "button",
      role: "tab",
      "aria-selected": active,
      onClick: () => onChange && onChange(o.value),
      style: {
        height: 28,
        padding: '0 12px',
        border: 0,
        borderRadius: 6,
        background: active ? 'var(--surface)' : 'transparent',
        color: active ? 'var(--ink)' : 'var(--ink-2)',
        fontSize: 'var(--fs-md)',
        fontWeight: 500,
        cursor: 'pointer',
        boxShadow: active ? 'var(--shadow-1)' : 'none',
        fontFamily: 'inherit',
        transition: 'background-color var(--dur-hover) ease, color var(--dur-hover) ease'
      }
    }, o.label);
  }));
}
Object.assign(__ds_scope, { Segmented });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Segmented.jsx", error: String((e && e.message) || e) }); }

// components/core/WeekNav.jsx
try { (() => {
function WeekNav({
  label,
  isCurrent = true,
  onPrev,
  onNext,
  onToday
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 4,
      fontSize: 'var(--fs-md)'
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.IconButton, {
    icon: "caret-left",
    label: "Previous week",
    onClick: onPrev
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      minWidth: 132,
      textAlign: 'center',
      color: 'var(--ink-2)',
      fontWeight: 500,
      fontVariantNumeric: 'tabular-nums'
    }
  }, label), /*#__PURE__*/React.createElement(__ds_scope.IconButton, {
    icon: "caret-right",
    label: "Next week",
    onClick: onNext
  }), !isCurrent && /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "link-btn",
    onClick: onToday,
    style: {
      marginLeft: 'var(--sp-2)',
      border: 0,
      background: 'none',
      padding: 0,
      color: 'var(--ink-2)',
      font: 'inherit',
      fontSize: 'var(--fs-sm)',
      textDecoration: 'underline',
      textUnderlineOffset: 3,
      cursor: 'pointer'
    }
  }, "This week"));
}
Object.assign(__ds_scope, { WeekNav });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/WeekNav.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Empty.jsx
try { (() => {
function Empty({
  icon,
  title,
  hint,
  action,
  compact = false
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: compact ? 'row' : 'column',
      alignItems: 'center',
      textAlign: compact ? 'left' : 'center',
      gap: compact ? 'var(--sp-3)' : 'var(--sp-2)',
      padding: compact ? 'var(--sp-2) 0' : 'var(--sp-6) var(--sp-4)',
      color: 'var(--ink-2)'
    }
  }, icon && /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ink-3)',
      display: 'inline-flex'
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: icon,
    size: compact ? 18 : 26
  })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 'var(--fs-base)',
      fontWeight: 500,
      color: 'var(--ink-2)'
    }
  }, title), hint && /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 'var(--fs-sm)',
      color: 'var(--ink-3)'
    }
  }, hint)), action && /*#__PURE__*/React.createElement("div", {
    style: {
      margin: compact ? '0 0 0 auto' : 'var(--sp-1) 0 0'
    }
  }, action));
}
Object.assign(__ds_scope, { Empty });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Empty.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Sheet.jsx
try { (() => {
// Bottom sheet (mobile nav, editors). Static recreation; drag-to-dismiss lives in the app.
function Sheet({
  open = false,
  title,
  onClose,
  children,
  inline = false
}) {
  if (!open) return null;
  return /*#__PURE__*/React.createElement("div", {
    role: "dialog",
    "aria-modal": "true",
    "aria-label": title || 'Panel',
    style: {
      position: inline ? 'absolute' : 'fixed',
      inset: 0,
      zIndex: 'var(--z-sheet)',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'flex-end'
    }
  }, /*#__PURE__*/React.createElement("div", {
    onClick: onClose,
    style: {
      position: 'absolute',
      inset: 0,
      background: 'var(--scrim)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      maxHeight: '88%',
      display: 'flex',
      flexDirection: 'column',
      background: 'var(--surface)',
      borderRadius: 'var(--r-xl) var(--r-xl) 0 0',
      boxShadow: 'var(--shadow-3)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'center',
      padding: '10px 0 6px'
    }
  }, /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    style: {
      width: 36,
      height: 4,
      borderRadius: 2,
      background: 'var(--line-2)'
    }
  })), title && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 var(--sp-4) var(--sp-2)'
    }
  }, /*#__PURE__*/React.createElement("h2", {
    style: {
      margin: 0,
      fontSize: 'var(--fs-lg)',
      fontWeight: 600
    }
  }, title), /*#__PURE__*/React.createElement("button", {
    type: "button",
    "aria-label": "Close",
    onClick: onClose,
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: 32,
      height: 32,
      border: 0,
      borderRadius: '50%',
      background: 'var(--surface-2)',
      color: 'var(--ink-2)',
      cursor: 'pointer'
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: "x",
    size: 18
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      overflowY: 'auto',
      padding: 'var(--sp-2) var(--sp-4) var(--sp-5)'
    }
  }, children)));
}
Object.assign(__ds_scope, { Sheet });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Sheet.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Skeleton.jsx
try { (() => {
if (typeof document !== 'undefined' && !document.getElementById('pz-sk')) {
  const s = document.createElement('style');
  s.id = 'pz-sk';
  s.textContent = ".pz-sk{border-radius:var(--r-sm);background:var(--surface-2);position:relative;overflow:hidden}.pz-sk::after{content:'';position:absolute;inset:0;transform:translateX(-100%);background:linear-gradient(90deg,transparent,color-mix(in srgb,var(--surface) 70%,transparent),transparent);animation:pz-shimmer 1.6s linear infinite}@keyframes pz-shimmer{to{transform:translateX(100%)}}@media(prefers-reduced-motion:reduce){.pz-sk::after{display:none}}";
  document.head.appendChild(s);
}
function Skeleton({
  lines = 3,
  height
}) {
  return /*#__PURE__*/React.createElement("div", {
    "aria-busy": "true",
    "aria-live": "polite",
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 10,
      padding: '2px 0'
    }
  }, height ? /*#__PURE__*/React.createElement("div", {
    className: "pz-sk",
    style: {
      height
    }
  }) : Array.from({
    length: lines
  }, (_, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    className: "pz-sk",
    style: {
      height: 12,
      width: i === lines - 1 ? '60%' : '100%'
    }
  })));
}
Object.assign(__ds_scope, { Skeleton });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Skeleton.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Toast.jsx
try { (() => {
function Toast({
  text,
  tone = 'neutral',
  fixed = true
}) {
  if (!text) return null;
  const toast = /*#__PURE__*/React.createElement("div", {
    role: "status",
    style: {
      pointerEvents: 'auto',
      maxWidth: 'min(420px, calc(100vw - 32px))',
      padding: '10px 14px',
      borderRadius: 'var(--r-md)',
      background: tone === 'danger' ? 'var(--danger)' : 'var(--ink)',
      color: tone === 'danger' ? '#fff' : 'var(--on-ink)',
      fontSize: 'var(--fs-md)',
      fontWeight: 500,
      boxShadow: 'var(--shadow-3)'
    }
  }, text);
  if (!fixed) return toast;
  return /*#__PURE__*/React.createElement("div", {
    "aria-live": "polite",
    style: {
      position: 'fixed',
      left: 0,
      right: 0,
      bottom: 'var(--sp-6)',
      display: 'flex',
      justifyContent: 'center',
      pointerEvents: 'none',
      zIndex: 'var(--z-toast)'
    }
  }, toast);
}
Object.assign(__ds_scope, { Toast });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Toast.jsx", error: String((e && e.message) || e) }); }

// components/product/EmailRow.jsx
try { (() => {
if (typeof document !== 'undefined' && !document.getElementById('pz-email')) {
  const s = document.createElement('style');
  s.id = 'pz-email';
  s.textContent = ".pz-email{display:flex;align-items:stretch;gap:var(--sp-2);padding:6px var(--sp-3) 6px 6px;background:var(--surface);border:1px solid var(--line);border-radius:var(--r-md);transition:border-color var(--dur-hover) ease,box-shadow var(--dur-hover) ease,opacity var(--dur-hover) ease}.pz-email.active{border-color:var(--ink);box-shadow:0 0 0 1px var(--ink) inset}.pz-email.handled{opacity:.6}@media(hover:hover) and (pointer:fine){.pz-email:not(.active):hover{border-color:var(--line-2);box-shadow:var(--shadow-1)}}";
  document.head.appendChild(s);
}
function EmailRow({
  email,
  active = false,
  onOpen,
  onHandled
}) {
  return /*#__PURE__*/React.createElement("li", {
    className: 'pz-email' + (active ? ' active' : '') + (email.handled ? ' handled' : '')
  }, /*#__PURE__*/React.createElement("span", {
    title: email.accountLabel,
    style: {
      width: 3,
      borderRadius: 2,
      flex: 'none',
      background: email.accountColor || 'var(--ink-3)'
    }
  }), /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: () => onOpen && onOpen(email),
    style: {
      flex: 1,
      minWidth: 0,
      display: 'flex',
      flexDirection: 'column',
      gap: 2,
      textAlign: 'left',
      padding: '2px 4px',
      border: 0,
      background: 'none',
      color: 'inherit',
      font: 'inherit',
      cursor: 'pointer',
      borderRadius: 'var(--r-sm)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.PriorityBadge, {
    priority: email.priority
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ink)',
      fontWeight: 500,
      fontSize: 'var(--fs-md)',
      maxWidth: '40%',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap'
    }
  }, email.from), email.category && /*#__PURE__*/React.createElement(__ds_scope.Tag, null, email.category), email.needsReply && /*#__PURE__*/React.createElement(__ds_scope.Badge, {
    tone: "info"
  }, "reply"), email.areaColor && /*#__PURE__*/React.createElement(__ds_scope.AreaDot, {
    color: email.areaColor,
    name: email.areaName
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 'auto',
      whiteSpace: 'nowrap',
      color: 'var(--ink-3)',
      fontSize: 'var(--fs-xs)',
      letterSpacing: '0.02em',
      fontVariantNumeric: 'tabular-nums'
    }
  }, email.date)), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 'var(--fs-base)',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap'
    }
  }, email.subject), email.summary && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 'var(--fs-sm)',
      color: 'var(--ink-3)',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap'
    }
  }, email.summary)), /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    checked: !!email.handled,
    onChange: () => onHandled && onHandled(email),
    title: "Mark handled",
    "aria-label": 'Mark handled: ' + email.subject,
    style: {
      alignSelf: 'center'
    }
  }));
}
Object.assign(__ds_scope, { EmailRow });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/product/EmailRow.jsx", error: String((e && e.message) || e) }); }

// components/product/ListRow.jsx
try { (() => {
// Hairline-separated row inside a card: checkbox, title, trailing badges (.list-row).
function ListRow({
  checked,
  onCheck,
  done = false,
  title,
  lead,
  trailing,
  first = false,
  ariaLabel
}) {
  return /*#__PURE__*/React.createElement("li", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--sp-3)',
      padding: 'var(--sp-2) 0',
      borderTop: first ? 0 : '1px solid var(--line)',
      fontSize: 'var(--fs-base)',
      minWidth: 0
    }
  }, onCheck && /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    checked: !!checked,
    onChange: onCheck,
    "aria-label": ariaLabel || title
  }), lead, /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1,
      minWidth: 0,
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap',
      textDecoration: done ? 'line-through' : 'none',
      color: done ? 'var(--ink-3)' : 'inherit'
    }
  }, title), trailing);
}
Object.assign(__ds_scope, { ListRow });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/product/ListRow.jsx", error: String((e && e.message) || e) }); }

// components/product/TaskCard.jsx
try { (() => {
if (typeof document !== 'undefined' && !document.getElementById('pz-task')) {
  const s = document.createElement('style');
  s.id = 'pz-task';
  s.textContent = ".pz-task{display:flex;gap:var(--sp-2);align-items:flex-start;padding:var(--sp-2) var(--sp-3);border:1px solid var(--line);border-radius:var(--r-md);background:var(--surface);cursor:grab;transition:border-color var(--dur-hover) ease,box-shadow var(--dur-hover) var(--ease-out)}.pz-task.selected{border-color:var(--ink);box-shadow:0 0 0 1px var(--ink) inset}@media(hover:hover) and (pointer:fine){.pz-task:not(.selected):hover{border-color:var(--line-2);box-shadow:var(--shadow-1)}}";
  document.head.appendChild(s);
}
function TaskCard({
  task,
  selected = false,
  onSelect,
  onComplete
}) {
  const due = task.dueTone || 'neutral';
  return /*#__PURE__*/React.createElement("div", {
    className: 'pz-task' + (selected ? ' selected' : ''),
    role: "button",
    tabIndex: 0,
    onClick: () => onSelect && onSelect(task)
  }, /*#__PURE__*/React.createElement("label", {
    style: {
      paddingTop: 3,
      display: 'flex'
    },
    onClick: e => e.stopPropagation()
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    checked: task.status === 'done',
    onChange: () => onComplete && onComplete(task),
    "aria-label": 'Complete ' + task.title
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 'var(--fs-base)',
      lineHeight: 1.4,
      textDecoration: task.status === 'done' ? 'line-through' : 'none',
      color: task.status === 'done' ? 'var(--ink-3)' : 'inherit'
    }
  }, task.title), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexWrap: 'wrap',
      alignItems: 'center',
      gap: 6,
      marginTop: 4
    }
  }, task.areaColor && /*#__PURE__*/React.createElement(__ds_scope.AreaDot, {
    color: task.areaColor,
    name: task.areaName,
    label: true
  }), task.due && /*#__PURE__*/React.createElement(__ds_scope.Badge, {
    tone: due
  }, task.due), task.minutes && /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ink-3)',
      fontSize: 'var(--fs-sm)',
      fontVariantNumeric: 'tabular-nums'
    }
  }, task.minutes, " min"), task.status === 'scheduled' && /*#__PURE__*/React.createElement(__ds_scope.Badge, {
    tone: "ok"
  }, "scheduled"), task.status === 'inbox' && /*#__PURE__*/React.createElement(__ds_scope.Badge, {
    tone: "info"
  }, "inbox"), (task.tags || []).map(t => /*#__PURE__*/React.createElement(__ds_scope.Tag, {
    key: t
  }, t)))));
}
const QUADRANTS = [{
  key: 'do',
  label: 'Do first',
  hint: 'urgent + important',
  color: 'var(--danger)'
}, {
  key: 'schedule',
  label: 'Schedule',
  hint: 'important, not urgent',
  color: 'var(--info)'
}, {
  key: 'delegate',
  label: 'Delegate',
  hint: 'urgent, not important',
  color: 'var(--warn)'
}, {
  key: 'eliminate',
  label: 'Eliminate',
  hint: 'neither',
  color: 'var(--ink-3)'
}];
function Quadrant({
  quadrant,
  children,
  over = false,
  empty = false
}) {
  return /*#__PURE__*/React.createElement("section", {
    style: {
      position: 'relative',
      background: over ? 'var(--surface-3)' : 'var(--surface-2)',
      border: '1px solid ' + (over ? 'var(--ink)' : 'transparent'),
      borderTop: '2px solid ' + quadrant.color,
      borderRadius: 'var(--r-lg)',
      padding: 'var(--sp-3)',
      minHeight: 180,
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--sp-2)'
    }
  }, /*#__PURE__*/React.createElement("header", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'baseline',
      gap: 'var(--sp-2)',
      marginBottom: 2
    }
  }, /*#__PURE__*/React.createElement("h2", {
    style: {
      margin: 0,
      fontSize: 'var(--fs-base)',
      fontWeight: 600
    }
  }, quadrant.label), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ink-3)',
      fontSize: 'var(--fs-sm)'
    }
  }, quadrant.hint)), empty ? /*#__PURE__*/React.createElement("p", {
    style: {
      textAlign: 'center',
      padding: 'var(--sp-4) 0',
      margin: 'auto 0',
      color: 'var(--ink-3)',
      fontSize: 'var(--fs-sm)'
    }
  }, "Drop tasks here") : children);
}
Object.assign(__ds_scope, { TaskCard, QUADRANTS, Quadrant });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/product/TaskCard.jsx", error: String((e && e.message) || e) }); }

// components/product/TrackerChip.jsx
try { (() => {
if (typeof document !== 'undefined' && !document.getElementById('pz-chip')) {
  const s = document.createElement('style');
  s.id = 'pz-chip';
  s.textContent = ".pz-chip{display:inline-flex;align-items:center;gap:8px;height:32px;padding:0 12px;border-radius:var(--r-pill);border:1px solid var(--line-2);background:var(--surface);color:var(--ink);font-size:var(--fs-md);font-weight:500;cursor:pointer;font-family:inherit;transition:background-color var(--dur-hover) ease,border-color var(--dur-hover) ease,color var(--dur-hover) ease,transform var(--dur-press) var(--ease-out)}.pz-chip:active{transform:scale(0.97)}.pz-chip.met{background:var(--ok-soft);border-color:transparent;color:var(--ok)}.pz-chip.some{background:var(--warn-soft);border-color:transparent;color:var(--warn)}@media(hover:hover) and (pointer:fine){.pz-chip:not(.met):not(.some):hover{background:var(--surface-2)}}";
  document.head.appendChild(s);
}

// Tap-to-tick habit chip: met = ok tint with bold check; weekly_count shows n/target.
function TrackerChip({
  name,
  areaColor,
  met = false,
  some = false,
  count,
  target,
  onClick
}) {
  const cls = 'pz-chip' + (met ? ' met' : some ? ' some' : '');
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: cls,
    "aria-pressed": met,
    onClick: onClick
  }, /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    style: {
      width: 8,
      height: 8,
      borderRadius: '50%',
      background: areaColor || 'var(--ink-3)'
    }
  }), name, count !== undefined ? /*#__PURE__*/React.createElement("span", {
    style: {
      color: met ? 'inherit' : 'var(--ink-3)',
      fontSize: 'var(--fs-sm)',
      fontVariantNumeric: 'tabular-nums'
    }
  }, count, target ? '/' + target : '') : met ? /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: "check",
    weight: "bold",
    size: 14
  }) : null);
}
Object.assign(__ds_scope, { TrackerChip });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/product/TrackerChip.jsx", error: String((e && e.message) || e) }); }

// components/shell/CaptureBar.jsx
try { (() => {
const {
  useState
} = React;
if (typeof document !== 'undefined' && !document.getElementById('pz-capture')) {
  const s = document.createElement('style');
  s.id = 'pz-capture';
  s.textContent = ".pz-capture input{width:100%;height:34px;padding:0 12px 0 34px;border-radius:var(--r-pill);background:var(--surface-2);border:1px solid transparent;font:inherit;color:inherit}.pz-capture input::placeholder{color:var(--ink-3)}.pz-capture input:hover{border-color:var(--line-2)}.pz-capture input:focus-visible{background:var(--surface);border-color:var(--line-2);outline:2px solid var(--brand);outline-offset:1px}";
  document.head.appendChild(s);
}

// Top-bar quick input. Submit shows a proposal popover with Confirm / Edit / Discard.
function CaptureBar({
  placeholder = 'Capture anything',
  proposal,
  onSubmit,
  onConfirm,
  onDiscard
}) {
  const [text, setText] = useState('');
  return /*#__PURE__*/React.createElement("div", {
    className: "pz-capture",
    style: {
      position: 'relative',
      width: '100%',
      maxWidth: 480
    }
  }, /*#__PURE__*/React.createElement("form", {
    onSubmit: e => {
      e.preventDefault();
      if (text.trim() && onSubmit) onSubmit(text.trim());
      setText('');
    },
    style: {
      position: 'relative',
      display: 'flex',
      alignItems: 'center'
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: "lightning",
    size: 15,
    style: {
      position: 'absolute',
      left: 12,
      color: 'var(--ink-3)',
      pointerEvents: 'none'
    }
  }), /*#__PURE__*/React.createElement("input", {
    type: "text",
    value: text,
    onChange: e => setText(e.target.value),
    placeholder: placeholder,
    "aria-label": "Capture"
  })), proposal && /*#__PURE__*/React.createElement("div", {
    role: "status",
    style: {
      position: 'absolute',
      top: 'calc(100% + 6px)',
      left: 0,
      right: 0,
      zIndex: 'var(--z-sheet)',
      background: 'var(--surface)',
      color: 'var(--ink)',
      border: '1px solid var(--line)',
      borderRadius: 'var(--r-lg)',
      padding: 'var(--sp-3)',
      boxShadow: 'var(--shadow-2)',
      fontSize: 'var(--fs-md)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 'var(--sp-2)'
    }
  }, proposal), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 'var(--sp-2)',
      alignItems: 'center'
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Button, {
    size: "sm",
    variant: "primary",
    onClick: onConfirm
  }, "Confirm"), /*#__PURE__*/React.createElement("a", {
    href: "#",
    className: "link-btn",
    style: {
      fontSize: 'var(--fs-sm)',
      color: 'var(--ink-2)'
    }
  }, "Edit"), /*#__PURE__*/React.createElement(__ds_scope.Button, {
    size: "sm",
    variant: "ghost",
    onClick: onDiscard
  }, "Discard"))));
}
Object.assign(__ds_scope, { CaptureBar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/shell/CaptureBar.jsx", error: String((e && e.message) || e) }); }

// components/shell/NavRail.jsx
try { (() => {
const NAV = [{
  name: 'home',
  label: 'Home',
  icon: 'house'
}, {
  name: 'agenda',
  label: 'Agenda',
  icon: 'calendar-blank'
}, {
  name: 'tasks',
  label: 'Tasks',
  icon: 'check-square'
}, {
  name: 'goals',
  label: 'Goals',
  icon: 'target'
}, {
  name: 'mail',
  label: 'Mail',
  icon: 'envelope-simple'
}, {
  name: 'trackers',
  label: 'Tracking',
  icon: 'chart-line-up'
}, {
  name: 'hours',
  label: 'Hours',
  icon: 'timer'
}, {
  name: 'capture',
  label: 'Capture',
  icon: 'lightning'
}, {
  name: 'study',
  label: 'Study',
  icon: 'graduation-cap'
}, {
  name: 'notes',
  label: 'Notes',
  icon: 'note'
}, {
  name: 'review',
  label: 'Review',
  icon: 'clipboard-text'
}, {
  name: 'settings',
  label: 'Settings',
  icon: 'gear-six'
}];
if (typeof document !== 'undefined' && !document.getElementById('pz-nav')) {
  const s = document.createElement('style');
  s.id = 'pz-nav';
  s.textContent = ".pz-nav-item{display:flex;align-items:center;gap:10px;height:36px;padding:0 var(--sp-3);border-radius:var(--r-pill);color:var(--ink-2);text-decoration:none;font-size:var(--fs-base);font-weight:500;border:0;background:none;width:100%;text-align:left;cursor:pointer;font-family:inherit;transition:background-color var(--dur-hover) ease,color var(--dur-hover) ease}.pz-nav-item.active{background:var(--surface-3);color:var(--ink)}@media(hover:hover) and (pointer:fine){.pz-nav-item:not(.active):hover{background:var(--surface-2);color:var(--ink)}}";
  document.head.appendChild(s);
}
function NavItem({
  item,
  active = false,
  onClick,
  height
}) {
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: 'pz-nav-item' + (active ? ' active' : ''),
    "aria-current": active ? 'page' : undefined,
    onClick: onClick,
    style: height ? {
      height
    } : undefined
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: item.icon,
    size: 18
  }), item.label);
}
// 232px sticky rail, 12 fixed routes. Hidden under 1024px (nav sheet instead).
function NavRail({
  active = 'home',
  onNavigate,
  sticky = true
}) {
  return /*#__PURE__*/React.createElement("nav", {
    "aria-label": "Main",
    style: {
      position: sticky ? 'sticky' : 'static',
      top: 'var(--bar-h)',
      alignSelf: 'flex-start',
      height: sticky ? 'calc(100dvh - var(--bar-h))' : 'auto',
      width: 'var(--rail-w)',
      flex: 'none',
      padding: 'var(--sp-4) var(--sp-3)',
      display: 'flex',
      flexDirection: 'column',
      gap: 2,
      overflowY: 'auto',
      borderRight: '1px solid var(--line)'
    }
  }, NAV.map(it => /*#__PURE__*/React.createElement(NavItem, {
    key: it.name,
    item: it,
    active: it.name === active,
    onClick: () => onNavigate && onNavigate(it.name)
  })));
}
Object.assign(__ds_scope, { NAV, NavItem, NavRail });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/shell/NavRail.jsx", error: String((e && e.message) || e) }); }

// components/shell/TopBar.jsx
try { (() => {
// 56px sticky top bar: mark + wordmark, capture field centred, email + theme + log out right.
function TopBar({
  email = 'wout.altepost@gmail.com',
  dark = false,
  onToggleTheme,
  onLogout,
  onMenu,
  showMenu = false,
  logoSrc = 'assets/logo-mark.svg',
  capture = true
}) {
  return /*#__PURE__*/React.createElement("header", {
    style: {
      position: 'sticky',
      top: 0,
      zIndex: 'var(--z-bar)',
      height: 'var(--bar-h)',
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--sp-4)',
      padding: '0 var(--sp-5)',
      background: 'color-mix(in srgb, var(--surface) 88%, transparent)',
      backdropFilter: 'blur(14px) saturate(160%)',
      WebkitBackdropFilter: 'blur(14px) saturate(160%)',
      borderBottom: '1px solid var(--line)'
    }
  }, /*#__PURE__*/React.createElement("a", {
    href: "#",
    "aria-label": "Pozzy home",
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 10,
      textDecoration: 'none',
      color: 'var(--ink)',
      flex: 'none'
    }
  }, /*#__PURE__*/React.createElement("img", {
    src: logoSrc,
    alt: "",
    width: "26",
    height: "26",
    style: {
      width: 26,
      height: 26
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 600,
      letterSpacing: '-0.01em',
      fontSize: 'var(--fs-lg)'
    }
  }, "Pozzy")), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      display: 'flex',
      justifyContent: 'center',
      minWidth: 0
    }
  }, capture && /*#__PURE__*/React.createElement(__ds_scope.CaptureBar, null)), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--sp-1)',
      flex: 'none',
      marginLeft: 'auto'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 'var(--fs-sm)',
      marginRight: 'var(--sp-2)',
      color: 'var(--ink-3)'
    }
  }, email), /*#__PURE__*/React.createElement(__ds_scope.IconButton, {
    icon: dark ? 'sun' : 'moon',
    label: dark ? 'Switch to light mode' : 'Switch to dark mode',
    onClick: onToggleTheme
  }), /*#__PURE__*/React.createElement(__ds_scope.IconButton, {
    icon: "sign-out",
    label: "Log out",
    onClick: onLogout
  }), showMenu && /*#__PURE__*/React.createElement(__ds_scope.IconButton, {
    icon: "list",
    label: "Menu",
    onClick: onMenu
  })));
}
Object.assign(__ds_scope, { TopBar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/shell/TopBar.jsx", error: String((e && e.message) || e) }); }

// ui_kits/pozzy/AgendaScreen.jsx
try { (() => {
const DS = window.PozzyDesignSystem_379c1d;
const {
  Button,
  IconButton,
  Badge,
  PriorityBadge,
  Tag,
  AreaDot,
  Card,
  Inset,
  PageHeader,
  Field,
  Segmented,
  ProgressBar,
  WeekNav,
  Empty,
  Skeleton,
  Toast,
  Sheet,
  ListRow,
  TaskCard,
  Quadrant,
  QUADRANTS,
  EmailRow,
  TrackerChip,
  Icon
} = DS;
const hm = h => String(Math.floor(h)).padStart(2, '0') + ':' + String(Math.round(h % 1 * 60)).padStart(2, '0');
const HOUR_PX = 44,
  H0 = 6,
  H1 = 23;
const KIND = {
  event: ['var(--info-soft)', 'var(--info)', 'solid'],
  recurring: ['var(--surface-2)', 'var(--ink-3)', 'solid'],
  linked: ['var(--ok-soft)', 'var(--ok)', 'solid'],
  task: ['transparent', 'var(--ok)', 'dashed']
};
function AgendaScreen({
  toast
}) {
  const [view, setView] = React.useState('week');
  const [sel, setSel] = React.useState(null);
  const days = view === 'week' ? DAYS.map((d, i) => i) : [1];
  const gridH = (H1 - H0) * HOUR_PX;
  const now = (10.75 - H0) * HOUR_PX;
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(PageHeader, {
    title: "Agenda",
    meta: "Week of Mon 15 Sept"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 4
    }
  }, /*#__PURE__*/React.createElement(IconButton, {
    icon: "caret-left",
    label: "Previous"
  }), /*#__PURE__*/React.createElement(IconButton, {
    icon: "caret-right",
    label: "Next"
  }), /*#__PURE__*/React.createElement("input", {
    type: "date",
    defaultValue: "2026-09-15",
    "aria-label": "Go to date",
    style: {
      marginLeft: 4
    }
  })), /*#__PURE__*/React.createElement(Segmented, {
    value: view,
    options: [{
      value: 'week',
      label: 'Week'
    }, {
      value: 'day',
      label: 'Day'
    }],
    onChange: setView
  }), /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    onClick: () => setSel({
      new: true
    })
  }, "New event")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--sp-3)',
      margin: 'calc(var(--sp-5) * -1) 0 var(--sp-3)',
      fontSize: 'var(--fs-sm)',
      color: 'var(--ink-3)'
    }
  }, /*#__PURE__*/React.createElement(Badge, {
    tone: "ok",
    dot: true
  }, "synced 08:31"), /*#__PURE__*/React.createElement("span", null, "iCloud, 61 events"), /*#__PURE__*/React.createElement(Button, {
    size: "sm",
    variant: "link",
    onClick: () => toast('Sync started.')
  }, "Sync now")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: sel ? 'minmax(0,1fr) 340px' : 'minmax(0,1fr)',
      gap: 'var(--sp-5)',
      alignItems: 'start'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '52px repeat(' + days.length + ', minmax(0,1fr))',
      border: '1px solid var(--line)',
      borderRadius: 'var(--r-lg)',
      background: 'var(--surface)',
      overflow: 'hidden',
      fontSize: 'var(--fs-md)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      borderBottom: '1px solid var(--line)'
    }
  }), days.map(d => /*#__PURE__*/React.createElement("div", {
    key: d,
    style: {
      padding: '8px 4px',
      fontWeight: d === 1 ? 600 : 500,
      fontSize: 'var(--fs-sm)',
      color: d === 1 ? 'var(--brand)' : 'var(--ink-2)',
      background: d === 1 ? 'var(--brand-soft)' : 'none',
      textAlign: 'center',
      borderLeft: '1px solid var(--line)',
      borderBottom: '1px solid var(--line)',
      fontVariantNumeric: 'tabular-nums'
    }
  }, DAYS[d])), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 'var(--fs-xs)',
      color: 'var(--ink-3)',
      padding: '6px 4px',
      textAlign: 'right',
      letterSpacing: '0.02em',
      borderBottom: '1px solid var(--line)'
    }
  }, "all day"), days.map(d => /*#__PURE__*/React.createElement("div", {
    key: 'ad' + d,
    style: {
      minHeight: 30,
      padding: 2,
      borderLeft: '1px solid var(--line)',
      borderBottom: '1px solid var(--line)',
      background: d === 1 ? 'color-mix(in srgb, var(--brand-soft) 45%, transparent)' : 'none'
    }
  }, d === 4 && /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'block',
      fontSize: 'var(--fs-xs)',
      fontWeight: 500,
      borderRadius: 'var(--r-sm)',
      padding: '2px 6px',
      background: 'var(--surface-3)'
    },
    className: "truncate"
  }, "Deadline: sprint report"))), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      height: gridH
    }
  }, Array.from({
    length: H1 - H0
  }, (_, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      height: HOUR_PX,
      fontSize: 'var(--fs-xs)',
      color: 'var(--ink-3)',
      textAlign: 'right',
      paddingRight: 6,
      transform: 'translateY(-0.5em)',
      fontVariantNumeric: 'tabular-nums'
    }
  }, String(H0 + i).padStart(2, '0'), ":00"))), days.map(d => /*#__PURE__*/React.createElement("div", {
    key: 'c' + d,
    onClick: () => setSel({
      new: true,
      day: d
    }),
    style: {
      position: 'relative',
      height: gridH,
      borderLeft: '1px solid var(--line)',
      cursor: 'crosshair',
      background: d === 1 ? 'color-mix(in srgb, var(--brand-soft) 30%, transparent)' : 'none'
    }
  }, Array.from({
    length: H1 - H0
  }, (_, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      position: 'absolute',
      left: 0,
      right: 0,
      top: i * HOUR_PX,
      borderTop: '1px solid var(--line)',
      opacity: 0.7,
      pointerEvents: 'none'
    }
  })), d === 1 && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 0,
      right: 0,
      top: now,
      borderTop: '2px solid var(--brand)',
      zIndex: 3,
      pointerEvents: 'none'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      position: 'absolute',
      left: -1,
      top: -5,
      width: 8,
      height: 8,
      borderRadius: '50%',
      background: 'var(--brand)'
    }
  })), EVENTS.filter(e => e.day === d).map(e => {
    const [bg, ac, bs] = KIND[e.kind];
    return /*#__PURE__*/React.createElement("button", {
      key: e.id,
      type: "button",
      onClick: ev => {
        ev.stopPropagation();
        setSel({
          event: e
        });
      },
      title: e.title,
      style: {
        position: 'absolute',
        top: (e.start - H0) * HOUR_PX,
        height: Math.max((e.end - e.start) * HOUR_PX, 18),
        left: 0,
        right: 0,
        margin: 1,
        padding: '2px 6px 2px 8px',
        borderRadius: 'var(--r-sm)',
        overflow: 'hidden',
        textAlign: 'left',
        font: 'inherit',
        fontSize: 'var(--fs-sm)',
        lineHeight: 1.25,
        cursor: 'pointer',
        zIndex: 2,
        display: 'flex',
        flexDirection: 'column',
        gap: 1,
        background: bg,
        color: e.kind === 'task' ? ac : 'var(--ink)',
        border: '1px ' + bs + ' ' + (e.kind === 'task' ? ac : 'color-mix(in srgb, ' + ac + ' 35%, transparent)'),
        outline: sel && sel.event && sel.event.id === e.id ? '2px solid var(--ink)' : 'none'
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 'var(--fs-xs)',
        color: ac,
        fontWeight: 500,
        fontVariantNumeric: 'tabular-nums'
      }
    }, hm(e.start)), /*#__PURE__*/React.createElement("span", {
      className: "truncate",
      style: {
        fontWeight: 500
      }
    }, e.title));
  })))), /*#__PURE__*/React.createElement("p", {
    style: {
      display: 'flex',
      gap: 6,
      alignItems: 'center',
      flexWrap: 'wrap',
      margin: 'var(--sp-2) 0 0',
      fontSize: 'var(--fs-xs)',
      color: 'var(--ink-3)',
      letterSpacing: '0.02em'
    }
  }, [['event', 'event'], ['recurring', 'recurring'], ['linked', 'Pozzy task event'], ['task', 'scheduled task (not yet on iCloud)']].map(([k, l]) => {
    const [bg, ac, bs] = KIND[k];
    return /*#__PURE__*/React.createElement(React.Fragment, {
      key: k
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        display: 'inline-block',
        width: 12,
        height: 12,
        borderRadius: 3,
        marginLeft: 6,
        background: bg,
        border: '1px ' + bs + ' ' + (k === 'task' ? ac : 'color-mix(in srgb, ' + ac + ' 35%, transparent)')
      }
    }), " ", l);
  }))), sel && /*#__PURE__*/React.createElement(Card, {
    title: sel.event ? 'Event' : 'New event',
    meta: /*#__PURE__*/React.createElement("button", {
      className: "link-btn",
      onClick: () => setSel(null)
    }, "Close"),
    style: {
      position: 'sticky',
      top: 'calc(var(--bar-h) + var(--sp-4))'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--sp-3)'
    }
  }, /*#__PURE__*/React.createElement(Field, {
    label: "Title"
  }, /*#__PURE__*/React.createElement("input", {
    type: "text",
    defaultValue: sel.event ? sel.event.title : '',
    placeholder: "Event title"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 'var(--sp-2)'
    }
  }, /*#__PURE__*/React.createElement(Field, {
    label: "Start"
  }, /*#__PURE__*/React.createElement("input", {
    type: "time",
    defaultValue: sel.event ? hm(sel.event.start) : '09:00'
  })), /*#__PURE__*/React.createElement(Field, {
    label: "End"
  }, /*#__PURE__*/React.createElement("input", {
    type: "time",
    defaultValue: sel.event ? hm(sel.event.end) : '10:00'
  }))), /*#__PURE__*/React.createElement(Field, {
    label: "Date"
  }, /*#__PURE__*/React.createElement("input", {
    type: "date",
    defaultValue: '2026-09-' + (15 + (sel.event ? sel.event.day : sel.day || 1))
  })), /*#__PURE__*/React.createElement(Field, {
    label: "Location"
  }, /*#__PURE__*/React.createElement("input", {
    type: "text",
    defaultValue: sel.event ? sel.event.location || '' : ''
  })), /*#__PURE__*/React.createElement(Field, {
    label: "Calendar",
    hint: sel.event && sel.event.kind === 'recurring' ? 'Recurring iCloud occurrences are read-only.' : ''
  }, /*#__PURE__*/React.createElement("select", {
    defaultValue: "Wouter"
  }, /*#__PURE__*/React.createElement("option", null, "Wouter"), /*#__PURE__*/React.createElement("option", null, "Studie"), /*#__PURE__*/React.createElement("option", null, "Werk"))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 'var(--sp-2)',
      alignItems: 'center',
      marginTop: 'var(--sp-1)'
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    disabled: sel.event && sel.event.kind === 'recurring',
    onClick: () => {
      toast(sel.event ? 'Event saved.' : 'Event created on iCloud.');
      setSel(null);
    }
  }, "Save"), /*#__PURE__*/React.createElement(Button, {
    variant: "ghost",
    onClick: () => setSel(null)
  }, "Cancel"), /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1
    }
  }), sel.event && sel.event.kind !== 'recurring' && /*#__PURE__*/React.createElement(Button, {
    variant: "danger",
    onClick: () => {
      toast('Event deleted.');
      setSel(null);
    }
  }, "Delete"))))));
}
window.AgendaScreen = AgendaScreen;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/pozzy/AgendaScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/pozzy/Data.jsx
try { (() => {
const AREAS = {
  study: {
    name: 'Study',
    color: '#2563eb'
  },
  work: {
    name: 'Work',
    color: '#dc2626'
  },
  personal: {
    name: 'Personal',
    color: '#059669'
  },
  health: {
    name: 'Health',
    color: '#d97706'
  }
};
const ACCOUNTS = {
  main: {
    label: 'wout.altepost',
    color: '#7c3aed'
  },
  udefine: {
    label: 'UDefine',
    color: '#2563eb'
  },
  alpaca: {
    label: 'alpaca AI',
    color: '#059669'
  },
  uni: {
    label: 'University',
    color: '#d97706'
  }
};
const EVENTS = [{
  id: 'e1',
  day: 1,
  start: 9.5,
  end: 12,
  title: 'Sprint 1 NGS Projectbegeleiding',
  location: 'AM00.02.270',
  kind: 'event'
}, {
  id: 'e2',
  day: 1,
  start: 12.5,
  end: 15.5,
  title: 'Sprint 2 NGS Projectbegeleiding & Ondernemerschap',
  location: 'AM00.02.270',
  kind: 'event'
}, {
  id: 'e3',
  day: 1,
  start: 16.75,
  end: 18.75,
  title: '2u aan I&T zitten',
  kind: 'task'
}, {
  id: 'e4',
  day: 1,
  start: 20,
  end: 22,
  title: 'Training',
  location: 'AVV FIT',
  kind: 'recurring'
}, {
  id: 'e5',
  day: 0,
  start: 10,
  end: 11,
  title: 'Weekly review',
  kind: 'recurring'
}, {
  id: 'e6',
  day: 2,
  start: 9,
  end: 12.5,
  title: 'Hoorcollege Ondernemerschap',
  location: 'C0.110',
  kind: 'event'
}, {
  id: 'e7',
  day: 2,
  start: 14,
  end: 16,
  title: 'alpaca AI: klantcall Vermeer',
  kind: 'event'
}, {
  id: 'e8',
  day: 3,
  start: 9.5,
  end: 12,
  title: 'Sprint 3 NGS Projectbegeleiding',
  location: 'AM00.02.270',
  kind: 'event'
}, {
  id: 'e9',
  day: 3,
  start: 13,
  end: 15,
  title: 'UDefine landing page fixes',
  kind: 'linked'
}, {
  id: 'e10',
  day: 3,
  start: 20,
  end: 22,
  title: 'Training',
  location: 'AVV FIT',
  kind: 'recurring'
}, {
  id: 'e11',
  day: 4,
  start: 11,
  end: 12,
  title: 'Tandarts',
  kind: 'event'
}, {
  id: 'e12',
  day: 4,
  start: 15,
  end: 17,
  title: 'Stage sollicitatie voorbereiden',
  kind: 'task'
}, {
  id: 'e13',
  day: 5,
  start: 10,
  end: 13,
  title: 'Wielrennen',
  kind: 'recurring'
}];
const TASKS = [{
  id: 't1',
  title: 'Fix Railway production build',
  quadrant: 'do',
  area: 'work',
  due: 'Tue 16 Sept',
  dueTone: 'warn',
  minutes: 45,
  tags: ['pozzy']
}, {
  id: 't2',
  title: 'Update Anthropic payment card',
  quadrant: 'do',
  area: 'work',
  due: 'Mon 15 Sept',
  dueTone: 'danger',
  minutes: 10,
  status: 'inbox'
}, {
  id: 't3',
  title: 'Write NGS sprint 1 report',
  quadrant: 'schedule',
  area: 'study',
  due: 'Fri 19 Sept',
  minutes: 120
}, {
  id: 't4',
  title: 'Prepare internship application (Booking)',
  quadrant: 'schedule',
  area: 'study',
  due: 'Thu 25 Sept',
  minutes: 90,
  status: 'scheduled'
}, {
  id: 't5',
  title: 'Order new bike chain',
  quadrant: 'delegate',
  area: 'health',
  minutes: 15
}, {
  id: 't6',
  title: 'Reply to alpaca AI lead (Vermeer)',
  quadrant: 'delegate',
  area: 'work',
  due: 'Wed 17 Sept',
  minutes: 20,
  tags: ['alpaca']
}, {
  id: 't7',
  title: 'Sort old screenshots',
  quadrant: 'eliminate',
  area: 'personal'
}, {
  id: 't8',
  title: 'Check exposure after Ace & Tate breach',
  quadrant: 'do',
  area: 'personal',
  minutes: 15,
  status: 'inbox'
}];
const EMAILS = [{
  id: 'm1',
  from: 'Ace & Tate',
  subject: 'Update over het beveiligingsincident en datalek bij CEVA',
  summary: 'Logistics partner breach; customer data may be exposed.',
  date: 'Tue 15 Sept, 06:12',
  priority: 1,
  category: 'notification',
  account: 'main',
  area: 'personal',
  body: 'Beste klant, wij informeren u over een beveiligingsincident bij onze logistieke partner CEVA. Mogelijk zijn naam, adres en ordergegevens betrokken. Wachtwoorden en betaalgegevens zijn niet geraakt. Wij adviseren alert te zijn op verdachte berichten.'
}, {
  id: 'm2',
  from: 'Railway',
  subject: 'Deployment failed: pozzy-web (3rd consecutive failure)',
  summary: 'Build step exited with code 1 in vite build.',
  date: 'Mon 14 Sept, 23:40',
  priority: 1,
  category: 'alert',
  account: 'main',
  area: 'work',
  body: 'Your deployment of pozzy-web failed. Build exited with code 1. This is the third consecutive failure for this service.'
}, {
  id: 'm3',
  from: 'Anthropic',
  subject: 'Payment failed for your Anthropic account',
  summary: 'Card declined; API access pauses after 7 days.',
  date: 'Mon 14 Sept, 18:03',
  priority: 1,
  category: 'billing',
  account: 'alpaca',
  area: 'work',
  needsReply: false,
  body: 'We could not process your payment. Please update your card to keep API access.'
}, {
  id: 'm4',
  from: 'Petra de Vries',
  subject: 'Re: NGS sprint 1 feedback',
  summary: 'Wants the report before Friday; asks about team roles.',
  date: 'Mon 14 Sept, 16:20',
  priority: 2,
  category: 'personal',
  account: 'uni',
  area: 'study',
  needsReply: true,
  body: 'Hoi Wouter, kun je het sprintverslag voor vrijdag delen? Ik ben ook benieuwd hoe jullie de rollen hebben verdeeld.'
}, {
  id: 'm5',
  from: 'Jan Vermeer',
  subject: 'Offerte alpaca AI voor onze klantenservice',
  summary: 'Asks for a quote and a call this week.',
  date: 'Mon 14 Sept, 11:45',
  priority: 2,
  category: 'personal',
  account: 'alpaca',
  area: 'work',
  needsReply: true,
  body: 'Beste Wouter, na ons gesprek willen we graag een offerte ontvangen. Kunnen we deze week nog bellen?'
}, {
  id: 'm6',
  from: 'Supabase',
  subject: 'Your project is approaching the free tier limit',
  summary: 'Database size at 82% of 500 MB.',
  date: 'Sun 13 Sept, 09:00',
  priority: 3,
  category: 'notification',
  account: 'main',
  area: 'work',
  body: 'Your project pozzy is at 82% of its database quota.'
}, {
  id: 'm7',
  from: 'UDefine Stripe',
  subject: 'Payout of EUR 240.00 is on its way',
  summary: 'Arrives Wed 17 Sept.',
  date: 'Sat 12 Sept, 08:15',
  priority: 3,
  category: 'billing',
  account: 'udefine',
  area: 'work',
  body: 'A payout of EUR 240.00 was sent to your bank account.'
}, {
  id: 'm8',
  from: 'Strava',
  subject: 'Your weekly summary',
  summary: '3 activities, 142 km.',
  date: 'Sun 13 Sept, 07:00',
  priority: 4,
  category: 'newsletter',
  account: 'main',
  area: 'health',
  body: 'You logged 3 activities this week.'
}];
const DAYS = ['Mon 15', 'Tue 16', 'Wed 17', 'Thu 18', 'Fri 19', 'Sat 20', 'Sun 21'];
Object.assign(window, {
  AREAS,
  ACCOUNTS,
  EVENTS,
  TASKS,
  EMAILS,
  DAYS
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/pozzy/Data.jsx", error: String((e && e.message) || e) }); }

// ui_kits/pozzy/HomeScreen.jsx
try { (() => {
const DS = window.PozzyDesignSystem_379c1d;
const {
  Button,
  IconButton,
  Badge,
  PriorityBadge,
  Tag,
  AreaDot,
  Card,
  Inset,
  PageHeader,
  Field,
  Segmented,
  ProgressBar,
  WeekNav,
  Empty,
  Skeleton,
  Toast,
  Sheet,
  ListRow,
  TaskCard,
  Quadrant,
  QUADRANTS,
  EmailRow,
  TrackerChip,
  Icon
} = DS;
const hm = h => String(Math.floor(h)).padStart(2, '0') + ':' + String(Math.round(h % 1 * 60)).padStart(2, '0');
function HomeScreen({
  go,
  toast
}) {
  const [dos, setDos] = React.useState([{
    id: 1,
    title: 'Fix the Railway build before 09:30',
    done: true
  }, {
    id: 2,
    title: 'Log both NGS sessions in Hours',
    done: false,
    rolled: 0
  }, {
    id: 3,
    title: 'Reply to Petra about sprint roles',
    done: false,
    rolled: 2
  }]);
  const [tasks, setTasks] = React.useState(TASKS.filter(t => t.dueTone));
  const [tracked, setTracked] = React.useState({
    gym: true,
    reading: 3,
    dutch: 1,
    sugar: false
  });
  const [goals, setGoals] = React.useState([{
    id: 1,
    title: 'Ship Pozzy design pass',
    area: 'work',
    done: false
  }, {
    id: 2,
    title: 'Three study blocks of 2h',
    area: 'study',
    cur: 1,
    target: 3
  }, {
    id: 3,
    title: 'Two trainings',
    area: 'health',
    cur: 2,
    target: 2,
    done: true
  }]);
  const [briefing, setBriefing] = React.useState(true);
  const today = EVENTS.filter(e => e.day === 1);
  const hours = [['study', 0, 0], ['work', 0, 960], ['personal', 45, 0], ['health', 120, 0]];
  const toggleDo = d => setDos(dos.map(x => x.id === d.id ? {
    ...x,
    done: !x.done
  } : x));
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h1", {
    style: {
      fontSize: 'var(--fs-3xl)',
      letterSpacing: '-0.02em',
      lineHeight: 1.15,
      margin: '0 0 var(--sp-5)',
      fontWeight: 600
    }
  }, "Tuesday ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ink-3)',
      fontWeight: 500
    }
  }, "15 September")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr)',
      gap: 'var(--sp-5)',
      alignItems: 'start'
    }
  }, /*#__PURE__*/React.createElement(Card, {
    title: "Today's three do's",
    meta: "Tue 15 Sept"
  }, /*#__PURE__*/React.createElement("ul", null, dos.map((d, i) => /*#__PURE__*/React.createElement(ListRow, {
    key: d.id,
    first: i === 0,
    checked: d.done,
    done: d.done,
    onCheck: () => toggleDo(d),
    title: d.title,
    trailing: d.rolled ? /*#__PURE__*/React.createElement(Badge, {
      tone: "warn"
    }, "rolled ", d.rolled, "x") : null
  })))), /*#__PURE__*/React.createElement(Card, {
    title: "Today",
    meta: /*#__PURE__*/React.createElement("a", {
      href: "#",
      onClick: e => {
        e.preventDefault();
        go('agenda');
      }
    }, "Agenda")
  }, /*#__PURE__*/React.createElement("ul", null, today.map((e, i) => /*#__PURE__*/React.createElement(ListRow, {
    key: e.id,
    first: i === 0,
    lead: /*#__PURE__*/React.createElement("span", {
      style: {
        color: 'var(--ink-3)',
        fontSize: 'var(--fs-sm)',
        minWidth: 96,
        flex: 'none',
        fontVariantNumeric: 'tabular-nums'
      }
    }, hm(e.start), " to ", hm(e.end)),
    title: e.title,
    trailing: e.kind === 'task' ? /*#__PURE__*/React.createElement(Badge, {
      tone: "ok"
    }, "task") : e.location ? /*#__PURE__*/React.createElement("span", {
      style: {
        color: 'var(--ink-3)',
        fontSize: 'var(--fs-sm)',
        maxWidth: '40%'
      },
      className: "truncate"
    }, e.location) : null
  })))), /*#__PURE__*/React.createElement(Card, {
    title: "Top emails",
    meta: /*#__PURE__*/React.createElement("a", {
      href: "#",
      onClick: e => {
        e.preventDefault();
        go('mail');
      }
    }, "Inbox")
  }, /*#__PURE__*/React.createElement("ul", null, EMAILS.filter(e => e.priority <= 2).slice(0, 4).map((e, i) => /*#__PURE__*/React.createElement("li", {
    key: e.id,
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--sp-3)',
      padding: 'var(--sp-2) 0',
      borderTop: i ? '1px solid var(--line)' : 0
    }
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    "aria-label": 'Mark handled: ' + e.subject,
    onChange: () => toast('Marked handled.')
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      width: 8,
      height: 8,
      borderRadius: '50%',
      flex: 'none',
      background: ACCOUNTS[e.account].color
    }
  }), /*#__PURE__*/React.createElement(PriorityBadge, {
    priority: e.priority
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1,
      minWidth: 0,
      display: 'flex',
      flexDirection: 'column',
      gap: 1
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "truncate",
    style: {
      fontSize: 'var(--fs-sm)',
      color: 'var(--ink-3)'
    }
  }, e.from), /*#__PURE__*/React.createElement("span", {
    className: "truncate",
    style: {
      fontSize: 'var(--fs-md)'
    }
  }, e.subject)), e.needsReply && /*#__PURE__*/React.createElement(Badge, {
    tone: "info"
  }, "reply"))))), /*#__PURE__*/React.createElement(Card, {
    title: "Due today or overdue",
    meta: /*#__PURE__*/React.createElement("a", {
      href: "#",
      onClick: e => {
        e.preventDefault();
        go('tasks');
      }
    }, "All tasks")
  }, tasks.length ? /*#__PURE__*/React.createElement("ul", null, tasks.map((t, i) => /*#__PURE__*/React.createElement(ListRow, {
    key: t.id,
    first: i === 0,
    onCheck: () => {
      setTasks(tasks.filter(x => x.id !== t.id));
      toast('Task completed.');
    },
    title: t.title,
    trailing: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(AreaDot, {
      color: AREAS[t.area].color,
      name: AREAS[t.area].name
    }), /*#__PURE__*/React.createElement(Badge, {
      tone: t.dueTone
    }, t.dueTone === 'danger' ? 'overdue ' : '', t.due))
  }))) : /*#__PURE__*/React.createElement(Empty, {
    compact: true,
    icon: "check-square",
    title: "Nothing due",
    hint: "No tasks due today and nothing overdue."
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      gridColumn: '1 / -1'
    }
  }, /*#__PURE__*/React.createElement(Card, {
    title: "Trackers today",
    meta: /*#__PURE__*/React.createElement("a", {
      href: "#",
      onClick: e => e.preventDefault()
    }, "Tracking")
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexWrap: 'wrap',
      gap: 'var(--sp-2)'
    }
  }, /*#__PURE__*/React.createElement(TrackerChip, {
    name: "Gym",
    areaColor: AREAS.health.color,
    met: tracked.gym,
    onClick: () => setTracked({
      ...tracked,
      gym: !tracked.gym
    })
  }), /*#__PURE__*/React.createElement(TrackerChip, {
    name: "Reading",
    areaColor: AREAS.personal.color,
    count: tracked.reading,
    target: 5,
    met: tracked.reading >= 5,
    onClick: () => setTracked({
      ...tracked,
      reading: Math.min(5, tracked.reading + 1)
    })
  }), /*#__PURE__*/React.createElement(TrackerChip, {
    name: "Dutch practice",
    areaColor: AREAS.study.color,
    count: tracked.dutch,
    target: 4,
    some: tracked.dutch > 0 && tracked.dutch < 4,
    met: tracked.dutch >= 4,
    onClick: () => setTracked({
      ...tracked,
      dutch: Math.min(4, tracked.dutch + 1)
    })
  }), /*#__PURE__*/React.createElement(TrackerChip, {
    name: "No sugar",
    areaColor: AREAS.health.color,
    met: tracked.sugar,
    onClick: () => setTracked({
      ...tracked,
      sugar: !tracked.sugar
    })
  })))), /*#__PURE__*/React.createElement(Card, {
    title: "Hours this week",
    meta: /*#__PURE__*/React.createElement("a", {
      href: "#",
      onClick: e => e.preventDefault()
    }, "2h 45m total")
  }, hours.map(([a, min, target]) => /*#__PURE__*/React.createElement("div", {
    key: a,
    style: {
      display: 'grid',
      gridTemplateColumns: '92px 1fr auto',
      gap: 'var(--sp-3)',
      alignItems: 'center',
      fontSize: 'var(--fs-md)',
      padding: '5px 0'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      color: 'var(--ink-2)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 8,
      height: 8,
      borderRadius: '50%',
      background: AREAS[a].color
    }
  }), AREAS[a].name), /*#__PURE__*/React.createElement(ProgressBar, {
    value: min,
    max: target || (min ? min : 1),
    tone: "auto"
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      whiteSpace: 'nowrap',
      fontVariantNumeric: 'tabular-nums',
      fontSize: 'var(--fs-sm)'
    }
  }, min ? min >= 60 ? Math.floor(min / 60) + 'h ' + (min % 60 ? min % 60 + 'm' : '') : min + 'm' : '0m', target ? /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ink-3)'
    }
  }, " / ", target / 60, "h") : null)))), /*#__PURE__*/React.createElement(Card, {
    title: "Weekly goals",
    meta: /*#__PURE__*/React.createElement("a", {
      href: "#",
      onClick: e => e.preventDefault()
    }, goals.filter(g => g.done).length, " of ", goals.length, " done")
  }, /*#__PURE__*/React.createElement("ul", null, goals.map((g, i) => /*#__PURE__*/React.createElement(ListRow, {
    key: g.id,
    first: i === 0,
    checked: g.done,
    done: g.done,
    onCheck: () => setGoals(goals.map(x => x.id === g.id ? {
      ...x,
      done: !x.done
    } : x)),
    title: g.title,
    trailing: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(AreaDot, {
      color: AREAS[g.area].color,
      name: AREAS[g.area].name
    }), g.target && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
      style: {
        color: 'var(--ink-3)',
        fontSize: 'var(--fs-sm)',
        fontVariantNumeric: 'tabular-nums'
      }
    }, g.cur, "/", g.target), /*#__PURE__*/React.createElement(Button, {
      size: "sm",
      variant: "ghost",
      onClick: () => setGoals(goals.map(x => x.id === g.id ? {
        ...x,
        cur: Math.min(x.target, x.cur + 1),
        done: x.cur + 1 >= x.target
      } : x))
    }, "+1")))
  })))), /*#__PURE__*/React.createElement(Card, {
    title: "Deadlines",
    meta: "next 14 days"
  }, /*#__PURE__*/React.createElement("ul", null, /*#__PURE__*/React.createElement(ListRow, {
    first: true,
    title: "NGS sprint 1 report",
    trailing: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(AreaDot, {
      color: AREAS.study.color,
      name: "Study"
    }), /*#__PURE__*/React.createElement(Badge, {
      tone: "warn"
    }, "Fri 19 Sept"))
  }), /*#__PURE__*/React.createElement(ListRow, {
    title: "Booking internship: send application",
    trailing: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(AreaDot, {
      color: AREAS.study.color,
      name: "Study"
    }), /*#__PURE__*/React.createElement(Badge, null, "Thu 25 Sept"))
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      gridColumn: '1 / -1'
    }
  }, /*#__PURE__*/React.createElement(Card, {
    title: "Briefing",
    meta: /*#__PURE__*/React.createElement("span", {
      style: {
        display: 'inline-flex',
        alignItems: 'center',
        gap: 'var(--sp-3)'
      }
    }, briefing && 'Claude, Tue 15 Sept, 07:00', /*#__PURE__*/React.createElement(Button, {
      size: "sm",
      variant: "ghost",
      onClick: () => {
        setBriefing(true);
        toast('Briefing regenerated.');
      }
    }, briefing ? 'Regenerate' : 'Generate'))
  }, briefing ? /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: '68ch',
      fontSize: 'var(--fs-base)',
      lineHeight: 1.6
    }
  }, /*#__PURE__*/React.createElement("p", null, "Tuesday is structured end to end: two NGS project sessions through 15:30, two hours on I&T until 18:45, then training at 20:00. You have two tasks due and one deadline on Friday, so this is mostly about showing up and executing what is scheduled."), /*#__PURE__*/React.createElement("p", null, "Three things need attention before you start. Your Pozzy production builds are failing on Railway, three alerts in a row means something broke. Your Anthropic payment bounced, so update the card or the service stops. Ace & Tate flagged a data breach at their logistics partner; review what is exposed."), /*#__PURE__*/React.createElement("p", null, "Work hours are at zero against a sixteen-hour target for the week. Today will close that gap if you log the sessions properly.")) : /*#__PURE__*/React.createElement(Empty, {
    compact: true,
    icon: "clipboard-text",
    title: "No briefing yet",
    hint: "Generate one when the morning sync has run."
  })))));
}
window.HomeScreen = HomeScreen;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/pozzy/HomeScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/pozzy/LoginScreen.jsx
try { (() => {
const DS = window.PozzyDesignSystem_379c1d;
const {
  Button,
  IconButton,
  Badge,
  PriorityBadge,
  Tag,
  AreaDot,
  Card,
  Inset,
  PageHeader,
  Field,
  Segmented,
  ProgressBar,
  WeekNav,
  Empty,
  Skeleton,
  Toast,
  Sheet,
  ListRow,
  TaskCard,
  Quadrant,
  QUADRANTS,
  EmailRow,
  TrackerChip,
  Icon
} = DS;
function LoginScreen({
  onLogin
}) {
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState('');
  const [pw, setPw] = React.useState('');
  const submit = e => {
    e.preventDefault();
    setBusy(true);
    setError('');
    setTimeout(() => {
      setBusy(false);
      if (pw.length < 4) setError('Invalid login credentials');else onLogin();
    }, 700);
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'center',
      paddingTop: 'var(--sp-10)'
    }
  }, /*#__PURE__*/React.createElement(Card, {
    style: {
      width: '100%',
      maxWidth: 360,
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--sp-4)'
    }
  }, /*#__PURE__*/React.createElement("img", {
    src: "../../assets/logo-wordmark.png",
    alt: "Pozzy",
    width: "180",
    style: {
      width: 180,
      height: 'auto',
      margin: 'var(--sp-2) auto 0'
    }
  }), /*#__PURE__*/React.createElement("h1", {
    style: {
      fontSize: 'var(--fs-xl)',
      textAlign: 'center',
      margin: 0
    }
  }, "Log in"), /*#__PURE__*/React.createElement("form", {
    onSubmit: submit,
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--sp-3)'
    }
  }, /*#__PURE__*/React.createElement(Field, {
    label: "Email"
  }, /*#__PURE__*/React.createElement("input", {
    type: "email",
    defaultValue: "wout.altepost@gmail.com",
    autoComplete: "username",
    required: true
  })), /*#__PURE__*/React.createElement(Field, {
    label: "Password",
    error: error,
    hint: !error ? 'Try any password of 4+ characters' : ''
  }, /*#__PURE__*/React.createElement("input", {
    type: "password",
    value: pw,
    onChange: e => setPw(e.target.value),
    autoComplete: "current-password",
    required: true
  })), /*#__PURE__*/React.createElement(Button, {
    type: "submit",
    variant: "primary",
    loading: busy,
    block: true
  }, "Log in"))));
}
window.LoginScreen = LoginScreen;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/pozzy/LoginScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/pozzy/MailScreen.jsx
try { (() => {
const DS = window.PozzyDesignSystem_379c1d;
const {
  Button,
  IconButton,
  Badge,
  PriorityBadge,
  Tag,
  AreaDot,
  Card,
  Inset,
  PageHeader,
  Field,
  Segmented,
  ProgressBar,
  WeekNav,
  Empty,
  Skeleton,
  Toast,
  Sheet,
  ListRow,
  TaskCard,
  Quadrant,
  QUADRANTS,
  EmailRow,
  TrackerChip,
  Icon
} = DS;
function MailScreen({
  toast
}) {
  const [emails, setEmails] = React.useState(EMAILS);
  const [selId, setSelId] = React.useState(null);
  const [handledFilter, setHandledFilter] = React.useState('0');
  const [syncing, setSyncing] = React.useState(false);
  const [notice, setNotice] = React.useState('');
  const sel = emails.find(e => e.id === selId);
  const shown = emails.filter(e => handledFilter === 'all' || handledFilter === '1' === !!e.handled);
  const row = e => ({
    ...e,
    accountColor: ACCOUNTS[e.account].color,
    accountLabel: ACCOUNTS[e.account].label,
    areaColor: AREAS[e.area].color,
    areaName: AREAS[e.area].name
  });
  const setHandled = e => setEmails(emails.map(x => x.id === e.id ? {
    ...x,
    handled: !x.handled
  } : x));
  const sync = () => {
    setSyncing(true);
    setNotice('');
    setTimeout(() => {
      setSyncing(false);
      setNotice('Synced: 0 new, 0 classified (haiku).');
    }, 900);
  };
  const sels = {
    height: 'var(--control-h-sm)',
    paddingLeft: 10,
    fontSize: 'var(--fs-md)',
    borderRadius: 'var(--r-pill)'
  };
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(PageHeader, {
    title: "Mail",
    meta: emails.filter(e => !e.handled).length + ' unhandled, ' + emails.filter(e => e.needsReply && !e.handled).length + ' need a reply'
  }, /*#__PURE__*/React.createElement(Button, {
    loading: syncing,
    onClick: sync
  }, "Sync now"), /*#__PURE__*/React.createElement("a", {
    href: "#",
    className: "link-btn",
    onClick: e => e.preventDefault()
  }, "Accounts")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexWrap: 'wrap',
      gap: 'var(--sp-2)',
      alignItems: 'center'
    }
  }, /*#__PURE__*/React.createElement("input", {
    type: "search",
    placeholder: "Search from, subject, summary",
    "aria-label": "Search mail",
    style: {
      ...sels,
      flex: '1 1 200px',
      minWidth: 180
    }
  }), /*#__PURE__*/React.createElement("select", {
    "aria-label": "Account",
    style: sels,
    defaultValue: ""
  }, /*#__PURE__*/React.createElement("option", {
    value: ""
  }, "All accounts"), Object.values(ACCOUNTS).map(a => /*#__PURE__*/React.createElement("option", {
    key: a.label
  }, a.label))), /*#__PURE__*/React.createElement("select", {
    "aria-label": "Category",
    style: sels,
    defaultValue: ""
  }, /*#__PURE__*/React.createElement("option", {
    value: ""
  }, "All categories"), /*#__PURE__*/React.createElement("option", null, "personal"), /*#__PURE__*/React.createElement("option", null, "notification"), /*#__PURE__*/React.createElement("option", null, "alert"), /*#__PURE__*/React.createElement("option", null, "billing"), /*#__PURE__*/React.createElement("option", null, "newsletter")), /*#__PURE__*/React.createElement("select", {
    "aria-label": "Area",
    style: sels,
    defaultValue: ""
  }, /*#__PURE__*/React.createElement("option", {
    value: ""
  }, "All areas"), Object.values(AREAS).map(a => /*#__PURE__*/React.createElement("option", {
    key: a.name
  }, a.name))), /*#__PURE__*/React.createElement("select", {
    "aria-label": "Priority",
    style: sels,
    defaultValue: ""
  }, /*#__PURE__*/React.createElement("option", {
    value: ""
  }, "Any priority"), /*#__PURE__*/React.createElement("option", null, "P1 Urgent"), /*#__PURE__*/React.createElement("option", null, "P2 Important"), /*#__PURE__*/React.createElement("option", null, "P3 Normal"), /*#__PURE__*/React.createElement("option", null, "P4 Low or noise")), /*#__PURE__*/React.createElement("select", {
    "aria-label": "Reply",
    style: sels,
    defaultValue: ""
  }, /*#__PURE__*/React.createElement("option", {
    value: ""
  }, "Reply: any"), /*#__PURE__*/React.createElement("option", null, "Needs reply"), /*#__PURE__*/React.createElement("option", null, "No reply needed")), /*#__PURE__*/React.createElement("select", {
    "aria-label": "Handled",
    style: sels,
    value: handledFilter,
    onChange: e => setHandledFilter(e.target.value)
  }, /*#__PURE__*/React.createElement("option", {
    value: "0"
  }, "Unhandled"), /*#__PURE__*/React.createElement("option", {
    value: "1"
  }, "Handled"), /*#__PURE__*/React.createElement("option", {
    value: "all"
  }, "All")), /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "link-btn",
    onClick: () => setHandledFilter('0')
  }, "Reset")), notice && /*#__PURE__*/React.createElement("p", {
    style: {
      marginTop: 'var(--sp-3)',
      fontSize: 'var(--fs-sm)',
      color: 'var(--ink-3)'
    }
  }, notice), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: sel ? 'minmax(0,1fr) minmax(340px, 44%)' : 'minmax(0,1fr)',
      gap: 'var(--sp-5)',
      marginTop: 'var(--sp-4)',
      alignItems: 'start'
    }
  }, /*#__PURE__*/React.createElement("ul", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--sp-2)',
      minWidth: 0
    }
  }, shown.length ? shown.map(e => /*#__PURE__*/React.createElement(EmailRow, {
    key: e.id,
    email: row(e),
    active: e.id === selId,
    onOpen: () => setSelId(e.id),
    onHandled: setHandled
  })) : /*#__PURE__*/React.createElement("li", null, /*#__PURE__*/React.createElement(Empty, {
    icon: "tray",
    title: "No emails match",
    hint: "Change the filters or sync."
  }))), sel && /*#__PURE__*/React.createElement(Card, {
    style: {
      position: 'sticky',
      top: 'calc(var(--bar-h) + var(--sp-4))'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'flex-start',
      justifyContent: 'space-between',
      gap: 'var(--sp-3)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("h2", {
    style: {
      fontSize: 'var(--fs-lg)',
      margin: 0
    }
  }, sel.subject), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      marginTop: 6,
      flexWrap: 'wrap'
    }
  }, /*#__PURE__*/React.createElement(PriorityBadge, {
    priority: sel.priority
  }), /*#__PURE__*/React.createElement(Tag, null, sel.category), sel.needsReply && /*#__PURE__*/React.createElement(Badge, {
    tone: "info"
  }, "reply"), /*#__PURE__*/React.createElement(Badge, {
    color: ACCOUNTS[sel.account].color,
    dot: true
  }, ACCOUNTS[sel.account].label), /*#__PURE__*/React.createElement(AreaDot, {
    color: AREAS[sel.area].color,
    name: AREAS[sel.area].name,
    label: true
  }))), /*#__PURE__*/React.createElement("button", {
    className: "link-btn",
    onClick: () => setSelId(null)
  }, "Close")), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 'var(--sp-3)',
      fontSize: 'var(--fs-sm)',
      color: 'var(--ink-3)'
    }
  }, sel.from, " ", /*#__PURE__*/React.createElement("span", {
    style: {
      fontVariantNumeric: 'tabular-nums'
    }
  }, sel.date)), /*#__PURE__*/React.createElement(Inset, {
    style: {
      marginTop: 'var(--sp-3)',
      fontSize: 'var(--fs-md)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 'var(--fs-xs)',
      letterSpacing: '0.02em',
      color: 'var(--ink-3)',
      fontWeight: 500
    }
  }, "SUMMARY"), /*#__PURE__*/React.createElement("p", {
    style: {
      marginTop: 4
    }
  }, sel.summary)), /*#__PURE__*/React.createElement("p", {
    style: {
      marginTop: 'var(--sp-4)',
      fontSize: 'var(--fs-md)',
      lineHeight: 1.6,
      maxWidth: '68ch'
    }
  }, sel.body), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 'var(--sp-2)',
      alignItems: 'center',
      marginTop: 'var(--sp-4)',
      flexWrap: 'wrap'
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    onClick: () => {
      setHandled(sel);
      toast('Marked handled.');
    }
  }, sel.handled ? 'Unhandle' : 'Mark handled'), /*#__PURE__*/React.createElement(Button, {
    onClick: () => toast('Task "' + sel.subject.slice(0, 32) + '" created.')
  }, "Create task"), /*#__PURE__*/React.createElement(Button, {
    variant: "ghost",
    onClick: () => toast('Reclassified by haiku: P' + sel.priority + '.')
  }, "Reclassify"), /*#__PURE__*/React.createElement("a", {
    href: "#",
    className: "link-btn",
    style: {
      marginLeft: 'auto'
    },
    onClick: e => e.preventDefault()
  }, "Open in Gmail")))));
}
window.MailScreen = MailScreen;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/pozzy/MailScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/pozzy/TasksScreen.jsx
try { (() => {
const DS = window.PozzyDesignSystem_379c1d;
const {
  Button,
  IconButton,
  Badge,
  PriorityBadge,
  Tag,
  AreaDot,
  Card,
  Inset,
  PageHeader,
  Field,
  Segmented,
  ProgressBar,
  WeekNav,
  Empty,
  Skeleton,
  Toast,
  Sheet,
  ListRow,
  TaskCard,
  Quadrant,
  QUADRANTS,
  EmailRow,
  TrackerChip,
  Icon
} = DS;
function TasksScreen({
  toast
}) {
  const [items, setItems] = React.useState(TASKS);
  const [mode, setMode] = React.useState('board');
  const [selId, setSelId] = React.useState(null);
  const [creating, setCreating] = React.useState(false);
  const [quick, setQuick] = React.useState('');
  const [over, setOver] = React.useState(null);
  const [dragId, setDragId] = React.useState(null);
  const open = items.filter(t => t.status !== 'done');
  const sel = items.find(t => t.id === selId);
  const panel = creating || sel;
  const card = t => ({
    ...t,
    areaColor: AREAS[t.area].color,
    areaName: AREAS[t.area].name
  });
  const complete = t => {
    setItems(items.filter(x => x.id !== t.id));
    if (selId === t.id) setSelId(null);
    toast('Task completed.');
  };
  const drop = q => {
    if (dragId) setItems(items.map(t => t.id === dragId ? {
      ...t,
      quadrant: q
    } : t));
    setOver(null);
    setDragId(null);
  };
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(PageHeader, {
    title: "Tasks",
    meta: open.length + ' open'
  }, /*#__PURE__*/React.createElement("form", {
    onSubmit: e => {
      e.preventDefault();
      if (!quick.trim()) return;
      const t = {
        id: 't' + Date.now(),
        title: quick.trim(),
        quadrant: 'do',
        area: 'work',
        status: 'inbox'
      };
      setItems([t, ...items]);
      setQuick('');
      setSelId(t.id);
      setCreating(false);
    },
    style: {
      display: 'flex',
      gap: 'var(--sp-2)',
      flex: '0 1 240px',
      minWidth: 180
    }
  }, /*#__PURE__*/React.createElement("input", {
    type: "text",
    value: quick,
    onChange: e => setQuick(e.target.value),
    placeholder: "Quick add to inbox",
    "aria-label": "Quick add to inbox",
    style: {
      flex: 1
    }
  }), /*#__PURE__*/React.createElement(Button, {
    type: "submit",
    disabled: !quick.trim()
  }, "Add")), /*#__PURE__*/React.createElement(Segmented, {
    value: mode,
    options: [{
      value: 'board',
      label: 'Board'
    }, {
      value: 'list',
      label: 'List'
    }],
    onChange: setMode
  }), /*#__PURE__*/React.createElement("select", {
    "aria-label": "Area",
    defaultValue: ""
  }, /*#__PURE__*/React.createElement("option", {
    value: ""
  }, "All areas"), Object.values(AREAS).map(a => /*#__PURE__*/React.createElement("option", {
    key: a.name
  }, a.name))), /*#__PURE__*/React.createElement("input", {
    type: "search",
    placeholder: "Search",
    "aria-label": "Search tasks",
    style: {
      width: 130
    }
  }), /*#__PURE__*/React.createElement("label", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      fontSize: 'var(--fs-md)',
      whiteSpace: 'nowrap'
    }
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox"
  }), " Show done"), /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    onClick: () => {
      setCreating(true);
      setSelId(null);
    }
  }, "New task")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: panel ? 'minmax(0,1fr) 360px' : 'minmax(0,1fr)',
      gap: 'var(--sp-5)',
      alignItems: 'start'
    }
  }, mode === 'board' ? /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr)',
      gap: 'var(--sp-3)'
    }
  }, QUADRANTS.map(q => {
    const list = open.filter(t => t.quadrant === q.key);
    return /*#__PURE__*/React.createElement("div", {
      key: q.key,
      onDragOver: e => {
        e.preventDefault();
        setOver(q.key);
      },
      onDragLeave: () => setOver(null),
      onDrop: e => {
        e.preventDefault();
        drop(q.key);
      }
    }, /*#__PURE__*/React.createElement(Quadrant, {
      quadrant: q,
      over: over === q.key,
      empty: !list.length
    }, list.map(t => /*#__PURE__*/React.createElement("div", {
      key: t.id,
      draggable: true,
      onDragStart: () => setDragId(t.id)
    }, /*#__PURE__*/React.createElement(TaskCard, {
      task: card(t),
      selected: t.id === selId,
      onSelect: () => {
        setSelId(t.id);
        setCreating(false);
      },
      onComplete: complete
    })))));
  })) : /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--sp-2)'
    }
  }, open.length ? open.map(t => /*#__PURE__*/React.createElement(TaskCard, {
    key: t.id,
    task: card(t),
    selected: t.id === selId,
    onSelect: () => {
      setSelId(t.id);
      setCreating(false);
    },
    onComplete: complete
  })) : /*#__PURE__*/React.createElement(Empty, {
    icon: "check-square",
    title: "No tasks",
    hint: "Quick add one above, or capture it from the top bar."
  })), panel && /*#__PURE__*/React.createElement(Card, {
    title: creating ? 'New task' : 'Edit task',
    meta: /*#__PURE__*/React.createElement("button", {
      className: "link-btn",
      onClick: () => {
        setCreating(false);
        setSelId(null);
      }
    }, "Close"),
    style: {
      position: 'sticky',
      top: 'calc(var(--bar-h) + var(--sp-4))'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--sp-3)'
    },
    key: selId || 'new'
  }, /*#__PURE__*/React.createElement(Field, {
    label: "Title"
  }, /*#__PURE__*/React.createElement("input", {
    type: "text",
    defaultValue: sel ? sel.title : ''
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 'var(--sp-2)'
    }
  }, /*#__PURE__*/React.createElement(Field, {
    label: "Area"
  }, /*#__PURE__*/React.createElement("select", {
    defaultValue: sel ? sel.area : 'work'
  }, Object.entries(AREAS).map(([k, a]) => /*#__PURE__*/React.createElement("option", {
    key: k,
    value: k
  }, a.name)))), /*#__PURE__*/React.createElement(Field, {
    label: "Quadrant"
  }, /*#__PURE__*/React.createElement("select", {
    defaultValue: sel ? sel.quadrant : 'do'
  }, QUADRANTS.map(q => /*#__PURE__*/React.createElement("option", {
    key: q.key,
    value: q.key
  }, q.label))))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 'var(--sp-2)'
    }
  }, /*#__PURE__*/React.createElement(Field, {
    label: "Due date"
  }, /*#__PURE__*/React.createElement("input", {
    type: "date",
    defaultValue: "2026-09-19"
  })), /*#__PURE__*/React.createElement(Field, {
    label: "Estimated minutes"
  }, /*#__PURE__*/React.createElement("input", {
    type: "number",
    defaultValue: sel ? sel.minutes || '' : ''
  }))), /*#__PURE__*/React.createElement(Field, {
    label: "Tags",
    hint: "Comma separated"
  }, /*#__PURE__*/React.createElement("input", {
    type: "text",
    defaultValue: sel && sel.tags ? sel.tags.join(', ') : ''
  })), /*#__PURE__*/React.createElement(Field, {
    label: "Notes"
  }, /*#__PURE__*/React.createElement("textarea", {
    rows: 3
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 'var(--sp-2)',
      alignItems: 'center'
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    onClick: () => {
      toast(creating ? 'Task created.' : 'Task saved.');
      setCreating(false);
    }
  }, "Save"), /*#__PURE__*/React.createElement(Button, {
    variant: "ghost",
    onClick: () => {
      setCreating(false);
      setSelId(null);
    }
  }, "Cancel"), /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1
    }
  }), sel && /*#__PURE__*/React.createElement(Button, {
    variant: "danger",
    onClick: () => {
      setItems(items.filter(x => x.id !== sel.id));
      setSelId(null);
      toast('Task deleted.');
    }
  }, "Delete")), sel && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 'var(--sp-2)',
      alignItems: 'center',
      marginTop: 'var(--sp-1)'
    }
  }, /*#__PURE__*/React.createElement(Button, {
    onClick: () => toast('Slots computed; Claude ranked 3 candidates.')
  }, "Suggest a slot"), sel.status === 'inbox' && /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ink-3)',
      fontSize: 'var(--fs-sm)'
    }
  }, "source: capture"))))));
}
window.TasksScreen = TasksScreen;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/pozzy/TasksScreen.jsx", error: String((e && e.message) || e) }); }

__ds_ns.AreaDot = __ds_scope.AreaDot;

__ds_ns.Badge = __ds_scope.Badge;

__ds_ns.PriorityBadge = __ds_scope.PriorityBadge;

__ds_ns.Tag = __ds_scope.Tag;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.Card = __ds_scope.Card;

__ds_ns.Inset = __ds_scope.Inset;

__ds_ns.Field = __ds_scope.Field;

__ds_ns.Icon = __ds_scope.Icon;

__ds_ns.IconButton = __ds_scope.IconButton;

__ds_ns.PageHeader = __ds_scope.PageHeader;

__ds_ns.ProgressBar = __ds_scope.ProgressBar;

__ds_ns.Segmented = __ds_scope.Segmented;

__ds_ns.WeekNav = __ds_scope.WeekNav;

__ds_ns.Empty = __ds_scope.Empty;

__ds_ns.Sheet = __ds_scope.Sheet;

__ds_ns.Skeleton = __ds_scope.Skeleton;

__ds_ns.Toast = __ds_scope.Toast;

__ds_ns.EmailRow = __ds_scope.EmailRow;

__ds_ns.ListRow = __ds_scope.ListRow;

__ds_ns.TaskCard = __ds_scope.TaskCard;

__ds_ns.QUADRANTS = __ds_scope.QUADRANTS;

__ds_ns.Quadrant = __ds_scope.Quadrant;

__ds_ns.TrackerChip = __ds_scope.TrackerChip;

__ds_ns.CaptureBar = __ds_scope.CaptureBar;

__ds_ns.NAV = __ds_scope.NAV;

__ds_ns.NavItem = __ds_scope.NavItem;

__ds_ns.NavRail = __ds_scope.NavRail;

__ds_ns.TopBar = __ds_scope.TopBar;

})();

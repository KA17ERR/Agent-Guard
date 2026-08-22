function toneFor(percent) {
  if (percent >= 80) return "bg-signal-safe";
  if (percent >= 50) return "bg-signal-warn";
  return "bg-signal-danger";
}

export default function ProgressBar({ value, max = 100, label, showValue = true, className = "" }) {
  const percent = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div className={className}>
      {(label || showValue) && (
        <div className="mb-1 flex items-center justify-between text-xs text-ink-soft">
          <span>{label}</span>
          {showValue && <span className="mono font-medium text-ink">{Math.round(value)}</span>}
        </div>
      )}
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-line">
        <div
          className={`h-full rounded-full transition-all ${toneFor(percent)}`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}

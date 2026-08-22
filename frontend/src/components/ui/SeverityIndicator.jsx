const DOT_COLORS = {
  low: "bg-signal-safe",
  medium: "bg-signal-warn",
  high: "bg-signal-danger",
  critical: "bg-signal-danger",
};

// A compact severity marker: a filled dot plus a short label. `critical`
// gets a pulsing ring so it reads distinctly from `high` at a glance —
// this is the same tick-mark language used along the TraceTimeline rail.
export default function SeverityIndicator({ level, label }) {
  const dot = DOT_COLORS[level] || "bg-signal-neutral";
  return (
    <span className="inline-flex items-center gap-2 text-sm text-ink-soft">
      <span className="relative inline-flex h-2.5 w-2.5">
        {level === "critical" && (
          <span className={`absolute inline-flex h-full w-full animate-ping rounded-full ${dot} opacity-60`} />
        )}
        <span className={`relative inline-flex h-2.5 w-2.5 rounded-full ${dot}`} />
      </span>
      {label}
    </span>
  );
}

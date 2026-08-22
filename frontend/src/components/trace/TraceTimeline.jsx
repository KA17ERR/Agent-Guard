import Icon from "../ui/Icon";
import StatusBadge from "../ui/StatusBadge";

const NODE_TONE = {
  safe: "border-signal-safe bg-signal-safe-soft text-signal-safe",
  warn: "border-signal-warn bg-signal-warn-soft text-signal-warn",
  danger: "border-signal-danger bg-signal-danger-soft text-signal-danger",
  neutral: "border-line bg-canvas text-ink-faint",
  accent: "border-accent bg-accent-soft text-accent",
};

const BADGE_TONE = { safe: "safe", warn: "warn", danger: "danger", neutral: "neutral", accent: "accent" };

/**
 * Renders a vertical execution trace: a rail with one node per step.
 *
 * Steps: [{
 *   id, title, detail, timestamp, tone, icon,
 *   badges?: [{ label, tone }],            // e.g. risk level, destructive flag, match/mismatch
 *   meta?: [{ label, value }],             // e.g. tool params, confidence, recommendation
 * }]
 *
 * `tone` is one of "safe" | "warn" | "danger" | "neutral" | "accent" and
 * drives the node color -- the same severity language used by
 * SeverityIndicator and Card's `rail` prop. Intentionally has no built-in
 * mock data: every step is built from real trace/replay data by the
 * calling page (see pages/failures/buildTimelineSteps.js).
 */
export default function TraceTimeline({ steps }) {
  if (!steps || steps.length === 0) {
    return <p className="text-sm text-ink-faint">No trace steps to display.</p>;
  }

  return (
    <ol className="relative border-l border-line pl-6">
      {steps.map((step, idx) => (
        <li key={step.id ?? idx} className="mb-6 last:mb-0">
          <span
            className={`absolute -left-[13px] flex h-6 w-6 items-center justify-center rounded-full border-2 ${
              NODE_TONE[step.tone] || NODE_TONE.neutral
            }`}
          >
            <Icon name={step.icon || "chevronRight"} className="h-3 w-3" />
          </span>

          <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
            <p className="text-sm font-medium text-ink">{step.title}</p>
            {step.timestamp && <span className="mono shrink-0 text-xs text-ink-faint">{step.timestamp}</span>}
          </div>

          {step.badges && step.badges.length > 0 && (
            <div className="mt-1 flex flex-wrap gap-1.5">
              {step.badges.map((b, i) => (
                <StatusBadge key={i} label={b.label} tone={BADGE_TONE[b.tone] || "neutral"} />
              ))}
            </div>
          )}

          {step.detail && <p className="mt-1 text-sm text-ink-soft">{step.detail}</p>}

          {step.meta && step.meta.length > 0 && (
            <dl className="mt-2 space-y-1 rounded-md border border-line bg-canvas p-2.5">
              {step.meta.map((m, i) => (
                <div key={i} className="flex gap-2 text-xs">
                  <dt className="shrink-0 font-medium text-ink-faint">{m.label}</dt>
                  <dd className="mono min-w-0 break-words text-ink-soft">{m.value}</dd>
                </div>
              ))}
            </dl>
          )}
        </li>
      ))}
    </ol>
  );
}

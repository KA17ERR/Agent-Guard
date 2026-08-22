// Base card. `rail` optionally draws the 3px severity-rail on the left
// edge — the same visual language used in StatusBadge and TraceTimeline —
// so a card can double as e.g. a "this tool is destructive" indicator.
const RAIL_COLORS = {
  safe: "before:bg-signal-safe",
  warn: "before:bg-signal-warn",
  danger: "before:bg-signal-danger",
  neutral: "before:bg-signal-neutral",
  accent: "before:bg-accent",
};

export default function Card({ children, className = "", rail, padded = true, ...props }) {
  const railClass = rail
    ? `relative pl-[calc(1rem+3px)] before:absolute before:left-0 before:top-0 before:bottom-0 before:w-[3px] before:rounded-l-lg ${RAIL_COLORS[rail]}`
    : "";
  return (
    <div
      className={`rounded-lg border border-line bg-surface shadow-card ${
        padded ? (rail ? "py-4 pr-4" : "p-4") : ""
      } ${railClass} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ title, subtitle, action }) {
  return (
    <div className="mb-3 flex items-start justify-between gap-3">
      <div>
        <h3 className="text-sm font-semibold text-ink">{title}</h3>
        {subtitle && <p className="mt-0.5 text-xs text-ink-faint">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

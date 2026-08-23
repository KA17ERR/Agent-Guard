import BlurText from "./BlurText";

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
      className={`rounded-lg border border-line/70 bg-surface-soft shadow-card ${
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
        {typeof title === "string" ? (
          <BlurText
            text={title}
            animateBy="words"
            direction="top"
            delay={40}
            stepDuration={0.3}
            className="text-sm font-semibold !leading-none text-ink"
          />
        ) : (
          <h3 className="text-sm font-semibold text-ink">{title}</h3>
        )}
        {subtitle && typeof subtitle === "string" ? (
          <BlurText
            text={subtitle}
            animateBy="words"
            direction="top"
            delay={20}
            stepDuration={0.3}
            className="mt-0.5 text-xs !leading-normal text-ink-faint"
          />
        ) : (
          subtitle && <p className="mt-0.5 text-xs text-ink-faint">{subtitle}</p>
        )}
      </div>
      {action}
    </div>
  );
}

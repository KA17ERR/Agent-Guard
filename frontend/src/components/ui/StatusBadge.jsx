import { humanize } from "../../utils/format";

// Shared tone system: every status/risk/severity concept in AgentGuard
// reduces to one of these four tones, so a single visual language covers
// tool risk levels, test statuses, and failure severities.
const TONES = {
  safe: "bg-signal-safe-soft text-signal-safe",
  warn: "bg-signal-warn-soft text-signal-warn",
  danger: "bg-signal-danger-soft text-signal-danger",
  neutral: "bg-signal-neutral-soft text-signal-neutral",
  accent: "bg-accent-soft text-accent",
};

const RISK_TONE = { low: "safe", medium: "warn", high: "danger", critical: "danger" };

export default function StatusBadge({ label, tone = "neutral", dot = true, className = "" }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ${TONES[tone]} ${className}`}
    >
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
      {label}
    </span>
  );
}

export function RiskBadge({ level, className = "" }) {
  const tone = RISK_TONE[level] || "neutral";
  return <StatusBadge label={humanize(level)} tone={tone} className={className} />;
}

export function DestructiveBadge({ destructive }) {
  if (!destructive) {
    return <StatusBadge label="Non-destructive" tone="safe" className="opacity-70" />;
  }
  return <StatusBadge label="Destructive" tone="danger" />;
}

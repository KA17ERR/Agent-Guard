import Card from "../../components/ui/Card";
import StatusBadge from "../../components/ui/StatusBadge";
import { humanize } from "../../utils/format";

const SEVERITY_TONE = { critical: "danger", high: "danger", medium: "warn", low: "neutral" };

export default function TopRisks({ risks }) {
  if (!risks || risks.length === 0) {
    return (
      <p className="text-sm text-ink-faint">No failures were recorded in this run — nothing to rank.</p>
    );
  }

  return (
    <div className="space-y-3">
      {risks.map((risk, i) => (
        <Card key={risk.category} rail={SEVERITY_TONE[risk.worst.severity] === "danger" ? "danger" : "warn"}>
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div className="flex items-center gap-2.5">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-canvas text-xs font-semibold text-ink-soft">
                {i + 1}
              </span>
              <p className="text-sm font-semibold text-ink">{humanize(risk.category)}</p>
            </div>
            <div className="flex items-center gap-2">
              <StatusBadge label={`${humanize(risk.worst.severity)} severity`} tone={SEVERITY_TONE[risk.worst.severity]} />
              <StatusBadge
                label={`${risk.count} occurrence${risk.count === 1 ? "" : "s"}`}
                tone="neutral"
              />
            </div>
          </div>
          <p className="mt-2 text-sm text-ink-soft">{risk.worst.explanation}</p>
          <p className="mt-1.5 text-sm text-ink-faint">
            <span className="font-medium text-ink-soft">Recommendation: </span>
            {risk.worst.recommendation}
          </p>
        </Card>
      ))}
    </div>
  );
}

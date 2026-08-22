import Card from "../../components/ui/Card";
import StatusBadge, { RiskBadge } from "../../components/ui/StatusBadge";
import { humanize } from "../../utils/format";

const CATEGORY_TONE = {
  normal_task: "neutral",
  ambiguous_instruction: "neutral",
};

export default function ScenarioCard({ scenario }) {
  const tone = CATEGORY_TONE[scenario.category] || "danger";
  const attackStrategy = scenario.metadata?.attack_strategy || "";

  return (
    <Card rail={scenario.severity === "critical" || scenario.severity === "high" ? "danger" : "neutral"}>
      <div className="flex flex-wrap items-center gap-2">
        <StatusBadge label={humanize(scenario.category)} tone={tone} />
        <RiskBadge level={scenario.severity} />
      </div>

      <dl className="mt-3 space-y-2.5 text-sm">
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-ink-faint">User input</dt>
          <dd className="mt-0.5 text-ink-soft">{scenario.user_input}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-ink-faint">Expected behavior</dt>
          <dd className="mt-0.5 text-ink-soft">{scenario.expected_behavior}</dd>
        </div>
        {attackStrategy && (
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-ink-faint">Attack strategy</dt>
            <dd className="mono mt-0.5 text-ink-soft">{attackStrategy}</dd>
          </div>
        )}
      </dl>
    </Card>
  );
}

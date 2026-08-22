import StatusBadge from "../../components/ui/StatusBadge";
import Table from "../../components/ui/Table";
import { humanize } from "../../utils/format";

// `getScenario` looks up a scenario's real category/user_input from
// RunContext (populated whenever scenarios were generated in this
// session) — purely a display nicety. When it isn't available (e.g. the
// scenario was generated in a different session), we still show the
// scenario id, we just skip the extra context line rather than guessing.
function ScenarioTag({ scenarioId, getScenario, tone }) {
  const scenario = getScenario ? getScenario(scenarioId) : null;
  return (
    <div className="rounded-md border border-line bg-canvas px-3 py-2">
      <div className="flex items-center justify-between gap-2">
        <span className="mono text-xs text-ink-soft">{scenarioId}</span>
        {scenario && <StatusBadge label={humanize(scenario.category)} tone={tone} className="opacity-80" />}
      </div>
      {scenario?.user_input && (
        <p className="mt-1 line-clamp-2 text-xs text-ink-faint">{scenario.user_input}</p>
      )}
    </div>
  );
}

function ScenarioList({ title, scenarioIds, tone, emptyLabel, getScenario }) {
  return (
    <div>
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-faint">{title}</h4>
      {scenarioIds.length === 0 ? (
        <p className="text-sm text-ink-faint">{emptyLabel}</p>
      ) : (
        <div className="space-y-2">
          {scenarioIds.map((id) => (
            <ScenarioTag key={id} scenarioId={id} tone={tone} getScenario={getScenario} />
          ))}
        </div>
      )}
    </div>
  );
}

const SEVERITY_TONE = { critical: "danger", high: "danger", medium: "warn", low: "safe", none: "neutral" };

export default function ScenarioDiffLists({ newlyFailing, newlyPassing, scenarioRegressions, getScenario }) {
  const regressionColumns = [
    { key: "scenario_id", header: "Scenario" },
    {
      key: "status",
      header: "Status change",
      render: (row) => (
        <span className="mono text-xs text-ink-soft">
          {row.previous_status} → {row.new_status}
        </span>
      ),
    },
    {
      key: "severity",
      header: "Worst severity",
      render: (row) => (
        <div className="flex items-center gap-1.5">
          <StatusBadge label={humanize(row.previous_worst_severity)} tone={SEVERITY_TONE[row.previous_worst_severity] || "neutral"} className="opacity-70" />
          <span className="text-ink-faint">→</span>
          <StatusBadge label={humanize(row.new_worst_severity)} tone={SEVERITY_TONE[row.new_worst_severity] || "neutral"} />
        </div>
      ),
    },
    { key: "reason", header: "Reason", render: (row) => <span className="text-ink-soft">{row.reason}</span> },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <ScenarioList
          title="🔴 Newly failing scenarios"
          scenarioIds={newlyFailing}
          tone="danger"
          emptyLabel="None — nothing that used to pass now fails."
          getScenario={getScenario}
        />
        <ScenarioList
          title="🟢 Newly passing scenarios"
          scenarioIds={newlyPassing}
          tone="safe"
          emptyLabel="No previously-failing scenarios started passing."
          getScenario={getScenario}
        />
      </div>

      <div>
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-faint">
          Scenarios with a more severe failure
        </h4>
        <Table
          columns={regressionColumns}
          rows={scenarioRegressions}
          rowKey="scenario_id"
          emptyMessage="No scenario got a more severe failure between the two runs."
        />
      </div>
    </div>
  );
}

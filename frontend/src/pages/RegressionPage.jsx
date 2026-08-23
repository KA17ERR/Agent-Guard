import { useEffect, useId, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useRunContext } from "../context/RunContext";
import regressionApi from "../api/regression";
import Card, { CardHeader } from "../components/ui/Card";
import Button from "../components/ui/Button";
import Spinner from "../components/ui/Spinner";
import ErrorBanner from "../components/ui/ErrorBanner";
import EmptyState from "../components/ui/EmptyState";
import StatusBadge from "../components/ui/StatusBadge";
import Icon from "../components/ui/Icon";
import { formatDateTime } from "../utils/format";
import CategoryChangeTable from "./regression/CategoryChangeTable";
import ScenarioDiffLists from "./regression/ScenarioDiffLists";

const DIMENSION_LABELS = [
  { key: "task_success", label: "Task success" },
  { key: "safety", label: "Safety" },
  { key: "tool_reliability", label: "Tool reliability" },
  { key: "goal_adherence", label: "Goal adherence" },
  { key: "truthfulness", label: "Truthfulness" },
];

function RunSelect({ label, runs, value, onChange }) {
  const selectId = useId();
  return (
    <div>
      <label htmlFor={selectId} className="mb-1 block text-xs font-medium text-ink-faint">
        {label}
      </label>
      <select
        id={selectId}
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-md border border-line bg-surface px-3 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
      >
        <option value="" disabled>
          Select a test run…
        </option>
        {runs.map((r) => (
          <option key={r.run_id} value={r.run_id}>
            {r.version} · {Math.round(r.reliability_score)}/100 · {r.run_id.slice(0, 8)}
          </option>
        ))}
      </select>
    </div>
  );
}

export default function RegressionPage() {
  const { agent, runHistory, getScenario } = useRunContext();

  const [runIdA, setRunIdA] = useState("");
  const [runIdB, setRunIdB] = useState("");
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Default to the two oldest runs in this session's history (chronological
  // "before" vs "after") the first time there are at least two to compare.
  useEffect(() => {
    if (runHistory.length >= 2 && !runIdA && !runIdB) {
      setRunIdA(runHistory[0].run_id);
      setRunIdB(runHistory[runHistory.length - 1].run_id);
    }
  }, [runHistory, runIdA, runIdB]);

  const canCompare = Boolean(agent?.id && runIdA && runIdB && runIdA !== runIdB);

  const handleCompare = () => {
    if (!canCompare) return;
    setLoading(true);
    setError("");
    setReport(null);
    regressionApi
      .compare(agent.id, { runIdA, runIdB })
      .then(setReport)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  const dimensionChanges = useMemo(() => {
    if (!report) return [];
    return DIMENSION_LABELS.map((d) => ({ key: d.key, label: d.label, change: report[d.key] }));
  }, [report]);

  if (!agent?.id) {
    return (
      <EmptyState
        icon="trend"
        title="No agent selected yet"
        description="Configure an agent and run at least two test suites first — regression comparison is built from those runs' real results."
        action={
          <Button as={Link} to="/agents">
            Go to Agent Configuration
          </Button>
        }
      />
    );
  }

  if (runHistory.length < 2) {
    return (
      <EmptyState
        icon="trend"
        title="Need at least two test runs to compare"
        description={`This session has recorded ${runHistory.length} test run${
          runHistory.length === 1 ? "" : "s"
        } so far. Run the test suite again — ideally after changing the agent's version — then come back here.`}
        action={
          <Button as={Link} to="/execution">
            Go to Test Execution
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader
          title="Compare two test runs"
          subtitle={`${agent.name} — choose two completed runs from this session to diff.`}
        />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <RunSelect label="Version 1 (baseline)" runs={runHistory} value={runIdA} onChange={setRunIdA} />
          <RunSelect label="Version 2 (candidate)" runs={runHistory} value={runIdB} onChange={setRunIdB} />
        </div>
        {runIdA && runIdB && runIdA === runIdB && (
          <p className="mt-2 text-xs text-signal-warn">Pick two different runs to compare.</p>
        )}
        <div className="mt-4">
          <Button onClick={handleCompare} disabled={!canCompare} loading={loading}>
            Compare runs
          </Button>
        </div>
      </Card>

      {error && <ErrorBanner message={error} />}
      {loading && <Spinner label="Comparing runs…" />}

      {report && (
        <>
          <Card
            rail={report.is_regression ? "danger" : "safe"}
            className={report.is_regression ? "bg-signal-danger-soft/40" : "bg-signal-safe-soft/40"}
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <Icon
                  name={report.is_regression ? "alert" : "shield"}
                  className={`h-5 w-5 ${report.is_regression ? "text-signal-danger" : "text-signal-safe"}`}
                />
                <div>
                  <p className={`text-sm font-semibold ${report.is_regression ? "text-signal-danger" : "text-signal-safe"}`}>
                    {report.is_regression ? "Regression detected" : "No regression detected"}
                  </p>
                  {report.regression_reasons.length > 0 && (
                    <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs text-ink-soft">
                      {report.regression_reasons.map((reason, i) => (
                        <li key={i}>{reason}</li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
              <StatusBadge
                label={`${report.run_a.version} → ${report.run_b.version}`}
                tone={report.is_regression ? "danger" : "safe"}
              />
            </div>
          </Card>

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <Card>
              <CardHeader title="Version 1" subtitle={report.run_a.version} />
              <p className="text-3xl font-bold text-ink">{Math.round(report.run_a.reliability_score)}</p>
              <p className="text-xs text-ink-faint">
                {report.run_a.passed_tests}/{report.run_a.total_tests} passed · run {report.run_a.run_id.slice(0, 8)} ·{" "}
                {formatDateTime(report.run_a.completed_at)}
              </p>
            </Card>
            <Card>
              <CardHeader title="Version 2" subtitle={report.run_b.version} />
              <p className="text-3xl font-bold text-ink">{Math.round(report.run_b.reliability_score)}</p>
              <p className="text-xs text-ink-faint">
                {report.run_b.passed_tests}/{report.run_b.total_tests} passed · run {report.run_b.run_id.slice(0, 8)} ·{" "}
                {formatDateTime(report.run_b.completed_at)}
              </p>
            </Card>
          </div>

          <Card>
            <CardHeader title="Category changes" subtitle="🟢 Improvement · 🔴 Regression · 🟡 Unchanged" />
            <CategoryChangeTable overall={report.overall} dimensions={dimensionChanges} />
          </Card>

          <Card>
            <CardHeader
              title="Scenario-level differences"
              subtitle="Scenarios matched by id across both runs — the same scenario set re-run against each version."
            />
            <ScenarioDiffLists
              newlyFailing={report.newly_failing_scenarios}
              newlyPassing={report.newly_passing_scenarios}
              scenarioRegressions={report.scenario_regressions}
              getScenario={getScenario}
            />
          </Card>
        </>
      )}
    </div>
  );
}

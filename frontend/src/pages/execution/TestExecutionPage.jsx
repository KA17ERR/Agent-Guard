import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useRunContext } from "../../context/RunContext";
import testRunsApi from "../../api/testRuns";
import Card, { CardHeader } from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import ErrorBanner from "../../components/ui/ErrorBanner";
import EmptyState from "../../components/ui/EmptyState";
import Icon from "../../components/ui/Icon";
import { RiskBadge } from "../../components/ui/StatusBadge";
import { CategoryBars } from "../../components/charts/ScoreTrendChart";
import { humanize } from "../../utils/format";
import TestResultRow from "./TestResultRow";

function ScoreStat({ label, value, tone = "neutral" }) {
  const toneClass = {
    neutral: "text-ink",
    safe: "text-signal-safe",
    warn: "text-signal-warn",
    danger: "text-signal-danger",
  }[tone];
  return (
    <div className="rounded-md border border-line bg-canvas px-3 py-2.5 text-center">
      <p className={`text-xl font-semibold ${toneClass}`}>{value}</p>
      <p className="mt-0.5 text-xs text-ink-faint">{label}</p>
    </div>
  );
}

export default function TestExecutionPage() {
  const { agent, scenarioList, recordRun } = useRunContext();

  const [selectedIds, setSelectedIds] = useState(() => new Set(scenarioList.map((s) => s.id)));
  const [running, setRunning] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [runError, setRunError] = useState("");
  const [runResult, setRunResult] = useState(null); // TestRunCreateResponse
  const [runId, setRunId] = useState(null);
  const [traces, setTraces] = useState(null);
  const [tracesError, setTracesError] = useState("");

  // Real elapsed-time counter. POST /api/test-runs blocks until every
  // scenario has been executed server-side — there is no per-scenario
  // progress event to poll, so this ticking timer (not a fabricated
  // percentage or fake "current scenario") is the only honest signal
  // available while the request is in flight.
  useEffect(() => {
    if (!running) return;
    setElapsedSeconds(0);
    const interval = setInterval(() => setElapsedSeconds((s) => s + 1), 1000);
    return () => clearInterval(interval);
  }, [running]);

  const toggle = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const runSuite = async () => {
    setRunError("");
    setRunResult(null);
    setTraces(null);
    setRunning(true);
    try {
      const response = await testRunsApi.create({
        agentId: agent.id,
        scenarioIds: Array.from(selectedIds),
      });
      setRunResult(response);
      setRunId(response.run_id);
      recordRun(response.run_id, response, agent.version);

      try {
        const traceData = await testRunsApi.traces(response.run_id);
        setTraces(traceData.traces);
      } catch (err) {
        setTracesError(err.message);
      }
    } catch (err) {
      setRunError(err.message);
    } finally {
      setRunning(false);
    }
  };

  if (!agent || scenarioList.length === 0) {
    return (
      <EmptyState
        icon="play"
        title="No test suite ready to run"
        description="Generate scenarios for an agent first — Test Execution runs the scenarios you generated there."
        action={
          <Button as={Link} to="/scenarios">
            Go to Scenario Generation
          </Button>
        }
      />
    );
  }

  const categoryBarData = runResult
    ? Object.entries(runResult.category_scores).map(([key, value]) => ({
        label: humanize(key),
        value: Math.round(value),
      }))
    : [];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader
          title={`Run test suite: ${agent.name}`}
          subtitle={`${agent.domain} — choose which generated scenarios to include in this run.`}
        />

        <div className="space-y-2">
          {scenarioList.map((scenario) => (
            <label
              key={scenario.id}
              className="flex items-center justify-between gap-3 rounded-md border border-line px-3 py-2 text-sm"
            >
              <div className="flex min-w-0 items-center gap-2.5">
                <input
                  type="checkbox"
                  checked={selectedIds.has(scenario.id)}
                  onChange={() => toggle(scenario.id)}
                  disabled={running}
                  className="h-4 w-4 shrink-0 rounded border-line text-accent focus:ring-accent"
                />
                <span className="truncate text-ink-soft">{scenario.user_input}</span>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <span className="text-xs text-ink-faint">{humanize(scenario.category)}</span>
                <RiskBadge level={scenario.severity} />
              </div>
            </label>
          ))}
        </div>

        <div className="mt-4 flex items-center justify-between border-t border-line pt-4">
          <p className="text-sm text-ink-faint">
            {selectedIds.size} of {scenarioList.length} scenario{scenarioList.length === 1 ? "" : "s"} selected
          </p>
          <Button onClick={runSuite} disabled={selectedIds.size === 0} loading={running}>
            <Icon name="play" className="h-4 w-4" />
            Run Test Suite
          </Button>
        </div>

        {running && (
          <div className="mt-3 flex items-center gap-2 text-sm text-ink-faint">
            <span className="h-2 w-2 animate-pulse rounded-full bg-accent" />
            Running {selectedIds.size} test{selectedIds.size === 1 ? "" : "s"} against {agent.name}… {elapsedSeconds}s
          </div>
        )}
        {runError && <ErrorBanner message={runError} className="mt-3" />}
      </Card>

      {runResult && (
        <Card>
          <CardHeader
            title="Reliability results"
            subtitle={`Run ${runResult.run_id}`}
            action={
              <Button as={Link} to={`/report?runId=${runResult.run_id}`} variant="secondary" size="sm">
                Full report
                <Icon name="chevronRight" className="h-3.5 w-3.5" />
              </Button>
            }
          />

          <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-6">
            <ScoreStat label="Total tests" value={runResult.total_tests} />
            <ScoreStat label="Passed" value={runResult.passed} tone="safe" />
            <ScoreStat label="Failed" value={runResult.failed} tone={runResult.failed > 0 ? "danger" : "neutral"} />
            <ScoreStat
              label="Critical failures"
              value={runResult.critical_failures}
              tone={runResult.critical_failures > 0 ? "danger" : "neutral"}
            />
            <ScoreStat
              label="Major failures"
              value={runResult.major_failures}
              tone={runResult.major_failures > 0 ? "warn" : "neutral"}
            />
            <ScoreStat label="Minor failures" value={runResult.minor_failures} />
          </div>

          <div className="mt-4 flex items-center gap-4 rounded-md border border-line bg-canvas p-4">
            <div>
              <p className="text-3xl font-semibold text-ink">{Math.round(runResult.reliability_score)}</p>
              <p className="text-xs text-ink-faint">Reliability score / 100</p>
            </div>
            <div className="h-10 w-px bg-line" />
            <div className="flex-1">
              <CategoryBars data={categoryBarData} color="accent" height={140} />
            </div>
          </div>
        </Card>
      )}

      {runResult && (
        <Card padded={false}>
          <div className="p-4 pb-0">
            <CardHeader title="Test results" subtitle="Click any test to open its execution trace." />
          </div>
          {tracesError && <ErrorBanner message={tracesError} className="mx-4 mb-3" />}
          {!traces && !tracesError && <p className="px-4 pb-4 text-sm text-ink-faint">Loading trace results…</p>}
          {traces && (
            <div>
              {traces.map((trace) => (
                <TestResultRow
                  key={trace.id}
                  trace={trace}
                  scenario={scenarioList.find((s) => s.id === trace.scenario_id)}
                  runId={runId}
                />
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

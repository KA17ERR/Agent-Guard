import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useRunContext } from "../context/RunContext";
import testRunsApi from "../api/testRuns";
import Card, { CardHeader } from "../components/ui/Card";
import Button from "../components/ui/Button";
import Spinner from "../components/ui/Spinner";
import ErrorBanner from "../components/ui/ErrorBanner";
import EmptyState from "../components/ui/EmptyState";
import Icon from "../components/ui/Icon";
import StatusBadge from "../components/ui/StatusBadge";
import { humanize, formatDateTime } from "../utils/format";
import TestResultRow from "./execution/TestResultRow";

const STATUS_TONE = { completed: "safe", running: "warn", failed: "danger" };

// Standalone results view for a single test run — GET /api/test-runs/{run_id}
// for the run summary plus GET /api/test-runs/{run_id}/traces for the
// per-scenario pass/fail rows. Defaults to the most recent run from this
// session (like the Reliability Report page) but also works from a direct
// ?runId= link, since run ids are stable server-side identifiers.
export default function TestResultsPage() {
  const [searchParams] = useSearchParams();
  const { lastRunId, scenarioList } = useRunContext();
  const runId = searchParams.get("runId") || lastRunId;

  const [run, setRun] = useState(null);
  const [runError, setRunError] = useState("");
  const [traces, setTraces] = useState(null);
  const [tracesError, setTracesError] = useState("");

  useEffect(() => {
    if (!runId) return;
    setRun(null);
    setRunError("");
    setTraces(null);
    setTracesError("");

    testRunsApi
      .get(runId)
      .then(setRun)
      .catch((err) => setRunError(err.message));

    testRunsApi
      .traces(runId)
      .then((data) => setTraces(data.traces))
      .catch((err) => setTracesError(err.message));
  }, [runId]);

  if (!runId) {
    return (
      <EmptyState
        icon="list"
        title="No test run to show results for yet"
        description="Run a test suite first — results are read directly from that run's real, persisted traces."
        action={
          <Button as={Link} to="/execution">
            Go to Test Execution
          </Button>
        }
      />
    );
  }

  if (runError) return <ErrorBanner message={runError} />;
  if (!run) return <Spinner label="Loading test run…" />;

  const passRate = run.total_tests > 0 ? Math.round((run.passed_tests / run.total_tests) * 100) : 0;

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="mono text-sm font-semibold text-ink">{run.id}</h2>
              <span className="mono text-xs text-ink-faint">{run.version}</span>
              <StatusBadge label={humanize(run.status)} tone={STATUS_TONE[run.status] || "neutral"} />
            </div>
            <p className="mt-1 text-xs text-ink-faint">
              Started {formatDateTime(run.started_at)}
              {run.completed_at && ` · completed ${formatDateTime(run.completed_at)}`}
            </p>
          </div>
          <Button as={Link} to={`/report?runId=${run.id}`} variant="secondary" size="sm">
            Full reliability report
            <Icon name="chevronRight" className="h-3.5 w-3.5" />
          </Button>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-2.5 sm:grid-cols-4">
          <div className="rounded-md border border-line bg-canvas px-3 py-2.5 text-center">
            <p className="text-xl font-semibold text-ink">{run.total_tests}</p>
            <p className="mt-0.5 text-xs text-ink-faint">Total tests</p>
          </div>
          <div className="rounded-md border border-line bg-canvas px-3 py-2.5 text-center">
            <p className="text-xl font-semibold text-signal-safe">{run.passed_tests}</p>
            <p className="mt-0.5 text-xs text-ink-faint">Passed</p>
          </div>
          <div className="rounded-md border border-line bg-canvas px-3 py-2.5 text-center">
            <p className={`text-xl font-semibold ${run.failed_tests > 0 ? "text-signal-danger" : "text-ink"}`}>
              {run.failed_tests}
            </p>
            <p className="mt-0.5 text-xs text-ink-faint">Failed</p>
          </div>
          <div className="rounded-md border border-line bg-canvas px-3 py-2.5 text-center">
            <p className="text-xl font-semibold text-ink">{passRate}%</p>
            <p className="mt-0.5 text-xs text-ink-faint">Pass rate</p>
          </div>
        </div>
      </Card>

      <Card padded={false}>
        <div className="p-4 pb-0">
          <CardHeader title="Test results" subtitle="Click any test to open its execution trace." />
        </div>
        {tracesError && <ErrorBanner message={tracesError} className="mx-4 mb-3" />}
        {!traces && !tracesError && <Spinner label="Loading trace results…" className="px-4 pb-4" />}
        {traces && traces.length === 0 && (
          <p className="px-4 pb-4 text-sm text-ink-faint">This run has no recorded traces.</p>
        )}
        {traces && traces.length > 0 && (
          <div>
            {traces.map((trace) => (
              <TestResultRow
                key={trace.id}
                trace={trace}
                scenario={scenarioList.find((s) => s.id === trace.scenario_id)}
                runId={run.id}
              />
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

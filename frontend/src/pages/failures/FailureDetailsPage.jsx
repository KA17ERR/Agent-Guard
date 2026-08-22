import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useRunContext } from "../../context/RunContext";
import testRunsApi from "../../api/testRuns";
import tracesApi from "../../api/traces";
import Card, { CardHeader } from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import ErrorBanner from "../../components/ui/ErrorBanner";
import EmptyState from "../../components/ui/EmptyState";
import Icon from "../../components/ui/Icon";
import StatusBadge, { RiskBadge } from "../../components/ui/StatusBadge";
import TraceTimeline from "../../components/trace/TraceTimeline";
import { humanize } from "../../utils/format";
import { buildTimelineSteps } from "./buildTimelineSteps";
import { buildReplayTimelineSteps } from "./buildReplayTimelineSteps";
import ReplayComparisonTable from "./ReplayComparisonTable";

const STATUS_TONE = { passed: "safe", failed: "danger", error: "danger" };

function FailureIndex() {
  const { lastRunId, lastRunResult, scenarioList } = useRunContext();
  const [traces, setTraces] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!lastRunId) return;
    testRunsApi
      .traces(lastRunId)
      .then((data) => setTraces(data.traces))
      .catch((err) => setError(err.message));
  }, [lastRunId]);

  if (!lastRunId) {
    return (
      <EmptyState
        icon="alert"
        title="No test run to inspect yet"
        description="Run a test suite first — failed tests show up here with a full execution trace."
        action={
          <Button as={Link} to="/execution">
            Go to Test Execution
          </Button>
        }
      />
    );
  }

  if (error) return <ErrorBanner message={error} />;
  if (!traces) return <Spinner label="Loading traces…" />;

  const failed = traces.filter((t) => t.final_status !== "passed");

  return (
    <div className="space-y-4">
      <p className="text-sm text-ink-faint">
        Run {lastRunId} · {lastRunResult?.failed ?? failed.length} failed of {lastRunResult?.total_tests ?? traces.length}
      </p>
      {failed.length === 0 ? (
        <EmptyState icon="shield" title="No failures in the last run" description="Every scenario passed — nothing to inspect here." />
      ) : (
        <Card padded={false}>
          {failed.map((trace) => {
            const scenario = scenarioList.find((s) => s.id === trace.scenario_id);
            return (
              <Link
                key={trace.id}
                to={`/failures/${lastRunId}/${trace.id}`}
                className="flex items-center justify-between gap-3 border-b border-line px-4 py-3 last:border-0 hover:bg-canvas"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-ink">
                    {scenario ? humanize(scenario.category) : `Trace ${trace.id}`}
                  </p>
                  <p className="truncate text-xs text-ink-faint">{scenario?.user_input}</p>
                </div>
                <StatusBadge label={humanize(trace.final_status)} tone="danger" />
              </Link>
            );
          })}
        </Card>
      )}
    </div>
  );
}

function TraceDetail({ runId, traceId }) {
  const { getScenario } = useRunContext();
  const [trace, setTrace] = useState(null);
  const [error, setError] = useState("");

  const [replaying, setReplaying] = useState(false);
  const [replayResult, setReplayResult] = useState(null);
  const [replayError, setReplayError] = useState("");

  useEffect(() => {
    setTrace(null);
    setError("");
    setReplayResult(null);
    setReplayError("");
    testRunsApi
      .traces(runId)
      .then((data) => {
        const found = data.traces.find((t) => t.id === traceId);
        if (!found) {
          setError(`Trace '${traceId}' was not found in run '${runId}'.`);
        } else {
          setTrace(found);
        }
      })
      .catch((err) => setError(err.message));
  }, [runId, traceId]);

  const handleReplay = async () => {
    setReplaying(true);
    setReplayError("");
    try {
      const result = await tracesApi.replay(traceId);
      setReplayResult(result);
    } catch (err) {
      setReplayError(err.message);
    } finally {
      setReplaying(false);
    }
  };

  if (error) return <ErrorBanner message={error} />;
  if (!trace) return <Spinner label="Loading trace…" />;

  const scenario = getScenario(trace.scenario_id);
  const steps = buildTimelineSteps(trace, scenario);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-ink-faint">
        <Link to="/failures" className="hover:text-ink">
          Failure Details
        </Link>
        <Icon name="chevronRight" className="h-3.5 w-3.5" />
        <span className="mono text-ink">{traceId}</span>
      </div>

      <Card>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge label={humanize(trace.final_status)} tone={STATUS_TONE[trace.final_status] || "neutral"} />
              {scenario && <StatusBadge label={humanize(scenario.category)} tone="neutral" />}
              {scenario && <RiskBadge level={scenario.severity} />}
            </div>
            {scenario ? (
              <>
                <p className="mt-2 text-sm font-medium text-ink">{scenario.user_input}</p>
                <p className="mt-1 text-sm text-ink-faint">Expected: {scenario.expected_behavior}</p>
              </>
            ) : (
              <p className="mt-2 text-sm text-ink-faint">
                Scenario details unavailable in this session — regenerate scenarios to restore them.
              </p>
            )}
          </div>
          <Button onClick={handleReplay} loading={replaying} variant="secondary">
            <Icon name="play" className="h-4 w-4" />
            Replay
          </Button>
        </div>
        {replayError && <ErrorBanner message={replayError} className="mt-3" />}
      </Card>

      <Card>
        <CardHeader title="Execution timeline" />
        <TraceTimeline steps={steps} />
      </Card>

      {replayResult && (
        <Card>
          <CardHeader
            title="Replay results"
            subtitle={replayResult.note}
            action={
              <StatusBadge
                label={replayResult.deterministic ? "Deterministic" : "Non-deterministic"}
                tone={replayResult.deterministic ? "safe" : "danger"}
              />
            }
          />
          <div className="space-y-5">
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-ink-faint">Replayed timeline</p>
              <TraceTimeline steps={buildReplayTimelineSteps(replayResult)} />
            </div>
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-ink-faint">Tool call comparisons</p>
              <ReplayComparisonTable comparisons={replayResult.tool_call_comparisons} />
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

export default function FailureDetailsPage() {
  const { runId, traceId } = useParams();
  if (runId && traceId) {
    return <TraceDetail runId={runId} traceId={traceId} />;
  }
  return <FailureIndex />;
}

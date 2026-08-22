import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useRunContext } from "../../context/RunContext";
import testRunsApi from "../../api/testRuns";
import Card, { CardHeader } from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import ErrorBanner from "../../components/ui/ErrorBanner";
import EmptyState from "../../components/ui/EmptyState";
import StatusBadge from "../../components/ui/StatusBadge";
import { CategoryPie, CategoryBars, TrendLine } from "../../components/charts/ScoreTrendChart";
import { humanize, formatDateTime } from "../../utils/format";
import CategoryScoreCards from "./CategoryScoreCards";
import TopRisks from "./TopRisks";
import { buildTopRisks } from "./buildTopRisks";

const STATUS_TONE = { completed: "safe", running: "warn", failed: "danger" };

function StatBox({ label, value, tone = "neutral" }) {
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

export default function ReliabilityReportPage() {
  const [searchParams] = useSearchParams();
  const { lastRunId, runHistory } = useRunContext();
  const runId = searchParams.get("runId") || lastRunId;

  const [report, setReport] = useState(null);
  const [reportError, setReportError] = useState("");
  const [traces, setTraces] = useState(null);
  const [tracesError, setTracesError] = useState("");

  useEffect(() => {
    if (!runId) return;
    setReport(null);
    setReportError("");
    setTraces(null);
    setTracesError("");

    testRunsApi
      .report(runId)
      .then(setReport)
      .catch((err) => setReportError(err.message));

    testRunsApi
      .traces(runId)
      .then((data) => setTraces(data.traces))
      .catch((err) => setTracesError(err.message));
  }, [runId]);

  if (!runId) {
    return (
      <EmptyState
        icon="shield"
        title="No test run to report on yet"
        description="Run a test suite first — the reliability report is built from that run's real results."
        action={
          <Button as={Link} to="/execution">
            Go to Test Execution
          </Button>
        }
      />
    );
  }

  if (reportError) return <ErrorBanner message={reportError} />;
  if (!report) return <Spinner label="Loading reliability report…" />;

  const distributionData = Object.entries(report.failures_by_category).map(([key, value]) => ({
    label: humanize(key),
    value,
  }));

  const categoryComparisonData = Object.entries(report.category_scores).map(([key, value]) => ({
    label: humanize(key),
    value: Math.round(value),
  }));

  const trendData = runHistory.map((r, i) => ({
    label: r.version !== "unknown" ? r.version : `Run ${i + 1}`,
    value: Math.round(r.reliability_score),
  }));

  const topRisks = traces ? buildTopRisks(traces) : [];

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-base font-semibold text-ink">{report.agent_name}</h2>
              <span className="mono text-xs text-ink-faint">{report.agent_version}</span>
              <StatusBadge label={humanize(report.status)} tone={STATUS_TONE[report.status] || "neutral"} />
            </div>
            <p className="mt-1 text-xs text-ink-faint">
              Run {report.run_id} · started {formatDateTime(report.started_at)}
              {report.completed_at && ` · completed ${formatDateTime(report.completed_at)}`}
            </p>
          </div>
          <div className="text-right">
            <p className="text-4xl font-bold text-ink">{Math.round(report.reliability_score)}</p>
            <p className="text-xs text-ink-faint">Overall reliability / 100</p>
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader title="Category scores" subtitle="Each dimension scored 0–100 from this run's traces and failures." />
        <CategoryScoreCards categoryScores={report.category_scores} />
      </Card>

      <Card>
        <CardHeader title="Test totals" />
        <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-6">
          <StatBox label="Total tests" value={report.total_tests} />
          <StatBox label="Passed" value={report.passed_tests} tone="safe" />
          <StatBox label="Failed" value={report.failed_tests} tone={report.failed_tests > 0 ? "danger" : "neutral"} />
          <StatBox
            label="Critical failures"
            value={report.critical_failures}
            tone={report.critical_failures > 0 ? "danger" : "neutral"}
          />
          <StatBox
            label="Major failures"
            value={report.major_failures}
            tone={report.major_failures > 0 ? "warn" : "neutral"}
          />
          <StatBox label="Minor failures" value={report.minor_failures} />
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Failure category distribution" subtitle="Share of failures by category, this run." />
          {distributionData.length > 0 ? (
            <CategoryPie data={distributionData} />
          ) : (
            <p className="py-10 text-center text-sm text-ink-faint">No failures recorded in this run.</p>
          )}
        </Card>

        <Card>
          <CardHeader title="Category score comparison" subtitle="Task Success, Safety, Tool Reliability, Goal Adherence, Truthfulness." />
          <CategoryBars data={categoryComparisonData} color="accent" />
        </Card>
      </div>

      <Card>
        <CardHeader
          title="Reliability trend across versions"
          subtitle={
            runHistory.length > 1
              ? "Based on test suites run in this browser session."
              : "Run more test suites in this session to build a trend — only one run so far."
          }
        />
        {trendData.length > 0 ? (
          <TrendLine data={trendData} color="accent" />
        ) : (
          <p className="py-10 text-center text-sm text-ink-faint">No completed runs in this session yet.</p>
        )}
      </Card>

      <Card>
        <CardHeader
          title="Top risks"
          subtitle="The most severe and frequent failure modes found in this run, ranked by severity then occurrence."
        />
        {tracesError && <ErrorBanner message={tracesError} className="mb-3" />}
        {!traces && !tracesError && <Spinner label="Loading failure details…" />}
        {traces && <TopRisks risks={topRisks} />}
      </Card>
    </div>
  );
}

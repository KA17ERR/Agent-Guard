import { Link } from "react-router-dom";
import { RiskBadge } from "../../components/ui/StatusBadge";
import { humanize } from "../../utils/format";

export default function TestResultRow({ trace, scenario, runId }) {
  const passed = trace.final_status === "passed";
  return (
    <Link
      to={`/failures/${runId}/${trace.id}`}
      className="flex items-center justify-between gap-3 border-b border-line px-4 py-3 last:border-0 hover:bg-canvas"
    >
      <div className="flex items-center gap-3 min-w-0">
        <span
          className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
            passed ? "bg-signal-safe-soft text-signal-safe" : "bg-signal-danger-soft text-signal-danger"
          }`}
        >
          {passed ? "✓" : "✗"}
        </span>
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-ink">
            {scenario ? humanize(scenario.category) : "Scenario"}
          </p>
          <p className="truncate text-xs text-ink-faint">
            {scenario?.user_input || `Trace ${trace.id}`}
          </p>
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {scenario && <RiskBadge level={scenario.severity} />}
        <span
          className={`text-xs font-semibold ${passed ? "text-signal-safe" : "text-signal-danger"}`}
        >
          {passed ? "PASS" : "FAIL"}
        </span>
      </div>
    </Link>
  );
}

import StatusBadge from "../../components/ui/StatusBadge";

export default function ReplayComparisonTable({ comparisons }) {
  if (!comparisons || comparisons.length === 0) {
    return <p className="text-sm text-ink-faint">No tool calls were recorded in this trace to replay.</p>;
  }

  return (
    <div className="space-y-3">
      {comparisons.map((c) => (
        <div key={c.step} className="rounded-md border border-line p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="mono text-sm font-medium text-ink">
              Step {c.step} · {c.tool_name}
            </p>
            <StatusBadge label={c.match ? "Match" : "Diverged"} tone={c.match ? "safe" : "danger"} />
          </div>
          <p className="mono mt-1 text-xs text-ink-faint">{JSON.stringify(c.params)}</p>
          <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
            <div className="rounded bg-canvas p-2">
              <p className="text-xs font-medium uppercase tracking-wide text-ink-faint">Original</p>
              <p className="mono mt-1 break-words text-xs text-ink-soft">
                {c.original_success ? JSON.stringify(c.original_data) : `Error: ${c.original_error}`}
              </p>
            </div>
            <div className="rounded bg-canvas p-2">
              <p className="text-xs font-medium uppercase tracking-wide text-ink-faint">Replayed</p>
              <p className="mono mt-1 break-words text-xs text-ink-soft">
                {c.replayed_success ? JSON.stringify(c.replayed_data) : `Error: ${c.replayed_error}`}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

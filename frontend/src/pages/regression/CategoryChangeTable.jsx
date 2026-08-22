import { humanize } from "../../utils/format";

// A change smaller than this (in points, on the 0-100 scale) reads as
// "unchanged" rather than a real improvement/regression — avoids painting
// harmless float noise (e.g. 79.98 vs 80.00) green or red.
const UNCHANGED_THRESHOLD = 0.5;

function classify(change) {
  if (change > UNCHANGED_THRESHOLD) return "improvement";
  if (change < -UNCHANGED_THRESHOLD) return "regression";
  return "unchanged";
}

const ROW_STYLE = {
  improvement: { emoji: "🟢", tone: "text-signal-safe", bg: "bg-signal-safe-soft" },
  regression: { emoji: "🔴", tone: "text-signal-danger", bg: "bg-signal-danger-soft" },
  unchanged: { emoji: "🟡", tone: "text-ink-faint", bg: "bg-canvas" },
};

function ChangeRow({ label, change }) {
  const status = classify(change.change);
  const style = ROW_STYLE[status];
  const sign = change.change > 0 ? "+" : "";
  return (
    <tr className="border-b border-line last:border-0">
      <td className="px-4 py-3 text-sm font-medium text-ink">{label}</td>
      <td className="px-4 py-3 text-sm text-ink-soft">{change.version_a.toFixed(1)}</td>
      <td className="px-4 py-3 text-sm text-ink-soft">{change.version_b.toFixed(1)}</td>
      <td className={`px-4 py-3 text-sm font-semibold ${style.tone}`}>
        {sign}
        {change.change.toFixed(1)}
      </td>
      <td className="px-4 py-3">
        <span className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ${style.bg} ${style.tone}`}>
          {style.emoji} {humanize(status)}
        </span>
      </td>
    </tr>
  );
}

// `dimensions` is [{ key, label, change: DimensionChange }], `overall` is the
// top-line DimensionChange shown as its own emphasized row.
export default function CategoryChangeTable({ overall, dimensions }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-line">
      <table className="w-full min-w-[560px] text-left text-sm">
        <thead>
          <tr className="border-b border-line bg-canvas text-xs uppercase tracking-wide text-ink-faint">
            <th className="px-4 py-2.5 font-medium">Dimension</th>
            <th className="px-4 py-2.5 font-medium">Version 1</th>
            <th className="px-4 py-2.5 font-medium">Version 2</th>
            <th className="px-4 py-2.5 font-medium">Difference</th>
            <th className="px-4 py-2.5 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          <ChangeRow label="Overall reliability" change={overall} />
          {dimensions.map((d) => (
            <ChangeRow key={d.key} label={d.label} change={d.change} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

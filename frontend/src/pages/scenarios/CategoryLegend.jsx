import { SCENARIO_CATEGORIES } from "../../utils/constants";
import { humanize } from "../../utils/format";

// Static taxonomy overview shown before generation — mirrors the backend's
// VALID_CATEGORIES exactly (see backend/app/schemas/scenario.py). Not
// generated content: this is the fixed set AgentGuard always tests
// against, shown so the user knows what "Generate Test Suite" will cover.
export default function CategoryLegend() {
  return (
    <div className="flex flex-wrap gap-1.5">
      {SCENARIO_CATEGORIES.map((c) => (
        <span
          key={c.value}
          className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${
            c.adversarial
              ? "border-signal-danger/25 bg-signal-danger-soft text-signal-danger"
              : "border-line bg-canvas text-ink-soft"
          }`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${c.adversarial ? "bg-signal-danger" : "bg-signal-neutral"}`} />
          {humanize(c.value)}
        </span>
      ))}
    </div>
  );
}

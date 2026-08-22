import { humanize } from "../../utils/format";

/**
 * Builds <TraceTimeline /> steps from a real TraceReplayResponse
 * (POST /api/traces/{trace_id}/replay). Mirrors buildTimelineSteps' event
 * handling but adds a match/mismatch badge on tool-call steps, since replay
 * re-executes each mocked tool call and reports whether it reproduced the
 * original result (see backend/app/schemas/replay.py).
 */
export function buildReplayTimelineSteps(replay) {
  const steps = [];

  for (const event of replay.timeline || []) {
    if (event.type === "llm_decision") {
      const d = event.data || {};
      steps.push({
        id: `replay-${event.step}-decision`,
        title: `Agent Decision (step ${event.step})`,
        detail: d.thought || null,
        tone: "accent",
        icon: "cpu",
        meta: [
          { label: "Action", value: d.action },
          ...(d.action === "call_tool" ? [{ label: "Tool", value: d.tool_name }] : []),
        ],
      });
    } else if (event.type === "tool_call") {
      const d = event.data || {};
      const dangerous = d.destructive || d.risk_level === "high" || d.risk_level === "critical";
      const badges = [
        { label: humanize(d.risk_level) + " risk", tone: dangerous ? "danger" : "safe" },
        { label: d.destructive ? "Destructive" : "Non-destructive", tone: d.destructive ? "danger" : "neutral" },
      ];
      if (event.replay_matches_original !== null && event.replay_matches_original !== undefined) {
        badges.push({
          label: event.replay_matches_original ? "Replay matched" : "Replay diverged",
          tone: event.replay_matches_original ? "safe" : "danger",
        });
      }
      steps.push({
        id: `replay-${event.step}-tool-call`,
        title: `Tool Call: ${d.tool_name}`,
        tone: event.replay_matches_original === false ? "danger" : dangerous ? "danger" : "neutral",
        icon: "cpu",
        badges,
        meta: [{ label: "Parameters", value: JSON.stringify(d.params || {}) }],
      });
    } else if (event.type === "final_response") {
      steps.push({
        id: `replay-${event.step}-final`,
        title: "Final Response",
        detail: (event.data || {}).response || "(empty response)",
        tone: "accent",
        icon: "chevronRight",
      });
    } else if (event.type === "error") {
      steps.push({
        id: `replay-${event.step}-error`,
        title: "Final Response",
        detail: `Execution error: ${(event.data || {}).error || "unknown error"}`,
        tone: "danger",
        icon: "alert",
      });
    }
  }

  return steps;
}

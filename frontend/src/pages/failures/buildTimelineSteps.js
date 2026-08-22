import { humanize } from "../../utils/format";

/**
 * Builds the step list for <TraceTimeline /> from real data only:
 *   - scenario.user_input             -> "User Input"
 *   - trace.events[type=llm_decision] -> "Agent Decision"
 *   - trace.events[type=tool_call]    -> "Tool Call" + "Mock Tool Response"
 *     (the backend records one fused event per tool call -- see
 *     backend/app/agent/executor.py ToolCallRecord -- so this splits that
 *     single real event into two display nodes to match the requested
 *     Tool Call -> Mock Tool Response narrative, without adding any data)
 *   - trace.events[type=final_response] -> "Final Response"
 *   - trace.events[type=error]          -> "Final Response" (error variant)
 *   - trace.failures                    -> "Failure Evaluation" (one per failure)
 *
 * Nothing here is generated or guessed: every field shown comes directly
 * from the trace/scenario objects returned by the backend.
 */
export function buildTimelineSteps(trace, scenario) {
  const steps = [];

  steps.push({
    id: "user-input",
    title: "User Input",
    detail: scenario ? scenario.user_input : "Scenario details unavailable for this trace (regenerate from Scenario Generation to restore them).",
    tone: "neutral",
    icon: "chevronRight",
  });

  for (const event of trace.events || []) {
    if (event.type === "llm_decision") {
      const d = event.data || {};
      steps.push({
        id: `step-${event.step}-decision`,
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
      steps.push({
        id: `step-${event.step}-tool-call`,
        title: `Tool Call: ${d.tool_name}`,
        tone: dangerous ? "danger" : "neutral",
        icon: "cpu",
        badges: [
          { label: humanize(d.risk_level) + " risk", tone: dangerous ? "danger" : "safe" },
          { label: d.destructive ? "Destructive" : "Non-destructive", tone: d.destructive ? "danger" : "neutral" },
        ],
        meta: [{ label: "Parameters", value: JSON.stringify(d.params || {}) }],
      });
      steps.push({
        id: `step-${event.step}-tool-response`,
        title: "Mock Tool Response",
        tone: d.success ? "safe" : "warn",
        icon: d.success ? "chevronRight" : "alert",
        badges: [{ label: d.success ? "Success" : "Failed", tone: d.success ? "safe" : "warn" }],
        meta: d.success
          ? [{ label: "Response", value: JSON.stringify(d.data || {}) }]
          : [{ label: "Error", value: d.error || "unknown error" }],
      });
    } else if (event.type === "final_response") {
      steps.push({
        id: `step-${event.step}-final`,
        title: "Final Response",
        detail: (event.data || {}).response || "(empty response)",
        tone: "accent",
        icon: "chevronRight",
      });
    } else if (event.type === "error") {
      steps.push({
        id: `step-${event.step}-error`,
        title: "Final Response",
        detail: `Execution error: ${(event.data || {}).error || "unknown error"}`,
        tone: "danger",
        icon: "alert",
      });
    }
  }

  const hasTerminalEvent = (trace.events || []).some(
    (e) => e.type === "final_response" || e.type === "error"
  );
  if (!hasTerminalEvent) {
    steps.push({
      id: "no-final-response",
      title: "Final Response",
      detail: "No final response was produced -- the agent exceeded the maximum tool-call step budget.",
      tone: "danger",
      icon: "alert",
    });
  }

  const failures = trace.failures || [];
  if (failures.length > 0) {
    for (const f of failures) {
      steps.push({
        id: `failure-${f.id}`,
        title: `Failure Evaluation: ${humanize(f.category)}`,
        detail: f.explanation,
        tone: f.severity === "critical" || f.severity === "high" ? "danger" : "warn",
        icon: "shield",
        badges: [{ label: `${humanize(f.severity)} severity`, tone: f.severity === "critical" || f.severity === "high" ? "danger" : "warn" }],
        meta: [
          { label: "Recommendation", value: f.recommendation },
          { label: "Confidence", value: `${Math.round(f.confidence * 100)}%` },
        ],
      });
    }
  } else if (trace.final_status !== "passed") {
    steps.push({
      id: "failure-status-only",
      title: "Failure Evaluation",
      detail: `Flagged as "${trace.final_status}" by the test runner, though no individual failure record was attached.`,
      tone: "warn",
      icon: "shield",
    });
  }

  return steps;
}

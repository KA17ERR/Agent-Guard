// Mirrors backend/app/schemas/tool.py VALID_RISK_LEVELS. Order is
// low -> critical so it can drive both <select> options and severity rails.
export const RISK_LEVELS = ["low", "medium", "high", "critical"];

// Mirrors backend/app/schemas/failure.py RULE_BASED_CATEGORIES +
// LLM_BASED_CATEGORIES exactly (10 categories — the backend does not
// implement a "timeout" category, despite it appearing in the original
// product brief).
export const FAILURE_CATEGORIES = [
  "tool_misuse",
  "tool_loop",
  "unsafe_destructive_action",
  "unauthorized_action",
  "invalid_tool_call",
  "hallucination",
  "goal_drift",
  "prompt_injection",
  "instruction_hijacking",
  "task_failure",
];

// Mirrors backend/app/schemas/scenario.py VALID_CATEGORIES — the scenario
// generation taxonomy is a superset of the failure taxonomy (it also
// includes the two non-adversarial categories used as a baseline).
export const SCENARIO_CATEGORIES = [
  { value: "normal_task", adversarial: false },
  { value: "ambiguous_instruction", adversarial: false },
  { value: "prompt_injection", adversarial: true },
  { value: "instruction_hijacking", adversarial: true },
  { value: "tool_misuse", adversarial: true },
  { value: "tool_loop", adversarial: true },
  { value: "hallucination", adversarial: true },
  { value: "goal_drift", adversarial: true },
  { value: "unsafe_destructive_action", adversarial: true },
  { value: "unauthorized_action", adversarial: true },
];

// Left-sidebar navigation, in the order defined by the product's core
// workflow (Agent Configuration -> Scenario Generation -> ... -> Regression).
export const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: "grid" },
  { to: "/agents", label: "Agent Configuration", icon: "cpu" },
  { to: "/scenarios", label: "Scenario Generation", icon: "flask" },
  { to: "/execution", label: "Test Execution", icon: "play" },
  { to: "/results", label: "Test Results", icon: "list" },
  { to: "/failures", label: "Failure Details", icon: "alert" },
  { to: "/report", label: "Reliability Report", icon: "shield" },
  { to: "/regression", label: "Regression", icon: "trend" },
];

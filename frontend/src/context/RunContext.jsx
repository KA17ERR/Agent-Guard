import { createContext, useContext, useEffect, useMemo, useState } from "react";

/**
 * Scenarios and test runs are also fetched fresh from the backend where
 * possible (GET /api/agents/{id}/scenarios; test runs still have no list
 * endpoint, only create-one/get-by-id/regression-compare). This context is
 * kept as a session-scoped cache on top of that so scenario/run details
 * stay available across pages within one browsing session (e.g. the Trace
 * Viewer showing a scenario's user_input) without every page having to
 * re-fetch, and so a mid-workflow refresh doesn't lose in-progress state.
 * Every downstream page still tolerates this being empty (e.g. a fresh
 * tab) and degrades to "data unavailable" rather than fabricating anything.
 *
 * Scenarios are cached per agent (scenariosByAgent: { [agentId]: { [scenarioId]: scenario } }),
 * not in one flat pool -- otherwise once you'd generated scenarios for two
 * or more agents in the same session, `scenarioList` would return every
 * agent's scenarios merged together with no way to tell which belonged to
 * which agent. `scenarioList` below always reflects only the *currently
 * selected* agent.
 */
const STORAGE_KEY = "agentguard_run_state";
const MAX_HISTORY = 25;

const RunContext = createContext(null);

function loadInitial() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function RunProvider({ children }) {
  const initial = loadInitial();

  const [agent, setAgent] = useState(initial?.agent || null);
  const [scenariosByAgent, setScenariosByAgent] = useState(initial?.scenariosByAgent || {});
  const [lastRunId, setLastRunId] = useState(initial?.lastRunId || null);
  const [lastRunResult, setLastRunResult] = useState(initial?.lastRunResult || null);
  const [runHistory, setRunHistory] = useState(initial?.runHistory || []);

  useEffect(() => {
    try {
      sessionStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ agent, scenariosByAgent, lastRunId, lastRunResult, runHistory })
      );
    } catch {
      // sessionStorage can fail (private browsing, quota) -- non-fatal,
      // the app still works within this render, just won't survive reload.
    }
  }, [agent, scenariosByAgent, lastRunId, lastRunResult, runHistory]);

  const value = useMemo(
    () => ({
      agent,
      scenarioList: Object.values(scenariosByAgent[agent?.id] || {}),
      lastRunId,
      lastRunResult,
      // Filtered to the currently selected agent -- runHistory is stored
      // flat (all agents, whole session) so it survives agent switches,
      // but Regression/Reliability Report should only ever compare runs
      // that belong to the same agent, so callers get the filtered view
      // here. Runs recorded before this field existed have agent_id: null
      // and are treated as belonging to no agent (won't show anywhere)
      // rather than leaking into every agent's history.
      runHistory: runHistory.filter((r) => r.agent_id === agent?.id),

      setAgentInfo: (a) => setAgent(a),

      addScenarios: (agentInfo, scenarios) => {
        // Guard against being called before the agent has fully loaded
        // (agentInfo missing or without an id) — bail out instead of
        // crashing or wiping out whatever agent is already selected.
        if (!agentInfo?.id) return;
        setAgent(agentInfo);
        setScenariosByAgent((prev) => {
          const agentId = agentInfo.id;
          const existing = prev[agentId] || {};
          const next = { ...existing };
          for (const s of scenarios) next[s.id] = s;
          return { ...prev, [agentId]: next };
        });
      },

      recordRun: (runId, result, agentVersion) => {
        setLastRunId(runId);
        setLastRunResult(result);
        setRunHistory((prev) => {
          if (prev.some((r) => r.run_id === runId)) return prev;
          const next = [
            ...prev,
            {
              run_id: runId,
              agent_id: agent?.id || null,
              version: agentVersion || "unknown",
              reliability_score: result.reliability_score,
              total_tests: result.total_tests,
              passed: result.passed,
              failed: result.failed,
            },
          ];
          return next.slice(-MAX_HISTORY);
        });
      },

      // Looked up by scenario id alone (ids are unique across agents), so
      // this searches every agent's cached scenarios, not just the
      // currently selected one -- e.g. the Regression page can be diffing
      // scenarios from a run that isn't for whichever agent is "current".
      getScenario: (scenarioId) => {
        for (const scenarios of Object.values(scenariosByAgent)) {
          if (scenarios[scenarioId]) return scenarios[scenarioId];
        }
        return null;
      },
    }),
    [agent, scenariosByAgent, lastRunId, lastRunResult, runHistory]
  );

  return <RunContext.Provider value={value}>{children}</RunContext.Provider>;
}

export function useRunContext() {
  const ctx = useContext(RunContext);
  if (!ctx) throw new Error("useRunContext must be used within a RunProvider");
  return ctx;
}

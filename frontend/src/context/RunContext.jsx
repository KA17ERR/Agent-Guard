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
  const [scenariosById, setScenariosById] = useState(initial?.scenariosById || {});
  const [lastRunId, setLastRunId] = useState(initial?.lastRunId || null);
  const [lastRunResult, setLastRunResult] = useState(initial?.lastRunResult || null);
  const [runHistory, setRunHistory] = useState(initial?.runHistory || []);

  useEffect(() => {
    try {
      sessionStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ agent, scenariosById, lastRunId, lastRunResult, runHistory })
      );
    } catch {
      // sessionStorage can fail (private browsing, quota) -- non-fatal,
      // the app still works within this render, just won't survive reload.
    }
  }, [agent, scenariosById, lastRunId, lastRunResult, runHistory]);

  const value = useMemo(
    () => ({
      agent,
      scenariosById,
      scenarioList: Object.values(scenariosById),
      lastRunId,
      lastRunResult,
      runHistory,

      setAgentInfo: (a) => setAgent(a),

      addScenarios: (agentInfo, scenarios) => {
        setAgent(agentInfo);
        setScenariosById((prev) => {
          const next = { ...prev };
          for (const s of scenarios) next[s.id] = s;
          return next;
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

      getScenario: (scenarioId) => scenariosById[scenarioId] || null,
    }),
    [agent, scenariosById, lastRunId, lastRunResult, runHistory]
  );

  return <RunContext.Provider value={value}>{children}</RunContext.Provider>;
}

export function useRunContext() {
  const ctx = useContext(RunContext);
  if (!ctx) throw new Error("useRunContext must be used within a RunProvider");
  return ctx;
}

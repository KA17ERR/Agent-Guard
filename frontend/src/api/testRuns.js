import apiClient from "./client";

// Wraps the Test Runner endpoints (backend/app/api/test_runs.py). The
// create call is synchronous on the backend — it blocks until every
// scenario has been executed and scored, then returns the full result in
// one response. There is no progress-polling endpoint, so the frontend
// must not simulate incremental progress while this call is in flight.
const testRunsApi = {
  create: ({ agentId, scenarioIds }) =>
    apiClient
      .post("/api/test-runs", { agent_id: agentId, scenario_ids: scenarioIds })
      .then((res) => res.data),

  get: (runId) => apiClient.get(`/api/test-runs/${runId}`).then((res) => res.data),

  traces: (runId) =>
    apiClient.get(`/api/test-runs/${runId}/traces`).then((res) => res.data),

  report: (runId) =>
    apiClient.get(`/api/test-runs/${runId}/report`).then((res) => res.data),
};

export default testRunsApi;

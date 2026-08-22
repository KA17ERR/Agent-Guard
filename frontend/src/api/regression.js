import apiClient from "./client";

// Wraps GET /api/agents/{agent_id}/regression (backend/app/api/regression.py).
// Exactly one selector pair should be provided per run: either a run id or
// a version string, never both for the same side.
const regressionApi = {
  compare: (agentId, { runIdA, runIdB, versionA, versionB } = {}) => {
    const params = {};
    if (runIdA) params.run_id_a = runIdA;
    if (runIdB) params.run_id_b = runIdB;
    if (versionA) params.version_a = versionA;
    if (versionB) params.version_b = versionB;
    return apiClient
      .get(`/api/agents/${agentId}/regression`, { params })
      .then((res) => res.data);
  },
};

export default regressionApi;

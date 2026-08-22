import apiClient from "./client";

// Wraps both scenario endpoints exposed by the backend
// (backend/app/api/scenarios.py, backend/app/api/agents.py):
//   - POST /api/scenarios/generate           generate new scenarios
//   - GET  /api/agents/{agentId}/scenarios   fetch previously generated
//                                             scenarios back from the DB
const scenariosApi = {
  generate: ({ agentId, numberOfScenarios }) =>
    apiClient
      .post("/api/scenarios/generate", {
        agent_id: agentId,
        number_of_scenarios: numberOfScenarios,
      })
      .then((res) => res.data),

  list: (agentId) =>
    apiClient.get(`/api/agents/${agentId}/scenarios`).then((res) => res.data),
};

export default scenariosApi;

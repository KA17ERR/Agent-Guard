import apiClient from "./client";

// Thin wrappers around the Agent Configuration endpoints
// (backend/app/api/agents.py). Kept separate from the Axios instance so
// call sites read like plain function calls: agentsApi.list(), etc.
const agentsApi = {
  list: () => apiClient.get("/api/agents").then((res) => res.data),

  get: (agentId) => apiClient.get(`/api/agents/${agentId}`).then((res) => res.data),

  create: (payload) => apiClient.post("/api/agents", payload).then((res) => res.data),

  update: (agentId, payload) =>
    apiClient.put(`/api/agents/${agentId}`, payload).then((res) => res.data),

  remove: (agentId) => apiClient.delete(`/api/agents/${agentId}`),

  listTools: (agentId) =>
    apiClient.get(`/api/agents/${agentId}/tools`).then((res) => res.data),

  createTool: (agentId, payload) =>
    apiClient.post(`/api/agents/${agentId}/tools`, payload).then((res) => res.data),
};

export default agentsApi;

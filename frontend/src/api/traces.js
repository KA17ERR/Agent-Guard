import apiClient from "./client";

// Wraps POST /api/traces/{trace_id}/replay (backend/app/api/traces.py).
const tracesApi = {
  replay: (traceId) =>
    apiClient.post(`/api/traces/${traceId}/replay`).then((res) => res.data),
};

export default tracesApi;

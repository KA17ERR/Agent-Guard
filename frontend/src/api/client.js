import axios from "axios";

// All requests go through this single Axios instance so the backend base
// URL and error shape only need to be handled in one place. The backend
// (see backend/app/main.py) returns errors as { error, status_code }.
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// Normalize error handling: every rejected promise carries a readable
// `.message` regardless of whether the failure came from the network or
// from the API's JSON error body.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const data = error.response.data;
      const detail =
        (typeof data?.error === "string" && data.error) ||
        (Array.isArray(data?.detail) &&
          data.detail.map((d) => d.msg || JSON.stringify(d)).join("; ")) ||
        (typeof data?.detail === "string" && data.detail) ||
        `Request failed with status ${error.response.status}`;
      error.message = detail;
    } else if (error.request) {
      error.message = "Could not reach the AgentGuard API. Is the backend running?";
    }
    return Promise.reject(error);
  }
);

export default apiClient;

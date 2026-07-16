import axios from "axios";

// In Codespaces, the frontend and backend run on different forwarded ports.
// VITE_API_URL is read from frontend/.env (see .env.example) so you can point
// this at whatever port/URL your backend is forwarded to.
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({ baseURL: API_URL });

export const getStats = () => api.get("/api/stats").then((r) => r.data);
export const listIncidents = () => api.get("/api/incidents").then((r) => r.data);
export const getIncident = (id) => api.get(`/api/incidents/${id}`).then((r) => r.data);
export const triggerScan = () => api.post("/api/incidents/scan").then((r) => r.data);
export const createIncident = (payload) => api.post("/api/incidents", payload).then((r) => r.data);
export const investigateIncident = (id) =>
  api.post(`/api/incidents/${id}/investigate`).then((r) => r.data);
export const getLineageGraph = () => api.get("/api/lineage-graph").then((r) => r.data);
export const searchKnowledge = (q) => api.get("/api/knowledge", { params: { q } }).then((r) => r.data);
export const sendChat = (message) => api.post("/api/chat", { message }).then((r) => r.data);

export default api;

import axios from "axios";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000";

export const api = axios.create({ baseURL: API_BASE });

export const createInteraction = (data) => api.post("/interactions/", data);
export const listInteractions = () => api.get("/interactions/");
export const updateInteraction = (id, data) => api.put(`/interactions/${id}`, data);
export const getHcpHistory = (name) => api.get(`/interactions/hcp/${name}/history`);
export const getHcpSummary = (name) => api.get(`/interactions/hcp/${name}/summary`);
export const scheduleFollowup = (id, days, note) =>
  api.post(`/interactions/${id}/followup`, null, { params: { days_from_now: days, note } });
export const sendChatMessage = (message, rep_name) =>
  api.post("/chat/", { message, rep_name });

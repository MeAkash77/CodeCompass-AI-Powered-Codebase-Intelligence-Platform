import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL;

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

api.interceptors.request.use(
  (config) => {
    const sessionId = localStorage.getItem("sessionId");
    if (sessionId) {
      config.headers["X-Session-Id"] = sessionId;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default api;

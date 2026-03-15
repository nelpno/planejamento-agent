import axios from 'axios';

// Fix #14: Use relative path by default (works through nginx proxy)
// Override with VITE_API_URL for local dev without nginx
const API_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: `${API_URL}/api`,
});

export default api;
export { API_URL };

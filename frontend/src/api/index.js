import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const register = (data) => api.post('/api/auth/register', data);
export const login = (data) => api.post('/api/auth/login', data);
export const getMe = () => api.get('/api/auth/me');

// Competitors
export const getCompetitors = () => api.get('/api/competitors');
export const getCompetitor = (id) => api.get(`/api/competitors/${id}`);
export const createCompetitor = (data) => api.post('/api/competitors', data);
export const updateCompetitor = (id, data) => api.put(`/api/competitors/${id}`, data);
export const deleteCompetitor = (id) => api.delete(`/api/competitors/${id}`);

// Reports
export const runScan = () => api.post('/api/reports/run');
export const getReports = (limit = 10) => api.get(`/api/reports?limit=${limit}`);
export const getReport = (id) => api.get(`/api/reports/${id}`);
export const getLatestSummary = () => api.get('/api/reports/latest/summary');

// Dashboard
export const getDashboardStats = () => api.get('/api/dashboard/stats');

export default api;

import axios from 'axios';
import type { Token, User } from '../types';

const API_BASE_URL = '/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          throw new Error('No refresh token');
        }

        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token, refresh_token } = response.data as Token;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (email: string, username: string, password: string) =>
    api.post<User>('/auth/register', { email, username, password }),

  login: (email: string, password: string) =>
    api.post<Token>('/auth/login', null, {
      params: { username: email, password },
    }),

  getCurrentUser: () => api.get<User>('/auth/me'),

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
};

// Dashboard API
export const dashboardAPI = {
  getSummary: () => api.get('/dashboard/'),
};

// Transactions API
export const transactionsAPI = {
  getAll: (params?: Record<string, string | number>) =>
    api.get('/transactions/', { params }),
  getById: (id: number) => api.get(`/transactions/${id}`),
  create: (data: Record<string, unknown>) => api.post('/transactions/', data),
  update: (id: number, data: Record<string, unknown>) =>
    api.put(`/transactions/${id}`, data),
  delete: (id: number) => api.delete(`/transactions/${id}`),
};

// Categories API
export const categoriesAPI = {
  getAll: () => api.get('/categories/'),
  getById: (id: number) => api.get(`/categories/${id}`),
  create: (data: Record<string, unknown>) => api.post('/categories/', data),
  update: (id: number, data: Record<string, unknown>) =>
    api.put(`/categories/${id}`, data),
  delete: (id: number) => api.delete(`/categories/${id}`),
};

// Recurring Payments API
export const recurringPaymentsAPI = {
  getAll: () => api.get('/recurring-payments/'),
  create: (data: Record<string, unknown>) =>
    api.post('/recurring-payments/', data),
  update: (id: number, data: Record<string, unknown>) =>
    api.put(`/recurring-payments/${id}`, data),
  delete: (id: number) => api.delete(`/recurring-payments/${id}`),
};

// Budgets API
export const budgetsAPI = {
  getAll: () => api.get('/budgets/'),
  create: (data: Record<string, unknown>) => api.post('/budgets/', data),
  update: (id: number, data: Record<string, unknown>) =>
    api.put(`/budgets/${id}`, data),
  delete: (id: number) => api.delete(`/budgets/${id}`),
};

// Goals API
export const goalsAPI = {
  getAll: () => api.get('/goals/'),
  create: (data: Record<string, unknown>) => api.post('/goals/', data),
  update: (id: number, data: Record<string, unknown>) =>
    api.put(`/goals/${id}`, data),
  delete: (id: number) => api.delete(`/goals/${id}`),
};

// Analytics API
export const analyticsAPI = {
  getAnalytics: (months?: number) =>
    api.get('/analytics/', { params: { months } }),
};

// Insights API
export const insightsAPI = {
  getInsights: () => api.get('/insights/'),
};

// Export API
export const exportAPI = {
  exportCSV: () => api.get('/export/csv', { responseType: 'blob' }),
  exportXLSX: () => api.get('/export/xlsx', { responseType: 'blob' }),
  importCSV: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/export/csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

export default api;

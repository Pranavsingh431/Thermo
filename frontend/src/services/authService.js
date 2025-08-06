import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
});

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authService = {
  // Login user
  async login(username, password) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await api.post('/auth/login', formData);
    const { access_token } = response.data;
    
    localStorage.setItem('token', access_token);
    return response.data;
  },

  // Get current user info
  async getCurrentUser() {
    const response = await api.get('/auth/me');
    return response.data;
  },

  // Verify token
  async verifyToken() {
    const response = await api.get('/auth/me');
    return response.data;
  },

  // Logout
  logout() {
    localStorage.removeItem('token');
  },

  // Check if user is logged in
  isAuthenticated() {
    return !!localStorage.getItem('token');
  },

  // Get stored token
  getToken() {
    return localStorage.getItem('token');
  }
};

export default api; 
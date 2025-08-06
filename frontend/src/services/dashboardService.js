import api from './authService';

export const dashboardService = {
  // Get dashboard statistics
  async getStats() {
    const response = await api.get('/dashboard/stats');
    return response.data;
  },

  // Get recent analyses
  async getRecentAnalyses(limit = 10) {
    const response = await api.get(`/dashboard/recent-analyses?limit=${limit}`);
    return response.data;
  },

  // Get substations summary
  async getSubstations() {
    const response = await api.get('/dashboard/substations');
    return response.data;
  },

  // Get thermal scans
  async getThermalScans(params = {}) {
    const queryParams = new URLSearchParams(params).toString();
    const response = await api.get(`/dashboard/thermal-scans?${queryParams}`);
    return response.data;
  },

  // Get analysis detections
  async getAnalysisDetections(analysisId) {
    const response = await api.get(`/dashboard/analysis/${analysisId}/detections`);
    return response.data;
  }
}; 
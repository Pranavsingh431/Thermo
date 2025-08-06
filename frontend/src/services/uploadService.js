import api from './authService';

export const uploadService = {
  // Upload thermal images
  async uploadThermalImages(files, metadata = {}) {
    const formData = new FormData();
    
    // Add files
    for (const file of files) {
      formData.append('files', file);
    }
    
    // Add metadata
    formData.append('ambient_temperature', metadata.ambientTemperature || '34.0');
    formData.append('notes', metadata.notes || 'React frontend upload');
    
    const response = await api.post('/upload/thermal-images', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: metadata.onProgress || undefined,
    });
    
    return response.data;
  },

  // Get batch status
  async getBatchStatus(batchId) {
    const response = await api.get(`/upload/batch/${batchId}/status`);
    return response.data;
  },

  // Get batch files
  async getBatchFiles(batchId) {
    const response = await api.get(`/upload/batch/${batchId}/files`);
    return response.data;
  },

  // Delete batch (admin only)
  async deleteBatch(batchId) {
    const response = await api.delete(`/upload/batch/${batchId}`);
    return response.data;
  }
}; 